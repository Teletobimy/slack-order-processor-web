# -*- coding: utf-8 -*-
"""
특정 제품 매칭 테스트
"""

from gpt_matcher import GPTMatcher

def test_specific_product():
    """특정 제품 매칭 테스트"""
    print("=== 특정 제품 매칭 테스트 ===")
    
    try:
        gpt_matcher = GPTMatcher()
        
        # 테스트할 제품들
        test_products = [
            "블루아쿠아마스크",
            "쌀겨수 클렌징패드",
            "쌀막걸리 에센스",
            "징크크림",
            "스팀시트 마스크",
            "블랙클레이 마스크",
            "갈바닉 세럼"
        ]
        
        for product_name in test_products:
            print(f"\n--- '{product_name}' 매칭 테스트 ---")
            
            # 정확한 매칭 시도
            print("1. 정확한 매칭 시도:")
            for brand_name, brand_products in gpt_matcher.products_db.items():
                for product_code, product_full_name in brand_products.items():
                    if product_full_name.strip().lower() == product_name.strip().lower():
                        print(f"  ✓ 정확한 매칭 발견!")
                        print(f"    브랜드: {brand_name}")
                        print(f"    품목코드: {product_code}")
                        print(f"    제품명: {product_full_name}")
                        break
                else:
                    continue
                break
            else:
                print("  ✗ 정확한 매칭 없음")
            
            # GPT 매칭 시도
            print("2. GPT 매칭 시도:")
            match_result = gpt_matcher.match_product_to_code(product_name)
            if match_result:
                print(f"  ✓ GPT 매칭 성공!")
                print(f"    품목코드: {match_result.get('품목코드')}")
                print(f"    제품명: {match_result.get('제품명')}")
                print(f"    브랜드: {match_result.get('브랜드')}")
                print(f"    신뢰도: {match_result.get('confidence')}")
            else:
                print("  ✗ GPT 매칭 실패")
        
        return True
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_specific_product()
