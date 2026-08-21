from __future__ import annotations

import json
import re
import statistics
import time

import fitz

import milstd461h_v2 as base


# ---------------------------------------------------------------------------
# Translation corrections
# ---------------------------------------------------------------------------
base.EXACT.update(
    {
        "REQUIREMENTS FOR THE CONTROL OF ELECTROMAGNETIC": "하위체계 및 장비의",
        "INTERFERENCE CHARACTERISTICS OF SUBSYSTEMS AND": "전자기 간섭 특성",
        "EQUIPMENT": "관리 요구사항",
        "17 APRIL 2026": "2026년 4월 17일",
        "11 DECEMBER 2015": "2015년 12월 11일",
        "DISTRIBUTION STATEMENT A. Approved for public release; distribution is unlimited.":
            "배포 성명서 A. 공개 배포 승인; 배포에 제한이 없음.",
        "Interface requirements.": "인터페이스 요구사항.",
        "Joint procurement.": "공동 조달.",
        "Filtering (Navy only).": "필터링(해군에만 적용).",
        "Self-compatibility.": "자체 적합성.",
        "Non-developmental items (NDI).": "비개발품(NDI).",
        "Commercial items (CI).": "상용품(CI).",
        "Selected by contractor.": "계약자가 선정한 경우.",
        "Specified by procuring activity.": "조달기관이 지정한 경우.",
        "The test setup shall be as follows:": "시험 구성은 다음과 같아야 한다:",
        "The test procedures shall be as follows:": "시험 절차는 다음과 같아야 한다:",
        "The test equipment shall be as follows:": "시험 장비는 다음과 같아야 한다:",
        "Placement of transmit antennas.": "송신 안테나 배치.",
        "Placement of electric field sensors.": "전계 센서 배치.",
        "Receive antennas.": "수신 안테나.",
        "Transmit antennas.": "송신 안테나.",
        "Measurement receiver.": "측정 수신기.",
        "Power meter.": "전력계.",
        "Directional coupler.": "방향성 결합기.",
        "Attenuator, 50 ohm.": "감쇠기, 50 Ω.",
        "Data recording device.": "데이터 기록 장치.",
        "Downloaded from https://ib-lenhardt.com | IBL-Lab GmbH - MIL-STD-461H / EMC Military Testing & Certification":
            "https://ib-lenhardt.com에서 내려받음 | IBL-Lab GmbH - MIL-STD-461H / EMC 군용 시험 및 인증",
    }
)

base.NORMALIZE_TERMS.update(
    {
        "하위체계은": "하위체계는",
        "하위체계이": "하위체계가",
        "요구 사항": "요구사항",
        "상업 품목": "상용품",
        "상업 항목": "상용품",
        "비개발 품목": "비개발품",
        "셀프 호환성": "자체 적합성",
        "셀프 호환": "자체 적합성",
        "마이크로파라드": "마이크로패럿",
        "마이크로패러드": "마이크로패럿",
        "마이크로파드": "마이크로패럿",
        "헤르츠": "Hz",
        "선에서 지면으로": "선-접지",
        "라인 대 접지": "선-접지",
        "라인-대-지면": "선-접지",
        "라인 투 지면": "선-접지",
        "지면 필터": "접지 필터",
        "커패시턴스": "정전용량",
        "기술 매뉴얼": "기술교범",
        "전기 기계": "전자기계식",
        "전기기계": "전자기계식",
        "전자 기계": "전자기계식",
        "필터링은": "필터는",
        "장치용 장치": "장비",
        "플랫폼 요구 사항": "플랫폼 요구사항",
        "계약상의 EMI 요구사항": "계약상 EMI 요구사항",
        "계약상의 EMI": "계약상 EMI",
        "특정된 CI": "지정된 CI",
        "3 dB 빔 폭": "3 dB 빔폭",
        "감응도": "내성",
        "DoD 활동": "DoD 기관",
        "EMC 군사 시험": "EMC 군용 시험",
        "군사 시험 및 인증": "군용 시험 및 인증",
        "Hz(Hz)": "Hz",
    }
)

# NLLB handles numbers, units and section references reliably. Protecting them
# produced duplicated placeholder tokens in the first draft, so only names,
# URLs, standard codes, test codes and acronyms are protected here.
base.PRESERVE_RE = re.compile(
    r"(?:https?://\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
    r"MIL-STD-\d+[A-Z]?|SD-\d+|(?:CE|CS|RE|RS)\d{3}|"
    r"\b(?:AMSC|AREA|ASSIST|DoD|DOD|EMC|EME|EMI|EMICP|EMITP|EMITR|ERP|ESD|EUT|FCC|FFT|FWHM|GFE|IF|ISO|LISN|MAD|NDI|RF|RMS|TEM|TPD|CI|CW|DC|AC|NIST|DTRA|DISA|NSA|CLF)\b)"
)


