from __future__ import annotations

import json
import math
import os
import re
import statistics
from pathlib import Path
from typing import Iterable, Sequence

import fitz
import numpy as np

import mil461h_full_ko_v2 as base

# Add approved terminology that appeared in the first pilot.
base.GLOSSARY.update({
    "3 dB beamwidth": "3 dB 빔폭",
    "transmit antenna": "송신 안테나",
    "receive antenna": "수신 안테나",
    "antenna positions": "안테나 위치",
    "antenna position": "안테나 위치",
    "EUT enclosure": "시험대상장비 함체",
    "interconnecting and power leads": "상호연결선 및 전원선",
    "interconnecting leads": "상호연결선",
    "data recording device": "데이터 기록장치",
    "reference point": "기준점",
    "test area": "시험 구역",
    "test personnel": "시험 인원",
    "RF hazards": "RF 위험",
    "Figures": "그림",
    "Figure": "그림",
})


def preprocess_for_translation(text: str) -> str:
    """Insert approved Korean terms directly instead of opaque placeholders."""
    value = text
    for phrase, korean in sorted(base.GLOSSARY.items(), key=lambda item: len(item[0]), reverse=True):
        value = re.sub(re.escape(phrase), korean, value, flags=re.I)
    return value


def postprocess_translation(text: str) -> str:
    value = text
    for pattern, replacement in base.POST_REPLACEMENTS:
        value = re.sub(pattern, replacement, value)
    value = re.sub(r"\s+([,.;:!?%)\]])", r"\1", value)
    value = re.sub(r"([([])\s+", r"\1", value)
    return re.sub(r"\s{2,}", " ", value).strip()


class TranslatorV21(base.Translator):
    def translate_all(self, texts: Iterable[str]) -> None:
        prepared: list[tuple[str, str, tuple[str, str] | None]] = []
        for source in texts:
            if source in self.cache:
                continue
            if not base.should_translate(source):
                self.cache[source] = source
                continue
            exact = base.EXACT.get(base.normalize(source))
            if exact is not None:
                self.cache[source] = exact
                continue
            toc = base.TOC_RE.match(source)
            if toc:
                label, dots, page = toc.groups()
                prepared.append((source, preprocess_for_translation(label.strip()), (dots, page)))
            else:
                prepared.append((source, preprocess_for_translation(source), None))
        print(f"Translation cache={len(self.cache)}; pending={len(prepared)}", flush=True)
        for offset in range(0, len(prepared), 24):
            batch = prepared[offset:offset + 24]
            source_tokens = [
                self.tokenizer.convert_ids_to_tokens(
                    self.tokenizer.encode(item[1], truncation=True, max_length=512)
                )
                for item in batch
            ]
            results = self.translator.translate_batch(
                source_tokens,
                target_prefix=[["kor_Hang"] for _ in batch],
                beam_size=4,
                max_decoding_length=512,
                batch_type="tokens",
                max_batch_size=1600,
            )
            for (original, _prepared, toc), result in zip(batch, results):
                tokens = result.hypotheses[0][1:]
                translated = self.tokenizer.decode(
                    self.tokenizer.convert_tokens_to_ids(tokens), skip_special_tokens=True
                )
                translated = postprocess_translation(translated)
                if toc:
                    translated = f"{translated} {toc[0]}{toc[1]}"
                self.cache[original] = translated if base.KOREAN_RE.search(translated) else original
            if offset % 240 == 0 or offset + 24 >= len(prepared):
                self.cache_path.write_text(
                    json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(f"Translated {min(len(prepared), offset + 24)}/{len(prepared)}", flush=True)
        self.cache_path.write_text(
            json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def group_units_v21(page: fitz.Page):
    units = base.group_units(page)
    page_width = page.rect.width
    for unit in units:
        x0, _y0, x1, _y1 = unit.bbox
        centered = (
            (x1 - x0) < page_width * 0.75
            and abs((x0 + x1) / 2 - page_width / 2) < page_width * 0.07
        )
        if unit.kind in ("heading", "header") and centered:
            unit.align = 1
        elif unit.kind == "footer" and abs((x0 + x1) / 2 - page_width / 2) < page_width * 0.08:
            unit.align = 1
        else:
            unit.align = 0
    return units


def page_background(page: fitz.Page):
    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), colorspace=fitz.csRGB, alpha=False)
    array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    return array, pix.width / page.rect.width, pix.height / page.rect.height


