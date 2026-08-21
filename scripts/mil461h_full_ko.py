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
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import fitz
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_CANDIDATES = (
    "Helsinki-NLP/opus-mt-tc-big-en-ko",
    "Helsinki-NLP/opus-mt-en-ko",
)
REG_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf",
)
BOLD_FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
)
GLOSSARY = {
    "requirements for the control of electromagnetic interference characteristics of subsystems and equipment": "하위체계 및 장비의 전자기 간섭 특성 관리 요구사항",
    "electromagnetic interference test procedures": "전자기 간섭 시험 절차",
    "electromagnetic interference control procedures": "전자기 간섭 관리 절차",
    "electromagnetic interference test report": "전자기 간섭 시험 보고서",
    "line impedance stabilization network": "선로 임피던스 안정화 회로망",
    "radiated susceptibility, transient electromagnetic field": "방사 내성, 과도 전자기장",
    "radiated susceptibility, electric field": "방사 내성, 전계",
    "conducted susceptibility": "전도 내성",
    "radiated susceptibility": "방사 내성",
    "conducted emissions": "전도 방출",
    "radiated emissions": "방사 방출",
    "electromagnetic environmental effects": "전자기 환경 영향",
    "electromagnetic compatibility": "전자기 적합성",
    "electromagnetic environment": "전자기 환경",
    "electromagnetic interference": "전자기 간섭",
    "transient protection device": "과도 보호소자",
    "equipment under test": "시험대상장비",
    "government furnished equipment": "정부 제공 장비",
    "non-developmental item": "비개발품",
    "commercial item": "상용품",
    "measurement receiver": "측정 수신기",
    "signal generator": "신호 발생기",
    "power amplifier": "전력 증폭기",
    "electric field sensor": "전계 센서",
    "test setup boundary": "시험 구성 경계",
    "shielded enclosure": "차폐 함체",
    "shielded room": "차폐실",
    "ground plane": "접지면",
    "procuring activity": "조달기관",
    "procurement specification": "조달 규격서",
    "verification requirements": "검증 요구사항",
    "interface requirements": "인터페이스 요구사항",
    "general requirements": "일반 요구사항",
    "test procedures": "시험 절차",
    "data presentation": "자료 제시",
    "applicability": "적용성",
    "frequency scanning": "주파수 스캔",
    "measurement tolerances": "측정 허용오차",
    "radio frequency": "무선주파수",
    "effective radiated power": "유효 방사전력",
    "electrostatic discharge": "정전기 방전",
    "full width half maximum": "반치전폭",
    "root mean square": "실효값",
    "transverse electromagnetic": "횡전자기",
    "fast Fourier transform": "고속 푸리에 변환",
    "Federal Communications Commission": "미국 연방통신위원회",
    "International Organization for Standardization": "국제표준화기구",
    "Defense Standardization Program Office": "국방 표준화 프로그램 사무국",
}
EXACT_TRANSLATIONS = {
    "METRIC": "미터법",
    "SUPERSEDING": "대체 문서",
    "DEPARTMENT OF DEFENSE": "미국 국방부",
    "INTERFACE STANDARD": "인터페이스 표준",
    "FOREWORD": "서문",
    "CONTENTS": "목차",
    "FIGURES": "그림 목록",
    "TABLES": "표 목록",
    "SCOPE": "적용범위",
    "APPLICABLE PUBLICATIONS": "적용 문서",
    "DEFINITIONS": "정의",
    "GENERAL REQUIREMENTS": "일반 요구사항",
    "DETAILED REQUIREMENTS": "세부 요구사항",
    "NOTES": "주",
    "APPENDIX A": "부록 A",
    "CONCLUDING MATERIAL": "마무리 자료",
    "Custodians:": "관리기관:",
    "Preparing activity:": "작성기관:",
    "Review activities:": "검토기관:",
    "PARAGRAPH": "항목",
    "PAGE": "쪽",
    "Purpose.": "목적.",
    "General.": "일반.",
    "Setup.": "시험 구성.",
    "Procedures.": "절차.",
    "Test equipment.": "시험 장비.",
    "Data presentation.": "자료 제시.",
    "Optional": "선택사항",
    "All": "전체",
    "Army": "육군",
    "Navy": "해군",
    "Air Force": "공군",
    "Floor": "바닥",
    "Wall": "벽",
    "Ceiling": "천장",
    "Power Input": "전원 입력",
    "Signal Generator": "신호 발생기",
    "Measurement Receiver": "측정 수신기",
    "Injection Probe": "주입 프로브",
    "Monitor Probe": "감시 프로브",
    "Test Setup Boundary": "시험 구성 경계",
    "Downloaded from https://ib-lenhardt.com  |  IBL-Lab GmbH - MIL-STD-461H / EMC Military Testing & Certification": "https://ib-lenhardt.com에서 내려받음  |  IBL-Lab GmbH - MIL-STD-461H / EMC 군용 시험 및 인증",
}
PRESERVE_RE = re.compile(
    r"(?:https?://\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
    r"MIL-STD-\d+[A-Z]?|SD-\d+|"
    r"(?:CE|CS|RE|RS)\d{3}|"
    r"\b(?:AMSC|AREA|ASSIST|DoD|DOD|EMC|EME|EMI|EMICP|EMITP|EMITR|ERP|ESD|EUT|FCC|FFT|FWHM|GFE|IF|ISO|LISN|MAD|NDI|RF|RMS|TEM|TPD|CI|CW|DC|AC|NIST|DTRA|DISA|NSA)\b|"
    r"\b\d+(?:\.\d+)*(?:\([a-zA-Z0-9]+\))*\b|"
    r"\b\d+(?:\.\d+)?\s*(?:Hz|kHz|MHz|GHz|dB|dBm|V/m|V|A|W|kW|m|cm|mm|ns|μs|ms|μF|ohm|Ω|%)\b)"
)
TOC_RE = re.compile(r"^(.*?)(\.{4,})(\s*[ivxlcdmIVXLCDM]+|\s*\d+)\s*$")
SECTION_HEADING_RE = re.compile(r"^\s*\d+(?:\.\d+)+(?:\.\d+)*\s+.+")
BULLET_RE = re.compile(r"^\s*(?:[a-z]\.|\([a-z0-9]+\)|\d+\.|\*|-)\s+", re.I)
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{2,}")
KOREAN_RE = re.compile(r"[가-힣]")

