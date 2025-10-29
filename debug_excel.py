# -*- coding: utf-8 -*-
"""
Excel 생성 오류 디버깅
"""

import json
from datetime import datetime
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator
import os
import traceback

def debug_excel_generation():
    """Excel 생성 오류 디버깅"""
    print("=== Excel 생성 오류 디버깅 ===")
    
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
        
        # 데이터 집계
        aggregator = DataAggregator()
        aggregated_data = aggregator.aggregate_products(processed_messages)
        
        aggregated_by_brand = aggregated_data.get("aggregated_by_brand", {})
        print(f"집계된 브랜드: {list(aggregated_by_brand.keys())}")
        
        # 각 브랜드의 데이터 구조 확인
        for brand_name, products in aggregated_by_brand.items():
            print(f"\n--- {brand_name} 브랜드 데이터 구조 ---")
            print(f"제품 수: {len(products)}")
            
            if products:
                print("첫 번째 제품 데이터:")
                first_product = products[0]
                for key, value in first_product.items():
                    print(f"  {key}: {value} (타입: {type(value)})")
        
        # Excel 생성 시도
        print("\n--- Excel 생성 시도 ---")
        generator = ExcelGenerator()
        
        # 출력 디렉토리 생성
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        created_files = generator.create_excel_files_by_brand(aggregated_data, output_dir)
        
        if created_files:
            print(f"생성된 Excel 파일: {len(created_files)}개")
            for filepath in created_files:
                print(f"  - {os.path.basename(filepath)}")
        else:
            print("Excel 파일 생성 실패")
        
        return True
        
    except Exception as e:
        print(f"디버깅 중 오류 발생: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_excel_generation()
