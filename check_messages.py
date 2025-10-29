# -*- coding: utf-8 -*-
"""
실제 메시지 내용 확인
"""

import json
from datetime import datetime
from slack_fetcher import SlackFetcher

def check_messages():
    """실제 메시지 내용 확인"""
    print("=== 실제 메시지 내용 확인 ===")
    
    try:
        # 오늘 날짜 계산
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"확인 날짜: {today}")
        
        # Slack 데이터 수집
        fetcher = SlackFetcher()
        messages = fetcher.fetch_messages(today, today)
        
        if not messages:
            print("오늘 메시지가 없습니다. 어제 데이터로 확인합니다.")
            yesterday = datetime.now().strftime('%Y-%m-%d')
            messages = fetcher.fetch_messages(yesterday, yesterday)
        
        print(f"수집된 메시지: {len(messages)}개")
        
        # 메시지 내용 출력
        for i, message in enumerate(messages, 1):
            print(f"\n--- 메시지 {i} ---")
            print(f"시간: {message.get('ts', 'N/A')}")
            print(f"사용자: {message.get('user', 'N/A')}")
            print(f"텍스트: {message.get('text', 'N/A')}")
            
            # 첨부파일 확인
            files = message.get('files', [])
            if files:
                print(f"첨부파일: {len(files)}개")
                for j, file_info in enumerate(files, 1):
                    print(f"  파일 {j}: {file_info.get('name', 'N/A')}")
                    print(f"    타입: {file_info.get('filetype', 'N/A')}")
                    print(f"    크기: {file_info.get('size', 'N/A')}")
        
        # 스레드 처리
        print("\n=== 스레드 처리 테스트 ===")
        processed_messages = fetcher.process_messages_with_threads(messages)
        
        for i, processed in enumerate(processed_messages, 1):
            print(f"\n--- 처리된 메시지 {i} ---")
            print(f"원본 텍스트: {processed.get('text', 'N/A')}")
            print(f"스레드 댓글 수: {len(processed.get('replies', []))}")
            print(f"첨부파일 수: {len(processed.get('files', []))}")
            
            # 댓글 내용
            replies = processed.get('replies', [])
            if replies:
                print("댓글 내용:")
                for j, reply in enumerate(replies, 1):
                    print(f"  댓글 {j}: {reply.get('text', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"확인 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_messages()