@dataclass
class VisualLine:
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    bold: bool
    italic: bool
    color: tuple[float, float, float]
    rotation: int
    x0: float
    width: float
    height: float
    page_no: int
    source_indices: tuple[int, ...]

@dataclass
class TextUnit:
    text: str
    bbox: tuple[float, float, float, float]
    font_size: float
    bold: bool
    italic: bool
    color: tuple[float, float, float]
    rotation: int
    align: int
    page_no: int
    kind: str
    line_count: int

def pick_file(candidates: Sequence[str]) -> str:
    for p in candidates:
        if Path(p).exists():
            return p
    raise FileNotFoundError(f"No usable font found: {candidates}")

def int_color_to_rgb(value: int) -> tuple[float, float, float]:
    return (((value >> 16) & 255) / 255.0, ((value >> 8) & 255) / 255.0, (value & 255) / 255.0)

def norm_text(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text.strip()

def should_translate(text: str) -> bool:
    t = norm_text(text)
    if not t or not ENGLISH_WORD_RE.search(t):
        return False
    if re.fullmatch(r"[\d\s.,;:()\[\]{}<>+=×÷/\\|_\-–—°πμΩ%]+", t):
        return False
    if re.fullmatch(r"(?:MIL-STD-\d+[A-Z]?|(?:CE|CS|RE|RS)\d{3}|[A-Z0-9/._-]{2,})", t):
        return False
    if len(ENGLISH_WORD_RE.findall(t)) == 1 and len(t) <= 3:
        return False
    return True

def infer_rotation(line: dict) -> int:
    dx, dy = line.get("dir", (1.0, 0.0))
    angle = int(round(math.degrees(math.atan2(-dy, dx)))) % 360
    if angle <= 10 or angle >= 350:
        return 0
    if 80 <= angle <= 100:
        return 90
    if 170 <= angle <= 190:
        return 180
    if 260 <= angle <= 280:
        return 270
    return angle

def extract_visual_lines(page: fitz.Page, page_no: int) -> list[VisualLine]:
    raw: list[VisualLine] = []
    idx = 0
    data = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s.get("text", "") for s in spans).rstrip("\n")
            bbox = tuple(float(x) for x in line["bbox"])
            sizes = [float(s.get("size", 10.0)) for s in spans if s.get("text", "").strip()]
            fs = statistics.median(sizes) if sizes else 10.0
            bold = any("bold" in s.get("font", "").lower() or (int(s.get("flags", 0)) & 16) for s in spans)
            italic = any("italic" in s.get("font", "").lower() or (int(s.get("flags", 0)) & 2) for s in spans)
            colors = [int_color_to_rgb(int(s.get("color", 0))) for s in spans if s.get("text", "").strip()]
            color = tuple(statistics.median(c[i] for c in colors) for i in range(3)) if colors else (0.0, 0.0, 0.0)
            rot = infer_rotation(line)
            raw.append(VisualLine(text=text, bbox=bbox, font_size=fs, bold=bold, italic=italic,
                                  color=color, rotation=rot, x0=bbox[0], width=bbox[2]-bbox[0],
                                  height=bbox[3]-bbox[1], page_no=page_no, source_indices=(idx,)))
            idx += 1
    raw.sort(key=lambda x: (round(x.bbox[1], 1), x.bbox[0]))
    merged: list[VisualLine] = []
    i = 0
    while i < len(raw):
        cur = raw[i]
        group = [cur]
        j = i + 1
        while j < len(raw):
            nxt = raw[j]
            if nxt.rotation != cur.rotation or abs(nxt.bbox[1] - cur.bbox[1]) > 1.5:
                break
            gap = nxt.bbox[0] - group[-1].bbox[2]
            if gap <= 36 and cur.bold == nxt.bold:
                group.append(nxt)
                j += 1
            else:
                break
        if len(group) > 1:
            text_parts = []
            for k, g in enumerate(group):
                if k:
                    gap = g.bbox[0] - group[k-1].bbox[2]
                    text_parts.append(" " * max(1, min(8, int(round(gap / max(3.0, cur.font_size * 0.45))))))
                text_parts.append(g.text.strip())
            bbox = (min(g.bbox[0] for g in group), min(g.bbox[1] for g in group),
                    max(g.bbox[2] for g in group), max(g.bbox[3] for g in group))
            merged.append(VisualLine(text="".join(text_parts), bbox=bbox,
                                     font_size=statistics.median(g.font_size for g in group),
                                     bold=all(g.bold for g in group), italic=all(g.italic for g in group),
                                     color=group[0].color, rotation=cur.rotation, x0=bbox[0],
                                     width=bbox[2]-bbox[0], height=bbox[3]-bbox[1], page_no=page_no,
                                     source_indices=tuple(x for g in group for x in g.source_indices)))
            i = j
        else:
            merged.append(cur)
            i += 1
    return merged

