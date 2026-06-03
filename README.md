# TranslatorCat 2026

작고 가벼운 데스크톱 번역 고양이입니다.

투명 창 위에서 픽셀 아트 고양이가 살짝 움직이고, 클립보드에 영어 문장이 들어오면 로컬 AI 번역 모델로 한국어 번역 결과를 말풍선에 보여줍니다.

![TranslatorCat screenshot](docs/translatorcat-screenshot.png)

## 기능

- 생성형 이미지 기반 픽셀 아트 고양이
- 오른쪽에 뜨는 프레임 없는 투명 Electron 창
- 걷기, 멈춤, 스트레칭, 낮잠 느낌의 가벼운 애니메이션
- 클립보드 영어 텍스트 자동 감지
- 영어 -> 한국어 로컬 AI 번역
- 설정 버튼에서 고양이와 말풍선 크기 조절
- 설치 없이 실행할 수 있는 portable exe 빌드

## 사용법

1. 앱을 실행합니다.
2. 영어 문장을 복사합니다.
3. 고양이 말풍선에 한국어 번역 결과가 자동으로 뜹니다.
4. 말풍선 오른쪽 위 설정 버튼에서 크기를 조절할 수 있습니다.

## 개발 실행

```powershell
npm install
npm start
```

## exe 만들기

```powershell
npm run build
```

빌드가 끝나면 아래 파일이 생성됩니다.

```text
release/TranslatorCat-0.1.0-x64.exe
```

`release/` 폴더는 빌드 산출물이라 Git에는 올리지 않습니다.

## 로컬 번역 모델

- 모델: `Xenova/m2m100_418M`
- 런타임: `@huggingface/transformers` + ONNX Runtime
- 실행 방식: API 키 없는 로컬 실행
- 모델 형식: q8 ONNX
- 모델 데이터: 약 632MB

첫 영어 번역 시 모델 파일이 없으면 한 번 다운로드합니다. 이후에는 PC에 캐시된 모델을 사용하므로 API 키나 외부 번역 API가 필요 없습니다.

## 배포 메모

모델 파일을 exe 안에 넣으면 실행 파일이 1GB급으로 커지기 때문에 현재 버전은 첫 실행 후 로컬 캐시에 저장하는 방식입니다.

Git에는 앱 소스, 고양이 이미지, README, 스크린샷만 올립니다. 아래 항목은 제외합니다.

- `node_modules/`
- `release/`
- `models/.cache/`
