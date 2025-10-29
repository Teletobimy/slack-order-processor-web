# -*- coding: utf-8 -*-
"""
전체 시스템 통합 테스트
"""

import json
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator

def test_full_system():
    """전체 시스템 테스트"""
    print("=== 전체 시스템 통합 테스트 ===")
    
    try:
        # 1. Slack 데이터 수집
        print("1. Slack 데이터 수집 중...")
        fetcher = SlackFetcher()
        
        # 최근 데이터 수집 (테스트용으로 하루만)
        messages = fetcher.fetch_messages("2025-10-16", "2025-10-16")
        print(f"   수집된 메시지: {len(messages)}개")
        
        if not messages:
            print("   수집된 메시지가 없습니다.")
            return
        
        # 스레드와 파일 처리
        processed_messages = fetcher.process_messages_with_threads(messages)
        print(f"   처리된 메시지: {len(processed_messages)}개")
        
        # 2. 데이터 집계
        print("2. 데이터 집계 중...")
        aggregator = DataAggregator()
        aggregated_data = aggregator.aggregate_products(processed_messages)
        
        products = aggregated_data.get("aggregated_products", [])
        print(f"   집계된 제품: {len(products)}개")
        
        # 결과 출력
        print("\n=== 집계 결과 ===")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['제품명']} (코드: {product['품목코드']}) - {product['총_수량']}개")
        
        # 3. Excel 생성
        print("\n3. Excel 파일 생성 중...")
        generator = ExcelGenerator()
        
        success = generator.generate_excel_with_summary(aggregated_data, "test_output.xlsx")
        
        if success:
            print("   Excel 파일 생성 성공: test_output.xlsx")
        else:
            print("   Excel 파일 생성 실패")
        
        # 4. 요약 리포트
        print("\n4. 요약 리포트:")
        report = aggregator.get_summary_report(aggregated_data)
        print(report)
        
        print("\n=== 테스트 완료 ===")
        return True
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_full_system()