def infer_alignment(bbox: Sequence[float], page_w: float, text: str) -> int:
    x0, _, x1, _ = bbox
    width = x1 - x0
    center = (x0 + x1) / 2
    if width < page_w * 0.72 and abs(center - page_w / 2) < page_w * 0.08:
        return 1
    if x0 > page_w * 0.58:
        return 2
    return 0

def make_units(page: fitz.Page, page_no: int) -> list[TextUnit]:
    lines = extract_visual_lines(page, page_no)
    units: list[TextUnit] = []
    page_w = page.rect.width
    i = 0
    while i < len(lines):
        line = lines[i]
        t = norm_text(line.text)
        if not t:
            i += 1
            continue
        if line.rotation not in (0, 90, 180, 270):
            i += 1
            continue
        is_toc = bool(TOC_RE.match(t))
        is_heading = line.bold or SECTION_HEADING_RE.match(t) or t.isupper()
        is_narrow = line.width < 250 or line.rotation != 0
        if is_toc or is_heading or is_narrow:
            align = infer_alignment(line.bbox, page_w, line.text)
            kind = "toc" if is_toc else ("heading" if is_heading else "label")
            units.append(TextUnit(t, line.bbox, line.font_size, line.bold, line.italic,
                                  line.color, line.rotation, align, page_no, kind, 1))
            i += 1
            continue
        group = [line]
        j = i + 1
        prev = line
        while j < len(lines):
            nxt = lines[j]
            nt = norm_text(nxt.text)
            if not nt or nxt.rotation != 0 or nxt.bold or nxt.width < 250:
                break
            vgap = nxt.bbox[1] - prev.bbox[3]
            typical = max(2.0, statistics.median([g.height for g in group]) * 0.25)
            if vgap > max(5.0, typical * 2.2):
                break
            if BULLET_RE.match(nt) and len(group) > 0:
                break
            if abs(nxt.x0 - line.x0) > 48 and not BULLET_RE.match(norm_text(group[0].text)):
                break
            group.append(nxt)
            prev = nxt
            j += 1
        if len(group) == 1:
            units.append(TextUnit(t, line.bbox, line.font_size, line.bold, line.italic,
                                  line.color, line.rotation, infer_alignment(line.bbox, page_w, t),
                                  page_no, "line", 1))
        else:
            text = re.sub(r"\s+", " ", " ".join(norm_text(g.text) for g in group)).strip()
            bbox = (min(g.bbox[0] for g in group), min(g.bbox[1] for g in group),
                    max(g.bbox[2] for g in group), max(g.bbox[3] for g in group))
            units.append(TextUnit(text, bbox, statistics.median(g.font_size for g in group),
                                  False, False, group[0].color, 0, 0, page_no, "paragraph", len(group)))
        i = j if len(group) > 1 else i + 1
    return units

