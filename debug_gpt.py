# -*- coding: utf-8 -*-
"""
GPT 매칭 과정 디버깅
"""

import json
from datetime import datetime
from slack_fetcher import SlackFetcher
from gpt_matcher import GPTMatcher

def debug_gpt_matching():
    """GPT 매칭 과정 디버깅"""
    print("=== GPT 매칭 과정 디버깅 ===")
    
    try:
        # 오늘 날짜 계산
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"디버깅 날짜: {today}")
        
        # Slack 데이터 수집
        fetcher = SlackFetcher()
        messages = fetcher.fetch_messages(today, today)
        
        if not messages:
            print("오늘 메시지가 없습니다.")
            return
        
        # 메시지 처리
        processed_messages = fetcher.process_messages_with_threads(messages)
        
        # GPT 매칭 테스트
        gpt_matcher = GPTMatcher()
        
        for i, message in enumerate(processed_messages, 1):
            print(f"\n--- 메시지 {i} GPT 매칭 테스트 ---")
            text = message.get("text", "")
            print(f"원본 텍스트: {text}")
            
            if text:
                # 제품 추출 테스트
                print("\n1. 제품 추출 테스트:")
                products = gpt_matcher.extract_products_from_text(text)
                print(f"추출된 제품: {len(products)}개")
                
                for j, product in enumerate(products, 1):
                    print(f"  제품 {j}: {product}")
                    
                    # 제품 매칭 테스트
                    if product.get("name"):
                        print(f"\n2. 제품 '{product['name']}' 매칭 테스트:")
                        match_result = gpt_matcher.match_product_to_code(product["name"])
                        print(f"매칭 결과: {match_result}")
                        
                        if match_result:
                            print(f"  - 품목코드: {match_result.get('품목코드')}")
                            print(f"  - 제품명: {match_result.get('제품명')}")
                            print(f"  - 브랜드: {match_result.get('브랜드')}")
                            print(f"  - 신뢰도: {match_result.get('confidence')}")
                        else:
                            print("  - 매칭 실패")
        
        return True
        
    except Exception as e:
        print(f"디버깅 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_gpt_matching()
