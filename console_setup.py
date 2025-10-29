# -*- coding: utf-8 -*-
"""
콘솔 인코딩 설정 및 Streamlit 웹 애플리케이션
"""

import sys
import os
import locale
import codecs

def setup_console_encoding():
    """콘솔 인코딩 설정"""
    try:
        # Windows 콘솔 인코딩 설정
        if sys.platform.startswith('win'):
            # UTF-8 모드 활성화
            os.system('chcp 65001 > nul')
            
            # stdout, stderr 인코딩 설정
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
            
            # locale 설정
            try:
                locale.setlocale(locale.LC_ALL, 'ko_KR.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_ALL, 'Korean_Korea.utf8')
                except:
                    pass
        
        print("✅ 콘솔 인코딩 설정 완료")
        return True
        
    except Exception as e:
        print(f"❌ 콘솔 인코딩 설정 실패: {e}")
        return False

def test_korean_display():
    """한글 표시 테스트"""
    print("\n=== 한글 표시 테스트 ===")
    print("브랜드별 시스템 테스트")
    print("탐뷰티, 바루랩, 피더린")
    print("제품 매칭 및 Excel 생성")
    print("✅ 한글이 정상적으로 표시됩니다!")

if __name__ == "__main__":
    setup_console_encoding()
    test_korean_display()
