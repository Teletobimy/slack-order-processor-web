# -*- coding: utf-8 -*-
"""
실제 데이터로 테스트하는 스크립트
"""

import json
from gpt_matcher import GPTMatcher
from aggregator import DataAggregator

def test_with_real_data():
    """실제 Slack 데이터로 테스트"""
    print("=== 실제 데이터 테스트 ===")
    
    # GPT 매처 초기화
    matcher = GPTMatcher()
    
    # 실제 메시지 텍스트들
    test_messages = [
        "리쥬부스터크림 100개 (사무실 추가생산분으로 출고)",
        "스템블리스 피더린 크림 10개 주문 부탁드려요",
        "피더린 크림1개, 피더린 토너1개, 피더린 엠플1개",
        "브이에스라인의원 피더린 크림 50개 주문 부탁드려요"
    ]
    
    print("실제 메시지에서 제품 추출 테스트:")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"{i}. 메시지: {message}")
        
        # 제품 추출
        products = matcher.extract_products_from_text(message)
        print(f"   추출된 제품: {products}")
        
        # 품목코드 매칭
        for product in products:
            match = matcher.match_product_to_code(product["product_name"])
            if match:
                print(f"   매칭 성공: {product['product_name']} → {match['품목코드']} ({match['제품명']})")
            else:
                print(f"   매칭 실패: {product['product_name']}")
        
        print()
    
    # 제품 데이터베이스 확인
    print("=== 제품 데이터베이스 샘플 ===")
    with open("products2_map__combined.json", 'r', encoding='utf-8') as f:
        products_db = json.load(f)
    
    print(f"총 제품 수: {len(products_db)}개")
    print("샘플 제품들:")
    for product in products_db[:5]:
        print(f"  - {product['품목코드']}: {product['제품명']}")

if __name__ == "__main__":
    test_with_real_data()
