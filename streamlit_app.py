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
        
        # 날짜 선택 (하루 단위만 처리)
        st.subheader("📅 처리 날짜")
        today = datetime.now().date()
        
        # 기본값 설정 (SlackFetcher 로직과 동일)
        if today.weekday() == 0:  # 월요일이면 금요일~일요일 중 일요일
            default_date = today - timedelta(days=1)  # 일요일
        else:
            # 평일인 경우 직전 날짜만
            default_date = today - timedelta(days=1)   # 어제
        
        target_date = st.date_input(
            "처리할 날짜",
            value=default_date,
            max_value=today,
            help="하루 단위로만 처리됩니다"
        )
        
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
        
        # 세션 상태 초기화
        if 'aggregated_data' not in st.session_state:
            st.session_state.aggregated_data = None
        if 'show_validation' not in st.session_state:
            st.session_state.show_validation = False
        if 'excel_ready' not in st.session_state:
            st.session_state.excel_ready = False
        
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
                
                # 하루 단위로 처리 (start_date와 end_date를 동일하게 설정)
                date_str = target_date.strftime('%Y-%m-%d')
                messages = fetcher.fetch_messages(date_str, date_str)
                
                if not messages:
                    st.warning(f"{target_date}에 메시지가 없습니다.")
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
                
                # 세션 상태에 저장
                st.session_state.aggregated_data = aggregated_data
                st.session_state.show_validation = True
                st.session_state.excel_ready = False
                
                aggregated_by_brand = aggregated_data.get("aggregated_by_brand", {})
                brands = aggregated_data.get("brands", [])
                
                if not brands:
                    st.warning("매칭된 제품이 없습니다.")
                    st.info("처리된 메시지 수: " + str(len(processed_messages)))
                    return
                
                st.success(f"✅ {len(brands)}개 브랜드에서 제품 매칭 완료")
                
                progress_bar.empty()
                status_text.empty()
                
                # 검증 화면 표시를 위해 다시 실행 (rerun)
                st.rerun()
                    
            except Exception as e:
                st.error(f"처리 중 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        # 검증 화면 표시 (세션 상태 사용)
        if st.session_state.show_validation and st.session_state.aggregated_data:
            aggregated_data = st.session_state.aggregated_data
            aggregated_by_brand = aggregated_data.get("aggregated_by_brand", {})
            brands = aggregated_data.get("brands", [])
            
            # 디버깅 정보 (접을 수 있는 형태)
            with st.expander("🔍 디버깅 정보 (개발자용)", expanded=False):
                st.subheader("집계된 데이터")
                st.json(aggregated_data)
                
                st.subheader("브랜드별 집계")
                st.json(aggregated_by_brand)
                
                st.subheader("발견된 브랜드")
                st.write(brands)
            
            # 검증 화면
            st.markdown("---")
            st.subheader("📝 제품 매칭 확인 및 조정")
            
            # 세션 상태에 선택된 제품 저장
            if 'selected_products' not in st.session_state:
                st.session_state.selected_products = {}
            
            # 모든 제품을 리스트로 구성
            all_products_list = []
            for brand in brands:
                for product in aggregated_by_brand.get(brand, []):
                    product_name = product.get('제품명', '') or product.get('상세_정보', [{}])[0].get('제품명', '알 수 없는 제품')
                    product_key = f"{brand}_{product.get('품목코드', '')}"
                    
                    # 기본값 설정
                    if product_key not in st.session_state.selected_products:
                        st.session_state.selected_products[product_key] = {
                            'selected': True,
                            'quantity': product.get('총_수량', 0)
                        }
                    
                    all_products_list.append({
                        'key': product_key,
                        '브랜드': brand,
                        '품목코드': product.get('품목코드', ''),
                        '제품명': product_name,
                        '수량': product.get('총_수량', 0),
                        '신뢰도': product.get('신뢰도', 0),
                        '원본데이터': product
                    })
            
            # 모호한 제품 표시
            ambiguous_products = aggregated_data.get("ambiguous_products", [])
            if ambiguous_products:
                st.warning(f"⚠️ {len(ambiguous_products)}개 제품이 모호합니다. 확인이 필요합니다.")
                st.write("**모호한 제품 목록:**")
                for i, product in enumerate(ambiguous_products, 1):
                    with st.expander(f"⚠️ 제품 {i}: {product.get('product_name', '알 수 없음')}"):
                        st.write(f"- 요청 제품: {product.get('product_name', '')}")
                        st.write(f"- 수량: {product.get('quantity', 0)} {product.get('unit', '')}")
                        st.write(f"- 용량: {product.get('capacity', '미기재')}")
                        st.write(f"- 신뢰도: {product.get('confidence', 0)}%")
                        st.write(f"- 매칭된 제품: {product.get('제품명', 'N/A')}")
            
            # 브랜드별로 제품 그룹화
            products_by_brand = {}
            for product in all_products_list:
                brand = product['브랜드']
                if brand not in products_by_brand:
                    products_by_brand[brand] = []
                products_by_brand[brand].append(product)
            
            # 브랜드 순서 정의 (피더린, 탐뷰티, 바루랩)
            brand_order = ['피더린', '탐뷰티', '바루랩']
            # 모든 브랜드를 항상 표시 (매칭되지 않았어도 수동 추가 가능)
            for brand in brand_order:
                if brand not in products_by_brand:
                    products_by_brand[brand] = []
            sorted_brands = brand_order + [b for b in brands if b not in brand_order]
            
            # 제품 추가용 세션 상태 초기화
            if 'manual_products' not in st.session_state:
                st.session_state.manual_products = {brand: [] for brand in brand_order}
            
            # 브랜드별 접는 형식으로 제품 표시
            for brand in sorted_brands:
                if brand not in products_by_brand:
                    products_by_brand[brand] = []
                
                brand_products = products_by_brand[brand]
                manual_products = st.session_state.manual_products.get(brand, [])
                total_brand_products = len(brand_products) + len(manual_products)
                
                with st.expander(f"🏷️ {brand} 브랜드 ({total_brand_products}개 제품)", expanded=True):
                    # 기존 매칭된 제품 테이블 형식으로 표시
                    if brand_products:
                        # 테이블 헤더
                        cols = st.columns([0.5, 3, 1, 1.5, 1, 1])
                        cols[0].write("**포함**")
                        cols[1].write("**제품명**")
                        cols[2].write("**품목코드**")
                        cols[3].write("**원본 수량**")
                        cols[4].write("**조정 수량**")
                        cols[5].write("**신뢰도**")
                        st.markdown("---")
                        
                        # 각 제품을 행으로 표시
                        for product in brand_products:
                            product_key = product['key']
                            
                            cols = st.columns([0.5, 3, 1, 1.5, 1, 1])
                            
                            # 포함 체크박스
                            with cols[0]:
                                selected = st.checkbox(
                                    "",
                                    value=st.session_state.selected_products[product_key]['selected'],
                                    key=f"checkbox_{product_key}",
                                    label_visibility="collapsed"
                                )
                                st.session_state.selected_products[product_key]['selected'] = selected
                            
                            # 제품명
                            with cols[1]:
                                st.write(product['제품명'])
                            
                            # 품목코드
                            with cols[2]:
                                st.write(product['품목코드'])
                            
                            # 원본 수량
                            with cols[3]:
                                st.write(f"{product['수량']}개")
                            
                            # 수량 조정
                            with cols[4]:
                                if selected:
                                    quantity = st.number_input(
                                        "",
                                        min_value=0,
                                        value=int(st.session_state.selected_products[product_key]['quantity']),
                                        key=f"quantity_{product_key}",
                                        label_visibility="collapsed"
                                    )
                                    st.session_state.selected_products[product_key]['quantity'] = quantity
                                else:
                                    st.write("-")
                            
                            # 신뢰도
                            with cols[5]:
                                st.write(f"{product['신뢰도']}%")
                    else:
                        # 매칭된 제품이 없을 때 안내 메시지
                        if not manual_products:
                            st.info(f"💡 {brand} 브랜드에서 매칭된 제품이 없습니다. 아래 버튼을 눌러 제품을 수동으로 추가할 수 있습니다.")
                    
                    st.markdown("---")
                    
                    # 수동 추가 제품 표시
                    if manual_products:
                        st.markdown("#### 수동 추가된 제품")
                        for idx, manual_product in enumerate(manual_products):
                            manual_key = f"manual_{brand}_{idx}"
                            
                            cols = st.columns([0.5, 2, 1, 1.5, 1, 1])
                            
                            with cols[0]:
                                selected = st.checkbox(
                                    "",
                                    value=st.session_state.selected_products.get(manual_key, {}).get('selected', True),
                                    key=f"checkbox_{manual_key}",
                                    label_visibility="collapsed"
                                )
                                if manual_key not in st.session_state.selected_products:
                                    st.session_state.selected_products[manual_key] = {'selected': True, 'quantity': manual_product.get('quantity', 0)}
                                st.session_state.selected_products[manual_key]['selected'] = selected
                            
                            with cols[1]:
                                product_name = st.text_input(
                                    "제품명",
                                    value=manual_product.get('제품명', ''),
                                    key=f"name_{manual_key}",
                                    label_visibility="collapsed"
                                )
                                manual_product['제품명'] = product_name
                            
                            with cols[2]:
                                product_code = st.text_input(
                                    "품목코드",
                                    value=manual_product.get('품목코드', ''),
                                    key=f"code_{manual_key}",
                                    label_visibility="collapsed"
                                )
                                manual_product['품목코드'] = product_code
                            
                            with cols[3]:
                                st.write("-")
                            
                            with cols[4]:
                                if selected:
                                    quantity = st.number_input(
                                        "수량",
                                        min_value=0,
                                        value=int(st.session_state.selected_products[manual_key].get('quantity', manual_product.get('quantity', 0))),
                                        key=f"quantity_{manual_key}",
                                        label_visibility="collapsed"
                                    )
                                    st.session_state.selected_products[manual_key]['quantity'] = quantity
                                else:
                                    st.write("-")
                            
                            with cols[5]:
                                if st.button("🗑️", key=f"delete_{manual_key}", help="삭제"):
                                    st.session_state.manual_products[brand].remove(manual_product)
                                    if manual_key in st.session_state.selected_products:
                                        del st.session_state.selected_products[manual_key]
                                    st.rerun()
                                else:
                                    st.write("-")
                            
                            st.markdown("---")
                    
                    # 제품 추가 버튼
                    if st.button(f"➕ {brand} 제품 추가", key=f"add_{brand}"):
                        if brand not in st.session_state.manual_products:
                            st.session_state.manual_products[brand] = []
                        st.session_state.manual_products[brand].append({
                            '브랜드': brand,
                            '제품명': '',
                            '품목코드': '',
                            '수량': 0
                        })
                        st.rerun()
            
            # 선택 요약
            selected_count = sum(1 for p in st.session_state.selected_products.values() if p.get('selected', False))
            total_quantity = sum(p['quantity'] for p in st.session_state.selected_products.values() if p.get('selected', False))
            st.info(f"✅ 총 {selected_count}개 제품이 선택되었습니다. (전체 {len(all_products_list) + sum(len(p) for p in st.session_state.manual_products.values())}개 중) | 선택된 총 수량: {total_quantity}개")
            
            # 최종 확인 버튼
            if st.button("✅ 최종 확인 및 Excel 생성", type="primary", key="final_confirm"):
                # 선택된 제품만 필터링하여 Excel 생성에 사용
                filtered_data = {
                    'aggregated_by_brand': {},
                    'brands': [],
                    'ambiguous_products': aggregated_data.get('ambiguous_products', []),
                    'thread_summaries': aggregated_data.get('thread_summaries', [])
                }
                
                # 선택된 제품만 집계
                all_brands_in_filter = set()
                
                for brand in brands:
                    brand_products = []
                    for product in aggregated_by_brand.get(brand, []):
                        product_key = f"{brand}_{product.get('품목코드', '')}"
                        if product_key in st.session_state.selected_products:
                            if st.session_state.selected_products[product_key].get('selected', False):
                                # 수량 수정 반영
                                modified_product = product.copy()
                                modified_product['총_수량'] = st.session_state.selected_products[product_key].get('quantity', product.get('총_수량', 0))
                                brand_products.append(modified_product)
                    
                    # 수동 추가된 제품 추가
                    if brand in st.session_state.manual_products:
                        for idx, manual_product in enumerate(st.session_state.manual_products[brand]):
                            manual_key = f"manual_{brand}_{idx}"
                            if manual_key in st.session_state.selected_products:
                                if st.session_state.selected_products[manual_key].get('selected', False):
                                    # 수동 추가 제품을 Excel 형식에 맞게 변환
                                    manual_excel_product = {
                                        '품목코드': manual_product.get('품목코드', ''),
                                        '제품명': manual_product.get('제품명', ''),
                                        '총_수량': st.session_state.selected_products[manual_key].get('quantity', 0),
                                        '신뢰도': 0,
                                        '출처_수': 1,
                                        '출처_목록': ['manual'],
                                        '상세_정보': [{
                                            'product_name': manual_product.get('제품명', ''),
                                            'quantity': st.session_state.selected_products[manual_key].get('quantity', 0),
                                            'source': 'manual'
                                        }]
                                    }
                                    brand_products.append(manual_excel_product)
                    
                    if brand_products:
                        filtered_data['aggregated_by_brand'][brand] = brand_products
                        all_brands_in_filter.add(brand)
                
                # 수동 추가 제품이 있는 브랜드도 포함
                for brand in st.session_state.manual_products.keys():
                    if brand not in all_brands_in_filter:
                        manual_brand_products = []
                        for idx, manual_product in enumerate(st.session_state.manual_products[brand]):
                            manual_key = f"manual_{brand}_{idx}"
                            if manual_key in st.session_state.selected_products:
                                if st.session_state.selected_products[manual_key].get('selected', False):
                                    manual_excel_product = {
                                        '품목코드': manual_product.get('품목코드', ''),
                                        '제품명': manual_product.get('제품명', ''),
                                        '총_수량': st.session_state.selected_products[manual_key].get('quantity', 0),
                                        '신뢰도': 0,
                                        '출처_수': 1,
                                        '출처_목록': ['manual'],
                                        '상세_정보': [{
                                            'product_name': manual_product.get('제품명', ''),
                                            'quantity': st.session_state.selected_products[manual_key].get('quantity', 0),
                                            'source': 'manual'
                                        }]
                                    }
                                    manual_brand_products.append(manual_excel_product)
                        
                        if manual_brand_products:
                            filtered_data['aggregated_by_brand'][brand] = manual_brand_products
                            all_brands_in_filter.add(brand)
                
                filtered_data['brands'] = list(all_brands_in_filter)
                
                if not filtered_data['brands']:
                    st.error("선택된 제품이 없습니다. 최소 1개 이상의 제품을 선택해주세요.")
                else:
                    with st.spinner("Excel 파일 생성 중..."):
                        # Excel 생성 (필터링된 데이터 사용)
                        generator = ExcelGenerator(config)
                        
                        # 임시 디렉토리에 파일 생성
                        with tempfile.TemporaryDirectory() as temp_dir:
                            created_files = generator.create_excel_files_by_brand(filtered_data, temp_dir)
                            
                            if created_files:
                                # ZIP 파일 생성
                                zip_buffer = BytesIO()
                                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                    for file_path in created_files:
                                        zip_file.write(file_path, os.path.basename(file_path))
                                zip_buffer.seek(0)
                                
                                # 세션 상태에 저장
                                st.session_state.excel_zip = zip_buffer.getvalue()
                                st.session_state.excel_filename = f"출고_데이터_{target_date.strftime('%Y-%m-%d')}.zip"
                                st.session_state.excel_ready = True
                                st.session_state.created_files = [os.path.basename(f) for f in created_files]
                                
                                st.success("✅ Excel 파일 생성 완료!")
                                st.rerun()
                            else:
                                st.error("Excel 파일 생성 실패")
        
        # Excel 다운로드 버튼 (세션 상태 사용)
        if st.session_state.excel_ready and 'excel_zip' in st.session_state:
            st.markdown("---")
            st.subheader("📥 파일 다운로드")
            
            st.download_button(
                label="📥 Excel 파일 다운로드 (ZIP)",
                data=st.session_state.excel_zip,
                file_name=st.session_state.excel_filename,
                mime="application/zip"
            )
            
            st.write("**생성된 파일:**")
            for filename in st.session_state.created_files:
                st.write(f"✅ {filename}")
            
            if st.button("🔄 새로 처리하기", key="reset"):
                # 세션 상태 초기화
                st.session_state.aggregated_data = None
                st.session_state.show_validation = False
                st.session_state.excel_ready = False
                if 'excel_zip' in st.session_state:
                    del st.session_state.excel_zip
                if 'excel_filename' in st.session_state:
                    del st.session_state.excel_filename
                if 'created_files' in st.session_state:
                    del st.session_state.created_files
                st.rerun()
    
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