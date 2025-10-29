# -*- coding: utf-8 -*-
"""
새로운 브랜드별 구조로 테스트
"""

import json
from datetime import datetime
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator
import os

def test_brand_based_system():
    """브랜드별 시스템 테스트"""
    print("=== 브랜드별 시스템 테스트 ===")
    
    try:
        # 오늘 날짜 계산
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"테스트 날짜: {today}")
        
        # 1. Slack 데이터 수집
        print("\n1. Slack 데이터 수집 중...")
        fetcher = SlackFetcher()
        
        # 최근 데이터 수집
        messages = fetcher.fetch_messages(today, today)
        print(f"   수집된 메시지: {len(messages)}개")
        
        if not messages:
            print("   오늘 메시지가 없습니다. 어제 데이터로 테스트합니다.")
            yesterday = datetime.now().strftime('%Y-%m-%d')
            messages = fetcher.fetch_messages(yesterday, yesterday)
            print(f"   어제 수집된 메시지: {len(messages)}개")
        
        if not messages:
            print("   수집할 메시지가 없습니다.")
            return
        
        # 스레드와 파일 처리
        processed_messages = fetcher.process_messages_with_threads(messages)
        print(f"   처리된 메시지: {len(processed_messages)}개")
        
        # 2. 데이터 집계
        print("\n2. 데이터 집계 중...")
        aggregator = DataAggregator()
        aggregated_data = aggregator.aggregate_products(processed_messages)
        
        aggregated_by_brand = aggregated_data.get("aggregated_by_brand", {})
        brands = aggregated_data.get("brands", [])
        
        print(f"   발견된 브랜드: {brands}")
        
        # 브랜드별 결과 출력
        print("\n=== 브랜드별 집계 결과 ===")
        for brand_name, products in aggregated_by_brand.items():
            print(f"\n📦 {brand_name} 브랜드:")
            if products:
                for i, product in enumerate(products, 1):
                    print(f"  {i}. {product['제품명']} (코드: {product['품목코드']}) - {product['총_수량']}개")
            else:
                print("  제품이 없습니다.")
        
        # 3. 브랜드별 Excel 생성
        if aggregated_by_brand:
            print("\n3. 브랜드별 Excel 파일 생성 중...")
            generator = ExcelGenerator()
            
            # 출력 디렉토리 생성
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            created_files = generator.create_excel_files_by_brand(aggregated_data, output_dir)
            
            if created_files:
                print(f"   생성된 Excel 파일: {len(created_files)}개")
                for filepath in created_files:
                    print(f"   - {os.path.basename(filepath)}")
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
    test_brand_based_system()


