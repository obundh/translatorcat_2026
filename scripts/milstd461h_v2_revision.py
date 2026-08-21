from __future__ import annotations

import re
import statistics

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
        "헤르츠": "Hz",
        "선에서 지면으로": "선-접지",
        "라인 대 접지": "선-접지",
        "커패시턴스": "정전용량",
        "기술 매뉴얼": "기술교범",
        "전기 기계": "전자기계식",
        "전기기계": "전자기계식",
        "전자 기계": "전자기계식",
        "필터링은": "필터는",
        "장치용 장치": "장비",
        "플랫폼 요구 사항": "플랫폼 요구사항",
        "계약상의 EMI 요구사항": "계약상 EMI 요구사항",
        "3 dB 빔 폭": "3 dB 빔폭",
        "펄스 변조": "펄스 변조",
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

            # Exact fixed labels (METRIC, SUPERSEDING, dates, cover title lines,
            # distribution statement, etc.) must be translated even when they
            # look like codes or all-caps identifiers.
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

            # Numeric list labels, page numbers and standard/test identifiers
            # remain untouched. The following body text is translated separately.
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

            # Translate a complete paragraph/list item as one semantic unit, but
            # retain every original line box so the Korean text is redistributed
            # onto the original baselines rather than creating a new page design.
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


if __name__ == "__main__":
    base.main()
