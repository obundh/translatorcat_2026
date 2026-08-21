from __future__ import annotations

import re

import mil461h_revision2 as rev

# Terminology normalized for Korean EMC / military test reports.
rev.EXACT.update({
    "Above deck.": "갑판 위.",
    "Antenna port.": "안테나 포트.",
    "Below deck.": "갑판 아래.",
    "Cable bundle.": "케이블 다발.",
    "Exposed below deck.": "노출된 갑판 아래.",
    "External installation.": "외부 설치.",
    "Flight-line equipment.": "비행장 운용장비.",
    "Input (primary) power leads.": "입력(주) 전원선.",
    "Internal installation.": "내부 설치.",
    "Metric units.": "미터법 단위.",
    "Primary power.": "주전원.",
    "Safety critical.": "안전필수.",
    "Test setup boundary.": "시험 구성 경계.",
    "Acronyms used in this standard.": "이 표준에서 사용하는 약어.",
    "Shielded enclosures.": "차폐 함체.",
    "Radio frequency (RF) absorber material.": "무선주파수(RF) 흡수체.",
    "Other test sites.": "그 밖의 시험장소.",
    "Ambient electromagnetic level.": "주변 전자기 레벨.",
    "Ground plane.": "접지면.",
    "Metallic ground plane.": "금속 접지면.",
    "Composite ground plane.": "복합재 접지면.",
    "Power source impedance.": "전원 임피던스.",
    "General test precautions.": "일반 시험 주의사항.",
    "Accessory equipment.": "부속장비.",
    "Excess personnel and equipment.": "불필요한 인원 및 장비.",
    "Overload precautions.": "과부하 방지조치.",
    "RF hazards.": "RF 위해.",
    "Shock hazard.": "감전 위험.",
    "EUT test configurations.": "EUT 시험 구성.",
    "EUT design status.": "EUT 설계 상태.",
    "Bonding of EUT.": "EUT 본딩.",
    "Shock and vibration isolators.": "충격 및 진동 절연체.",
    "Safety grounds.": "안전접지.",
    "Orientation of EUTs.": "EUT 방향.",
    "Construction and arrangement of EUT cables.": "EUT 케이블의 구성 및 배치.",
    "Electrical and mechanical interfaces.": "전기적·기계적 인터페이스.",
    "Operation of EUT.": "EUT 운용.",
    "Susceptibility monitoring.": "내성 감시.",
    "Use of measurement equipment.": "측정장비 사용.",
    "Detector.": "검파기.",
    "Computer-controlled instrumentation.": "컴퓨터 제어 계측기.",
    "Emission testing.": "방출 시험.",
    "Bandwidths.": "대역폭.",
    "Emission identification.": "방출 식별.",
    "Frequency scanning.": "주파수 스캔.",
    "Emission data presentation.": "방출 자료 제시.",
    "Susceptibility testing.": "내성 시험.",
    "Modulation of susceptibility signals.": "내성 시험신호의 변조.",
    "Thresholds of susceptibility.": "내성 임계값.",
    "Calibration of measuring equipment.": "측정장비 교정.",
    "Signal generators.": "신호발생기.",
    "Power amplifiers.": "전력증폭기.",
    "Transmit antennas.": "송신 안테나.",
    "Receive antennas.": "수신 안테나.",
    "Electric field sensors (physically small - electrically short).": "전계 센서(물리적으로 작고 전기적으로 짧은 형식).",
    "Measurement receiver.": "측정수신기.",
    "Power meter.": "전력계.",
    "Directional coupler.": "방향성 결합기.",
    "Attenuator.": "감쇠기.",
    "Data recording device.": "자료 기록장치.",
    "Current probe.": "전류 프로브.",
    "Injection probe.": "주입 프로브.",
    "Monitor probe.": "감시 프로브.",
    "Pulse modulation": "펄스 변조",
    "Duty cycle": "듀티비",
    "Vertical polarization": "수직 편파",
    "Horizontal polarization": "수평 편파",
    "Circular polarization": "원편파",
    "Reverberation chamber": "잔향실",
    "Mode-tuned": "모드 동조",
    "Mode-stirred": "모드 교반",
    "Field uniformity": "전계 균일도",
    "Line Replaceable Unit": "현장교환단위(LRU)",
    "Shop Replaceable Unit": "정비소교환단위(SRU)",
    "Integrated Equipment Rack": "통합 장비 랙",
    "Downloaded from https://ib-lenhardt.com | IBL-Lab GmbH - MIL-STD-461H / EMC Military Testing & Certification": "https://ib-lenhardt.com에서 내려받음 | IBL-Lab GmbH - MIL-STD-461H / EMC 군용 시험 및 인증",
})

