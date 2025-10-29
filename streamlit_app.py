# -*- coding: utf-8 -*-
"""
Slack 출고 데이터 처리 자동화 - Streamlit 웹 애플리케이션
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import tempfile
import zipfile
from io import BytesIO

# 로컬 모듈 import
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator

# 페이지 설정
st.set_page_config(
    page_title="Slack 출고 데이터 처리",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 콘솔 인코딩 설정
def setup_console_encoding():
    """콘솔 인코딩 설정"""
    try:
        if os.name == 'nt':  # Windows
            os.system('chcp 65001 > nul')
        return True
    except:
        return False

# 설정 로드
@st.cache_data
def load_config():
    """설정 로드 (환경 변수만 사용)"""
    try:
        # 환경 변수에서 설정 로드
        config = {
            "slack_bot_token": os.getenv("SLACK_BOT_TOKEN"),
            "channel_id": os.getenv("CHANNEL_ID"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "warehouse_code": os.getenv("WAREHOUSE_CODE", "100")
        }
        
        # 필수 환경 변수 확인
        required_vars = ["slack_bot_token", "channel_id", "openai_api_key"]
        missing_vars = [var for var in required_vars if not config.get(var)]
        
        if missing_vars:
            st.error(f"다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
            st.info("Streamlit Cloud에서 환경 변수를 설정해주세요.")
            return None
        
        return config
    except Exception as e:
        st.error(f"설정 로드 오류: {e}")
        return None

# 제품 데이터베이스 로드
@st.cache_data
def load_products_db():
    """제품 데이터베이스 로드"""
    try:
        # 파일 존재 확인
        if not os.path.exists("products_map.json"):
            st.error("products_map.json 파일을 찾을 수 없습니다.")
            with st.expander("🔍 파일 목록 확인", expanded=False):
                st.info("현재 디렉토리 파일들:")
                for file in os.listdir("."):
                    st.write(f"- {file}")
            return None
            
        with open("products_map.json", 'r', encoding='utf-8') as f:
            products_db = json.load(f)
            st.success(f"제품 데이터베이스 로드 성공: {len(products_db)}개 브랜드")
            return products_db
    except Exception as e:
        st.error(f"제품 데이터베이스 로드 오류: {e}")
        with st.expander("🔍 상세 오류 정보", expanded=False):
            import traceback
            st.code(traceback.format_exc())
        return None

def main():
    """메인 애플리케이션"""
    st.title("📦 Slack 출고 데이터 처리 자동화")
    st.markdown("---")
    
    # 설정 로드
    config = load_config()
    if not config:
        st.error("환경 변수가 설정되지 않았습니다.")
        st.markdown("""
        ### 🔧 환경 변수 설정 방법
        
        Streamlit Cloud에서 다음 환경 변수를 설정해주세요:
        
        1. **SLACK_BOT_TOKEN**: Slack Bot Token (xoxb-로 시작)
        2. **OPENAI_API_KEY**: OpenAI API Key (sk-로 시작)  
        3. **CHANNEL_ID**: Slack 채널 ID (C로 시작)
        4. **WAREHOUSE_CODE**: 창고 코드 (기본값: 100)
        
        환경 변수 설정 후 페이지를 새로고침해주세요.
        """)
        return
    
    products_db = load_products_db()
    if not products_db:
        st.error("제품 데이터베이스를 확인해주세요.")
        return
    
    # 사이드바 - 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # 날짜 선택
        st.subheader("📅 처리 기간")
        today = datetime.now().date()
        
        # SlackFetcher 로직과 동일하게 설정
        if today.weekday() == 0:  # 월요일이면 금요일~일요일
            default_start = today - timedelta(days=3)  # 금요일
            default_end = today - timedelta(days=1)     # 일요일
        else:
            # 평일인 경우 직전 날짜만
            default_start = today - timedelta(days=1)   # 어제
            default_end = today - timedelta(days=1)     # 어제
        
        start_date = st.date_input(
            "시작 날짜",
            value=default_start,
            max_value=today
        )
        
        end_date = st.date_input(
            "종료 날짜", 
            value=default_end,
            max_value=today
        )
        
        if start_date > end_date:
            st.error("시작 날짜는 종료 날짜보다 이전이어야 합니다.")
            return
        
        # 채널 선택
        st.subheader("📢 채널 설정")
        channel_id = st.text_input(
            "채널 ID",
            value=config.get("channel_id", ""),
            help="Slack 채널 ID를 입력하세요"
        )
        
        # 처리 옵션
        st.subheader("🔧 처리 옵션")
        include_threads = st.checkbox("스레드 댓글 포함", value=True)
        include_files = st.checkbox("첨부파일 처리", value=True)
    
    # 메인 영역
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📊 데이터 처리")
        
        # 처리 시작 버튼
        if st.button("🚀 데이터 처리 시작", type="primary"):
            if not channel_id:
                st.error("채널 ID를 입력해주세요.")
                return
            
            # 진행 상황 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # 1. Slack 데이터 수집
                status_text.text("📡 Slack 데이터 수집 중...")
                progress_bar.progress(10)
                
                fetcher = SlackFetcher(config)
                fetcher.channel_id = channel_id
                
                messages = fetcher.fetch_messages(
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                if not messages:
                    st.warning("선택한 기간에 메시지가 없습니다.")
                    return
                
                st.success(f"✅ {len(messages)}개 메시지 수집 완료")
                
                # 2. 메시지 처리
                status_text.text("🔄 메시지 처리 중...")
                progress_bar.progress(30)
                
                processed_messages = fetcher.process_messages_with_threads(messages)
                st.success(f"✅ {len(processed_messages)}개 메시지 처리 완료")
                
                # 3. 데이터 집계
                status_text.text("📊 데이터 집계 중...")
                progress_bar.progress(60)
                
                aggregator = DataAggregator(config)
                aggregated_data = aggregator.aggregate_products(processed_messages)
                
                aggregated_by_brand = aggregated_data.get("aggregated_by_brand", {})
                brands = aggregated_data.get("brands", [])
                
                if not brands:
                    st.warning("매칭된 제품이 없습니다.")
                    st.info("처리된 메시지 수: " + str(len(processed_messages)))
                    return
                
                st.success(f"✅ {len(brands)}개 브랜드에서 제품 매칭 완료")
                
                # 디버깅 정보 (접을 수 있는 형태)
                with st.expander("🔍 디버깅 정보 (개발자용)", expanded=False):
                    st.subheader("처리된 메시지")
                    for i, msg in enumerate(processed_messages, 1):
                        st.write(f"**메시지 {i}:** {msg.get('text', '')[:100]}...")
                    
                    st.subheader("집계된 데이터")
                    st.json(aggregated_data)
                    
                    st.subheader("브랜드별 집계")
                    st.json(aggregated_by_brand)
                    
                    st.subheader("발견된 브랜드")
                    st.write(brands)
                
                # 4. 검증 화면
                st.markdown("---")
                st.subheader("📝 제품 매칭 확인")
                
                # 모호한 제품 표시
                ambiguous_products = aggregated_data.get("ambiguous_products", [])
                if ambiguous_products:
                    st.warning(f"⚠️ {len(ambiguous_products)}개 제품이 모호합니다. 확인이 필요합니다.")
                    st.write("**모호한 제품 목록:**")
                    for i, product in enumerate(ambiguous_products, 1):
                        with st.expander(f"제품 {i}: {product.get('product_name', '알 수 없음')}"):
                            st.write(f"- 요청 제품: {product.get('product_name', '')}")
                            st.write(f"- 수량: {product.get('quantity', 0)} {product.get('unit', '')}")
                            st.write(f"- 용량: {product.get('capacity', '미기재')}")
                            st.write(f"- 신뢰도: {product.get('confidence', 0)}%")
                            
                            # 사용자 선택
                            key = f"ambiguous_choice_{i}"
                            selected = st.radio(
                                "이 제품이 맞습니까?",
                                options=["매칭 유지", "제외"],
                                key=key,
                                index=0
                            )
                            if selected == "제외":
                                # 제품 제외 로직 (나중에 구현)
                                pass
                else:
                    st.success("✅ 모든 제품이 명확하게 매칭되었습니다.")
                
                # 정상 매칭된 제품 요약
                st.write("**매칭된 제품 요약:**")
                for brand in brands:
                    with st.expander(f"{brand} 브랜드 ({len(aggregated_by_brand.get(brand, []))}개 제품)"):
                        for product in aggregated_by_brand.get(brand, []):
                            st.write(f"- {product.get('제품명', '')} × {product.get('총_수량', 0)}개")
                
                # 최종 확인 버튼
                if st.button("✅ 최종 확인 및 Excel 생성", type="primary"):
                    progress_bar.progress(80)
                    status_text.text("📄 Excel 파일 생성 중...")
                    
                    # 5. Excel 생성
                    generator = ExcelGenerator(config)
                    
                    # 임시 디렉토리에 파일 생성
                    with tempfile.TemporaryDirectory() as temp_dir:
                        created_files = generator.create_excel_files_by_brand(aggregated_data, temp_dir)
                        
                        if created_files:
                            progress_bar.progress(100)
                            status_text.text("✅ 완료!")
                            
                            # ZIP 파일 생성
                            zip_buffer = BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for file_path in created_files:
                                    zip_file.write(file_path, os.path.basename(file_path))
                            zip_buffer.seek(0)
                            
                            st.download_button(
                                label="📥 Excel 파일 다운로드 (ZIP)",
                                data=zip_buffer,
                                file_name=f"출고_데이터_{start_date}_{end_date}.zip",
                                mime="application/zip"
                            )
                            
                            # 미리보기
                            for file_path in created_files:
                                st.write(f"✅ {os.path.basename(file_path)} 생성 완료")
                        else:
                            st.error("Excel 파일 생성 실패")
                    
                    progress_bar.empty()
                    status_text.empty()
                
                return
                
            except Exception as e:
                st.error(f"처리 중 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    with col2:
        st.header("📈 통계")
        
        if 'aggregated_data' in locals():
            st.metric("총 제품 종류", aggregated_data.get('unique_products', 0))
            st.metric("처리된 스레드", len(aggregated_data.get('thread_summaries', [])))
            st.metric("발견된 브랜드", len(brands))
        
        st.header("ℹ️ 정보")
        st.info("""
        **처리 과정:**
        1. Slack 메시지 수집
        2. 제품명 및 수량 추출
        3. GPT를 통한 제품 매칭
        4. 브랜드별 Excel 파일 생성
        """)
        
        st.header("🏷️ 지원 브랜드")
        for brand in products_db.keys():
            st.write(f"• {brand}")

if __name__ == "__main__":
    setup_console_encoding()
    main()