from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Iterable, Sequence

import ctranslate2
import fitz
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoTokenizer

import mil461h_full_ko as base

MODEL_NAME = "NHNDQ/nllb-finetuned-en2ko"
REG_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)
BOLD_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
)

EXACT = {
    "METRIC": "미터법",
    "SUPERSEDING": "대체 문서",
    "DEPARTMENT OF DEFENSE": "미국 국방부",
    "INTERFACE STANDARD": "인터페이스 표준",
    "DEPARTMENT OF DEFENSE INTERFACE STANDARD": "미국 국방부 인터페이스 표준",
    "REQUIREMENTS FOR THE CONTROL OF ELECTROMAGNETIC INTERFERENCE CHARACTERISTICS OF SUBSYSTEMS AND EQUIPMENT": "하위체계 및 장비의 전자기 간섭 특성 관리 요구사항",
    "DISTRIBUTION STATEMENT A. Approved for public release; distribution is unlimited.": "배포문 A. 공개 배포 승인; 배포에 제한 없음.",
    "FOREWORD": "서문",
    "CONTENTS": "목차",
    "FIGURES": "그림 목록",
    "TABLES": "표 목록",
    "PARAGRAPH": "항목",
    "PAGE": "쪽",
    "SCOPE": "적용범위",
    "Purpose": "목적",
    "Purpose.": "목적.",
    "Application": "적용",
    "General applicability": "일반 적용성",
    "Tailoring of requirements": "요구사항 조정",
    "Structure": "구성",
    "Emission and susceptibility designations": "방출 및 내성 표기",
    "APPLICABLE PUBLICATIONS": "적용 문서",
    "Government publications": "정부 문서",
    "Other Government publications": "그 밖의 정부 문서",
    "Non-Government publications": "비정부 문서",
    "Order of precedence": "우선순위",
    "DEFINITIONS": "정의",
    "GENERAL REQUIREMENTS": "일반 요구사항",
    "General.": "일반.",
    "Interface requirements.": "인터페이스 요구사항.",
    "Joint procurement.": "공동 조달.",
    "Filtering (Navy only).": "필터링(해군만 해당).",
    "Self-compatibility.": "자기 적합성.",
    "Non-developmental items (NDI).": "비개발품(NDI).",
    "Commercial items (CI).": "상용품(CI).",
    "Selected by contractor.": "계약자가 선정한 경우.",
    "Specified by procuring activity.": "조달기관이 지정한 경우.",
    "Procurement of equipment or subsystems having met other EMI requirements.": "다른 EMI 요구사항을 충족한 장비 또는 하위체계의 조달.",
    "Government furnished equipment (GFE).": "정부 제공 장비(GFE).",
    "Switching transients.": "스위칭 과도현상.",
    "Interchangeable modular equipment.": "상호교환식 모듈형 장비.",
    "Verification requirements.": "검증 요구사항.",
    "Measurement tolerances.": "측정 허용오차.",
    "Test equipment.": "시험 장비.",
    "Setup.": "시험 구성.",
    "Procedures.": "절차.",
    "Data presentation.": "자료 제시.",
    "Applicability": "적용성",
    "Description": "설명",
    "Requirement": "요구항목",
    "Frequency Range": "주파수 범위",
    "Frequency Range (MHz)": "주파수 범위(MHz)",
    "Tuner Positions": "튜너 위치 수",
    "Above 600": "600 초과",
    "Minimum absorption": "최소 흡수성능",
    "Minimum Dwell Time": "최소 체류시간",
    "Parameters": "매개변수",
    "Values": "값",
    "Method": "방법",
    "Level": "레벨",
    "Test Voltage (kV)": "시험전압(kV)",
    "Air": "기중",
    "Contact/Air": "접촉/기중",
    "LIMIT LEVELS (VOLTS/METER)": "한계 레벨(V/m)",
    "PLATFORM FREQUENCY RANGE": "플랫폼 / 주파수 범위",
    "ALL AIRCRAFT (EXTERNAL OR SAFETY CRITICAL) ALL SERVICES": "전 항공기\n(외부 또는 안전필수)\n전 군",
    "AIRCRAFT INTERNAL - ARMY": "항공기 내부\n육군",
    "AIRCRAFT INTERNAL - NAVY": "항공기 내부\n해군",
    "AIRCRAFT INTERNAL - AIR FORCE": "항공기 내부\n공군",
    "SHIPS - ABOVE DECK & EXPOSED BELOW DECK **": "선박\n갑판 위 및 노출된\n갑판 아래**",
    "SUBMARINES (EXTERNAL)*": "잠수함 외부*",
    "METALLIC SHIPS - BELOW DECK": "금속 선박\n갑판 아래",
    "NON-METALLIC SHIPS - BELOW DECK": "비금속 선박\n갑판 아래",
    "SUBMARINE (INTERNAL)": "잠수함 내부",
    "GROUND - ARMY": "지상\n육군",
    "GROUND - NAVY AND AIR FORCE": "지상\n해군·공군",
    "SPACE": "우주",
    "TABLE XI. RS103 limits.": "표 XI. RS103 한계값.",
    "TABLE XII. Required number of tuner positions for a reverberation chamber.": "표 XII. 잔향실에 필요한 튜너 위치 수.",
    "RS103, radiated susceptibility, electric field.": "RS103, 방사 내성, 전계.",
    "RS105, radiated susceptibility, transient electromagnetic field.": "RS105, 방사 내성, 과도 전자기장.",
    "RS105, radiated susceptibility, transient, electromagnetic field.": "RS105, 방사 내성, 과도 전자기장.",
    "radiated susceptibility, electric field": "방사 내성, 전계",
    "radiated susceptibility, transient electromagnetic field": "방사 내성, 과도 전자기장",
    "conducted susceptibility": "전도 내성",
    "radiated susceptibility": "방사 내성",
    "conducted emissions": "전도 방출",
    "radiated emissions": "방사 방출",
    "Equipment Under Test": "시험대상장비",
    "Equipment under test": "시험대상장비",
    "Defense Standardization Program Office": "국방 표준화 프로그램 사무국",
    "Electromagnetic Environmental Effects": "전자기 환경 영향",
    "Electromagnetic Compatibility": "전자기 적합성",
    "Electromagnetic Environment": "전자기 환경",
    "Electromagnetic Interference": "전자기 간섭",
    "Electromagnetic Interference Control Procedures": "전자기 간섭 관리 절차",
    "Electromagnetic Interference Test Procedures": "전자기 간섭 시험 절차",
    "Electromagnetic Interference Test Report": "전자기 간섭 시험 보고서",
    "Effective Radiated Power": "유효 방사전력",
    "Electrostatic Discharge": "정전기 방전",
    "Fast Fourier Transform": "고속 푸리에 변환",
    "Full Width Half Maximum": "반치전폭",
    "Government Furnished Equipment": "정부 제공 장비",
    "Intermediate Frequency": "중간주파수",
    "International Organization for Standardization": "국제표준화기구",
    "Line Impedance Stabilization Network": "선로 임피던스 안정화 회로망",
    "Non-Developmental Item": "비개발품",
    "Radio Frequency": "무선주파수",
    "Root Mean Square": "실효값",
    "Transverse Electromagnetic": "횡전자기",
    "Transient Protection Device": "과도 보호소자",
    "CONCLUDING MATERIAL": "마무리 자료",
    "Custodians:": "관리기관:",
    "Preparing activity:": "작성기관:",
    "Review activities:": "검토기관:",
}