def protect_text(text: str) -> tuple[str, dict[str, str]]:
    exact = EXACT_TRANSLATIONS.get(text.strip())
    if exact is not None:
        return "ZXQEXACT0QXZ", {"ZXQEXACT0QXZ": exact}
    mapping: dict[str, str] = {}
    counter = 0
    def token(value: str, replacement: str | None = None) -> str:
        nonlocal counter
        key = f"ZXQPH{counter:04d}QXZ"
        counter += 1
        mapping[key] = replacement if replacement is not None else value
        return key
    work = text
    for phrase, ko in sorted(GLOSSARY.items(), key=lambda kv: len(kv[0]), reverse=True):
        pattern = re.compile(re.escape(phrase), re.I)
        while True:
            m = pattern.search(work)
            if not m:
                break
            key = token(m.group(0), ko)
            work = work[:m.start()] + key + work[m.end():]
    pos = 0
    parts: list[str] = []
    for m in PRESERVE_RE.finditer(work):
        parts.append(work[pos:m.start()])
        parts.append(token(m.group(0)))
        pos = m.end()
    parts.append(work[pos:])
    return "".join(parts), mapping

def restore_text(text: str, mapping: dict[str, str]) -> str:
    out = text
    out = re.sub(r"Z\s*X\s*Q\s*(PH|EXACT)\s*(\d+)\s*Q\s*X\s*Z", lambda m: f"ZXQ{m.group(1)}{int(m.group(2)):04d}QXZ" if m.group(1)=="PH" else f"ZXQEXACT{int(m.group(2))}QXZ", out, flags=re.I)
    for key, value in mapping.items():
        out = out.replace(key, value)
    out = out.replace("ZXQ", "")
    out = re.sub(r"\s+([,.;:!?%)\]])", r"\1", out)
    out = re.sub(r"([([])\s+", r"\1", out)
    return re.sub(r"\s{2,}", " ", out).strip()

def split_for_model(text: str, tokenizer, max_tokens: int = 380) -> list[str]:
    if len(tokenizer(text, add_special_tokens=True)["input_ids"]) <= max_tokens:
        return [text]
    pieces = re.split(r"(?<=[.!?;:])\s+|\n+", text)
    chunks: list[str] = []
    cur = ""
    for p in pieces:
        p = p.strip()
        if not p:
            continue
        candidate = (cur + " " + p).strip() if cur else p
        if len(tokenizer(candidate, add_special_tokens=True)["input_ids"]) <= max_tokens:
            cur = candidate
        else:
            if cur:
                chunks.append(cur)
            if len(tokenizer(p, add_special_tokens=True)["input_ids"]) <= max_tokens:
                cur = p
            else:
                sub = ""
                for w in p.split():
                    cand = (sub + " " + w).strip() if sub else w
                    if len(tokenizer(cand, add_special_tokens=True)["input_ids"]) <= max_tokens:
                        sub = cand
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = w
                cur = sub
    if cur:
        chunks.append(cur)
    return chunks or [text]

