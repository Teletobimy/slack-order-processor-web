@echo off
echo === Slack 출고 데이터 처리 자동화 프로그램 빌드 ===
echo.

REM Python 가상환경 활성화 (선택사항)
REM call venv\Scripts\activate

echo 1. 의존성 패키지 설치 중...
pip install -r requirements.txt

echo.
echo 2. PyInstaller로 EXE 파일 생성 중...
pyinstaller SlackOrderProcessor.spec

echo.
echo 3. 빌드 완료!
echo 생성된 파일: dist\SlackOrderProcessor.exe
echo.

REM 빌드된 파일이 있는지 확인
if exist "dist\SlackOrderProcessor.exe" (
    echo 빌드 성공!
    echo 실행하려면: dist\SlackOrderProcessor.exe
) else (
    echo 빌드 실패! 오류를 확인해주세요.
)

echo.
pause