REQUIREMENT_DESCRIPTIONS = {
    "Conducted Emissions, Audio Frequency Currents, Power Leads": "전도 방출, 전원선의 음성주파수 전류",
    "Conducted Emissions, Radio Frequency Potentials, Power Leads": "전도 방출, 전원선의 무선주파수 전위",
    "Conducted Emissions, Antenna Port": "전도 방출, 안테나 포트",
    "Conducted Susceptibility, Power Leads": "전도 내성, 전원선",
    "Conducted Susceptibility, Antenna Port, Intermodulation": "전도 내성, 안테나 포트, 상호변조",
    "Conducted Susceptibility, Antenna Port, Rejection of Undesired Signals": "전도 내성, 안테나 포트, 불요신호 제거",
    "Conducted Susceptibility, Antenna Port, Cross-Modulation": "전도 내성, 안테나 포트, 교차변조",
    "Conducted Susceptibility, Structure Current": "전도 내성, 구조물 전류",
    "Conducted Susceptibility, Bulk Cable Injection": "전도 내성, 케이블 다발 주입",
    "Conducted Susceptibility, Bulk Cable Injection, Impulse Excitation": "전도 내성, 케이블 다발 주입, 임펄스 여기",
    "Conducted Susceptibility, Damped Sinusoidal Transients, Cables and Power Leads": "전도 내성, 감쇠 정현파 과도현상, 케이블 및 전원선",
    "Conducted Susceptibility, Lightning Induced Transients, Cables and Power Leads": "전도 내성, 낙뢰 유도 과도현상, 케이블 및 전원선",
    "Personnel Borne Electrostatic Discharge": "인체 대전 정전기 방전",
    "Radiated Emissions, Magnetic Field": "방사 방출, 자기장",
    "Radiated Emissions, Electric Field": "방사 방출, 전계",
    "Radiated Emissions, Antenna Spurious and Harmonic Outputs": "방사 방출, 안테나 불요 및 고조파 출력",
    "Radiated Susceptibility, Magnetic Field": "방사 내성, 자기장",
    "Radiated Susceptibility, Electric Field": "방사 내성, 전계",
    "Radiated Susceptibility, Transient Electromagnetic Field": "방사 내성, 과도 전자기장",
}
EXACT.update(REQUIREMENT_DESCRIPTIONS)

STANDARD_REPLACEMENTS = (
    (r"일반 요구 사항", "일반 요구사항"),
    (r"서브\s*시스템", "하위체계"),
    (r"하위 시스템", "하위체계"),
    (r"방사선 감수성|방사형 감수성|복사 감수성|방사 감수성", "방사 내성"),
    (r"전도(?:성)? 감수성", "전도 내성"),
    (r"감수성", "내성"),
    (r"라인[- ]?(?:투|대)[- ]?그라운드", "선-접지"),
    (r"접지 평면", "접지면"),
    (r"인클로저", "함체"),
    (r"조달 활동|획득 활동", "조달기관"),
    (r"테스트", "시험"),
    (r"요건", "요구사항"),
    (r"데크", "갑판"),
    (r"모든 서비스", "전 군"),
    (r"안전 중요", "안전필수"),
    (r"압력 선체", "내압선체"),
    (r"상부 구조", "상부구조"),
    (r"공통 모드", "공통모드"),
    (r"마이크로 패럿", "마이크로패럿"),
    (r"오작동해서는 안 된다", "오작동하여서는 아니 된다"),
    (r"준수해야 한다", "준수하여야 한다"),
    (r"사용해야 한다", "사용하여야 한다"),
    (r"충족해야 한다", "충족하여야 한다"),
)