def restore_placeholders(text: str, mapping: dict[str, str]) -> str:
    out = re.sub(
        r"Z\s*X\s*Q\s*P\s*H\s*(\d+)\s*Q\s*X\s*Z",
        lambda match: f"ZXQPH{int(match.group(1)) % 10000:04d}QXZ",
        text,
        flags=re.I,
    )
    for key, value in mapping.items():
        out = out.replace(key, value)
    return out


base.restore_placeholders = restore_placeholders


_original_should_translate = base.should_translate


def should_translate(text: str) -> bool:
    return base.translate_exact_or_none(text) is not None or _original_should_translate(text)


base.should_translate = should_translate


# ---------------------------------------------------------------------------
# Coherent paragraph translation. Long paragraphs are split at sentence
# boundaries before NLLB generation, preventing the 512-token decoder cutoff
# that truncated the first pilot's longer requirements.
# ---------------------------------------------------------------------------
def _split_for_nllb(translator: base.NLLBTranslator, text: str, max_tokens: int = 280) -> list[str]:
    def token_count(value: str) -> int:
        return len(translator._encode(value))

    if token_count(text) <= max_tokens:
        return [text]

    sentences = [item.strip() for item in re.split(r"(?<=[.!?;:])\s+", text) if item.strip()]
    if len(sentences) <= 1:
        sentences = [item.strip() for item in re.split(r"(?<=,)\s+", text) if item.strip()]

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if token_count(candidate) <= max_tokens:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if token_count(sentence) <= max_tokens:
            current = sentence
            continue
        # Last-resort word grouping for an exceptionally long sentence.
        current = ""
        for word in sentence.split():
            candidate = f"{current} {word}".strip() if current else word
            if token_count(candidate) <= max_tokens:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = word
    if current:
        chunks.append(current)
    return chunks or [text]


def translate_all(self: base.NLLBTranslator, texts) -> None:
    pending: list[dict] = []
    for source in texts:
        if source in self.cache:
            continue
        exact = base.translate_exact_or_none(source)
        if exact is not None:
            self.cache[source] = base.normalize_translation(exact)
            continue
        toc = base.TOC_RE.match(source)
        if toc:
            label, dots, page_no = toc.groups()
            exact_label = base.translate_exact_or_none(label.strip())
            if exact_label is not None:
                self.cache[source] = f"{exact_label} {dots}{page_no}"
                continue
            protected, mapping = base.protect_text(label.strip())
            pending.append(
                {
                    "source": source,
                    "chunks": _split_for_nllb(self, protected),
                    "mapping": mapping,
                    "suffix": f" {dots}{page_no}",
                }
            )
            continue
        protected, mapping = base.protect_text(source)
        pending.append(
            {
                "source": source,
                "chunks": _split_for_nllb(self, protected),
                "mapping": mapping,
                "suffix": "",
            }
        )

    flat: list[tuple[int, int, str]] = []
    for item_index, item in enumerate(pending):
        for chunk_index, chunk in enumerate(item["chunks"]):
            flat.append((item_index, chunk_index, chunk))

    translated_chunks: dict[int, dict[int, str]] = {}
    print(f"Translation cache={len(self.cache)}; pending units={len(pending)}; chunks={len(flat)}", flush=True)
    start = time.time()
    batch_limit = 64
    for offset in range(0, len(flat), batch_limit):
        batch = flat[offset : offset + batch_limit]
        source_tokens = [self._encode(item[2]) for item in batch]
        results = self.translator.translate_batch(
            source_tokens,
            target_prefix=[["kor_Hang"] for _ in source_tokens],
            beam_size=4,
            max_decoding_length=512,
            batch_type="tokens",
            max_batch_size=1536,
            return_scores=False,
            replace_unknowns=True,
        )
        for (item_index, chunk_index, _chunk), result in zip(batch, results):
            translated_chunks.setdefault(item_index, {})[chunk_index] = self._decode(result.hypotheses[0])
        if offset % (batch_limit * 5) == 0 or offset + batch_limit >= len(flat):
            done = min(len(flat), offset + batch_limit)
            elapsed = max(1.0, time.time() - start)
            print(f"Translated {done}/{len(flat)} chunks ({done / elapsed:.2f} chunks/s)", flush=True)

    for item_index, item in enumerate(pending):
        translated = " ".join(
            translated_chunks[item_index][index].strip()
            for index in range(len(item["chunks"]))
        )
        translated = base.restore_placeholders(translated, item["mapping"])
        translated = base.normalize_translation(translated) + item["suffix"]
        if not base.KOREAN_RE.search(translated) and base.should_translate(item["source"]):
            translated = item["source"]
        self.cache[item["source"]] = translated

    self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")


