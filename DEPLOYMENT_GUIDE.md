# 배포 가이드 - Slack 출고 데이터 처리 자동화

## 🚀 온라인 배포 옵션

### 1. Streamlit Cloud (가장 간단)

**장점:**
- 무료 배포 가능
- GitHub 연동으로 자동 배포
- 설정이 매우 간단

**단계:**
1. GitHub에 코드 업로드
2. [Streamlit Cloud](https://share.streamlit.io) 접속
3. GitHub 저장소 연결
4. 자동 배포 완료

**필요한 파일:**
```
requirements.txt (Streamlit 포함)
streamlit_app.py
config.json (보안상 환경변수로 설정 권장)
```

### 2. Heroku

**장점:**
- 무료 티어 제공 (제한적)
- 다양한 언어 지원
- 확장성 좋음

**단계:**
1. Heroku CLI 설치
2. `Procfile` 생성:
   ```
   web: python flask_app.py
   ```
3. Heroku 앱 생성 및 배포

**필요한 파일:**
```
Procfile
requirements.txt
runtime.txt (Python 버전 지정)
```

### 3. Railway

**장점:**
- 무료 티어 제공
- 간단한 배포
- GitHub 연동

**단계:**
1. [Railway](https://railway.app) 접속
2. GitHub 저장소 연결
3. 자동 배포

### 4. Render

**장점:**
- 무료 티어 제공
- 자동 HTTPS
- 간단한 설정

**단계:**
1. [Render](https://render.com) 접속
2. GitHub 저장소 연결
3. 웹 서비스 생성

## 🔧 로컬 실행 방법

### Streamlit 버전
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 앱 실행
streamlit run streamlit_app.py
```

### Flask 버전
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 앱 실행
python flask_app.py
```

## 🔐 보안 고려사항

### API 키 보안
- `config.json` 파일을 공개 저장소에 업로드하지 마세요
- 환경변수 사용 권장:
  ```python
  import os
  slack_token = os.getenv('SLACK_BOT_TOKEN')
  openai_key = os.getenv('OPENAI_API_KEY')
  ```

### 환경변수 설정 예시
```bash
# Windows
set SLACK_BOT_TOKEN=xoxb-your-token
set OPENAI_API_KEY=sk-your-key

# Linux/Mac
export SLACK_BOT_TOKEN=xoxb-your-token
export OPENAI_API_KEY=sk-your-key
```

## 📱 모바일 지원

두 웹앱 모두 반응형 디자인으로 모바일에서도 사용 가능합니다.

## 🔄 업데이트 방법

### Streamlit Cloud
- GitHub에 코드 푸시하면 자동 업데이트

### Heroku
```bash
git add .
git commit -m "Update"
git push heroku main
```

## 💡 추천 배포 방법

**초보자용:** Streamlit Cloud
- 가장 간단하고 빠름
- 무료
- GitHub 연동으로 자동 배포

**고급 사용자용:** Heroku 또는 Railway
- 더 많은 제어 옵션
- 확장성 좋음
- 커스터마이징 가능

## 🆘 문제 해결

### 일반적인 문제
1. **포트 충돌**: 다른 포트 사용 (`--port 8502`)
2. **의존성 오류**: `pip install --upgrade -r requirements.txt`
3. **권한 오류**: 관리자 권한으로 실행

### 로그 확인
- Streamlit: 터미널에서 실시간 로그 확인
- Flask: `app.run(debug=True)`로 디버그 모드 활성화