ALLOWED_ENGLISH = re.compile(
    r"(?:https?://\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|MIL-STD-\d+[A-Z]?|SD-\d+|"
    r"(?:CE|CS|RE|RS)\d{3}|\b(?:AMSC|AREA|ASSIST|DoD|DOD|EMC|EME|EMI|EMICP|EMITP|EMITR|ERP|ESD|EUT|FCC|FFT|FWHM|GFE|IF|ISO|LISN|MAD|NDI|RF|RMS|TEM|TPD|CI|CW|DC|AC|NIST|DTRA|DISA|NSA|IBL|Lab|GmbH)\b|"
    r"\b\d+(?:\.\d+)?\s*(?:Hz|kHz|MHz|GHz|dB|dBm|V/m|V|A|W|kW|m|cm|mm|ns|μs|ms|μF|ohm|Ω|%)\b)"
)
KOREAN_RE = re.compile(r"[가-힣]")
ENGLISH_RE = re.compile(r"[A-Za-z]{2,}")
TOC_RE = re.compile(r"^(.*?)(\.{4,})(\s*[ivxlcdmIVXLCDM]+|\s*\d+)\s*$")


def pick_file(candidates: Sequence[str]) -> str:
    for p in candidates:
        if Path(p).exists():
            return p
    raise FileNotFoundError(str(candidates))


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00ad", "").replace("\ufeff", " ")).strip()


def exact_lookup(text: str) -> str | None:
    t = norm(text)
    if t in EXACT:
        return EXACT[t]
    stripped = t.rstrip(".")
    if stripped in EXACT:
        v = EXACT[stripped]
        return v + ("." if t.endswith(".") and not v.endswith(".") else "")
    return None


def should_translate(text: str) -> bool:
    t = norm(text)
    if not t or not ENGLISH_RE.search(t):
        return False
    if re.fullmatch(r"(?:MIL-STD-\d+[A-Z]?|(?:CE|CS|RE|RS)\d{3}|[A-Z0-9/._-]{2,})", t):
        return False
    if re.fullmatch(r"[\d\s.,;:()\[\]{}<>+=×÷/\\|_\-–—°πμΩ%]+", t):
        return False
    return True


def protect(text: str) -> tuple[str, dict[str, str]]:
    mapping: dict[str, str] = {}
    counter = 0
    def repl(m: re.Match[str]) -> str:
        nonlocal counter
        key = f"ZXQPH{counter:04d}QXZ"
        counter += 1
        mapping[key] = m.group(0)
        return key
    return ALLOWED_ENGLISH.sub(repl, text), mapping


def restore(text: str, mapping: dict[str, str]) -> str:
    out = re.sub(
        r"Z\s*X\s*Q\s*P\s*H\s*(\d+)\s*Q\s*X\s*Z",
        lambda m: f"ZXQPH{int(m.group(1)):04d}QXZ",
        text,
        flags=re.I,
    )
    for key, value in mapping.items():
        out = out.replace(key, value)
    return out