base.NLLBTranslator.translate_all = translate_all


# ---------------------------------------------------------------------------
# Layout corrections
# ---------------------------------------------------------------------------
def is_heading_line(line: base.LineBox, page_width: float) -> bool:
    text = base.normalize_source(line.text)
    english = base.ENGLISH_WORD_RE.findall(text)
    upper = bool(english) and all(word.isupper() for word in english)
    section_heading = bool(base.SECTION_PREFIX_RE.match(text)) and (line.bold or len(text) < 120)
    centered = (
        line.width < page_width * 0.65
        and abs((line.bbox[0] + line.bbox[2]) / 2 - page_width / 2) < page_width * 0.08
    )
    return line.bold or upper or section_heading or (centered and line.font_size >= 10.5)


base.is_heading_line = is_heading_line


def make_units(page, page_no: int) -> list[base.Unit]:
    lines = base.extract_lines(page)
    page_width = page.rect.width
    by_block: dict[int, list[base.LineBox]] = {}
    for line in lines:
        by_block.setdefault(line.block_no, []).append(line)

    units: list[base.Unit] = []
    for block_no in sorted(by_block):
        block_lines = sorted(by_block[block_no], key=lambda item: (item.bbox[1], item.bbox[0]))
        i = 0
        while i < len(block_lines):
            line = block_lines[i]
            text = base.normalize_source(line.text)
            if not text or line.rotation not in (0, 90, 180, 270):
                i += 1
                continue

            exact = base.translate_exact_or_none(text)
            toc = base.TOC_RE.match(text)
            heading = is_heading_line(line, page_width)

            if exact is not None:
                units.append(
                    base.Unit(
                        source_text=text,
                        lines=[line],
                        kind="heading" if heading else "label",
                        align=base.infer_alignment([line], page_width),
                        font_size=line.font_size,
                        bold=line.bold or heading,
                        page_no=page_no,
                        block_no=block_no,
                    )
                )
                i += 1
                continue

            if (
                base.SECTION_ONLY_RE.fullmatch(text)
                or base.BULLET_ONLY_RE.fullmatch(text)
                or base.CODE_ONLY_RE.fullmatch(text)
            ):
                i += 1
                continue

            if toc or heading or line.rotation != 0:
                units.append(
                    base.Unit(
                        source_text=text,
                        lines=[line],
                        kind="toc" if toc else ("heading" if heading else "label"),
                        align=base.infer_alignment([line], page_width),
                        font_size=line.font_size,
                        bold=line.bold or heading,
                        page_no=page_no,
                        block_no=block_no,
                    )
                )
                i += 1
                continue

            group = [line]
            start_x = line.bbox[0]
            start_bullet = bool(base.BULLET_PREFIX_RE.match(text))
            j = i + 1
            while j < len(block_lines):
                nxt = block_lines[j]
                next_text = base.normalize_source(nxt.text)
                if not next_text or nxt.rotation != 0:
                    break
                if base.translate_exact_or_none(next_text) is not None:
                    break
                if (
                    base.SECTION_ONLY_RE.fullmatch(next_text)
                    or base.BULLET_ONLY_RE.fullmatch(next_text)
                    or base.CODE_ONLY_RE.fullmatch(next_text)
                ):
                    break
                if base.TOC_RE.match(next_text) or is_heading_line(nxt, page_width):
                    break
                vertical_gap = nxt.bbox[1] - group[-1].bbox[3]
                line_height = statistics.median(item.height for item in group)
                if vertical_gap > max(4.8, line_height * 0.55):
                    break
                if base.BULLET_PREFIX_RE.match(next_text) and group:
                    break
                if not start_bullet and abs(nxt.bbox[0] - start_x) > 28:
                    break
                if start_bullet and nxt.bbox[0] + 2 < start_x:
                    break
                group.append(nxt)
                j += 1

            units.append(
                base.Unit(
                    source_text=base.source_from_lines(group),
                    lines=group,
                    kind="bullet" if start_bullet else ("paragraph" if len(group) > 1 else "line"),
                    align=0,
                    font_size=statistics.median(item.font_size for item in group),
                    bold=all(item.bold for item in group),
                    page_no=page_no,
                    block_no=block_no,
                )
            )
            i = j

    units.sort(key=lambda unit: (unit.lines[0].bbox[1], unit.lines[0].bbox[0], unit.block_no))
    return units


