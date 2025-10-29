# -*- coding: utf-8 -*-
"""
콘솔 버전 - Slack 출고 데이터 처리 자동화
"""

import json
import os
from datetime import datetime, timedelta
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator

# -*- coding: utf-8 -*-
"""
콘솔 버전 - Slack 출고 데이터 처리 자동화
"""

import json
import os
from datetime import datetime, timedelta
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator

def get_api_keys():
    """API 키 입력받기"""
    print("=== Slack 출고 데이터 처리 자동화 (콘솔 버전) ===")
    print()
    
    # config.json 파일이 있으면 사용
    if os.path.exists("config.json"):
        try:
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            print("[OK] config.json 파일에서 설정을 불러왔습니다.")
            return config
        except Exception as e:
            print(f"[ERROR] config.json 파일 읽기 오류: {e}")
    
    # 수동 입력
    print("API 키를 입력해주세요:")
    slack_bot_token = input("Slack Bot Token (xoxb-로 시작): ").strip()
    channel_id = input("Slack Channel ID (예: C01AA471D46): ").strip()
    openai_api_key = input("OpenAI API Key (sk-proj-로 시작): ").strip()
    warehouse_code = input("Warehouse Code (기본값: 100): ").strip() or "100"
    
    return {
        "slack_bot_token": slack_bot_token,
        "channel_id": channel_id,
        "openai_api_key": openai_api_key,
        "warehouse_code": warehouse_code
    }

def get_date_range():
    """날짜 범위 입력받기"""
    print("\n=== 날짜 선택 ===")
    print("1. 자동 날짜 계산 (직전 날짜, 월요일이면 금~일)")
    print("2. 수동 날짜 입력")
    
    choice = input("선택 (1 또는 2): ").strip()
    
    if choice == "1":
        # 자동 날짜 계산
        today = datetime.now()
        if today.weekday() == 0:  # 월요일
            start_date = today - timedelta(days=3)  # 금요일
            end_date = today - timedelta(days=1)     # 일요일
        else:
            start_date = today - timedelta(days=1)
            end_date = today - timedelta(days=1)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        print(f"자동 계산된 날짜: {start_date_str} ~ {end_date_str}")
        return start_date_str, end_date_str
    else:
        # 수동 입력
        start_date = input("시작일 (YYYY-MM-DD): ").strip()
        end_date = input("종료일 (YYYY-MM-DD): ").strip()
        return start_date, end_date

def main():
    """메인 함수"""
    try:
        # API 키 가져오기
        api_keys = get_api_keys()
        
        # 필수 키 확인
        required_keys = ["slack_bot_token", "channel_id", "openai_api_key"]
        missing_keys = [key for key in required_keys if not api_keys.get(key)]
        
        if missing_keys:
            print(f"❌ 다음 키가 누락되었습니다: {', '.join(missing_keys)}")
            return
        
        # 날짜 범위 가져오기
        start_date, end_date = get_date_range()
        
        print(f"\n=== 데이터 수집 시작 ===")
        print(f"날짜 범위: {start_date} ~ {end_date}")
        
        # 모듈 초기화
        slack_fetcher = SlackFetcher(api_keys=api_keys)
        aggregator = DataAggregator(api_keys=api_keys)
        excel_generator = ExcelGenerator()
        
        # 1단계: Slack API 연결 테스트
        print("\n1. Slack API 연결 테스트...")
        test_result = slack_fetcher.test_api_connection()
        if test_result['success']:
            print(f"✅ {test_result['message']}")
        else:
            print(f"❌ {test_result['message']}")
            return
        
        # 2단계: 메시지 수집
        print("\n2. Slack 메시지 수집...")
        messages = slack_fetcher.fetch_messages(start_date, end_date)
        print(f"📊 수집된 메시지 수: {len(messages) if messages else 0}")
        
        if not messages:
            print("⚠️ 메시지가 수집되지 않았습니다.")
            print("다음을 확인해주세요:")
            print("1. Slack Bot Token이 올바른지 확인")
            print("2. 채널 ID가 정확한지 확인")
            print("3. Bot이 해당 채널에 초대되었는지 확인")
            print("4. 해당 날짜 범위에 메시지가 있는지 확인")
            return
        
        # 3단계: 메시지 처리
        print("\n3. 메시지 처리...")
        processed_messages = slack_fetcher.process_messages_with_threads(messages)
        print(f"📊 처리된 메시지 수: {len(processed_messages) if processed_messages else 0}")
        
        # 4단계: 데이터 집계
        print("\n4. 데이터 집계...")
        aggregated_data = aggregator.aggregate_products(processed_messages)
        products = aggregated_data.get("aggregated_products", [])
        print(f"📊 집계된 제품 수: {len(products)}")
        
        if not products:
            print("⚠️ 집계된 제품이 없습니다.")
            return
        
        # 5단계: 결과 표시
        print("\n=== 집계 결과 ===")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['제품명']} ({product['품목코드']}) - 수량: {product['총_수량']} - 신뢰도: {product['신뢰도']}%")
        
        # 6단계: Excel 파일 생성
        print("\n5. Excel 파일 생성...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"output/출고데이터_{timestamp}.xlsx"
        
        # output 폴더가 없으면 생성
        os.makedirs("output", exist_ok=True)
        
        success = excel_generator.generate_excel_with_summary(aggregated_data, filename)
        if success:
            print(f"✅ Excel 파일이 생성되었습니다: {filename}")
        else:
            print("❌ Excel 파일 생성에 실패했습니다.")
        
        # 7단계: JSON 파일 저장
        json_filename = f"output/출고데이터_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 파일이 저장되었습니다: {json_filename}")
        
        print("\n🎉 데이터 처리가 완료되었습니다!")
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