def post_edit(source: str, translated: str) -> str:
    exact = exact_lookup(source)
    if exact is not None:
        return exact
    out = translated.strip()
    for pattern, replacement in STANDARD_REPLACEMENTS:
        out = re.sub(pattern, replacement, out)
    if re.search(r"\bemissions?\b", source, re.I):
        out = out.replace("배출", "방출")
    if re.search(r"\bsusceptibility\b", source, re.I):
        out = re.sub(r"감수성", "내성", out)
    if re.search(r"\bshall\b", source, re.I):
        out = re.sub(r"해야 한다\.?$", "하여야 한다.", out)
        out = re.sub(r"되어야 한다\.?$", "되어야 한다.", out)
    out = re.sub(r"\s+([,.;:!?%)\]])", r"\1", out)
    out = re.sub(r"([([])\s+", r"\1", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


class NLLBTranslator:
    def __init__(self, model_dir: Path, cache_path: Path):
        self.model_dir = model_dir
        self.cache_path = cache_path
        self.cache: dict[str, str] = {}
        if cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}
        self.tokenizer = None
        self.translator = None
        self.target_token = "kor_Hang"

    def load(self) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, src_lang="eng_Latn")
        self.translator = ctranslate2.Translator(
            str(self.model_dir), device="cpu", compute_type="int8",
            inter_threads=1, intra_threads=max(2, min(8, os.cpu_count() or 4)),
        )
        print("NLLB CTranslate2 translator ready", flush=True)

    def split(self, text: str, max_tokens: int = 420) -> list[str]:
        ids = self.tokenizer(text, add_special_tokens=True)["input_ids"]
        if len(ids) <= max_tokens:
            return [text]
        pieces = re.split(r"(?<=[.!?;:])\s+|\n+", text)
        chunks: list[str] = []
        cur = ""
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            candidate = f"{cur} {piece}".strip() if cur else piece
            if len(self.tokenizer(candidate, add_special_tokens=True)["input_ids"]) <= max_tokens:
                cur = candidate
            else:
                if cur:
                    chunks.append(cur)
                cur = piece
        if cur:
            chunks.append(cur)
        return chunks or [text]

    def _translate_batch(self, texts: list[str]) -> list[str]:
        token_batches = []
        maps = []
        for text in texts:
            protected, mapping = protect(text)
            ids = self.tokenizer(protected, add_special_tokens=True)["input_ids"]
            token_batches.append(self.tokenizer.convert_ids_to_tokens(ids))
            maps.append(mapping)
        results = self.translator.translate_batch(
            token_batches,
            target_prefix=[[self.target_token] for _ in token_batches],
            beam_size=4,
            max_decoding_length=640,
            repetition_penalty=1.05,
        )
        outputs = []
        for source, result, mapping in zip(texts, results, maps):
            tokens = result.hypotheses[0]
            ids = self.tokenizer.convert_tokens_to_ids(tokens)
            text = self.tokenizer.decode(ids, skip_special_tokens=True)
            outputs.append(post_edit(source, restore(text, mapping)))
        return outputs

    def translate_all(self, texts: Iterable[str], batch_size: int = 12) -> None:
        pending_chunks: list[tuple[str, int, str, int]] = []
        chunk_counts: dict[str, int] = {}
        for original in texts:
            if original in self.cache:
                continue
            exact = exact_lookup(original)
            if exact is not None:
                self.cache[original] = exact
                continue
            if not should_translate(original):
                self.cache[original] = original
                continue
            chunks = self.split(original)
            chunk_counts[original] = len(chunks)
            for idx, chunk in enumerate(chunks):
                pending_chunks.append((original, idx, chunk, len(chunks)))
        translated: dict[str, dict[int, str]] = {}
        print(f"Translation cache={len(self.cache)}, chunks={len(pending_chunks)}", flush=True)
        start = time.time()
        for offset in range(0, len(pending_chunks), batch_size):
            batch = pending_chunks[offset:offset + batch_size]
            outs = self._translate_batch([x[2] for x in batch])
            for (original, idx, _chunk, _count), out in zip(batch, outs):
                translated.setdefault(original, {})[idx] = out
            done = min(len(pending_chunks), offset + batch_size)
            if done % 120 < batch_size or done == len(pending_chunks):
                for original, pieces in translated.items():
                    if len(pieces) == chunk_counts.get(original, -1):
                        joined = " ".join(pieces[i] for i in range(len(pieces))).strip()
                        self.cache[original] = post_edit(original, joined)
                self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")
                elapsed = max(1.0, time.time() - start)
                print(f"Translated {done}/{len(pending_chunks)} chunks ({done/elapsed:.2f}/s)", flush=True)
        for original, pieces in translated.items():
            if len(pieces) == chunk_counts.get(original, -1):
                self.cache[original] = post_edit(original, " ".join(pieces[i] for i in range(len(pieces))).strip())
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, text: str) -> str:
        return self.cache.get(text, exact_lookup(text) or text)


def rect_intersection_ratio(a: Sequence[float], b: Sequence[float]) -> float:
    ra, rb = fitz.Rect(a), fitz.Rect(b)
    inter = ra & rb
    if inter.is_empty:
        return 0.0
    area = max(0.01, ra.width * ra.height)
    return inter.width * inter.height / area


def page_tables(page: fitz.Page):
    try:
        return list(page.find_tables().tables)
    except Exception:
        return []


def units_without_tables(page: fitz.Page, page_no: int, table_bboxes: list[Sequence[float]]):
    units = base.make_units(page, page_no)
    return [u for u in units if not any(rect_intersection_ratio(u.bbox, b) > 0.25 for b in table_bboxes)]


def sample_background(page: fitz.Page, bbox: Sequence[float]) -> tuple[float, float, float]:
    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), colorspace=fitz.csRGB, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    x0, y0, x1, y1 = bbox
    ix0, iy0 = max(0, int(x0)), max(0, int(y0))
    ix1, iy1 = min(arr.shape[1], int(math.ceil(x1))), min(arr.shape[0], int(math.ceil(y1)))
    samples = []
    for yy in range(max(0, iy0 - 2), min(arr.shape[0], iy1 + 2)):
        for xx in range(max(0, ix0 - 2), min(arr.shape[1], ix1 + 2)):
            if ix0 <= xx < ix1 and iy0 <= yy < iy1:
                continue
            samples.append(arr[yy, xx])
    if not samples:
        return (1.0, 1.0, 1.0)
    med = np.median(np.asarray(samples), axis=0) / 255.0
    return tuple(float(x) for x in med)


def add_text_redactions(page: fitz.Page, rects: Iterable[tuple[Sequence[float], tuple[float, float, float]]]) -> None:
    for bbox, fill in rects:
        r = fitz.Rect(bbox)
        r.x0 -= 0.35; r.y0 -= 0.25; r.x1 += 0.35; r.y1 += 0.25
        page.add_redact_annot(r, fill=fill, cross_out=False)