base.make_units = make_units


_original_choose_wrap = base.choose_wrap


def choose_wrap(unit: base.Unit, translation: str, font: fitz.Font):
    wrapped, size, width_scale, fits = _original_choose_wrap(unit, translation, font)
    if fits and len(wrapped) <= len(unit.lines):
        return wrapped, size, width_scale, True

    widths = [max(8.0, line.width + 2.0) for line in unit.lines]
    for factor in (0.66, 0.62, 0.58, 0.54, 0.50, 0.46):
        candidate_size = max(3.0, unit.font_size * factor)
        for scale in (1.0, 0.96, 0.92, 0.88):
            candidate, candidate_fits = base.wrap_to_widths(font, translation, candidate_size, widths, scale)
            if candidate_fits and len(candidate) <= len(widths):
                return candidate, candidate_size, scale, True
    # This path should be exceptionally rare. It is kept as a QA failure rather
    # than silently dropping the end of a translated requirement.
    return wrapped, size, width_scale, False


base.choose_wrap = choose_wrap


def redact_and_place(page, units, regular_font_file: str, bold_font_file: str) -> list[dict]:
    arr, sx, sy = base.page_background(page)
    todo = []
    for unit in units:
        translation = unit.translated_text
        if not translation or (translation == unit.source_text and not base.KOREAN_RE.search(translation)):
            continue
        background = base.sample_background(arr, sx, sy, unit.bbox)
        todo.append((unit, translation, background))
        for line in unit.lines:
            if line.rotation == 0:
                # PyMuPDF line bboxes overlap adjacent baselines. A tight box
                # derived from the actual baseline prevents a translated date or
                # heading from erasing an untranslated MIL-STD code above it.
                rect = fitz.Rect(
                    line.bbox[0] - 0.35,
                    line.origin[1] - line.font_size * 0.84,
                    line.bbox[2] + 0.35,
                    line.origin[1] + line.font_size * 0.20,
                )
            else:
                rect = fitz.Rect(line.bbox)
                rect.x0 -= 0.35
                rect.y0 -= 0.20
                rect.x1 += 0.35
                rect.y1 += 0.20
            page.add_redact_annot(rect, fill=background, cross_out=False)

    if not todo:
        return []

    page.apply_redactions(
        images=fitz.PDF_REDACT_IMAGE_NONE,
        graphics=fitz.PDF_REDACT_LINE_ART_NONE,
        text=fitz.PDF_REDACT_TEXT_REMOVE,
    )

    regular_font = fitz.Font(fontfile=regular_font_file)
    bold_font = fitz.Font(fontfile=bold_font_file)
    records: list[dict] = []
    for unit, translation, _background in todo:
        font_file = bold_font_file if unit.bold else regular_font_file
        font = bold_font if unit.bold else regular_font
        wrapped, size, width_scale, fits = base.choose_wrap(unit, translation, font)
        for index, line in enumerate(unit.lines):
            if index >= len(wrapped):
                continue
            value = wrapped[index]
            if not value:
                continue
            if line.rotation == 0:
                x = base.line_alignment(unit, line, value, font, size)
                y = line.origin[1] - max(0.0, (line.font_size - size) * 0.08) + 0.05
                page.insert_text(
                    fitz.Point(x, y),
                    value,
                    fontfile=font_file,
                    fontname="kob" if unit.bold else "kor",
                    fontsize=size,
                    color=line.color if max(line.color) > 0.1 else (0, 0, 0),
                    overlay=True,
                )
            else:
                rect = fitz.Rect(line.bbox)
                page.insert_textbox(
                    rect,
                    value,
                    fontfile=font_file,
                    fontname="kob" if unit.bold else "kor",
                    fontsize=size,
                    color=line.color if max(line.color) > 0.1 else (0, 0, 0),
                    align=unit.align,
                    rotate=line.rotation,
                    overlay=True,
                    lineheight=1.0,
                )
        records.append(
            {
                "page": unit.page_no,
                "kind": unit.kind,
                "source": unit.source_text,
                "translation": translation,
                "line_count_original": len(unit.lines),
                "line_count_used": len(wrapped),
                "font_size_original": unit.font_size,
                "font_size_used": size,
                "font_scale": size / unit.font_size if unit.font_size else None,
                "width_scale": width_scale,
                "fit": fits,
                "bbox": list(unit.bbox),
            }
        )
    return records


base.redact_and_place = redact_and_place


if __name__ == "__main__":
    base.main()
