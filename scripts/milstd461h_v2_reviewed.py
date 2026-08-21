from __future__ import annotations

import milstd461h_v2_final as final

base = final.base


# Human-reviewed corrections for recurrent MIL/EMC terminology and the most
# error-prone regulatory passages, especially RS103 and RS105.
final.FINAL_REPLACEMENTS.update(
    {
        "도급인": "계약자",
        "시험를": "시험을",
        "시험는": "시험은",
        "전계을": "전계를",
        "전계은": "전계는",
        "데이터 제시은": "데이터 제시는",
        "표형 데이터": "표 형식의 데이터",
        "표 형 데이터": "표 형식의 데이터",
        "임의의 내성 임계값": "확인된 내성 임계값",
        "시험 셋업": "시험 구성",
        "지상 평면": "접지면",
        "내성 효과": "내성 이상",
        "내성이 있는 경우": "내성 이상이 관찰되는 경우",
        "로그 주기 또는 이중 능선 경음": "대수주기 안테나 또는 이중 리지 혼 안테나",
        "더블 리지 호른입니다": "이중 리지 혼 안테나",
        "이중 능선 경음": "이중 리지 혼 안테나",
        "방사선 내성": "방사 내성",
        "과도성": "과도",
        "시정수 요구량": "시정수 요구조건",
        "커브 진폭": "곡선 진폭",
        "장비를 소진시킬": "장비를 소손시킬",
        "오버레이하고 빼세요": "중첩한 후 감산한다",
        "뒤집으세요": "뒤집는다",
        "필드를 표시": "전계를 나타내",
        "데이터의 5시프트": "데이터를 다섯 번 이동시키는 동안",
        "정보의 통화": "정보의 최신성",
    }
)