def safe_rect(unit, units, table_bboxes: list[Sequence[float]], page: fitz.Page) -> fitz.Rect:
    r = fitz.Rect(unit.bbox)
    if unit.rotation != 0:
        r.x0 -= 0.5; r.x1 += 0.5; r.y0 -= 0.5; r.y1 += 0.5
        return r
    r.x1 = min(page.rect.width - 45, max(r.x1 + 2, 539)) if r.x0 < 100 else min(page.rect.width - 35, r.x1 + 3)
    if unit.kind in ("paragraph", "line"):
        limit = min(page.rect.height - 43, r.y1 + max(3.0, unit.font_size * 0.35))
        for other in units:
            if other is unit or other.bbox[1] <= r.y0 + 0.5:
                continue
            overlap = max(0.0, min(r.x1, other.bbox[2]) - max(r.x0, other.bbox[0]))
            if overlap >= min(r.width, other.bbox[2] - other.bbox[0]) * 0.35:
                limit = min(limit if limit > r.y1 else page.rect.height - 43, other.bbox[1] - 1.8)
                break
        for tb in table_bboxes:
            tr = fitz.Rect(tb)
            if tr.y0 > r.y0 and max(0, min(r.x1, tr.x1) - max(r.x0, tr.x0)) > 10:
                limit = min(limit, tr.y0 - 2)
        r.y1 = max(r.y1 + 1.0, limit)
    else:
        r.y0 -= 0.4; r.y1 += max(1.0, unit.font_size * 0.18)
    return r


def measure_fit(page: fitz.Page, rect: fitz.Rect, text: str, fontfile: str, size: float, align: int, rotate: int, lineheight: float) -> float:
    shape = page.new_shape()
    return shape.insert_textbox(rect, text, fontfile=fontfile, fontname="fit", fontsize=size, lineheight=lineheight, color=(0, 0, 0), align=align, rotate=rotate)


def place_unit(page: fitz.Page, unit, text: str, rect: fitz.Rect, regular_font: str, bold_font: str) -> dict:
    fontfile = bold_font if unit.bold or unit.kind in ("heading", "toc") else regular_font
    if unit.kind in ("paragraph", "line"):
        start = min(unit.font_size * 0.96, 8.4)
        minimum = 6.6
        lineheight = 1.14
        align = 0
    elif unit.kind == "heading":
        start = min(unit.font_size * 0.98, 10.5)
        minimum = 7.2
        lineheight = 1.08
        align = unit.align
    else:
        start = min(unit.font_size * 0.96, 8.2)
        minimum = 5.2
        lineheight = 1.06
        align = unit.align
    size = max(minimum, start)
    spare = -1.0
    while size >= minimum - 0.01:
        spare = measure_fit(page, rect, text, fontfile, size, align, unit.rotation, lineheight)
        if spare >= -0.05:
            break
        size -= 0.2
    overflow = spare < -0.05
    if overflow and unit.rotation == 0:
        rect.y1 = min(page.rect.height - 42, rect.y1 + max(5, unit.font_size * 1.2))
        spare = measure_fit(page, rect, text, fontfile, minimum, align, unit.rotation, 1.04)
        size = minimum
        lineheight = 1.04
        overflow = spare < -0.05
    color = unit.color if max(unit.color) > 0.2 else (0, 0, 0)
    page.insert_textbox(rect, text, fontfile=fontfile, fontname="nbbold" if fontfile == bold_font else "nbreg", fontsize=size, lineheight=lineheight, color=color, align=align, rotate=unit.rotation, overlay=True)
    return {"page": unit.page_no, "kind": unit.kind, "source": unit.text[:220], "translation": text[:220], "font_original": unit.font_size, "font_used": size, "overflow": overflow, "bbox": list(rect)}


def font_for_cell(cell: fitz.Rect, bold: bool, regular_path: str, bold_path: str) -> tuple[fitz.Font, str]:
    path = bold_path if bold else regular_path
    return fitz.Font(fontfile=path), path


def wrap_text(text: str, font: fitz.Font, size: float, width: float) -> list[str]:
    paragraphs = text.split("\n")
    lines: list[str] = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip() if current else word
            if font.text_length(candidate, fontsize=size) <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
            if font.text_length(word, fontsize=size) <= width:
                current = word
                continue
            piece = ""
            for ch in word:
                cand = piece + ch
                if font.text_length(cand, fontsize=size) <= width:
                    piece = cand
                else:
                    if piece:
                        lines.append(piece)
                    piece = ch
            current = piece
        if current:
            lines.append(current)
    return lines or [""]


def cell_source_font_size(page: fitz.Page, cell: fitz.Rect) -> float:
    sizes = []
    data = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                sb = fitz.Rect(span["bbox"])
                center = ((sb.x0 + sb.x1) / 2, (sb.y0 + sb.y1) / 2)
                if cell.contains(center) and span.get("text", "").strip():
                    sizes.append(float(span.get("size", 7)))
    return statistics.median(sizes) if sizes else 7.0


def table_cell_translation(source: str, page_no: int, translator: NLLBTranslator) -> str:
    t = norm(source)
    exact = exact_lookup(t)
    if exact is not None:
        return exact
    if page_no == 165:
        special = {
            "PLATFORM FREQUENCY RANGE": "플랫폼 /\n주파수 범위",
            "ALL AIRCRAFT (EXTERNAL OR SAFETY CRITICAL) ALL SERVICES": "전 항공기\n(외부 또는 안전필수)\n전 군",
            "AIRCRAFT INTERNAL - ARMY": "항공기 내부\n육군",
            "AIRCRAFT INTERNAL - NAVY": "항공기 내부\n해군",
            "AIRCRAFT INTERNAL - AIR FORCE": "항공기 내부\n공군",
            "SHIPS - ABOVE DECK & EXPOSED BELOW DECK **": "선박\n갑판 위 및 노출된\n갑판 아래**",
            "SUBMARINES (EXTERNAL)*": "잠수함 외부*",
            "METALLIC SHIPS - BELOW DECK": "금속 선박\n갑판 아래",
            "NON- METALLIC SHIPS - BELOW DECK": "비금속 선박\n갑판 아래",
            "NON-METALLIC SHIPS - BELOW DECK": "비금속 선박\n갑판 아래",
            "SUBMARINE (INTERNAL)": "잠수함 내부",
            "GROUND - ARMY": "지상\n육군",
            "GROUND - NAVY AND AIR FORCE": "지상\n해군·공군",
            "SPACE": "우주",
        }
        if t in special:
            return special[t]
    if not should_translate(t):
        return source
    return translator.get(t)


