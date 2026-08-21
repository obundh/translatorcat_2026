from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import ctranslate2
import fitz
import numpy as np
from huggingface_hub import snapshot_download
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoTokenizer

MODEL_REPO = "skywood/NHNDQ-nllb-finetuned-en2ko-ct2-float16"
TOKENIZER_REPO = "NHNDQ/nllb-finetuned-en2ko"
REG_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf",
)
BOLD_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/unfonts-core/UnDotumBold.ttf",
)

EXACT = {
    "METRIC": "미터법", "SUPERSEDING": "대체 문서", "DEPARTMENT OF DEFENSE": "미국 국방부",
    "INTERFACE STANDARD": "인터페이스 표준",
    "REQUIREMENTS FOR THE CONTROL OF ELECTROMAGNETIC INTERFERENCE CHARACTERISTICS OF SUBSYSTEMS AND EQUIPMENT": "하위체계 및 장비의 전자기 간섭 특성 관리 요구사항",
    "FOREWORD": "서문", "CONTENTS": "목차", "FIGURES": "그림 목록", "TABLES": "표 목록",
    "PARAGRAPH": "항목", "PAGE": "쪽", "SCOPE": "적용범위", "APPLICABLE PUBLICATIONS": "적용 문서",
    "DEFINITIONS": "정의", "GENERAL REQUIREMENTS": "일반 요구사항", "DETAILED REQUIREMENTS": "세부 요구사항",
    "NOTES": "주", "APPENDIX A": "부록 A", "CONCLUDING MATERIAL": "마무리 자료",
    "Purpose.": "목적.", "General.": "일반.", "Application.": "적용.", "Applicability.": "적용성.",
    "Setup.": "시험 구성.", "Procedures.": "절차.", "Test procedure.": "시험 절차.",
    "Test procedures.": "시험 절차.", "Test equipment.": "시험 장비.", "Test requirements.": "시험 요구사항.",
    "Data presentation.": "시험 결과 제시.", "Interface requirements.": "인터페이스 요구사항.",
    "Verification requirements.": "검증 요구사항.", "Measurement tolerances.": "측정 허용오차.",
    "Joint procurement.": "공동 조달.", "Filtering (Navy only).": "필터링(해군만 해당).",
    "Self-compatibility.": "자체 적합성.", "Non-developmental items (NDI).": "비개발품(NDI).",
    "Commercial items (CI).": "상용품(CI).", "Selected by contractor.": "계약자가 선정한 경우.",
    "Specified by procuring activity.": "조달기관이 지정한 경우.",
    "Government furnished equipment (GFE).": "정부제공장비(GFE).", "Switching transients.": "스위칭 과도현상.",
    "Interchangeable modular equipment.": "교체형 모듈 장비.", "Shielded enclosures.": "차폐 함체.",
    "Ground plane.": "접지면.", "Metallic ground plane.": "금속 접지면.", "Composite ground plane.": "복합재 접지면.",
    "Power source impedance.": "전원 임피던스.", "General test precautions.": "일반 시험 주의사항.",
    "EUT test configurations.": "시험대상장비 시험 구성.", "Operation of EUT.": "시험대상장비 운용.",
    "Use of measurement equipment.": "측정장비 사용.", "Detector.": "검파기.", "Emission testing.": "방출 시험.",
    "Susceptibility testing.": "내성 시험.", "Frequency scanning.": "주파수 스캔.",
    "Thresholds of susceptibility.": "내성 임계값.", "Calibration of measuring equipment.": "측정장비 교정.",
    "Measurement system test.": "측정시스템 점검.", "Antenna factors.": "안테나 계수.",
    "CE101 applicability.": "CE101 적용성.", "CE101 limits.": "CE101 한계값.", "CE101 test procedure.": "CE101 시험 절차.",
    "CE102 applicability.": "CE102 적용성.", "CE102 limits.": "CE102 한계값.", "CE102 test procedure.": "CE102 시험 절차.",
    "RS103 applicability.": "RS103 적용성.", "RS103 limit.": "RS103 한계값.", "RS103 test procedures.": "RS103 시험 절차.",
    "RS105 applicability.": "RS105 적용성.", "RS105 limit.": "RS105 한계값.", "RS105 test procedures.": "RS105 시험 절차.",
    "RS105, radiated susceptibility, transient electromagnetic field.": "RS105, 방사 내성, 과도 전자기장.",
    "RS103, radiated susceptibility, electric field.": "RS103, 방사 내성, 전계.",
    "Custodians:": "관리기관:", "Preparing activity:": "작성기관:", "Review activities:": "검토기관:",
    "Optional": "선택사항", "All": "전체", "Army": "육군", "Navy": "해군", "Air Force": "공군",
    "Floor": "바닥", "Wall": "벽", "Ceiling": "천장", "Power Input": "전원 입력",
    "Signal Generator": "신호발생기", "Measurement Receiver": "측정 수신기", "Power Meter": "전력계",
    "Injection Probe": "주입 프로브", "Monitor Probe": "감시 프로브", "Test Setup Boundary": "시험 구성 경계",
    "Downloaded from https://ib-lenhardt.com  |  IBL-Lab GmbH - MIL-STD-461H / EMC Military Testing & Certification": "https://ib-lenhardt.com에서 내려받음 | IBL-Lab GmbH - MIL-STD-461H / 군용 EMC 시험 및 인증",
}

