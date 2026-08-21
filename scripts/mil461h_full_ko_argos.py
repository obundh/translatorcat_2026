from __future__ import annotations

import json
import re
import sys
import time
import types
from pathlib import Path

# Argos imports Stanza, which uses the real PyTorch dependency installed with
# Argos.  Import it before stubbing the Transformers-only Marian fallback.
import argostranslate.package
import argostranslate.translate

transformers_stub = types.ModuleType("transformers")
transformers_stub.AutoModelForSeq2SeqLM = object
transformers_stub.AutoTokenizer = object
sys.modules.setdefault("transformers", transformers_stub)

import mil461h_full_ko as base


class ArgosTranslator:
    """Fast offline EN→KO translator using the Argos / CTranslate2 package."""

    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache: dict[str, str] = {}
        if cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}
        self.translation = None
        self.model_name = "Argos Translate en→ko"

    def load(self) -> None:
        installed = argostranslate.translate.get_installed_languages()
        en = next((x for x in installed if x.code == "en"), None)
        ko = next((x for x in installed if x.code == "ko"), None)
        if en is None or ko is None:
            print("Installing Argos English→Korean package", flush=True)
            argostranslate.package.update_package_index()
            packages = argostranslate.package.get_available_packages()
            candidates = [p for p in packages if p.from_code == "en" and p.to_code == "ko"]
            if not candidates:
                raise RuntimeError("Argos English→Korean package is unavailable")
            package = sorted(candidates, key=lambda p: str(getattr(p, "package_version", "")), reverse=True)[0]
            download_path = package.download()
            argostranslate.package.install_from_path(download_path)
            installed = argostranslate.translate.get_installed_languages()
            en = next(x for x in installed if x.code == "en")
            ko = next(x for x in installed if x.code == "ko")
        self.translation = en.get_translation(ko)
        print("Argos translator ready", flush=True)

    @staticmethod
    def _split(text: str, max_chars: int = 750) -> list[str]:
        if len(text) <= max_chars:
            return [text]
        pieces = re.split(r"(?<=[.!?;:])\s+|\n+", text)
        chunks: list[str] = []
        cur = ""
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            candidate = f"{cur} {piece}".strip() if cur else piece
            if len(candidate) <= max_chars:
                cur = candidate
                continue
            if cur:
                chunks.append(cur)
            while len(piece) > max_chars:
                cut = piece.rfind(" ", 0, max_chars)
                if cut < max_chars // 2:
                    cut = max_chars
                chunks.append(piece[:cut].strip())
                piece = piece[cut:].strip()
            cur = piece
        if cur:
            chunks.append(cur)
        return chunks or [text]

    def translate_all(self, texts, batch_size: int = 1) -> None:
        pending = [t for t in texts if t not in self.cache]
        print(f"Argos cache={len(self.cache)}; pending blocks={len(pending)}", flush=True)
        start = time.time()
        for idx, original in enumerate(pending, start=1):
            if not base.should_translate(original):
                self.cache[original] = original
                continue
            toc = base.TOC_RE.match(original)
            source = toc.group(1).strip() if toc else original
            protected, mapping = base.protect_text(source)
            translated_parts = [self.translation.translate(chunk) for chunk in self._split(protected)]
            translated = base.restore_text(" ".join(translated_parts), mapping)
            if toc:
                translated = f"{translated} {toc.group(2)}{toc.group(3)}"
            if not base.KOREAN_RE.search(translated):
                translated = original
            self.cache[original] = translated
            if idx % 50 == 0 or idx == len(pending):
                self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")
                elapsed = max(1.0, time.time() - start)
                print(f"Translated {idx}/{len(pending)} blocks ({idx/elapsed:.2f} blocks/s)", flush=True)
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, text: str) -> str:
        return self.cache.get(text, text)


base.Translator = ArgosTranslator

if __name__ == "__main__":
    base.main()