def table_text_spans(page: fitz.Page, table_bboxes: list[Sequence[float]]) -> list[Sequence[float]]:
    rects = []
    data = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                sb = fitz.Rect(span["bbox"])
                center = ((sb.x0 + sb.x1) / 2, (sb.y0 + sb.y1) / 2)
                if any(fitz.Rect(tb).contains(center) for tb in table_bboxes):
                    rects.append(span["bbox"])
    return rects


def place_cell(page: fitz.Page, cell_bbox: Sequence[float], text: str, source_size: float, bold: bool, regular_font: str, bold_font: str) -> dict:
    cell = fitz.Rect(cell_bbox)
    font, fontfile = font_for_cell(cell, bold, regular_font, bold_font)
    width = max(3.0, cell.width - 3.0)
    height = max(3.0, cell.height - 2.0)
    if re.fullmatch(r"[\d\s.,+\-–—±≤≥/%()]+", text):
        start = min(7.4, max(5.5, source_size))
        minimum = 5.0
    elif cell.width < 48:
        start = min(5.6, max(4.8, source_size * 0.9))
        minimum = 4.3
    elif cell.width < 80:
        start = min(6.4, max(5.2, source_size * 0.92))
        minimum = 4.8
    else:
        start = min(7.5, max(5.8, source_size * 0.95))
        minimum = 5.2
    size = start
    lines = [text]
    while size >= minimum - 0.01:
        lines = wrap_text(text, font, size, width)
        total_h = len(lines) * size * 1.18
        if total_h <= height and all(font.text_length(line, fontsize=size) <= width + 0.2 for line in lines):
            break
        size -= 0.15
    overflow = size < minimum - 0.01
    size = max(minimum, size)
    lines = wrap_text(text, font, size, width)
    total_h = len(lines) * size * 1.18
    y = cell.y0 + max(0.5, (cell.height - total_h) / 2) + size
    for line in lines:
        tw = font.text_length(line, fontsize=size)
        x = cell.x0 + max(1.0, (cell.width - tw) / 2)
        page.insert_text((x, y), line, fontfile=fontfile, fontname="tbold" if bold else "treg", fontsize=size, color=(0, 0, 0), overlay=True)
        y += size * 1.18
    return {"bbox": list(cell), "text": text, "font_used": size, "overflow": overflow or total_h > height + 0.5}


def compose_cover(page: fitz.Page, regular_font: str, bold_font: str) -> list[dict]:
    placements = []
    lines = base.extract_visual_lines(page, 1)
    redactions = []
    for line in lines:
        if should_translate(line.text) or norm(line.text) in ("METRIC", "SUPERSEDING"):
            redactions.append((line.bbox, sample_background(page, line.bbox)))
    add_text_redactions(page, redactions)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_REMOVE)
    items = [
        ((494, 18, 593, 40), "미터법", regular_font, 10.0, 1),
        ((500, 47, 592, 110), "MIL-STD-461H\n2026년 4월 17일\n────────\nMIL-STD-461G 대체\n2015년 12월 11일", regular_font, 8.5, 0),
        ((142, 156, 470, 198), "미국 국방부\n인터페이스 표준", bold_font, 13.2, 1),
        ((72, 222, 540, 283), "하위체계 및 장비의 전자기 간섭 특성\n관리 요구사항", bold_font, 14.2, 1),
        ((64, 548, 548, 578), "AMSC 10490                                      분야 EMCS\n배포문 A. 공개 배포 승인; 배포에 제한 없음.", regular_font, 8.2, 0),
        ((93, 748, 520, 770), "https://ib-lenhardt.com에서 내려받음 | IBL-Lab GmbH - MIL-STD-461H / EMC 군용 시험 및 인증", regular_font, 5.5, 1),
    ]
    for bbox, text, font, size, align in items:
        page.insert_textbox(fitz.Rect(bbox), text, fontfile=font, fontname="cover", fontsize=size, lineheight=1.12, align=align, color=(0, 0, 0), overlay=True)
        placements.append({"bbox": list(bbox), "text": text, "font_used": size, "overflow": False})
    return placements


def leader_text(page: fitz.Page, bbox: Sequence[float], title: str, page_label: str, fontfile: str, size: float, color: tuple[float, float, float]) -> None:
    r = fitz.Rect(bbox)
    font = fitz.Font(fontfile=fontfile)
    baseline = r.y1 - max(1.0, size * 0.12)
    right = min(page.rect.width - 42, 540)
    title_width = font.text_length(title, fontsize=size)
    page_width = font.text_length(page_label.strip(), fontsize=size)
    max_title_width = max(20, right - r.x0 - page_width - 8)
    while title_width > max_title_width and size > 5.4:
        size -= 0.2
        title_width = font.text_length(title, fontsize=size)
        page_width = font.text_length(page_label.strip(), fontsize=size)
        max_title_width = max(20, right - r.x0 - page_width - 8)
    page.insert_text((r.x0, baseline), title, fontfile=fontfile, fontname="toc", fontsize=size, color=color, overlay=True)
    page.insert_text((right - page_width, baseline), page_label.strip(), fontfile=fontfile, fontname="toc", fontsize=size, color=color, overlay=True)
    dot_width = font.text_length(".", fontsize=size)
    start = r.x0 + title_width + 2
    end = right - page_width - 2
    count = max(0, int((end - start) / max(0.8, dot_width)))
    if count:
        page.insert_text((start, baseline), "." * count, fontfile=fontfile, fontname="toc", fontsize=size, color=color, overlay=True)