GLOSSARY = {
    "requirements for the control of electromagnetic interference characteristics of subsystems and equipment": "하위체계 및 장비의 전자기 간섭 특성 관리 요구사항",
    "electromagnetic interference control procedures": "전자기 간섭 관리절차",
    "electromagnetic interference test procedures": "전자기 간섭 시험절차",
    "electromagnetic interference test report": "전자기 간섭 시험보고서",
    "line impedance stabilization network": "선로 임피던스 안정화 회로망",
    "radiated susceptibility, transient electromagnetic field": "방사 내성, 과도 전자기장",
    "radiated susceptibility, electric field": "방사 내성, 전계",
    "radiated susceptibility, magnetic field": "방사 내성, 자계",
    "conducted susceptibility": "전도 내성", "radiated susceptibility": "방사 내성",
    "conducted emissions": "전도 방출", "radiated emissions": "방사 방출",
    "electromagnetic environmental effects": "전자기 환경 영향", "electromagnetic compatibility": "전자기 적합성",
    "electromagnetic environment": "전자기 환경", "electromagnetic interference": "전자기 간섭",
    "transient electromagnetic field": "과도 전자기장", "transient protection device": "과도 보호소자",
    "equipment under test": "시험대상장비", "government furnished equipment": "정부제공장비",
    "non-developmental item": "비개발품", "commercial item": "상용품", "measurement receiver": "측정 수신기",
    "signal generator": "신호발생기", "power amplifier": "전력증폭기", "power meter": "전력계",
    "electric field sensor": "전계 센서", "electric field strength": "전계강도", "magnetic field strength": "자계강도",
    "electric field": "전계", "magnetic field": "자계", "test setup boundary": "시험 구성 경계",
    "test setup": "시험 구성", "test procedure": "시험 절차", "test procedures": "시험 절차",
    "test equipment": "시험 장비", "shielded enclosure": "차폐 함체", "shielded room": "차폐실",
    "ground plane": "접지면", "metallic ground plane": "금속 접지면", "composite ground plane": "복합재 접지면",
    "line-to-ground filter": "선로-접지 필터", "line-to-ground filters": "선로-접지 필터",
    "line-to-ground capacitance": "선로-접지 정전용량", "common mode": "공통모드", "differential mode": "차동모드",
    "procuring activity": "조달기관", "procurement specification": "조달 규격서", "verification requirements": "검증 요구사항",
    "interface requirements": "인터페이스 요구사항", "general requirements": "일반 요구사항", "detailed requirements": "세부 요구사항",
    "data presentation": "시험 결과 제시", "applicability": "적용성", "frequency scanning": "주파수 스캔",
    "measurement tolerances": "측정 허용오차", "radio frequency": "무선주파수", "effective radiated power": "유효 방사전력",
    "electrostatic discharge": "정전기 방전", "full width half maximum": "반치전폭", "root mean square": "실효값",
    "transverse electromagnetic": "횡전자기", "fast Fourier transform": "고속 푸리에 변환",
    "Federal Communications Commission": "미국 연방통신위원회", "International Organization for Standardization": "국제표준화기구",
    "Defense Standardization Program Office": "국방 표준화 프로그램 사무국", "reverberation chamber": "잔향실",
    "mode-tuned": "모드 조정", "mode-stirred": "모드 교반", "bounded wave": "경계파",
    "parallel plate transmission lines": "평행판 전송선", "parallel plate transmission line": "평행판 전송선",
    "fast rise time": "급상승시간", "free-field": "자유공간", "orthogonal axes": "직교축",
    "correlation coefficient": "상관계수", "beamwidth": "빔폭", "current probe": "전류 프로브",
    "injection probe": "주입 프로브", "monitor probe": "감시 프로브", "directional coupler": "방향성 결합기",
    "attenuator": "감쇠기", "calibration": "교정", "verification": "검증", "susceptibility": "내성",
    "emissions": "방출", "emission": "방출", "above deck": "갑판상부", "below deck": "갑판하부",
    "external installation": "외부 설치", "internal installation": "내부 설치", "safety critical": "안전필수",
    "input (primary) power leads": "입력(주) 전원선", "power leads": "전원선", "interconnecting cables": "상호연결 케이블",
    "cable bundle": "케이블 묶음", "antenna port": "안테나 포트", "antenna terminal": "안테나 단자",
    "audio frequency": "오디오 주파수", "intermodulation": "상호변조", "cross modulation": "교차변조",
    "undesired signals": "불요신호", "structure current": "구조물 전류", "bulk cable injection": "케이블 벌크 전류 주입",
    "impulse excitation": "임펄스 여기", "damped sinusoidal transients": "감쇠 정현파 과도현상",
    "lightning induced transients": "낙뢰 유도 과도현상", "personnel borne electrostatic discharge": "인체 대전 정전기 방전",
}