def sample_background(array: np.ndarray, sx: float, sy: float, bbox: Sequence[float]):
    x0, y0, x1, y1 = bbox
    ix0, iy0 = max(0, int(x0 * sx)), max(0, int(y0 * sy))
    ix1, iy1 = min(array.shape[1], int(math.ceil(x1 * sx))), min(array.shape[0], int(math.ceil(y1 * sy)))
    samples = []
    for yy in range(max(0, iy0 - 3), min(array.shape[0], iy1 + 3)):
        for xx in range(max(0, ix0 - 3), min(array.shape[1], ix1 + 3)):
            if iy0 <= yy < iy1 and ix0 <= xx < ix1:
                continue
            samples.append(array[yy, xx])
    if not samples:
        return (1.0, 1.0, 1.0)
    median = np.median(np.asarray(samples), axis=0) / 255.0
    return tuple(float(value) for value in median)


def translate_pdf_v21(source: Path, output: Path, cache: Path, qa_path: Path, pages_spec: str | None):
    regular_font = base.pick_file(base.REG_FONT_CANDIDATES)
    bold_font = base.pick_file(base.BOLD_FONT_CANDIDATES)
    source_doc = fitz.open(source)
    pages = base.selected_pages(pages_spec, source_doc.page_count)
    all_units = {}
    unique = []
    seen = set()
    for page_no in pages:
        units = group_units_v21(source_doc[page_no - 1])
        all_units[page_no] = units
        for unit in units:
            if base.should_translate(unit.text) and unit.text not in seen:
                seen.add(unit.text)
                unique.append(unit.text)
    print(
        f"Selected pages={len(pages)}; units={sum(len(x) for x in all_units.values())}; "
        f"unique translations={len(unique)}",
        flush=True,
    )
    translator = TranslatorV21(cache)
    translator.load()
    translator.translate_all(unique)
    out_doc = fitz.open()
    placements = []
    page_map = {}
    for source_page_no in pages:
        out_doc.insert_pdf(source_doc, from_page=source_page_no - 1, to_page=source_page_no - 1)
        out_index = out_doc.page_count - 1
        page_map[source_page_no] = out_index + 1
        page = out_doc[out_index]
        units = all_units[source_page_no]
        background_array, sx, sy = page_background(page)
        for unit in units:
            rect = fitz.Rect(unit.bbox)
            rect.x0 -= 0.35
            rect.y0 -= 0.25
            rect.x1 += 0.35
            rect.y1 += 0.25
            page.add_redact_annot(
                rect,
                fill=sample_background(background_array, sx, sy, unit.bbox),
                cross_out=False,
            )
        page.apply_redactions(
            images=fitz.PDF_REDACT_IMAGE_NONE,
            graphics=fitz.PDF_REDACT_LINE_ART_NONE,
            text=fitz.PDF_REDACT_TEXT_REMOVE,
        )
        for unit in units:
            placements.append(
                {
                    "source_page": source_page_no,
                    **base.place_unit(
                        page, unit, translator.get(unit.text), regular_font, bold_font
                    ),
                }
            )
        print(f"Composed source page {source_page_no}", flush=True)
    metadata = source_doc.metadata or {}
    metadata.update(
        {
            "title": "MIL-STD-461H 한국어 전체 번역본 v2.1",
            "subject": "비공식 한국어 번역본 - 영문 원문 우선",
        }
    )
    out_doc.set_metadata(metadata)
    out_doc.save(output, garbage=4, deflate=True, clean=True)
    out_doc.close()
    source_doc.close()
    qa = {
        "source": str(source),
        "output": str(output),
        "source_page_count": fitz.open(source).page_count,
        "output_page_count": len(pages),
        "selected_source_pages": pages,
        "page_map": page_map,
        "unit_count": sum(len(x) for x in all_units.values()),
        "unique_translations": len(unique),
        "placements": len(placements),
        "overflow_count": sum(1 for item in placements if item["overflow"]),
        "model": translator.model_name,
        "placement_samples": placements[:200],
    }
    output_doc = fitz.open(output)
    full_text = "\n".join(page.get_text("text") for page in output_doc)
    output_doc.close()
    qa["bad_phrase_hits"] = {
        phrase: full_text.count(phrase)
        for phrase in base.BAD_PHRASES
        if phrase in full_text
    }
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


base.Translator = TranslatorV21
base.group_units = group_units_v21
base.translate_pdf = translate_pdf_v21

if __name__ == "__main__":
    base.main()
