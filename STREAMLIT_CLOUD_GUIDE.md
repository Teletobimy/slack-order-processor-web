# 🚀 Streamlit Cloud 배포 가이드

## 📋 배포 전 준비사항

### 1. 필수 파일 확인
다음 파일들이 프로젝트에 있는지 확인하세요:
- ✅ `streamlit_app.py` - 메인 Streamlit 앱
- ✅ `requirements.txt` - Python 패키지 의존성
- ✅ `.streamlit/config.toml` - Streamlit 설정
- ✅ `.gitignore` - Git 무시 파일 목록
- ✅ `slack_fetcher.py` - Slack 데이터 수집 모듈
- ✅ `aggregator.py` - 데이터 집계 모듈
- ✅ `excel_generator.py` - Excel 생성 모듈
- ✅ `gpt_matcher.py` - GPT 매칭 모듈
- ✅ `products2_map__combined.json` - 제품 데이터베이스
- ✅ `Template_json_with_rows_columns.json` - Excel 템플릿

### 2. 보안 설정
**중요**: `config.json` 파일은 절대 GitHub에 업로드하지 마세요!
- API 키가 포함된 파일은 보안상 위험합니다
- 대신 Streamlit Cloud의 환경변수를 사용합니다

## 🔧 GitHub 저장소 생성 및 업로드

### 1단계: GitHub 저장소 생성
1. [GitHub.com](https://github.com) 접속
2. "New repository" 클릭
3. 저장소 이름 입력 (예: `slack-order-processor`)
4. "Public" 또는 "Private" 선택
5. "Create repository" 클릭

### 2단계: 로컬에서 Git 초기화
```bash
# Git 초기화
git init

# 원격 저장소 연결 (GitHub에서 제공하는 URL 사용)
git remote add origin https://github.com/사용자명/저장소명.git

# 파일 추가
git add .

# 커밋
git commit -m "Initial commit: Slack Order Processor"

# GitHub에 푸시
git push -u origin main
```

### 3단계: 파일 업로드 확인
GitHub 저장소에서 다음 파일들이 업로드되었는지 확인:
- ✅ 모든 Python 파일들
- ✅ `requirements.txt`
- ✅ `.streamlit/config.toml`
- ✅ `.gitignore`
- ✅ JSON 데이터 파일들
- ❌ `config.json` (업로드되지 않아야 함)

## 🌐 Streamlit Cloud 배포

### 1단계: Streamlit Cloud 접속
1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인

### 2단계: 새 앱 생성
1. "New app" 버튼 클릭
2. GitHub 저장소 선택
3. 브랜치: `main` (또는 `master`)
4. 메인 파일 경로: `streamlit_app.py`
5. 앱 URL 설정 (예: `slack-order-processor`)

### 3단계: 환경변수 설정
1. 앱 생성 후 "Settings" 클릭
2. "Secrets" 탭 선택
3. 다음 내용 입력:

```toml
SLACK_BOT_TOKEN = "xoxb-your-actual-slack-token"
SLACK_CHANNEL_ID = "C01AA471D46"
OPENAI_API_KEY = "sk-proj-your-actual-openai-key"
WAREHOUSE_CODE = "100"
```

### 4단계: 배포 완료
1. "Save" 버튼 클릭
2. 자동으로 배포 시작
3. 배포 완료 후 제공되는 URL로 접속

## 🔐 보안 주의사항

### API 키 보호
- ✅ GitHub에 `config.json` 업로드 금지
- ✅ Streamlit Cloud 환경변수 사용
- ✅ API 키는 절대 코드에 하드코딩하지 마세요

### 접근 권한
- 🔒 Slack Bot Token: 해당 채널에만 접근 가능
- 🔒 OpenAI API Key: 사용량 제한 설정 권장
- 🔒 앱 URL: 필요시 비공개로 설정

## 🚨 문제 해결

### 일반적인 오류
1. **모듈을 찾을 수 없음**
   - `requirements.txt`에 모든 의존성 포함 확인
   - 패키지 이름 정확성 확인

2. **환경변수 오류**
   - Streamlit Cloud Secrets 설정 확인
   - 환경변수 이름 대소문자 정확성 확인

3. **파일을 찾을 수 없음**
   - JSON 파일들이 GitHub에 업로드되었는지 확인
   - 파일 경로 정확성 확인

### 로그 확인
- Streamlit Cloud 대시보드에서 "Logs" 탭 확인
- 오류 메시지 자세히 읽기

## 📱 사용 방법

### 배포 완료 후
1. 제공된 URL로 접속 (예: `https://slack-order-processor.streamlit.app`)
2. 날짜 선택 (자동 또는 수동)
3. "데이터 수집 시작" 버튼 클릭
4. 결과 확인 및 파일 다운로드

### 업데이트 방법
1. 로컬에서 코드 수정
2. GitHub에 푸시:
   ```bash
   git add .
   git commit -m "Update description"
   git push
   ```
3. Streamlit Cloud에서 자동 재배포

## 🎉 완료!

이제 전 세계 어디서나 접속 가능한 웹앱이 완성되었습니다!

**장점:**
- 🌍 전 세계 접속 가능
- 🔒 보안 설정 완료
- 📱 모바일 지원
- 🔄 자동 업데이트
- 💰 완전 무료

**접속 URL 예시:**
`https://your-app-name.streamlit.app`