POST_REPLACEMENTS = (
    (r"서브시스템", "하위체계"), (r"요건", "요구사항"), (r"테스트 설정", "시험 구성"),
    (r"테스트 절차", "시험 절차"), (r"테스트 장비", "시험 장비"), (r"\b테스트\b", "시험"),
    (r"인클로저", "함체"), (r"인터페이싱", "접속"), (r"라인-투-그라운드", "선로-접지"),
    (r"라인 투 그라운드", "선로-접지"), (r"지상 평면", "접지면"), (r"접지 평면", "접지면"),
    (r"방사선 감수성", "방사 내성"), (r"방사 감수성", "방사 내성"), (r"감수성", "내성"),
    (r"도전 배출", "전도 방출"), (r"도전 내성", "전도 내성"), (r"방사선 배출", "방사 방출"),
    (r"힘 미터", "전력계"), (r"반전 약실", "잔향실"), (r"역경 챔버", "잔향실"),
    (r"반향 챔버", "잔향실"), (r"라디에이터", "방사기"), (r"병렬 플레이트", "평행판"),
    (r"데크 아래", "갑판하부"), (r"데크 위", "갑판상부"), (r"모든 서비스", "전 군"),
    (r"전자기 필드", "전자기장"), (r"EMP 필드", "EMP 전자기장"), (r"자유 필드", "자유공간"),
    (r"상승 시간", "상승시간"), (r"설정 경계", "구성 경계"), (r"설정에 대한 수정", "시험 구성의 보완"),
)