class Translator:
    def __init__(self, cache_path: Path):
        self.cache_path = cache_path
        self.cache: dict[str, str] = {}
        if cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}
        self.tokenizer = None
        self.model = None
        self.model_name = None
        self.prefix = ""
    def load(self) -> None:
        torch.set_num_threads(max(1, min(4, os.cpu_count() or 2)))
        errors = []
        for model_name in MODEL_CANDIDATES:
            try:
                print(f"Loading translation model: {model_name}", flush=True)
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                model.eval()
                self.tokenizer, self.model, self.model_name = tokenizer, model, model_name
                self.prefix = self._detect_prefix()
                print(f"Model ready: {model_name}; prefix={self.prefix!r}", flush=True)
                return
            except Exception as exc:
                errors.append(f"{model_name}: {exc!r}")
        raise RuntimeError("Could not load translation model: " + " | ".join(errors))
    def _detect_prefix(self) -> str:
        tests = ["", ">>kor_Hang<< ", ">>ko<< "]
        src = "This requirement is applicable to equipment enclosures and interconnecting cables."
        for prefix in tests:
            try:
                out = self._translate_batch_raw([prefix + src], max_new_tokens=160)[0]
                if KOREAN_RE.search(out):
                    return prefix
            except Exception:
                continue
        return ""
    @torch.inference_mode()
    def _translate_batch_raw(self, batch: list[str], max_new_tokens: int = 520) -> list[str]:
        toks = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        outputs = self.model.generate(**toks, max_new_tokens=max_new_tokens, num_beams=2, do_sample=False,
                                      length_penalty=1.0, early_stopping=True)
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
    def translate_all(self, texts: Iterable[str], batch_size: int = 8) -> None:
        pending: list[tuple[str, list[str], list[dict[str, str]]]] = []
        for original in texts:
            if original in self.cache:
                continue
            if not should_translate(original):
                self.cache[original] = original
                continue
            toc = TOC_RE.match(original)
            if toc:
                label, dots, page = toc.groups()
                protected, mp = protect_text(label.strip())
                pending.append((original, [self.prefix + protected], [mp | {"__TOC_DOTS__": dots, "__TOC_PAGE__": page}]))
                continue
            protected, mp = protect_text(original)
            chunks = split_for_model(protected, self.tokenizer)
            pending.append((original, [self.prefix + c for c in chunks], [mp for _ in chunks]))
        flat: list[tuple[str, int, str, dict[str, str]]] = []
        for original, chunks, maps in pending:
            for idx, (chunk, mp) in enumerate(zip(chunks, maps)):
                flat.append((original, idx, chunk, mp))
        print(f"Translation cache={len(self.cache)}; pending blocks={len(pending)}, chunks={len(flat)}", flush=True)
        translated_chunks: dict[str, dict[int, str]] = {}
        start = time.time()
        for offset in range(0, len(flat), batch_size):
            batch_meta = flat[offset:offset + batch_size]
            outputs = self._translate_batch_raw([x[2] for x in batch_meta])
            for (original, idx, _chunk, mp), out in zip(batch_meta, outputs):
                translated_chunks.setdefault(original, {})[idx] = restore_text(out, mp)
            if (offset // batch_size) % 20 == 0 or offset + batch_size >= len(flat):
                elapsed = max(1.0, time.time() - start)
                done = min(len(flat), offset + batch_size)
                print(f"Translated {done}/{len(flat)} chunks ({done/elapsed:.2f} chunks/s)", flush=True)
                self._flush_partial(pending, translated_chunks)
        self._flush_partial(pending, translated_chunks, final=True)
    def _flush_partial(self, pending, translated_chunks, final: bool = False) -> None:
        for original, chunks, _maps in pending:
            got = translated_chunks.get(original, {})
            if len(got) != len(chunks):
                continue
            text = " ".join(got[i].strip() for i in range(len(chunks)) if got[i].strip()).strip()
            toc = TOC_RE.match(original)
            if toc:
                _label, dots, page = toc.groups()
                text = f"{text} {dots}{page}"
            if not KOREAN_RE.search(text) and should_translate(original):
                text = original
            self.cache[original] = text
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding="utf-8")
        if final:
            print(f"Saved translation cache: {len(self.cache)} entries", flush=True)
    def get(self, text: str) -> str:
        return self.cache.get(text, text)

def page_background_pixmap(page: fitz.Page) -> tuple[np.ndarray, float, float]:
    pix = page.get_pixmap(matrix=fitz.Matrix(1, 1), colorspace=fitz.csRGB, alpha=False)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    return arr, pix.width / page.rect.width, pix.height / page.rect.height

