# -*- coding: utf-8 -*-
"""
Flask 웹앱 버전 - Slack 출고 데이터 처리 자동화
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import json
import os
from datetime import datetime, timedelta
import pandas as pd
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator
import tempfile
import threading

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 실제 사용시 변경 필요

# 전역 변수로 데이터 저장 (실제 운영시에는 데이터베이스 사용 권장)
app_data = {
    'aggregated_data': None,
    'processing_status': 'idle',
    'progress': 0,
    'status_message': '대기 중...'
}

def check_dependencies():
    """필수 파일 및 의존성 확인"""
    required_files = [
        "config.json",
        "products2_map__combined.json", 
        "Template_json_with_rows_columns.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def check_config():
    """설정 파일 검증"""
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
        
        return missing_keys
        
    except Exception as e:
        return [f"설정 파일 읽기 오류: {e}"]

def process_data_thread(start_date, end_date):
    """데이터 처리 스레드"""
    try:
        app_data['processing_status'] = 'processing'
        app_data['progress'] = 0
        app_data['status_message'] = 'Slack 메시지 수집 중...'
        
        # 모듈 초기화
        slack_fetcher = SlackFetcher()
        aggregator = DataAggregator()
        
        # 1단계: Slack 데이터 수집
        app_data['progress'] = 20
        messages = slack_fetcher.fetch_messages(start_date, end_date)
        processed_messages = slack_fetcher.process_messages_with_threads(messages)
        
        # 2단계: 데이터 집계
        app_data['status_message'] = '데이터 집계 중...'
        app_data['progress'] = 60
        
        aggregated_data = aggregator.aggregate_products(processed_messages)
        
        # 3단계: 완료
        app_data['status_message'] = '데이터 수집 완료'
        app_data['progress'] = 100
        app_data['aggregated_data'] = aggregated_data
        app_data['processing_status'] = 'completed'
        
    except Exception as e:
        app_data['processing_status'] = 'error'
        app_data['status_message'] = f'오류 발생: {str(e)}'

@app.route('/')
def index():
    """메인 페이지"""
    # 의존성 확인
    missing_files = check_dependencies()
    missing_keys = check_config()
    
    return render_template('index.html', 
                         missing_files=missing_files,
                         missing_keys=missing_keys,
                         app_data=app_data)

@app.route('/api/process', methods=['POST'])
def process_data():
    """데이터 처리 API"""
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    auto_date = data.get('auto_date', True)
    
    if auto_date:
        slack_fetcher = SlackFetcher()
        start_date, end_date = slack_fetcher.get_date_range()
    
    # 별도 스레드에서 처리
    thread = threading.Thread(target=process_data_thread, args=(start_date, end_date))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/status')
def get_status():
    """처리 상태 확인 API"""
    return jsonify(app_data)

@app.route('/api/download/excel')
def download_excel():
    """Excel 파일 다운로드"""
    if not app_data['aggregated_data']:
        return jsonify({'error': '데이터가 없습니다'}), 400
    
    try:
        excel_generator = ExcelGenerator()
        
        # 임시 파일 생성
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_filename = temp_file.name
        temp_file.close()
        
        success = excel_generator.generate_excel_with_summary(
            app_data['aggregated_data'], temp_filename
        )
        
        if success:
            return send_file(
                temp_filename,
                as_attachment=True,
                download_name=f"출고데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify({'error': 'Excel 파일 생성 실패'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/json')
def download_json():
    """JSON 파일 다운로드"""
    if not app_data['aggregated_data']:
        return jsonify({'error': '데이터가 없습니다'}), 400
    
    try:
        json_str = json.dumps(app_data['aggregated_data'], ensure_ascii=False, indent=2)
        
        # 임시 파일 생성
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
        temp_file.write(json_str)
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f"출고데이터_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 템플릿 폴더 생성
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True, host='0.0.0.0', port=5000)