PRESERVE_RE = re.compile(r"(?:https?://\S+|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|MIL-STD-\d+[A-Z]?|SD-\d+|(?:CE|CS|RE|RS)\d{3}|\b(?:AMSC|AREA|ASSIST|DoD|DOD|EMC|EME|EMI|EMICP|EMITP|EMITR|ERP|ESD|EUT|FCC|FFT|FWHM|GFE|IF|ISO|LISN|MAD|NDI|RF|RMS|TEM|TPD|CI|CW|DC|AC|NIST|DTRA|DISA|NSA)\b|\b\d+(?:\.\d+)*(?:\([a-zA-Z0-9]+\))*\b|\b\d+(?:\.\d+)?\s*(?:Hz|kHz|MHz|GHz|dB|dBm|V/m|V|A|W|kW|m|cm|mm|ns|μs|ms|μF|ohm|Ω|%)\b)")
ENGLISH_RE = re.compile(r"[A-Za-z]{2,}")
KOREAN_RE = re.compile(r"[가-힣]")
TOC_RE = re.compile(r"^(.*?)(\.{4,})(\s*[ivxlcdmIVXLCDM]+|\s*\d+)\s*$")
MARKER_ONLY_RE = re.compile(r"^(?:\d+(?:\.\d+)*\.?|[a-z]\.|\([a-z0-9]+\)|\*)$", re.I)
LEADING_MARKER_RE = re.compile(r"^(\d+(?:\.\d+)*\.?|[a-z]\.|\([a-z0-9]+\))\s+(.+)$", re.I)
TEST_PREFIX_RE = re.compile(r"^((?:A\.)?\d+(?:\.\d+)*(?:\s+\(\d+(?:\.\d+)*\))?\s+(?:CE|CS|RE|RS)\d{3},?)\s+(.+)$")
CODE_RE = re.compile(r"^(?:MIL-STD-\d+[A-Z]?|(?:CE|CS|RE|RS)\d{3}|[ivxlcdmIVXLCDM]+|\d+)$")
BAD_PHRASES = ("사이트맵", "힘 미터", "반전 약실", "역경 챔버", "방사선 감수성", "도전 배출", "모델 번호")

@dataclass
class Line:
    text: str; bbox: tuple[float, float, float, float]; size: float; bold: bool; italic: bool; color: int; rotation: int; chars: list[dict]; source_line_id: int; kind: str = "body"

@dataclass
class Unit:
    text: str; bbox: tuple[float, float, float, float]; size: float; bold: bool; italic: bool; color: int; rotation: int; kind: str; lines: list[Line]; source_line_ids: tuple[int, ...]; align: int = 0; fit_bbox: tuple[float, float, float, float] | None = None


def pick_file(candidates: Sequence[str]) -> str:
    for path in candidates:
        if Path(path).exists(): return path
    raise FileNotFoundError(str(candidates))

def normalize(text: str) -> str:
    text = text.replace("\u00ad", "").replace("\ufeff", "")
    return re.sub(r"\s+", " ", text).strip()

def should_translate(text: str) -> bool:
    text = normalize(text)
    return bool(text and ENGLISH_RE.search(text) and not CODE_RE.fullmatch(text) and not re.fullmatch(r"[\d\s.,;:()\[\]{}<>+=×÷/\\|_\-–—°πμΩ%]+", text))

def infer_rotation(raw_line: dict) -> int:
    dx, dy = raw_line.get("dir", (1.0, 0.0)); angle = int(round(math.degrees(math.atan2(-dy, dx)))) % 360
    for candidate in (0, 90, 180, 270):
        if abs((angle - candidate + 180) % 360 - 180) <= 10: return candidate
    return angle

def extract_lines(page: fitz.Page) -> list[Line]:
    data = page.get_text("rawdict", flags=fitz.TEXTFLAGS_RAWDICT); result=[]; line_id=0
    for block in data.get("blocks", []):
        if block.get("type") != 0: continue
        for raw_line in block.get("lines", []):
            spans=raw_line.get("spans", []); chars=[ch for span in spans for ch in span.get("chars", [])]
            text="".join(ch.get("c", "") for ch in chars)
            if not text.strip(): line_id += 1; continue
            sizes=[float(span.get("size", 10.0)) for span in spans if "".join(ch.get("c", "") for ch in span.get("chars", [])).strip()]
            result.append(Line(normalize(text), tuple(float(x) for x in raw_line["bbox"]), statistics.median(sizes) if sizes else 10.0,
                any("bold" in span.get("font", "").lower() or int(span.get("flags", 0)) & 16 for span in spans),
                any("italic" in span.get("font", "").lower() or int(span.get("flags", 0)) & 2 for span in spans),
                next((int(span.get("color", 0)) for span in spans if "".join(ch.get("c", "") for ch in span.get("chars", [])).strip()), 0), infer_rotation(raw_line), chars, line_id))
            line_id += 1
    return sorted(result, key=lambda line: (round(line.bbox[1], 1), line.bbox[0]))