def sample_background(arr: np.ndarray, sx: float, sy: float, bbox: Sequence[float]) -> tuple[float, float, float]:
    x0, y0, x1, y1 = bbox
    ix0, iy0 = max(0, int(x0 * sx)), max(0, int(y0 * sy))
    ix1, iy1 = min(arr.shape[1], int(math.ceil(x1 * sx))), min(arr.shape[0], int(math.ceil(y1 * sy)))
    if ix1 <= ix0 or iy1 <= iy0:
        return (1.0, 1.0, 1.0)
    samples = []
    for yy in range(max(0, iy0-2), min(arr.shape[0], iy1+2)):
        for xx in range(max(0, ix0-2), min(arr.shape[1], ix1+2)):
            if iy0 <= yy < iy1 and ix0 <= xx < ix1:
                continue
            samples.append(arr[yy, xx])
    if not samples:
        samples = [arr[min(arr.shape[0]-1, (iy0+iy1)//2), min(arr.shape[1]-1, (ix0+ix1)//2)]]
    med = np.median(np.asarray(samples), axis=0) / 255.0
    return tuple(float(x) for x in med)

def measure_fit(page: fitz.Page, rect: fitz.Rect, text: str, fontfile: str, fontsize: float,
                align: int, rotation: int, lineheight: float) -> float:
    shape = page.new_shape()
    return shape.insert_textbox(rect, text, fontfile=fontfile, fontname="kofit", fontsize=fontsize,
                                lineheight=lineheight, color=(0, 0, 0), align=align, rotate=rotation,
                                render_mode=0)

def place_text_fit(page: fitz.Page, unit: TextUnit, text: str, regular_font: str, bold_font: str) -> dict:
    rect = fitz.Rect(unit.bbox)
    if unit.rotation == 0:
        rect.y0 -= 0.4
        rect.y1 += max(0.8, unit.font_size * 0.15)
        rect.x1 += 1.5
    else:
        rect.x0 -= 0.5; rect.x1 += 0.5; rect.y0 -= 0.5; rect.y1 += 0.5
    fontfile = bold_font if unit.bold else regular_font
    start_size = max(4.2, unit.font_size * (0.96 if unit.kind == "paragraph" else 0.94))
    min_size = max(3.4, unit.font_size * 0.52)
    lineheight = 1.08 if unit.kind in ("paragraph", "line") else 1.02
    size = start_size
    fit_value = -1.0
    while size >= min_size:
        fit_value = measure_fit(page, rect, text, fontfile, size, unit.align, unit.rotation, lineheight)
        if fit_value >= -0.05:
            break
        size -= 0.3
    overflow = fit_value < -0.05
    if overflow:
        size = min_size
        if unit.rotation == 0:
            rect.y1 += unit.font_size * max(1.0, unit.line_count * 0.25)
    color = unit.color if max(unit.color) >= 0.15 else (0.0, 0.0, 0.0)
    page.insert_textbox(rect, text, fontfile=fontfile, fontname="kobold" if unit.bold else "koreg",
                        fontsize=size, lineheight=lineheight, color=color, align=unit.align,
                        rotate=unit.rotation, overlay=True)
    return {"font_size_original": unit.font_size, "font_size_used": size, "overflow": overflow,
            "bbox": list(unit.bbox), "kind": unit.kind, "page": unit.page_no,
            "source": unit.text[:180], "translation": text[:180]}

def translate_pdf(src: Path, out: Path, cache_path: Path, qa_path: Path) -> dict:
    regular_font = pick_file(REG_FONT_CANDIDATES)
    bold_font = pick_file(BOLD_FONT_CANDIDATES)
    source_doc = fitz.open(src)
    all_units: list[list[TextUnit]] = []
    unique_texts: list[str] = []
    seen = set()
    for pno, page in enumerate(source_doc, start=1):
        units = make_units(page, pno)
        all_units.append(units)
        for u in units:
            if should_translate(u.text) and u.text not in seen:
                seen.add(u.text); unique_texts.append(u.text)
    print(f"Pages={source_doc.page_count}; units={sum(map(len, all_units))}; unique translatable={len(unique_texts)}", flush=True)
    translator = Translator(cache_path)
    translator.load()
    translator.translate_all(unique_texts)
    doc = fitz.open(src)
    placements: list[dict] = []
    pages_with_korean = set()
    for pno, (page, units) in enumerate(zip(doc, all_units), start=1):
        if not units:
            continue
        for link in list(page.get_links()):
            try:
                page.delete_link(link)
            except Exception:
                pass
        arr, sx, sy = page_background_pixmap(page)
        todo: list[tuple[TextUnit, str, tuple[float, float, float]]] = []
        for unit in units:
            if not should_translate(unit.text):
                continue
            translated = translator.get(unit.text)
            if translated == unit.text and not KOREAN_RE.search(translated):
                continue
            bg = sample_background(arr, sx, sy, unit.bbox)
            todo.append((unit, translated, bg))
            rect = fitz.Rect(unit.bbox)
            rect.x0 -= 0.35; rect.y0 -= 0.25; rect.x1 += 0.35; rect.y1 += 0.25
            page.add_redact_annot(rect, fill=bg, cross_out=False)
        if todo:
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                                  text=fitz.PDF_REDACT_TEXT_REMOVE)
            for unit, translated, _bg in todo:
                placements.append(place_text_fit(page, unit, translated, regular_font, bold_font))
                if KOREAN_RE.search(translated):
                    pages_with_korean.add(pno)
        if pno % 25 == 0 or pno == doc.page_count:
            print(f"Composed {pno}/{doc.page_count} pages", flush=True)
    metadata = doc.metadata or {}
    metadata.update({"title": "MIL-STD-461H 한국어 전체 번역본", "subject": "비공식 한국어 번역본 - 영문 원문 우선",
                     "keywords": "MIL-STD-461H, EMC, EMI, 한국어 번역"})
    doc.set_metadata(metadata)
    doc.save(out, garbage=4, deflate=True, clean=True)
    doc.close(); source_doc.close()
    font_ratios = [p["font_size_used"] / p["font_size_original"] for p in placements if p["font_size_original"]]
    qa = {
        "source": str(src), "output": str(out), "page_count": len(all_units),
        "unit_count": sum(map(len, all_units)), "unique_translated_texts": len(unique_texts),
        "placements": len(placements), "pages_with_korean": sorted(pages_with_korean),
        "overflow_count": sum(1 for p in placements if p["overflow"]),
        "font_scale_min": min(font_ratios) if font_ratios else None,
        "font_scale_median": statistics.median(font_ratios) if font_ratios else None,
        "small_font_placements": [p for p in placements if p["font_size_used"] < 5.0][:200],
        "overflow_samples": [p for p in placements if p["overflow"]][:200],
        "model": translator.model_name,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa

def validate(src: Path, out: Path, qa_path: Path, regression_path: Path, comparison_path: Path) -> dict:
    s = fitz.open(src); o = fitz.open(out)
    result = {"source_pages": s.page_count, "output_pages": o.page_count,
              "page_count_equal": s.page_count == o.page_count == 294}
    geometry_mismatch = []
    image_mismatch = []
    pages_without_korean = []
    residual_samples = []
    korean_pages = 0
    source_english_pages = 0
    allowed_words = {"MIL", "STD", "AMSC", "AREA", "ASSIST", "DoD", "DOD", "EMC", "EME", "EMI", "EMICP", "EMITP", "EMITR", "ERP", "ESD", "EUT", "FCC", "FFT", "FWHM", "GFE", "IF", "ISO", "LISN", "MAD", "NDI", "RF", "RMS", "TEM", "TPD", "CI", "CW", "DC", "AC", "NIST", "DTRA", "DISA", "NSA", "IBL", "Lab", "GmbH", "Hz", "kHz", "MHz", "GHz", "dB", "dBm"}
    for i in range(s.page_count):
        sp, op = s[i], o[i]
        if tuple(sp.mediabox) != tuple(op.mediabox) or tuple(sp.cropbox) != tuple(op.cropbox) or sp.rotation != op.rotation:
            geometry_mismatch.append(i+1)
        si, oi = len(sp.get_images(full=True)), len(op.get_images(full=True))
        if si != oi:
            image_mismatch.append({"page": i+1, "source": si, "output": oi})
        st, ot = sp.get_text("text"), op.get_text("text")
        if ENGLISH_WORD_RE.search(st):
            source_english_pages += 1
            if not KOREAN_RE.search(ot):
                pages_without_korean.append(i+1)
        if KOREAN_RE.search(ot):
            korean_pages += 1
        words = ENGLISH_WORD_RE.findall(re.sub(r"https?://\S+", "", ot))
        residual = [w for w in words if w not in allowed_words and not w.isupper()]
        if residual and len(residual_samples) < 300:
            residual_samples.append({"page": i+1, "words": residual[:40], "text": ot[:700]})
    match_rates = []
    mean_diffs = []
    worst = []
    for i in range(s.page_count):
        sp, op = s[i], o[i]
        pa = sp.get_pixmap(dpi=55, alpha=False)
        pb = op.get_pixmap(dpi=55, alpha=False)
        a = np.frombuffer(pa.samples, dtype=np.uint8).reshape(pa.height, pa.width, pa.n)[:, :, :3]
        b = np.frombuffer(pb.samples, dtype=np.uint8).reshape(pb.height, pb.width, pb.n)[:, :, :3]
        h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
        a, b = a[:h, :w], b[:h, :w]
        mask = np.ones((h, w), dtype=bool)
        sx, sy = w / sp.rect.width, h / sp.rect.height
        for page in (sp, op):
            for block in page.get_text("dict", flags=fitz.TEXTFLAGS_DICT).get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    r = fitz.Rect(line["bbox"])
                    x0, x1 = max(0, int((r.x0-2)*sx)), min(w, int((r.x1+2)*sx))
                    y0, y1 = max(0, int((r.y0-2)*sy)), min(h, int((r.y1+2)*sy))
                    mask[y0:y1, x0:x1] = False
        delta = np.abs(a.astype(np.int16) - b.astype(np.int16)).mean(axis=2)
        md = float(delta[mask].mean()) if mask.any() else 0.0
        mr = float((delta[mask] <= 6).mean()) if mask.any() else 1.0
        mean_diffs.append(md); match_rates.append(mr); worst.append((mr, md, i+1))
    qa = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.exists() else {}
    result.update({
        "geometry_mismatch_pages": geometry_mismatch,
        "image_count_mismatch_pages": image_mismatch,
        "korean_pages": korean_pages,
        "source_english_pages": source_english_pages,
        "pages_without_korean_despite_source_english": pages_without_korean,
        "english_residual_samples": residual_samples,
        "non_text_match_rate_avg": statistics.mean(match_rates),
        "non_text_mean_abs_diff_avg": statistics.mean(mean_diffs),
        "non_text_worst_pages": [{"page": p, "match_rate": mr, "mean_abs_diff": md} for mr, md, p in sorted(worst)[:25]],
        "generation_qa": qa,
    })
    result["pass_criteria"] = {
        "page_count": result["page_count_equal"],
        "geometry": not geometry_mismatch,
        "images": not image_mismatch,
        "translation_coverage": len(pages_without_korean) <= 3,
        "non_text_layout": result["non_text_match_rate_avg"] >= 0.975,
        "overflow": int(qa.get("overflow_count", 9999)) <= 12,
    }
    result["validated"] = all(result["pass_criteria"].values())
    regression_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    pages = [1, 2, 3, 4, 20, 21, 22, 35, 60, 90, 120, 145, 158, 162, 180, 220, 260, 292, 293, 294]
    reg_font = pick_file(REG_FONT_CANDIDATES)
    try:
        font = ImageFont.truetype(reg_font, 17)
    except Exception:
        font = ImageFont.load_default()
    panels = []
    for pno in pages:
        ims = []
        for d in (s, o):
            pix = d[pno-1].get_pixmap(dpi=82, alpha=False)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            im.thumbnail((550, 720))
            ims.append(im)
        canvas = Image.new("RGB", (ims[0].width + ims[1].width + 24, max(ims[0].height, ims[1].height) + 34), "white")
        canvas.paste(ims[0], (0, 32)); canvas.paste(ims[1], (ims[0].width + 24, 32))
        dr = ImageDraw.Draw(canvas)
        dr.text((4, 4), f"원문 {pno}쪽", font=font, fill="black")
        dr.text((ims[0].width + 28, 4), f"번역본 {pno}쪽", font=font, fill="black")
        panels.append(canvas)
    width = max(im.width for im in panels)
    height = sum(im.height for im in panels) + 8*(len(panels)-1)
    sheet = Image.new("RGB", (width, height), "white")
    yy = 0
    for im in panels:
        sheet.paste(im, (0, yy)); yy += im.height + 8
    sheet.save(comparison_path, optimize=True)
    s.close(); o.close()
    return result

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024*1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--outdir", required=True)
    args = parser.parse_args()
    src = Path(args.source)
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "MIL_STD_461H_2026_KO_FULL.pdf"
    cache = outdir / "translation_cache.json"
    qa = outdir / "MIL_STD_461H_2026_KO_QA.json"
    regression = outdir / "MIL_STD_461H_2026_KO_REGRESSION.json"
    comparison = outdir / "MIL_STD_461H_2026_KO_COMPARISON.png"
    readme = outdir / "README_KO.txt"
    hashes = outdir / "SHA256SUMS.txt"
    translate_pdf(src, out, cache, qa)
    result = validate(src, out, qa, regression, comparison)
    hashes.write_text(f"{sha256(out)}  {out.name}\n{sha256(regression)}  {regression.name}\n", encoding="utf-8")
    readme.write_text(
        "MIL-STD-461H 한국어 전체 번역본\n================================\n\n"
        "- 원문과 동일한 294쪽 구성\n- 원본 표, 그림, 수식, 선, 페이지 크기 및 배치 유지\n"
        "- 추출 가능한 영문 텍스트를 한국어로 교체\n- 비공식 참고 번역본이며 공식 해석은 영문 원문 우선\n\n"
        f"자동 검수 통과: {result.get('validated')}\n검수 항목: {json.dumps(result.get('pass_criteria', {}), ensure_ascii=False)}\n"
        f"비텍스트 영역 평균 일치율: {result.get('non_text_match_rate_avg')}\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "validated": result.get("validated"), "pass_criteria": result.get("pass_criteria"), "size": out.stat().st_size}, ensure_ascii=False, indent=2), flush=True)
    if not result.get("page_count_equal") or result.get("geometry_mismatch_pages") or result.get("image_count_mismatch_pages"):
        sys.exit(3)

if __name__ == "__main__":
    main()
