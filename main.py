# -*- coding: utf-8 -*-
"""
Slack 출고 데이터 처리 자동화 프로그램
메인 진입점
"""

import sys
import os
import json
from gui_app import SlackOrderProcessorGUI

def check_dependencies():
    """필수 파일 및 의존성 확인"""
    required_files = [
        "config.json",
        "products2_map__combined.json", 
        "Template_json_with_rows_columns.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("다음 필수 파일이 없습니다:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True

def check_config():
    """설정 파일 검증"""
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = [
            "slack_bot_token",
            "channel_id", 
            "openai_api_key",
            "warehouse_code"
        ]
        
        missing_keys = []
        for key in required_keys:
            if key not in config or not config[key]:
                missing_keys.append(key)
        
        if missing_keys:
            print("설정 파일에서 다음 키가 누락되었습니다:")
            for key in missing_keys:
                print(f"  - {key}")
            return False
        
        return True
        
    except Exception as e:
        print(f"설정 파일 읽기 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("=== Slack 출고 데이터 처리 자동화 프로그램 ===")
    print()
    
    # 의존성 확인
    if not check_dependencies():
        print("\n필수 파일을 확인한 후 다시 실행해주세요.")
        input("엔터를 눌러 종료...")
        return
    
    # 설정 확인
    if not check_config():
        print("\n설정 파일을 확인한 후 다시 실행해주세요.")
        input("엔터를 눌러 종료...")
        return
    
    print("모든 필수 파일과 설정이 확인되었습니다.")
    print("GUI 애플리케이션을 시작합니다...")
    print()
    
    try:
        # GUI 애플리케이션 시작
        app = SlackOrderProcessorGUI()
        app.run()
        
    except Exception as e:
        print(f"애플리케이션 실행 중 오류 발생: {e}")
        input("엔터를 눌러 종료...")

if __name__ == "__main__":
    main()