def bbox_for_chars(chars: list[dict]) -> tuple[float, float, float, float]:
    return (min(float(ch["bbox"][0]) for ch in chars), min(float(ch["bbox"][1]) for ch in chars), max(float(ch["bbox"][2]) for ch in chars), max(float(ch["bbox"][3]) for ch in chars))

def split_line(line: Line) -> list[Line]:
    match = TEST_PREFIX_RE.match(line.text) or LEADING_MARKER_RE.match(line.text)
    if not match: return [line]
    prefix, rest = match.group(1), match.group(2); raw="".join(ch.get("c", "") for ch in line.chars); rest_start=raw.find(rest)
    if rest_start < 0: return [line]
    prefix_chars=line.chars[:rest_start]; rest_chars=line.chars[rest_start:]
    if not prefix_chars or not rest_chars: return [line]
    return [Line(prefix.strip(), bbox_for_chars(prefix_chars), line.size, line.bold, line.italic, line.color, line.rotation, prefix_chars, line.source_line_id, "marker"),
            Line(rest.strip(), bbox_for_chars(rest_chars), line.size, line.bold, line.italic, line.color, line.rotation, rest_chars, line.source_line_id, "heading" if line.bold or TEST_PREFIX_RE.match(line.text) else "body")]

def classify_line(line: Line, page: fitz.Page) -> None:
    text=normalize(line.text)
    if MARKER_ONLY_RE.fullmatch(text) or CODE_RE.fullmatch(text): line.kind="marker"
    elif line.bbox[3] > page.rect.height-28: line.kind="footer"
    elif line.bbox[1] < 58 and ("MIL-STD" in text or CODE_RE.fullmatch(text)): line.kind="header"
    elif TOC_RE.match(text): line.kind="toc"
    elif line.bold or (text.isupper() and len(text)>3): line.kind="heading"
    else: line.kind="body"

def group_units(page: fitz.Page) -> list[Unit]:
    split=[]
    for line in extract_lines(page): split.extend(split_line(line))
    split.sort(key=lambda line:(round(line.bbox[1],1),line.bbox[0]))
    for line in split: classify_line(line,page)
    units=[]; used=[False]*len(split)
    for index,line in enumerate(split):
        if used[index]: continue
        if line.kind!="body" or line.rotation!=0:
            units.append(Unit(line.text,line.bbox,line.size,line.bold,line.italic,line.color,line.rotation,line.kind,[line],(line.source_line_id,))); used[index]=True; continue
        group=[line]; used[index]=True; previous=line
        for next_index in range(index+1,len(split)):
            if used[next_index]: continue
            nxt=split[next_index]
            if nxt.kind!="body" or nxt.rotation!=0 or abs(nxt.bbox[1]-previous.bbox[1])<2.0: break
            if nxt.bbox[1]-previous.bbox[1] > max(line.size*1.55,17.0) or abs(nxt.bbox[0]-line.bbox[0])>8.0 or abs(nxt.size-line.size)>1.0: break
            if (line.bbox[2]-line.bbox[0])<190 and len(group)==1: break
            if (nxt.bbox[2]-nxt.bbox[0])<70 and len(group)==1: break
            group.append(nxt); used[next_index]=True; previous=nxt
        if len(group)==1: units.append(Unit(line.text,line.bbox,line.size,line.bold,line.italic,line.color,line.rotation,"body",group,(line.source_line_id,)))
        else:
            bbox=(min(x.bbox[0] for x in group),min(x.bbox[1] for x in group),max(x.bbox[2] for x in group),max(x.bbox[3] for x in group))
            units.append(Unit(normalize(" ".join(x.text for x in group)),bbox,statistics.median(x.size for x in group),False,False,group[0].color,0,"paragraph",group,tuple(x.source_line_id for x in group)))
    units.sort(key=lambda unit:(round(unit.bbox[1],1),unit.bbox[0])); page_right=page.rect.width-69.0; content_bottom=page.rect.height-48.0
    for idx,unit in enumerate(units):
        x0,y0,x1,y1=unit.bbox; next_y=content_bottom
        for later in units[idx+1:]:
            if later.bbox[1]<=y0+1: continue
            overlap=max(0.0,min(max(x1,page_right if unit.kind in ("heading","paragraph") else x1),later.bbox[2])-max(x0,later.bbox[0]))
            if overlap>12: next_y=max(y1,later.bbox[1]-1.0); break
        fit_x1=page_right if unit.kind=="heading" and x0<220 and x1<page_right else (max(x1,page_right) if unit.kind=="paragraph" and x0<160 else x1+1)
        unit.fit_bbox=(x0,y0-0.35,fit_x1,max(y1+0.6,next_y))
        unit.align=1 if (x1-x0)<page.rect.width*0.75 and abs((x0+x1)/2-page.rect.width/2)<page.rect.width*0.07 else 0
    return units