base.EXACT.update(
    {
        # RS103 procedure and data presentation
        "Perform testing over the required frequency range with the transmit antenna vertically polarized:":
            "송신 안테나를 수직 편파로 설정하여 요구되는 주파수 범위 전체에 대해 시험한다:",
        "(a) Set the signal source to 1 kHz pulse modulation, 50% duty cycle. Verify that the modulation is present on the drive signal for each signal generator/modulation source combination. Ensure that the modulation frequency, waveform, and depth (40 dB minimum from peak to baseline) are correct. Using appropriate amplifier and transmit antenna, establish an electric field at the test start frequency. Gradually increase the electric field level until it reaches the applicable limit.":
            "(a) 신호원을 1 kHz 펄스 변조, 듀티 사이클 50%로 설정한다. 각 신호 발생기와 변조원 조합의 구동 신호에 변조가 존재하는지 확인한다. 변조 주파수, 파형 및 변조 깊이(피크에서 기준선까지 최소 40 dB)가 올바른지 확인한다. 적절한 증폭기와 송신 안테나를 사용하여 시험 시작 주파수에서 전계를 형성한다. 해당 한계값에 도달할 때까지 전계강도를 점진적으로 증가시킨다.",
        "(b) Scan the required frequency ranges in accordance with the rates and durations specified in Table III. Maintain field strength levels in accordance with the applicable limit. Monitor EUT performance for susceptibility effects.":
            "(b) 표 III에 규정된 속도와 지속시간에 따라 요구 주파수 범위를 스캔한다. 해당 한계값에 맞게 전계강도를 유지하고 EUT의 내성 이상 여부를 감시한다.",
        "(c) Ensure that the E-field sensor is indicating the field from the fundamental frequency and not from the harmonics.":
            "(c) 전계 센서가 고조파가 아니라 기본 주파수 성분의 전계를 나타내는지 확인한다.",
        "If susceptibility is noted, determine the threshold level in accordance with":
            "내성 이상이 관찰되면 다음 항목에 따라 임계 레벨을 결정한다:",
        "Data presentation shall be as follows:": "데이터 제시는 다음과 같아야 한다:",
        "Provide graphical or tabular data showing frequency ranges and field strength levels tested.":
            "시험한 주파수 범위와 전계강도 수준을 나타내는 그래프 또는 표 형식의 데이터를 제시한다.",
        "Provide the correction factors necessary to adjust sensor output readings for equivalent peak detection of modulated waveforms.":
            "변조 파형을 등가 피크 검출값으로 환산하기 위해 센서 출력 판독값에 적용하는 보정계수를 제시한다.",
        "Provide graphs or tables listing any susceptibility thresholds that were determined along with their associated frequencies.":
            "확인된 내성 임계값과 해당 주파수를 그래프 또는 표로 제시한다.",
        "Provide photographs showing actual equipment test setup, including equipment grounding and the associated dimensions.":
            "장비 접지와 관련 치수를 포함한 실제 시험 구성을 사진으로 제시한다.",
        "Provide photographs showing actual equipment setup and the associated dimensions. The following dimensions shall be clearly shown in the respective photographs:":
            "실제 장비 구성과 관련 치수를 사진으로 제시한다. 각 사진에는 다음 치수를 명확히 표시하여야 한다:",
        "Dimensions of the EUT, as well as dimensions of the basic test setup shown on":
            "EUT의 치수와 다음에 제시된 기본 시험 구성의 치수:",
        "Figures 2 through 5 and 4.3.8 as applicable in 5.21.3.3a.":
            "5.21.3.3a에 따라 적용되는 그림 2~5 및 4.3.8.",
        "3 dB beamwidth coverage for each transmit antenna used.":
            "사용한 각 송신 안테나의 3 dB 빔폭 커버리지.",
        "Distance of the physical reference point of each antenna to the test setup boundary for all antenna positions required in 5.21.3.3c(1).":
            "5.21.3.3c(1)에서 요구되는 모든 안테나 위치에 대해 각 안테나의 물리적 기준점에서 시험 구성 경계까지의 거리.",
        "Placement of the electric field sensor(s) with respect to the EUT and distance":
            "EUT에 대한 전계 센서의 배치 및",
        "above the ground plane in 5.21.3.3d.":
            "5.21.3.3d에 규정된 접지면 위 높이.",

        # Reverberation chamber antenna terminology
        "This test procedure is an alternative technique used to verify the ability of the EUT and associated cabling to withstand electric fields.":
            "이 시험 절차는 EUT와 관련 케이블이 전계를 견딜 수 있는지를 확인하기 위한 대체 시험기법이다.",
        "200 MHz to 1 GHz, log periodic or double ridge horns.":
            "200 MHz~1 GHz: 대수주기 안테나 또는 이중 리지 혼 안테나.",
        "1 GHz to 18 GHz, double ridge horns.":
            "1 GHz~18 GHz: 이중 리지 혼 안테나.",
        "18 GHz to 40 GHz, other antennas as approved by the procuring activity.":
            "18 GHz~40 GHz: 조달기관이 승인한 기타 안테나.",
        "Electric field sensors (physically small - electrically short), each axis independently displayed.":
            "전계 센서(물리적으로 작고 전기적으로 짧은 센서), 각 축을 독립적으로 표시할 수 있어야 한다.",

        # Appendix A / RS105 rationale
        "If the chamber time constant is greater than 0.4 of the pulse width of the modulation waveform, absorber material must be added to the chamber, or the pulse width must be increased. If absorber material is added, repeat the measurement and the Q calculation until the time constant requirement is satisfied with the least":
            "챔버의 시정수가 변조 파형 펄스폭의 0.4보다 크면 챔버에 흡수재를 추가하거나 펄스폭을 증가시켜야 한다. 흡수재를 추가한 경우에는 최소한의 흡수재로 시정수 요구조건을 만족할 때까지 측정과 Q 계산을 반복한다.",
        "possible absorber material. A new required.":
            "최소한의 흡수재를 사용한다. 새로운",
        "( ) CLF f must be defined if absorber material is":
            "CLF(f)는 흡수재가 필요한 경우 정의하여야 한다.",
        "A.5.22 (5.22) RS105, radiated susceptibility, transient, electromagnetic field.":
            "A.5.22 (5.22) RS105, 방사 내성, 과도 전자기장.",
        "Applicability and limits: This requirement is primarily intended for EUTs to withstand the fast":
            "적용성 및 한계: 이 요구사항은 주로 EUT가 EMP의 빠른",
        "rise time, free-field transient environment of EMP. It applies for equipment enclosures which are directly exposed to the incident field outside of the platform structure or for equipment inside poorly shielded or unshielded platforms. This requirement may be tailored in adjustment of the curve amplitude either higher or lower based on degree of field enhancement or protection provided in the area of the platform where the equipment will be located. This requirement is applicable only for EUT enclosures. The electrical interface cabling should be protected in shielded conduit. Potential equipment responses due to cable coupling are controlled under":
            "상승시간을 갖는 자유공간 과도 환경을 견디도록 하기 위한 것이다. 플랫폼 구조 외부에서 입사 전계에 직접 노출되는 장비 함체 또는 차폐가 불충분하거나 차폐되지 않은 플랫폼 내부 장비에 적용한다. 장비가 설치되는 플랫폼 영역의 전계 증강 정도 또는 제공되는 보호 수준에 따라 곡선 진폭을 높이거나 낮추어 조정할 수 있다. 이 요구사항은 EUT 함체에만 적용한다. 전기 인터페이스 케이블은 차폐 도관으로 보호하는 것이 바람직하다. 케이블 결합으로 인한 잠재적 장비 응답은 다음 요구사항에서 관리한다:",
        "Test procedures: To protect the EUT and actual and simulated loads and signal equipment, all":
            "시험 절차: EUT와 실제 및 모의 부하, 신호 장비를 보호하기 위해 모든",
        "cabling should be treated with overall shielding; kept as short as possible within the test cell; and oriented to minimize coupling to the EMP fields.":
            "케이블은 전체 차폐를 적용하고 시험 셀 내부에서 가능한 한 짧게 유지하며 EMP 전계와의 결합이 최소화되도록 배치하여야 한다.",
        "The EMP field is simulated in the laboratory using bounded wave TEM radiators such as TEM cells and parallel plate transmission lines. To ensure the EUT does not significantly distort the field in the test volume, the largest EUT dimension should be no more than a third of the dimension":
            "EMP 전계는 TEM 셀이나 평행판 전송선과 같은 경계파 TEM 방사기를 사용하여 실험실에서 모의한다. EUT가 시험 체적의 전계를 크게 왜곡하지 않도록 EUT의 최대 치수는 다음 치수의 3분의 1을 초과하지 않아야 한다:",
        "between the radiating plates of the simulator. In these simulators the electric field is perpendicular to the surfaces of the radiator. Since the polarization of the incident EMP field in the installation is not known, the EUT must be tested in all orthogonal axes.":
            "시뮬레이터 방사판 사이의 간격. 이러한 시뮬레이터에서 전계는 방사판 표면에 수직이다. 실제 설치 환경에서 입사 EMP 전계의 편파를 알 수 없으므로 EUT는 서로 직교하는 모든 축 방향에서 시험하여야 한다.",
        "There is a requirement to first test at 10% of the specified limit and then increase the amplitude in steps of 2 or 3 until the specified limit is reached for several reasons. This test has the potential to burnout equipment and starting at lower levels provides a degree of protection. Also, the equipment may exhibit susceptibility problems at lower test levels that do not occur at higher test levels due to the presence of transient protection devices (TPDs). At lower test levels, the devices might not actuate resulting in higher stresses on circuits than for higher levels where they do actuate.":
            "먼저 규정 한계값의 10%에서 시험한 후 규정 한계값에 도달할 때까지 진폭을 2배 또는 3배씩 증가시켜야 한다. 이는 이 시험이 장비를 소손시킬 가능성이 있어 낮은 레벨에서 시작함으로써 장비를 어느 정도 보호할 수 있기 때문이다. 또한 과도 보호소자(TPD)로 인해 높은 시험 레벨에서는 나타나지 않는 내성 문제가 낮은 시험 레벨에서 나타날 수 있다. 낮은 레벨에서는 보호소자가 동작하지 않아, 보호소자가 동작하는 높은 레벨보다 회로에 더 큰 스트레스가 가해질 수 있다.",
        "Common mode signals can result on cables with inadequate isolation or leaky connectors in the presence of radiated fields. A method of checking for potential problems is as follows:":
            "방사 전계가 존재할 때 절연이 불충분하거나 누설이 있는 커넥터를 사용하는 케이블에는 공통모드 신호가 발생할 수 있다. 잠재적 문제를 확인하는 방법은 다음과 같다:",
        "Measure the E-field with the B-dot or D-dot probe.":
            "B-dot 또는 D-dot 프로브로 전계를 측정한다.",
        "Invert the probe by rotating it 180 degrees.":
            "프로브를 180도 회전하여 뒤집는다.",
        "Measure the E-field again and invert the signal.":
            "전계를 다시 측정한 후 신호의 극성을 반전한다.",
        "Overlay and subtract the two signals.":
            "두 신호를 중첩하여 감산한다.",
        "The result is the common mode signal.":
            "그 결과가 공통모드 신호이다.",
        "If any significant level is present, corrections to the setup should be undertaken, such as tightening of connectors and introduction of additional isolation, such as better shielded cables, alternative routing, or shielding barriers.":
            "유의한 수준의 공통모드 신호가 존재하면 커넥터를 조이고, 차폐 성능이 더 좋은 케이블을 사용하거나 케이블 경로를 변경하고 차폐 장벽을 추가하는 등 시험 구성을 보완하여야 한다.",

        # Concluding material - preserve original columns and line spacing
        "Army - AV": "육군 - AV",
        "Air Force - 11": "공군 - 11",
        "Navy - AS": "해군 - AS",
        "(Project EMCS-2021-004)": "(프로젝트 EMCS-2021-004)",
        "DISA/JSC - DC5": "DISA/JSC - DC5",
        "Army - AT, CR, MD, MI, MR, TE": "육군 - AT, CR, MD, MI, MR, TE",
        "Navy - CG, EC, MC, OS, SH": "해군 - CG, EC, MC, OS, SH",
        "Air Force - 13, 19, 84": "공군 - 13, 19, 84",
        "NSA - NS": "NSA - NS",
        "DTRA - DS": "DTRA - DS",
        "NOTE: The activities listed above were interested in this document as of the date of this":
            "주: 위에 열거한 기관은 이 문서의 발행일 현재 본 문서에 관심을 표명한 기관이다.",
        "document. Since organizations and responsibilities can change, you should verify the currency of the information above using the ASSIST Online database at https://assist.dla.mil/.":
            "기관과 책임은 변경될 수 있으므로 https://assist.dla.mil/의 ASSIST Online 데이터베이스에서 위 정보의 최신성을 확인하여야 한다.",
    }
)


if __name__ == "__main__":
    base.main()
