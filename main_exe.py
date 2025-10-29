# -*- coding: utf-8 -*-
"""
Slack 주문서 처리 시스템 - 메인 실행 파일
브랜드별 Excel 파일 생성
"""

import sys
import os
import json
from datetime import datetime, timedelta
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator

def load_config():
    """설정 파일 로드"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ config.json 파일을 찾을 수 없습니다.")
        return None
    except Exception as e:
        print(f"❌ 설정 파일 로드 오류: {e}")
        return None

def get_default_date_range():
    """기본 날짜 범위 계산"""
    today = datetime.now()
    
    # 월요일이면 금요일-일요일, 아니면 어제
    if today.weekday() == 0:  # 월요일
        friday = today - timedelta(days=3)
        sunday = today - timedelta(days=1)
        return friday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')
    else:
        yesterday = today - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 Slack 주문서 처리 시스템 (브랜드별)")
    print("=" * 60)
    
    # 설정 로드
    config = load_config()
    if not config:
        input("엔터를 눌러 종료하세요...")
        return
    
    print(f"📅 처리 기간: 기본값 사용 (월요일이면 금-일, 아니면 어제)")
    print(f"📦 제품 데이터베이스: {config['products_db']}")
    print(f"🏢 출하창고: {config['warehouse_code']}")
    print()
    
    try:
        # 날짜 범위 계산
        start_date, end_date = get_default_date_range()
        print(f"📅 처리 날짜: {start_date} ~ {end_date}")
        
        # 1. Slack 데이터 수집
        print("\n1️⃣ Slack 데이터 수집 중...")
        fetcher = SlackFetcher()
        messages = fetcher.fetch_messages(start_date, end_date)
        
        if not messages:
            print("❌ 해당 기간에 메시지가 없습니다.")
            input("엔터를 눌러 종료하세요...")
            return
        
        print(f"✅ 수집된 메시지: {len(messages)}개")
        
        # 메시지 처리
        processed_messages = fetcher.process_messages_with_threads(messages)
        print(f"✅ 처리된 메시지: {len(processed_messages)}개")
        
        # 2. 데이터 집계
        print("\n2️⃣ 데이터 집계 중...")
        aggregator = DataAggregator()
        aggregated_data = aggregator.aggregate_products(processed_messages)
        
        aggregated_by_brand = aggregated_data.get("aggregated_by_brand", {})
        brands = aggregated_data.get("brands", [])
        
        if not brands:
            print("❌ 매칭된 제품이 없습니다.")
            input("엔터를 눌러 종료하세요...")
            return
        
        print(f"✅ 발견된 브랜드: {', '.join(brands)}")
        
        # 브랜드별 결과 출력
        print("\n📊 브랜드별 집계 결과:")
        for brand_name, products in aggregated_by_brand.items():
            print(f"\n📦 {brand_name} 브랜드:")
            if products:
                for i, product in enumerate(products, 1):
                    print(f"  {i}. {product['제품명']} (코드: {product['품목코드']}) - {product['총_수량']}개")
            else:
                print("  제품이 없습니다.")
        
        # 3. 브랜드별 Excel 생성
        print("\n3️⃣ 브랜드별 Excel 파일 생성 중...")
        generator = ExcelGenerator()
        
        # 출력 디렉토리 생성
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        created_files = generator.create_excel_files_by_brand(aggregated_data, output_dir)
        
        if created_files:
            print(f"✅ 생성된 Excel 파일: {len(created_files)}개")
            for filepath in created_files:
                filename = os.path.basename(filepath)
                print(f"  📄 {filename}")
        else:
            print("❌ Excel 파일 생성 실패")
            input("엔터를 눌러 종료하세요...")
            return
        
        # 4. 요약 리포트
        print("\n4️⃣ 요약 리포트:")
        report = aggregator.get_summary_report(aggregated_data)
        print(report)
        
        print("\n🎉 처리 완료!")
        print(f"📁 결과 파일 위치: {os.path.abspath(output_dir)}")
        
    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    input("엔터를 눌러 종료하세요...")

if __name__ == "__main__":
    main()