def protect(text: str) -> tuple[str,dict[str,str]]:
    exact=EXACT.get(normalize(text))
    if exact is not None: return "ZXQEXACT0000QXZ",{"ZXQEXACT0000QXZ":exact}
    mapping={}; counter=0
    def make_token(value:str)->str:
        nonlocal counter
        token=f"ZXQPH{counter:04d}QXZ"; mapping[token]=value; counter+=1; return token
    work=text
    for phrase,korean in sorted(GLOSSARY.items(),key=lambda item:len(item[0]),reverse=True):
        pattern=re.compile(re.escape(phrase),re.I)
        while True:
            match=pattern.search(work)
            if not match: break
            token=make_token(korean); work=work[:match.start()]+token+work[match.end():]
    output=[]; cursor=0
    for match in PRESERVE_RE.finditer(work):
        output.append(work[cursor:match.start()]); output.append(make_token(match.group(0))); cursor=match.end()
    output.append(work[cursor:]); return "".join(output),mapping

def restore(text:str,mapping:dict[str,str])->str:
    value=text
    value=re.sub(r"Z\s*X\s*Q\s*(?:PH|EXACT)\s*(\d+)\s*Q\s*X\s*Z",lambda m:f"ZXQPH{int(m.group(1)):04d}QXZ" if f"ZXQPH{int(m.group(1)):04d}QXZ" in mapping else "ZXQEXACT0000QXZ",value,flags=re.I)
    for token,replacement in mapping.items(): value=value.replace(token,replacement)
    value=value.replace("ZXQ","")
    for pattern,replacement in POST_REPLACEMENTS: value=re.sub(pattern,replacement,value)
    value=re.sub(r"\s+([,.;:!?%)\]])",r"\1",value); value=re.sub(r"([([])\s+",r"\1",value)
    return re.sub(r"\s{2,}"," ",value).strip()

class Translator:
    def __init__(self,cache_path:Path):
        self.cache_path=cache_path; self.cache={}; self.model_name="NHNDQ NLLB English-to-Korean (CTranslate2 int8)"
        if cache_path.exists():
            try:self.cache=json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:self.cache={}
    def load(self)->None:
        model_dir=snapshot_download(MODEL_REPO); self.tokenizer=AutoTokenizer.from_pretrained(TOKENIZER_REPO,src_lang="eng_Latn")
        self.translator=ctranslate2.Translator(model_dir,device="cpu",compute_type="int8",inter_threads=2,intra_threads=max(1,min(4,os.cpu_count() or 2)))
    def translate_all(self,texts:Iterable[str])->None:
        prepared=[]
        for source in [x for x in texts if x not in self.cache]:
            if not should_translate(source): self.cache[source]=source; continue
            toc=TOC_RE.match(source)
            if toc:
                label,dots,page=toc.groups(); protected,mapping=protect(label.strip()); prepared.append((source,protected,mapping,(dots,page)))
            else:
                protected,mapping=protect(source); prepared.append((source,protected,mapping,None))
        print(f"Translation cache={len(self.cache)}; pending={len(prepared)}",flush=True)
        for offset in range(0,len(prepared),24):
            batch=prepared[offset:offset+24]
            source_tokens=[self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(item[1],truncation=True,max_length=512)) for item in batch]
            results=self.translator.translate_batch(source_tokens,target_prefix=[["kor_Hang"] for _ in batch],beam_size=4,max_decoding_length=512,batch_type="tokens",max_batch_size=1600)
            for (original,_protected,mapping,toc),result in zip(batch,results):
                tokens=result.hypotheses[0][1:]; translated=self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(tokens),skip_special_tokens=True); translated=restore(translated,mapping)
                if toc: translated=f"{translated} {toc[0]}{toc[1]}"
                self.cache[original]=translated if KOREAN_RE.search(translated) else original
            if offset%240==0 or offset+24>=len(prepared):
                self.cache_path.write_text(json.dumps(self.cache,ensure_ascii=False,indent=2),encoding="utf-8"); print(f"Translated {min(len(prepared),offset+24)}/{len(prepared)}",flush=True)
    def get(self,text:str)->str:
        return text if not should_translate(text) else self.cache.get(text,EXACT.get(normalize(text),text))

