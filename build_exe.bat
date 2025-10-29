@echo off
echo ========================================
echo Slack 주문서 처리 시스템 EXE 빌드
echo ========================================

echo.
echo 1. PyInstaller 설치 확인 중...
pip install pyinstaller

echo.
echo 2. 필요한 패키지 설치 중...
pip install openpyxl requests openai pandas xlrd

echo.
echo 3. EXE 파일 빌드 중...
pyinstaller SlackOrderProcessor.spec

echo.
echo 4. 빌드 완료!
echo 생성된 파일: dist\SlackOrderProcessor.exe

echo.
echo 5. 필요한 파일들을 dist 폴더로 복사 중...
copy config.json dist\
copy products_map.json dist\
copy Template_json_with_rows_columns.json dist\

echo.
echo ========================================
echo 빌드 완료!
echo 실행 파일: dist\SlackOrderProcessor.exe
echo ========================================
pause