def translate_document(src: Path, out: Path, model_dir: Path, cache_path: Path, qa_path: Path, selected_pages: set[int] | None = None) -> dict:
    regular_font = pick_file(REG_FONT_CANDIDATES)
    bold_font = pick_file(BOLD_FONT_CANDIDATES)
    source = fitz.open(src)
    page_numbers = sorted(selected_pages) if selected_pages else list(range(1, source.page_count + 1))
    texts: list[str] = []
    seen = set()
    page_data = {}
    for pno in page_numbers:
        page = source[pno - 1]
        tables = page_tables(page)
        tbboxes = [t.bbox for t in tables]
        units = units_without_tables(page, pno, tbboxes)
        page_data[pno] = (tables, tbboxes, units)
        for u in units:
            t = norm(u.text)
            if should_translate(t) and t not in seen:
                seen.add(t); texts.append(t)
        for table in tables:
            for row in table.extract():
                for cell_text in row:
                    if cell_text:
                        t = norm(cell_text)
                        if should_translate(t) and t not in seen:
                            seen.add(t); texts.append(t)
    translator = NLLBTranslator(model_dir, cache_path)
    translator.load()
    translator.translate_all(texts)
    if selected_pages:
        doc = fitz.open()
        for pno in page_numbers:
            doc.insert_pdf(source, from_page=pno - 1, to_page=pno - 1)
        page_map = {pno: idx for idx, pno in enumerate(page_numbers)}
    else:
        doc = fitz.open(src)
        page_map = {pno: pno - 1 for pno in page_numbers}
    qa_placements = []
    table_qa = []
    page_issues = []
    for count, pno in enumerate(page_numbers, start=1):
        page = doc[page_map[pno]]
        original_page = source[pno - 1]
        tables, tbboxes, units = page_data[pno]
        if pno == 1:
            qa_placements.extend(compose_cover(page, regular_font, bold_font))
            continue
        todo_units = []
        redactions = []
        toc_tasks = []
        for u in units:
            source_text = norm(u.text)
            if not should_translate(source_text):
                continue
            translated = translator.get(source_text)
            if translated == source_text and not KOREAN_RE.search(translated):
                continue
            bg = sample_background(original_page, u.bbox)
            redactions.append((u.bbox, bg))
            m = TOC_RE.match(source_text) if 3 <= pno <= 14 else None
            if m:
                toc_tasks.append((u, translator.get(norm(m.group(1))), m.group(3), bg))
            else:
                todo_units.append((u, translated, bg))
        if tables:
            for span_bbox in table_text_spans(original_page, tbboxes):
                redactions.append((span_bbox, (1.0, 1.0, 1.0)))
        add_text_redactions(page, redactions)
        if redactions:
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE, text=fitz.PDF_REDACT_TEXT_REMOVE)
        for table in tables:
            extracted = table.extract()
            for r_idx, row in enumerate(table.rows):
                for c_idx, cell_bbox in enumerate(row.cells):
                    if cell_bbox is None:
                        continue
                    source_text = extracted[r_idx][c_idx] if r_idx < len(extracted) and c_idx < len(extracted[r_idx]) else ""
                    if source_text is None or not str(source_text).strip():
                        continue
                    text = table_cell_translation(str(source_text), pno, translator)
                    source_size = cell_source_font_size(original_page, fitz.Rect(cell_bbox))
                    is_header = r_idx < 2 or (should_translate(str(source_text)) and not re.search(r"\d", str(source_text)))
                    result = place_cell(page, cell_bbox, text, source_size, is_header, regular_font, bold_font)
                    result.update({"page": pno, "source": str(source_text)[:180]})
                    table_qa.append(result)
        for u, translated, _bg in todo_units:
            rect = safe_rect(u, units, tbboxes, page)
            qa_placements.append(place_unit(page, u, translated, rect, regular_font, bold_font))
        for u, title, page_label, _bg in toc_tasks:
            color = u.color if max(u.color) > 0.2 else (0.0, 0.0, 0.8)
            leader_text(page, u.bbox, title, page_label, bold_font if u.bold else regular_font, max(5.8, min(8.2, u.font_size * 0.96)), color)
            qa_placements.append({"page": pno, "kind": "toc", "source": u.text, "translation": title, "font_used": max(5.8, min(8.2, u.font_size * 0.96)), "overflow": False, "bbox": list(u.bbox)})
        extracted_text = page.get_text("text")
        if should_translate(original_page.get_text("text")) and not KOREAN_RE.search(extracted_text):
            page_issues.append({"page": pno, "issue": "no_korean_text"})
        if count % 20 == 0 or count == len(page_numbers):
            print(f"Composed {count}/{len(page_numbers)} pages", flush=True)
    metadata = doc.metadata or {}
    metadata.update({"title": "MIL-STD-461H 한국어 전체 번역본 - 교정판", "subject": "원문 레이아웃 보존 비공식 한국어 번역본; 영문 원문 우선"})
    doc.set_metadata(metadata)
    doc.save(out, garbage=4, deflate=True, clean=True)
    doc.close(); source.close()
    qa = {
        "source": str(src), "output": str(out), "pages_processed": page_numbers,
        "page_count": len(page_numbers) if selected_pages else 294,
        "model": MODEL_NAME, "font_regular": regular_font, "font_bold": bold_font,
        "placements": len(qa_placements), "table_cells": len(table_qa),
        "body_overflow_count": sum(1 for x in qa_placements if x.get("overflow")),
        "table_overflow_count": sum(1 for x in table_qa if x.get("overflow")),
        "small_body_text": [x for x in qa_placements if x.get("font_used", 99) < 6.5][:300],
        "small_table_text": [x for x in table_qa if x.get("font_used", 99) < 4.5][:300],
        "body_overflows": [x for x in qa_placements if x.get("overflow")][:300],
        "table_overflows": [x for x in table_qa if x.get("overflow")][:300],
        "page_issues": page_issues,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(src: Path, out: Path, qa_path: Path, result_path: Path, selected_pages: list[int] | None = None) -> dict:
    source = fitz.open(src); output = fitz.open(out)
    expected_pages = len(selected_pages) if selected_pages else 294
    geometry = []
    image_mismatch = []
    residual_pages = []
    for idx in range(output.page_count):
        source_idx = selected_pages[idx] - 1 if selected_pages else idx
        sp, op = source[source_idx], output[idx]
        if tuple(sp.mediabox) != tuple(op.mediabox) or sp.rotation != op.rotation:
            geometry.append(idx + 1)
        if len(sp.get_images(full=True)) != len(op.get_images(full=True)):
            image_mismatch.append({"page": idx + 1, "source": len(sp.get_images(full=True)), "output": len(op.get_images(full=True))})
        text = op.get_text("text")
        stripped = ALLOWED_ENGLISH.sub("", text)
        residual = sorted(set(w for w in ENGLISH_RE.findall(stripped) if len(w) > 2 and not w.isupper()))
        if residual:
            residual_pages.append({"page": idx + 1, "words": residual[:50]})
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    result = {
        "expected_pages": expected_pages, "output_pages": output.page_count,
        "page_count_equal": output.page_count == expected_pages,
        "geometry_mismatch_pages": geometry,
        "image_count_mismatch_pages": image_mismatch,
        "body_overflow_count": qa.get("body_overflow_count"),
        "table_overflow_count": qa.get("table_overflow_count"),
        "residual_english_pages": residual_pages,
    }
    result["validated"] = bool(result["page_count_equal"] and not geometry and not image_mismatch and not qa.get("body_overflow_count") and not qa.get("table_overflow_count"))
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    source.close(); output.close()
    return result


def make_comparison(src: Path, out: Path, target: Path, selected_pages: list[int]) -> None:
    source = fitz.open(src); output = fitz.open(out)
    panels = []
    for idx, pno in enumerate(selected_pages):
        sp = source[pno - 1].get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
        op = output[idx].get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
        a = Image.frombytes("RGB", (sp.width, sp.height), sp.samples)
        b = Image.frombytes("RGB", (op.width, op.height), op.samples)
        panels.append((pno, a, b))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    width = max(a.width for _, a, _ in panels)
    total_h = sum(max(a.height, b.height) + 34 for _, a, b in panels)
    canvas = Image.new("RGB", (width * 2, total_h), "white")
    draw = ImageDraw.Draw(canvas)
    y = 0
    for pno, a, b in panels:
        draw.text((5, y + 5), f"ORIGINAL p{pno}", font=font, fill="black")
        draw.text((width + 5, y + 5), f"REVISION p{pno}", font=font, fill="black")
        canvas.paste(a, (0, y + 34)); canvas.paste(b, (width, y + 34))
        y += max(a.height, b.height) + 34
    canvas.save(target)
    source.close(); output.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--pages", default="")
    args = parser.parse_args()
    src = Path(args.source)
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    selected = [int(x) for x in args.pages.split(",") if x.strip()] if args.pages else None
    suffix = "_SAMPLE" if selected else ""
    out = outdir / f"MIL_STD_461H_2026_KO_REVISION2{suffix}.pdf"
    cache = outdir / "translation_cache_revision2.json"
    qa = outdir / f"MIL_STD_461H_2026_KO_REVISION2{suffix}_QA.json"
    validation = outdir / f"MIL_STD_461H_2026_KO_REVISION2{suffix}_VALIDATION.json"
    comparison = outdir / f"MIL_STD_461H_2026_KO_REVISION2{suffix}_COMPARISON.png"
    hashes = outdir / "SHA256SUMS.txt"
    translate_document(src, out, Path(args.model_dir), cache, qa, set(selected) if selected else None)
    result = validate(src, out, qa, validation, selected)
    compare_pages = selected or [1, 3, 21, 40, 84, 118, 165, 166, 292, 294]
    make_comparison(src, out, comparison, compare_pages)
    hashes.write_text(f"{sha256(out)}  {out.name}\n{sha256(qa)}  {qa.name}\n{sha256(validation)}  {validation.name}\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "validation": result, "size": out.stat().st_size}, ensure_ascii=False, indent=2), flush=True)
    if not result["page_count_equal"] or result["geometry_mismatch_pages"] or result["image_count_mismatch_pages"]:
        sys.exit(3)

if __name__ == "__main__":
    main()
