# -*- coding: utf-8 -*-
import requests
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

class SlackFetcher:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Slack 데이터 수집 클래스 초기화"""
        if config is None:
            # 환경 변수에서 설정 로드
            self.config = {
                "slack_bot_token": os.getenv("SLACK_BOT_TOKEN"),
                "channel_id": os.getenv("CHANNEL_ID"),
                "openai_api_key": os.getenv("OPENAI_API_KEY"),
                "warehouse_code": os.getenv("WAREHOUSE_CODE", "100")
            }
        else:
            self.config = config
        
        if not self.config.get("slack_bot_token"):
            raise ValueError("SLACK_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        
        self.headers = {
            "Authorization": f"Bearer {self.config['slack_bot_token']}"
        }
        self.channel_id = self.config.get('channel_id')
        
    def get_date_range(self, custom_start: Optional[str] = None, custom_end: Optional[str] = None) -> tuple:
        """
        날짜 범위 계산
        - 기본: 직전 날짜 (월요일이면 금~일)
        - 커스텀: 사용자 지정 날짜
        """
        if custom_start and custom_end:
            return custom_start, custom_end
        
        today = datetime.now()
        
        # 월요일인 경우 금요일~일요일
        if today.weekday() == 0:  # 월요일
            start_date = today - timedelta(days=3)  # 금요일
            end_date = today - timedelta(days=1)     # 일요일
        else:
            # 평일인 경우 직전 날짜
            start_date = today - timedelta(days=1)
            end_date = today - timedelta(days=1)
        
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def fetch_messages(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        지정된 날짜 범위의 메시지들을 가져옴
        """
        print(f"메시지 수집 중: {start_date} ~ {end_date}")
        
        # Unix timestamp로 변환
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp()) + 86399  # 하루 끝까지
        
        all_messages = []
        cursor = None
        
        while True:
            params = {
                "channel": self.channel_id,
                "oldest": start_ts,
                "latest": end_ts,
                "limit": 200
            }
            
            if cursor:
                params["cursor"] = cursor
            
            try:
                response = requests.get(
                    "https://slack.com/api/conversations.history",
                    headers=self.headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                if not data.get("ok"):
                    print(f"API 오류: {data.get('error')}")
                    break
                
                messages = data.get("messages", [])
                all_messages.extend(messages)
                
                print(f"수집된 메시지: {len(messages)}개 (총 {len(all_messages)}개)")
                
                # 페이지네이션 확인
                if not data.get("has_more"):
                    break
                    
                cursor = data.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
                    
                # API 제한 고려
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"요청 오류: {e}")
                break
        
        print(f"총 {len(all_messages)}개 메시지 수집 완료")
        return all_messages
    
    def fetch_thread_replies(self, message_ts: str) -> List[Dict[str, Any]]:
        """
        특정 메시지의 스레드 댓글들을 가져옴
        """
        params = {
            "channel": self.channel_id,
            "ts": message_ts
        }
        
        try:
            response = requests.get(
                "https://slack.com/api/conversations.replies",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                replies = data.get("messages", [])
                # 첫 번째 메시지는 원본이므로 제외
                return replies[1:] if len(replies) > 1 else []
            else:
                print(f"댓글 수집 오류: {data.get('error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"댓글 요청 오류: {e}")
            return []
    
    def download_file(self, file_info: Dict[str, Any], download_dir: str = "downloads") -> Optional[str]:
        """
        첨부 파일을 다운로드
        """
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        file_url = file_info.get("url_private_download")
        if not file_url:
            print(f"다운로드 URL이 없습니다: {file_info.get('name', 'Unknown')}")
            return None
        
        filename = file_info.get("name", "unknown_file")
        filepath = os.path.join(download_dir, filename)
        
        try:
            response = requests.get(file_url, headers=self.headers, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"파일 다운로드 완료: {filename}")
            return filepath
            
        except requests.exceptions.RequestException as e:
            print(f"파일 다운로드 오류: {e}")
            return None
    
    def process_messages_with_threads(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        메시지와 스레드 댓글을 함께 처리
        """
        processed_messages = []
        
        for i, message in enumerate(messages):
            print(f"메시지 처리 중: {i+1}/{len(messages)}")
            
            # 원본 메시지 정보
            message_data = {
                "ts": message["ts"],
                "user": message.get("user"),
                "text": message.get("text", ""),
                "thread_ts": message.get("thread_ts"),
                "original_message": message,
                "thread_replies": [],
                "downloaded_files": []
            }
            
            # 스레드 댓글 수집
            if message.get("thread_ts"):
                replies = self.fetch_thread_replies(message["thread_ts"])
                message_data["thread_replies"] = replies
                print(f"  - 댓글 {len(replies)}개 수집")
            
            # 첨부 파일 다운로드
            if message.get("files"):
                for file_info in message["files"]:
                    if file_info.get("filetype") in ["xls", "xlsx"]:
                        filepath = self.download_file(file_info)
                        if filepath:
                            message_data["downloaded_files"].append({
                                "file_info": file_info,
                                "filepath": filepath
                            })
            
            processed_messages.append(message_data)
            
            # API 제한 고려
            time.sleep(0.5)
        
        return processed_messages
    
    def save_processed_data(self, processed_messages: List[Dict[str, Any]], filename: str = "processed_slack_data.json"):
        """
        처리된 데이터를 JSON 파일로 저장
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(processed_messages, f, ensure_ascii=False, indent=2)
        print(f"처리된 데이터 저장: {filename}")
    
    def fetch_all_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        전체 데이터 수집 프로세스 실행
        """
        # 날짜 범위 계산
        start_date, end_date = self.get_date_range(start_date, end_date)
        
        # 메시지 수집
        messages = self.fetch_messages(start_date, end_date)
        
        # 스레드와 파일 처리
        processed_messages = self.process_messages_with_threads(messages)
        
        # 데이터 저장
        self.save_processed_data(processed_messages)
        
        return processed_messages

if __name__ == "__main__":
    # 테스트 실행
    fetcher = SlackFetcher()
    data = fetcher.fetch_all_data()
    print(f"수집 완료: {len(data)}개 메시지 처리됨")
