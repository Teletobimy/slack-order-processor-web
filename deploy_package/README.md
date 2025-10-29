# Slack 주문서 처리 시스템 - 배포 패키지

## 📁 포함된 파일들

### 실행 파일
- `SlackOrderProcessor_Clean.exe` - PyInstaller로 빌드된 실행 파일 (DLL 문제로 실행 안 될 수 있음)
- `run_slack_processor.py` - Python 스크립트 실행 파일 (권장)

### 설정 파일
- `config.json` - 애플리케이션 설정 (API 키, 채널 ID 등)
- `products_map.json` - 제품 매핑 데이터
- `Template_json_with_rows_columns.json` - Excel 템플릿

### 모듈 파일
- `slack_fetcher.py` - Slack 데이터 수집 모듈
- `aggregator.py` - 데이터 집계 모듈
- `excel_generator.py` - Excel 파일 생성 모듈
- `excel_parser.py` - Excel 파일 파싱 모듈
- `gpt_matcher.py` - GPT 제품 매칭 모듈

### 출력 폴더
- `output/` - 생성된 Excel 파일들이 저장되는 폴더

## 🚀 실행 방법

### 방법 1: Python 스크립트 실행 (권장)
```bash
python run_slack_processor.py
```

### 방법 2: 실행 파일 실행
```bash
SlackOrderProcessor_Clean.exe
```
*주의: DLL 문제로 실행이 안 될 수 있습니다.*

## 📋 사전 요구사항

### Python 환경
- Python 3.8 이상
- 필요한 패키지들:
  - requests
  - openpyxl
  - pandas
  - openai

### 패키지 설치
```bash
pip install requests openpyxl pandas openai
```

## ⚙️ 설정

`config.json` 파일에서 다음 설정을 확인/수정하세요:

```json
{
  "slack_bot_token": "xoxb-...",
  "channel_id": "C...",
  "openai_api_key": "sk-proj-...",
  "warehouse_code": "100",
  "products_db": "products_map.json",
  "template": "Template_json_with_rows_columns.json"
}
```

## 📊 실행 결과

실행이 성공하면 `output/` 폴더에 브랜드별 Excel 파일들이 생성됩니다:
- `바루랩_주문서_YYYYMMDD_HHMMSS.xlsx`
- `탐뷰티_주문서_YYYYMMDD_HHMMSS.xlsx`
- `피더린_주문서_YYYYMMDD_HHMMSS.xlsx`

## 🔧 문제 해결

### 모듈을 찾을 수 없다는 오류
- 모든 `.py` 파일들이 같은 폴더에 있는지 확인
- Python 경로가 올바른지 확인

### API 오류
- `config.json`의 API 키가 유효한지 확인
- 인터넷 연결 상태 확인

### Excel 파일 생성 실패
- `output/` 폴더에 쓰기 권한이 있는지 확인
- 디스크 공간이 충분한지 확인

## 📞 지원

문제가 발생하면 다음 정보와 함께 문의하세요:
- 오류 메시지
- 실행 환경 (OS, Python 버전)
- 설정 파일 내용 (API 키 제외)
