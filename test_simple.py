# -*- coding: utf-8 -*-
"""
간단한 테스트용 EXE 파일
"""

import sys
import os

def main():
    print("=" * 50)
    print("Slack Order Processor - Test Version")
    print("=" * 50)
    print()
    
    print("1. Python 버전:", sys.version)
    print("2. 현재 디렉토리:", os.getcwd())
    print("3. 파일 목록:")
    
    try:
        files = os.listdir('.')
        for file in files:
            print(f"   - {file}")
    except Exception as e:
        print(f"   오류: {e}")
    
    print()
    print("4. 설정 파일 확인:")
    
    config_files = ['config.json', 'products_map.json', 'Template_json_with_rows_columns.json']
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   ✓ {config_file} 존재")
        else:
            print(f"   ✗ {config_file} 없음")
    
    print()
    print("=" * 50)
    print("테스트 완료!")
    print("=" * 50)
    
    input("엔터를 눌러 종료하세요...")

if __name__ == "__main__":
    main()