rev.STANDARD_REPLACEMENTS = rev.STANDARD_REPLACEMENTS + (
    (r"\bFigure\b", "그림"),
    (r"\bFigures\b", "그림"),
    (r"\bTable\b", "표"),
    (r"\bTables\b", "표"),
    (r"\bNOTE\b", "주"),
    (r"\bNote\b", "주"),
    (r"측정 수신기", "측정수신기"),
    (r"신호 발생기", "신호발생기"),
    (r"전력 증폭기", "전력증폭기"),
    (r"전기장", "전계"),
    (r"자기 필드", "자기장"),
    (r"전기 필드", "전계"),
    (r"방사 전기장", "방사 전계"),
    (r"내성 효과", "내성 현상"),
    (r"감쇠 사인파", "감쇠 정현파"),
    (r"벌크 케이블", "케이블 다발"),
    (r"펄스 폭", "펄스폭"),
    (r"상승 시간", "상승시간"),
    (r"체류 시간", "체류시간"),
    (r"보정 계수", "보정계수"),
    (r"방향 결합기", "방향성 결합기"),
    (r"라인 임피던스 안정화 네트워크", "선로 임피던스 안정화 회로망"),
    (r"라인 임피던스 안정화 망", "선로 임피던스 안정화 회로망"),
    (r"일반 인터페이스 요구사항", "일반 인터페이스 요구사항"),
    (r"성능의 저하", "성능 저하"),
    (r"규정된 표시", "지정된 표시값"),
    (r"지정된 지시", "지정된 표시값"),
    (r"공차", "허용오차"),
)

_original_post_edit = rev.post_edit
_original_page_tables = rev.page_tables


def reviewed_post_edit(source: str, translated: str) -> str:
    out = _original_post_edit(source, translated)
    # Keep mandatory language consistent with Korean standards.
    if re.search(r"\bshall not\b", source, re.I):
        out = re.sub(r"해서는 안 된다\.?$", "하여서는 아니 된다.", out)
        out = re.sub(r"하지 않아야 한다\.?$", "하여서는 아니 된다.", out)
    if re.search(r"\bshall\b", source, re.I) and not re.search(r"\bshall not\b", source, re.I):
        out = re.sub(r"해야 한다\.?$", "하여야 한다.", out)
    return out


def reviewed_page_tables(page):
    """Reject graph grids and technical diagrams falsely detected as tables.

    PyMuPDF's generic table detector correctly finds the document's actual tables,
    but dense graph grids and chamber drawings can also look tabular.  The false
    positives are sparse or consist mostly of one-character fragments.  Keeping
    those as ordinary page text preserves the graph/diagram and prevents tiny-cell
    clipping while still translating its labels through the normal text path.
    """
    kept = []
    for table in _original_page_tables(page):
        rows = len(table.rows)
        cols = max((len(row.cells) for row in table.rows), default=0)
        cell_count = rows * cols
        extracted = table.extract()
        values = [str(cell or "").strip() for row in extracted for cell in row]
        nonempty = [value for value in values if value]
        density = len(nonempty) / max(1, cell_count)
        average_chars = sum(len(value) for value in nonempty) / max(1, len(nonempty))

        # Single-row label boxes are better handled as ordinary figure labels.
        if rows < 2 or cols < 2:
            continue
        # Diagrams and graphs produce very sparse pseudo-cells.
        if density < 0.15:
            continue
        # Dense graph grids have many cells but only tiny character fragments.
        if cell_count >= 80 and average_chars < 8.0:
            continue
        kept.append(table)
    return kept


rev.post_edit = reviewed_post_edit
rev.page_tables = reviewed_page_tables

if __name__ == "__main__":
    rev.main()
