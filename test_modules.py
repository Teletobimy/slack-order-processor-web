# -*- coding: utf-8 -*-
"""
테스트 실행 스크립트
개발 중 모듈별 테스트용
"""

import os
import json
from datetime import datetime

def test_slack_fetcher():
    """Slack 데이터 수집 테스트"""
    print("=== Slack 데이터 수집 테스트 ===")
    try:
        from slack_fetcher import SlackFetcher
        
        fetcher = SlackFetcher()
        
        # 최근 1일 데이터 수집
        start_date = "2025-10-16"
        end_date = "2025-10-16"
        
        print(f"테스트 날짜: {start_date} ~ {end_date}")
        
        # 메시지 수집
        messages = fetcher.fetch_messages(start_date, end_date)
        print(f"수집된 메시지: {len(messages)}개")
        
        if messages:
            # 첫 번째 메시지 정보 출력
            first_msg = messages[0]
            print(f"첫 번째 메시지: {first_msg.get('text', '')[:50]}...")
            
            # 첨부 파일 확인
            if first_msg.get('files'):
                print(f"첨부 파일: {len(first_msg['files'])}개")
                for file_info in first_msg['files']:
                    print(f"  - {file_info.get('name', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        return False

def test_excel_parser():
    """Excel 파싱 테스트"""
    print("\n=== Excel 파싱 테스트 ===")
    try:
        from excel_parser import ExcelParser
        
        parser = ExcelParser()
        
        # 테스트용 Excel 파일이 있는지 확인
        test_files = []
        for file in os.listdir("."):
            if file.endswith(('.xls', '.xlsx')):
                test_files.append(file)
        
        if test_files:
            print(f"발견된 Excel 파일: {test_files}")
            
            for file in test_files[:1]:  # 첫 번째 파일만 테스트
                print(f"파싱 중: {file}")
                products = parser.parse_excel_file(file)
                print(f"추출된 제품: {len(products)}개")
                
                for product in products[:3]:  # 처음 3개만 출력
                    print(f"  - {product['product_name']}: {product['quantity']}개")
        else:
            print("테스트용 Excel 파일이 없습니다.")
        
        return True
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        return False

def test_gpt_matcher():
    """GPT 매칭 테스트"""
    print("\n=== GPT 매칭 테스트 ===")
    try:
        from gpt_matcher import GPTMatcher
        
        matcher = GPTMatcher()
        
        # 테스트 텍스트
        test_text = "탐뷰티 더 클라우드 컨실러 4홋수 각 10개씩, 시그니처 세트 1ea"
        
        print(f"테스트 텍스트: {test_text}")
        
        # 제품 추출
        products = matcher.extract_products_from_text(test_text)
        print(f"추출된 제품: {products}")
        
        # 품목코드 매칭
        for product in products:
            match = matcher.match_product_to_code(product["product_name"])
            print(f"매칭 결과: {match}")
        
        return True
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        return False

def test_config():
    """설정 파일 테스트"""
    print("\n=== 설정 파일 테스트 ===")
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = ["slack_bot_token", "channel_id", "openai_api_key"]
        
        for key in required_keys:
            if key in config and config[key]:
                print(f"✓ {key}: 설정됨")
            else:
                print(f"✗ {key}: 누락됨")
        
        # 제품 데이터베이스 확인
        if os.path.exists("products2_map__combined.json"):
            with open("products2_map__combined.json", 'r', encoding='utf-8') as f:
                products = json.load(f)
            print(f"✓ 제품 데이터베이스: {len(products)}개 제품")
        else:
            print("✗ 제품 데이터베이스: 파일 없음")
        
        return True
        
    except Exception as e:
        print(f"테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("=== 모듈별 테스트 시작 ===")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("설정 파일", test_config),
        ("Slack 데이터 수집", test_slack_fetcher),
        ("Excel 파싱", test_excel_parser),
        ("GPT 매칭", test_gpt_matcher),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{test_name} 테스트 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    passed = 0
    for test_name, result in results:
        status = "✓ 통과" if result else "✗ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n전체 결과: {passed}/{len(results)} 통과")
    
    if passed == len(results):
        print("모든 테스트가 통과했습니다! 프로그램을 실행할 수 있습니다.")
    else:
        print("일부 테스트가 실패했습니다. 설정을 확인해주세요.")

if __name__ == "__main__":
    main()
