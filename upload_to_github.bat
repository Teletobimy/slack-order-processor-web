@echo off
echo ========================================
echo GitHub 업로드 및 Streamlit Cloud 배포
echo ========================================
echo.

REM Git이 설치되어 있는지 확인
git --version >nul 2>&1
if errorlevel 1 (
    echo Git이 설치되어 있지 않습니다.
    echo https://git-scm.com/downloads 에서 Git을 설치해주세요.
    pause
    exit /b 1
)

echo Git이 설치되어 있습니다.
echo.

REM 현재 디렉토리가 Git 저장소인지 확인
if not exist ".git" (
    echo Git 저장소를 초기화합니다...
    git init
    echo.
)

REM 파일 추가
echo 변경된 파일들을 추가합니다...
git add .

REM 커밋
echo 변경사항을 커밋합니다...
git commit -m "Update Slack Order Processor for Streamlit Cloud deployment"

echo.
echo ========================================
echo 다음 단계를 진행하세요:
echo ========================================
echo.
echo 1. GitHub에서 새 저장소를 생성하세요
echo 2. 다음 명령어를 실행하세요:
echo.
echo    git remote add origin https://github.com/사용자명/저장소명.git
echo    git push -u origin main
echo.
echo 3. https://share.streamlit.io 에서 배포하세요
echo.
echo 자세한 가이드는 STREAMLIT_CLOUD_GUIDE.md 파일을 참고하세요.
echo.

pause
