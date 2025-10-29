# -*- coding: utf-8 -*-
"""
Streamlit 웹앱 버전 - Slack 출고 데이터 처리 자동화
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator
import io

def check_dependencies():
    """필수 파일 및 의존성 확인"""
    required_files = [
        "products2_map__combined.json", 
        "Template_json_with_rows_columns.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def get_api_keys_from_session():
    """세션 상태에서 API 키 가져오기"""
    return {
        "slack_bot_token": st.session_state.get('slack_bot_token', ''),
        "channel_id": st.session_state.get('slack_channel_id', ''),
        "openai_api_key": st.session_state.get('openai_api_key', ''),
        "warehouse_code": st.session_state.get('warehouse_code', '100')
    }

def check_config():
    """설정 파일 검증 (세션 상태 우선)"""
    import os
    
    # 세션 상태에서 먼저 확인
    session_config = get_api_keys_from_session()
    if all(session_config.values()):
        return []
    
    # 환경변수에서 확인
    env_config = {
        "slack_bot_token": os.getenv('SLACK_BOT_TOKEN'),
        "channel_id": os.getenv('SLACK_CHANNEL_ID'),
        "openai_api_key": os.getenv('OPENAI_API_KEY'),
        "warehouse_code": os.getenv('WAREHOUSE_CODE', '100')
    }
    
    if all(env_config.values()):
        return []
    
    # config.json 파일 확인 (선택사항)
    if os.path.exists("config.json"):
        try:
            with open("config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_keys = [
                "slack_bot_token",
                "channel_id", 
                "openai_api_key",
                "warehouse_code"
            ]
            
            missing_keys = []
            for key in required_keys:
                if key not in config or not config[key]:
                    missing_keys.append(key)
            
            if not missing_keys:
                return []
                
        except Exception as e:
            pass  # config.json 파일이 있지만 읽기 실패한 경우 무시
    
    # 모든 방법이 실패한 경우 누락된 키 반환
    return ["slack_bot_token", "channel_id", "openai_api_key", "warehouse_code"]

def main():
    """메인 Streamlit 앱"""
    st.set_page_config(
        page_title="Slack 출고 데이터 처리 자동화",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Slack 출고 데이터 처리 자동화")
    st.markdown("---")
    
    # 의존성 확인
    missing_files = check_dependencies()
    if missing_files:
        st.error("다음 필수 파일이 없습니다:")
        for file in missing_files:
            st.error(f"  - {file}")
        st.stop()
    
    # 설정 확인
    missing_keys = check_config()
    if missing_keys:
        st.warning("API 키 설정이 필요합니다. 아래에서 직접 입력하거나 환경변수를 설정해주세요.")
        
        # API 키 입력 섹션
        with st.expander("🔐 API 키 직접 입력", expanded=True):
            st.markdown("**보안 주의**: API 키는 브라우저 세션에만 저장되며, 페이지를 새로고침하면 사라집니다.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                slack_bot_token = st.text_input(
                    "Slack Bot Token",
                    key="slack_bot_token",
                    type="password",
                    help="xoxb-로 시작하는 Slack Bot Token"
                )
                
                slack_channel_id = st.text_input(
                    "Slack Channel ID",
                    key="slack_channel_id",
                    help="예: C01AA471D46"
                )
            
            with col2:
                openai_api_key = st.text_input(
                    "OpenAI API Key",
                    key="openai_api_key",
                    type="password",
                    help="sk-proj-로 시작하는 OpenAI API Key"
                )
                
                warehouse_code = st.text_input(
                    "Warehouse Code",
                    key="warehouse_code",
                    value="100",
                    help="출하창고 코드 (기본값: 100)"
                )
            
            # 입력된 값들을 변수로 저장 (세션 상태는 자동으로 관리됨)
            # st.text_input의 key 매개변수가 자동으로 세션 상태를 관리합니다
            
            # 설정 확인 버튼
            if st.button("✅ 설정 확인", type="primary"):
                # 디버깅: 세션 상태 확인
                st.write("**디버깅 정보:**")
                st.write(f"Slack Bot Token: {'설정됨' if st.session_state.get('slack_bot_token') else '없음'}")
                st.write(f"Channel ID: {'설정됨' if st.session_state.get('slack_channel_id') else '없음'}")
                st.write(f"OpenAI API Key: {'설정됨' if st.session_state.get('openai_api_key') else '없음'}")
                st.write(f"Warehouse Code: {st.session_state.get('warehouse_code', '없음')}")
                
                # 다시 설정 확인
                missing_keys = check_config()
                if not missing_keys:
                    st.success("✅ 모든 API 키가 설정되었습니다!")
                    st.rerun()
                else:
                    st.error("아직 누락된 설정이 있습니다:")
                    for key in missing_keys:
                        st.error(f"  - {key}")
        
        # 환경변수 설정 가이드
        with st.expander("🌐 Streamlit Cloud 환경변수 설정 방법"):
            st.markdown("""
            **Streamlit Cloud 배포 시 사용:**
            1. Streamlit Cloud 대시보드에서 앱 선택
            2. Settings → Secrets 탭 클릭
            3. 다음 내용 추가:
            ```toml
            SLACK_BOT_TOKEN = "xoxb-your-token"
            SLACK_CHANNEL_ID = "C01AA471D46"
            OPENAI_API_KEY = "sk-proj-your-key"
            WAREHOUSE_CODE = "100"
            ```
            """)
        
        st.stop()
    
    st.success("✅ 모든 필수 파일과 설정이 확인되었습니다.")
    
    # 사이드바 - 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 날짜 선택
        st.subheader("📅 날짜 선택")
        auto_date = st.checkbox("자동 날짜 계산", value=True, 
                               help="직전 날짜, 월요일이면 금~일")
        
        if auto_date:
            # API 키가 설정되어 있으면 사용, 없으면 기본값으로 날짜 계산
            api_keys = get_api_keys_from_session()
            if api_keys.get('slack_bot_token'):
                slack_fetcher = SlackFetcher(api_keys=api_keys)
            else:
                slack_fetcher = SlackFetcher()
            start_date, end_date = slack_fetcher.get_date_range()
            st.info(f"자동 계산된 날짜:\n시작: {start_date}\n종료: {end_date}")
        else:
            start_date = st.date_input("시작일", value=datetime.now().date() - timedelta(days=1))
            end_date = st.date_input("종료일", value=datetime.now().date() - timedelta(days=1))
            start_date = start_date.strftime("%Y-%m-%d")
            end_date = end_date.strftime("%Y-%m-%d")
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🚀 데이터 처리")
        
        if st.button("📥 데이터 수집 시작", type="primary", use_container_width=True):
            with st.spinner("데이터 수집 중..."):
                try:
                    # API 키 가져오기
                    api_keys = get_api_keys_from_session()
                    
                    # 모듈 초기화 (API 키 전달)
                    slack_fetcher = SlackFetcher(api_keys=api_keys)
                    aggregator = DataAggregator(api_keys=api_keys)
                    
                    # 진행률 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 0단계: Slack API 연결 테스트
                    status_text.text("Slack API 연결 테스트 중...")
                    progress_bar.progress(10)
                    
                    # API 연결 테스트
                    test_result = slack_fetcher.test_api_connection()
                    if test_result['success']:
                        st.success(f"✅ Slack API 연결 성공: {test_result['message']}")
                    else:
                        st.error(f"❌ Slack API 연결 실패: {test_result['message']}")
                        st.stop()
                    
                    # 1단계: Slack 데이터 수집
                    status_text.text("Slack 메시지 수집 중...")
                    progress_bar.progress(20)
                    
                    messages = slack_fetcher.fetch_messages(start_date, end_date)
                    st.write(f"📊 수집된 메시지 수: {len(messages) if messages else 0}")
                    
                    if not messages:
                        st.warning("⚠️ 메시지가 수집되지 않았습니다. 다음을 확인해주세요:")
                        st.write("1. Slack Bot Token이 올바른지 확인")
                        st.write("2. 채널 ID가 정확한지 확인")
                        st.write("3. Bot이 해당 채널에 초대되었는지 확인")
                        st.write("4. 해당 날짜 범위에 메시지가 있는지 확인")
                        st.stop()
                    
                    processed_messages = slack_fetcher.process_messages_with_threads(messages)
                    st.write(f"📊 처리된 메시지 수: {len(processed_messages) if processed_messages else 0}")
                    
                    # 2단계: 데이터 집계
                    status_text.text("데이터 집계 중...")
                    progress_bar.progress(60)
                    
                    aggregated_data = aggregator.aggregate_products(processed_messages)
                    st.write(f"📊 집계된 제품 수: {len(aggregated_data.get('aggregated_products', [])) if aggregated_data else 0}")
                    
                    # 3단계: 결과 표시
                    status_text.text("결과 표시 중...")
                    progress_bar.progress(80)
                    
                    # 세션 상태에 저장
                    st.session_state.aggregated_data = aggregated_data
                    
                    # 완료
                    status_text.text("✅ 데이터 수집 완료")
                    progress_bar.progress(100)
                    
                    st.success("데이터 수집이 완료되었습니다!")
                    
                except Exception as e:
                    st.error(f"데이터 수집 중 오류 발생: {str(e)}")
    
    with col2:
        st.header("📋 결과")
        
        if 'aggregated_data' in st.session_state:
            aggregated_data = st.session_state.aggregated_data
            products = aggregated_data.get("aggregated_products", [])
            
            if products:
                st.success(f"총 {len(products)}개 제품 발견")
                
                # 데이터프레임으로 표시
                df_data = []
                for product in products:
                    df_data.append({
                        "품목코드": product["품목코드"],
                        "제품명": product["제품명"],
                        "수량": product["총_수량"],
                        "신뢰도": f"{product['신뢰도']}%"
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                # 다운로드 버튼들
                st.markdown("---")
                
                # Excel 다운로드
                if st.button("📊 Excel 파일 생성", use_container_width=True):
                    with st.spinner("Excel 파일 생성 중..."):
                        try:
                            excel_generator = ExcelGenerator()
                            
                            # 임시 파일로 생성
                            temp_filename = f"temp_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            success = excel_generator.generate_excel_with_summary(aggregated_data, temp_filename)
                            
                            if success:
                                # 파일 읽기
                                with open(temp_filename, 'rb') as f:
                                    excel_data = f.read()
                                
                                # 다운로드 버튼
                                st.download_button(
                                    label="📥 Excel 파일 다운로드",
                                    data=excel_data,
                                    file_name=f"출고데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                                
                                # 임시 파일 삭제
                                os.remove(temp_filename)
                                
                            else:
                                st.error("Excel 파일 생성에 실패했습니다.")
                                
                        except Exception as e:
                            st.error(f"Excel 생성 중 오류 발생: {str(e)}")
                
                # JSON 다운로드
                if st.button("💾 JSON 데이터 다운로드", use_container_width=True):
                    json_str = json.dumps(aggregated_data, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="📥 JSON 파일 다운로드",
                        data=json_str,
                        file_name=f"출고데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            else:
                st.warning("수집된 데이터가 없습니다.")
        else:
            st.info("데이터를 수집해주세요.")
    
    # 하단 정보
    st.markdown("---")
    st.markdown("### 📝 사용 방법")
    st.markdown("""
    1. **날짜 선택**: 자동 계산 또는 수동 입력
    2. **데이터 수집**: Slack에서 메시지와 첨부파일 수집
    3. **결과 확인**: 제품별 수량 집계 결과 확인
    4. **파일 다운로드**: Excel 또는 JSON 형태로 다운로드
    """)
    
    st.markdown("### 🔧 기술 스택")
    st.markdown("""
    - **Python 3.10+**
    - **Streamlit**: 웹 인터페이스
    - **Slack API**: 메시지 및 파일 수집
    - **OpenAI GPT-4o**: 제품명 추출 및 매칭
    - **openpyxl**: Excel 파일 처리
    - **pandas**: 데이터 처리
    """)

if __name__ == "__main__":
    main()