def rgb(color:int)->tuple[float,float,float]: return (((color>>16)&255)/255,((color>>8)&255)/255,(color&255)/255)
def measure(page:fitz.Page,rect:fitz.Rect,text:str,fontfile:str|None,fontname:str,size:float,lineheight:float,align:int,rotation:int)->float:
    return page.new_shape().insert_textbox(rect,text,fontfile=fontfile,fontname=fontname,fontsize=size,lineheight=lineheight,align=align,rotate=rotation,color=(0,0,0))
def place_unit(page:fitz.Page,unit:Unit,translated:str,regular_font:str,bold_font:str)->dict:
    rect=fitz.Rect(unit.fit_bbox or unit.bbox); preserved=translated==unit.text and not KOREAN_RE.search(translated)
    if preserved: fontfile=None; fontname="hebo" if unit.bold else "helv"; start=unit.size; minimum=unit.size*0.94; lineheight=1.0
    else:
        fontfile=bold_font if unit.bold or unit.kind=="heading" else regular_font; fontname="kobold" if unit.bold or unit.kind=="heading" else "koreg"
        if unit.kind=="paragraph": start=unit.size*0.89; minimum=unit.size*0.76; lineheight=1.04
        elif unit.kind in ("body","toc"): start=unit.size*0.90; minimum=unit.size*0.76; lineheight=1.03
        elif unit.kind=="footer": start=unit.size*0.86; minimum=unit.size*0.72; lineheight=1.0
        else: start=unit.size*0.92; minimum=unit.size*0.78; lineheight=1.0
    size=start; fit=-999.0
    while size>=minimum:
        fit=measure(page,rect,translated,fontfile,fontname,size,lineheight,unit.align,unit.rotation)
        if fit>=-0.05: break
        size-=0.12
    overflow=fit<-0.05
    if overflow:size=minimum
    page.insert_textbox(rect,translated,fontfile=fontfile,fontname=fontname,fontsize=size,lineheight=lineheight,align=unit.align,rotate=unit.rotation,color=rgb(unit.color),overlay=True)
    return {"source":unit.text,"translation":translated,"kind":unit.kind,"bbox":list(unit.bbox),"fit_bbox":list(rect),"font_original":unit.size,"font_used":size,"overflow":overflow,"source_line_ids":list(unit.source_line_ids)}
def selected_pages(spec:str|None,page_count:int)->list[int]:
    if not spec:return list(range(1,page_count+1))
    result=set()
    for part in spec.split(","):
        part=part.strip()
        if not part:continue
        if "-" in part:
            start,end=part.split("-",1); result.update(range(int(start),int(end)+1))
        else:result.add(int(part))
    return sorted(page for page in result if 1<=page<=page_count)
