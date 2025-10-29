# 🚀 Streamlit Cloud 배포 가이드

## 1. GitHub 저장소 준비

1. **새 저장소 생성**
   - GitHub에서 새 저장소 생성
   - 저장소 이름: `slack-order-processor` (또는 원하는 이름)

2. **코드 업로드**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/slack-order-processor.git
   git push -u origin main
   ```

## 2. Streamlit Cloud 배포

1. **Streamlit Cloud 접속**
   - [https://share.streamlit.io/](https://share.streamlit.io/) 접속
   - GitHub 계정으로 로그인

2. **새 앱 생성**
   - "New app" 버튼 클릭
   - Repository: `yourusername/slack-order-processor`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

3. **환경 변수 설정**
   - "Advanced settings" 클릭
   - 다음 환경 변수 추가:

   ```
   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   OPENAI_API_KEY=sk-your-openai-api-key
   CHANNEL_ID=C-your-channel-id
   WAREHOUSE_CODE=100
   ```

4. **배포 시작**
   - "Deploy!" 버튼 클릭
   - 배포 완료까지 2-3분 소요

## 3. 배포 후 확인

1. **앱 접속**
   - 배포 완료 후 제공되는 URL로 접속
   - 예: `https://yourusername-slack-order-processor.streamlit.app`

2. **기능 테스트**
   - 날짜 범위 선택
   - 채널 ID 입력
   - "데이터 처리 시작" 버튼 클릭
   - 결과 확인 및 파일 다운로드

## 4. 문제 해결

### 일반적인 문제들:

1. **모듈 import 오류**
   - `requirements.txt`에 모든 의존성이 포함되어 있는지 확인
   - 로컬 모듈들이 같은 디렉토리에 있는지 확인

2. **환경 변수 오류**
   - 모든 필수 환경 변수가 설정되어 있는지 확인
   - 환경 변수 이름이 정확한지 확인

3. **Slack API 오류**
   - Bot Token이 유효한지 확인
   - Bot이 해당 채널에 초대되어 있는지 확인

4. **OpenAI API 오류**
   - API Key가 유효한지 확인
   - API 사용량 한도를 확인

## 5. 업데이트 방법

1. **코드 수정 후**
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```

2. **자동 재배포**
   - Streamlit Cloud는 main 브랜치 변경 시 자동으로 재배포
   - 배포 상태는 Streamlit Cloud 대시보드에서 확인 가능

## 6. 보안 고려사항

- **환경 변수 보호**: 민감한 정보는 환경 변수로만 설정
- **API 키 관리**: 정기적으로 API 키 갱신
- **접근 권한**: 필요한 사용자만 앱에 접근할 수 있도록 설정

## 7. 모니터링

- **사용량 모니터링**: OpenAI API 사용량 확인
- **오류 로그**: Streamlit Cloud 로그 확인
- **성능 모니터링**: 응답 시간 및 처리량 확인
