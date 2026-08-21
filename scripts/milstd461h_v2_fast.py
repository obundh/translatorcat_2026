from __future__ import annotations

import json
import time

import milstd461h_v2_reviewed as reviewed

base = reviewed.base
final = reviewed.final


def translate_all_fast(self: base.NLLBTranslator, texts) -> None:
    pending: list[dict] = []
    for source in texts:
        if source in self.cache:
            continue
        exact = base.translate_exact_or_none(source)
        if exact is not None:
            self.cache[source] = final.final_normalize(exact)
            continue
        toc = base.TOC_RE.match(source)
        if toc:
            label, dots, page_no = toc.groups()
            exact_label = base.translate_exact_or_none(label.strip())
            if exact_label is not None:
                self.cache[source] = f"{final.final_normalize(exact_label)} {dots}{page_no}"
                continue
            protected, mapping = base.protect_text(label.strip())
            pending.append({"source": source, "chunks": final.split_for_nllb(self, protected),
                            "mapping": mapping, "suffix": f" {dots}{page_no}"})
            continue
        protected, mapping = base.protect_text(source)
        pending.append({"source": source, "chunks": final.split_for_nllb(self, protected),
                        "mapping": mapping, "suffix": ""})

    flat: list[tuple[int, int, str]] = []
    for item_index, item in enumerate(pending):
        for chunk_index, chunk in enumerate(item["chunks"]):
            flat.append((item_index, chunk_index, chunk))

    translated_chunks: dict[int, dict[int, str]] = {}
    print(f"FAST translation cache={len(self.cache)}; pending units={len(pending)}; chunks={len(flat)}", flush=True)
    started = time.time()
    batch_limit = 160
    for offset in range(0, len(flat), batch_limit):
        batch = flat[offset:offset + batch_limit]
        source_tokens = [self._encode(meta[2]) for meta in batch]
        results = self.translator.translate_batch(
            source_tokens,
            target_prefix=[["kor_Hang"] for _ in source_tokens],
            beam_size=1,
            max_decoding_length=384,
            batch_type="tokens",
            max_batch_size=4096,
            return_scores=False,
            replace_unknowns=True,
        )
        for (item_index, chunk_index, _chunk), result in zip(batch, results):
            translated_chunks.setdefault(item_index, {})[chunk_index] = self._decode(result.hypotheses[0])
        if offset % (batch_limit * 3) == 0 or offset + batch_limit >= len(flat):
            done = min(len(flat), offset + batch_limit)
            elapsed = max(1.0, time.time() - started)
            print(f"FAST translated {done}/{len(flat)} chunks ({done / elapsed:.2f} chunks/s)", flush=True)

    for item_index, item in enumerate(pending):
        translated = " ".join(
            translated_chunks[item_index][chunk_index].strip()
            for chunk_index in range(len(item["chunks"]))
        )
        translated = base.restore_placeholders(translated, item["mapping"])
        translated = final.final_normalize(translated) + item["suffix"]
        if not base.KOREAN_RE.search(translated) and base.should_translate(item["source"]):
            translated = item["source"]
        self.cache[item["source"]] = translated

    self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")


base.NLLBTranslator.translate_all = translate_all_fast


if __name__ == "__main__":
    base.main()