def translate_pdf(source:Path,output:Path,cache:Path,qa_path:Path,pages_spec:str|None)->dict:
    regular_font=pick_file(REG_FONT_CANDIDATES); bold_font=pick_file(BOLD_FONT_CANDIDATES); source_doc=fitz.open(source); pages=selected_pages(pages_spec,source_doc.page_count)
    all_units={}; unique=[]; seen=set()
    for page_no in pages:
        units=group_units(source_doc[page_no-1]); all_units[page_no]=units
        for unit in units:
            if should_translate(unit.text) and unit.text not in seen:seen.add(unit.text);unique.append(unit.text)
    print(f"Selected pages={len(pages)}; units={sum(len(x) for x in all_units.values())}; unique translations={len(unique)}",flush=True)
    translator=Translator(cache);translator.load();translator.translate_all(unique);out_doc=fitz.open();placements=[];page_map={}
    for source_page_no in pages:
        out_doc.insert_pdf(source_doc,from_page=source_page_no-1,to_page=source_page_no-1);out_index=out_doc.page_count-1;page_map[source_page_no]=out_index+1;page=out_doc[out_index];units=all_units[source_page_no]
        for unit in units:
            rect=fitz.Rect(unit.bbox);rect.x0-=0.35;rect.y0-=0.25;rect.x1+=0.35;rect.y1+=0.25;page.add_redact_annot(rect,fill=(1,1,1),cross_out=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,graphics=fitz.PDF_REDACT_LINE_ART_NONE,text=fitz.PDF_REDACT_TEXT_REMOVE)
        for unit in units:placements.append({"source_page":source_page_no,**place_unit(page,unit,translator.get(unit.text),regular_font,bold_font)})
        print(f"Composed source page {source_page_no}",flush=True)
    metadata=source_doc.metadata or {};metadata.update({"title":"MIL-STD-461H 한국어 전체 번역본 v2","subject":"비공식 한국어 번역본 - 영문 원문 우선"});out_doc.set_metadata(metadata);out_doc.save(output,garbage=4,deflate=True,clean=True);out_doc.close();source_doc.close()
    qa={"source":str(source),"output":str(output),"source_page_count":fitz.open(source).page_count,"output_page_count":len(pages),"selected_source_pages":pages,"page_map":page_map,"unit_count":sum(len(x) for x in all_units.values()),"unique_translations":len(unique),"placements":len(placements),"overflow_count":sum(1 for x in placements if x["overflow"]),"model":translator.model_name,"placement_samples":placements[:200]}
    output_doc=fitz.open(output);full_text="\n".join(page.get_text("text") for page in output_doc);output_doc.close();qa["bad_phrase_hits"]={phrase:full_text.count(phrase) for phrase in BAD_PHRASES if phrase in full_text};qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding="utf-8");return qa
def create_comparison(source:Path,output:Path,pages:list[int],comparison:Path)->None:
    src=fitz.open(source);out=fitz.open(output);panels=[];font_path=pick_file(REG_FONT_CANDIDATES)
    try:font=ImageFont.truetype(font_path,16)
    except Exception:font=ImageFont.load_default()
    for out_index,source_page_no in enumerate(pages):
        images=[]
        for page in (src[source_page_no-1],out[out_index]):
            pix=page.get_pixmap(dpi=95,alpha=False);image=Image.frombytes("RGB",(pix.width,pix.height),pix.samples);image.thumbnail((560,760));images.append(image)
        canvas=Image.new("RGB",(images[0].width+images[1].width+24,max(images[0].height,images[1].height)+34),"white");canvas.paste(images[0],(0,34));canvas.paste(images[1],(images[0].width+24,34));draw=ImageDraw.Draw(canvas);draw.text((8,7),f"원문 {source_page_no}쪽",fill="black",font=font);draw.text((images[0].width+32,7),f"번역본 {source_page_no}쪽",fill="black",font=font);panels.append(canvas)
    sheet=Image.new("RGB",(max(x.width for x in panels),sum(x.height for x in panels)),"white");y=0
    for panel in panels:sheet.paste(panel,(0,y));y+=panel.height
    sheet.save(comparison);src.close();out.close()
def sha256(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):digest.update(chunk)
    return digest.hexdigest()
def main()->None:
    parser=argparse.ArgumentParser();parser.add_argument("--source",required=True,type=Path);parser.add_argument("--output",required=True,type=Path);parser.add_argument("--cache",type=Path,default=Path("translation_cache_v2.json"));parser.add_argument("--qa",type=Path,default=Path("qa_v2.json"));parser.add_argument("--comparison",type=Path,default=Path("comparison_v2.png"));parser.add_argument("--pages",default=None);args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True);qa=translate_pdf(args.source,args.output,args.cache,args.qa,args.pages);create_comparison(args.source,args.output,qa["selected_source_pages"],args.comparison);Path(str(args.output)+".sha256").write_text(f"{sha256(args.output)}  {args.output.name}\n",encoding="utf-8");print(json.dumps({key:qa[key] for key in ("output_page_count","overflow_count","bad_phrase_hits","model")},ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__":main()
