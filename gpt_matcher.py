# -*- coding: utf-8 -*-
import openai
import json
from typing import Dict, List, Any, Optional
import re
import os

class GPTMatcher:
    def __init__(self, config_path: str = "config.json"):
        """GPT 매칭 클래스 초기화"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # OpenAI API 설정
        openai.api_key = config['openai_api_key']
        self.client = openai.OpenAI(api_key=config['openai_api_key'])
        
        # 제품 데이터베이스 로드
        self.products_db = self.load_products_db(config['products_db'])
        
    def load_products_db(self, db_path: str) -> Dict[str, Dict[str, str]]:
        """제품 데이터베이스 로드 (브랜드별 구조)"""
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                products_db = json.load(f)
            
            total_products = sum(len(brand_products) for brand_products in products_db.values())
            print(f"제품 데이터베이스 로드 완료: {len(products_db)}개 브랜드, {total_products}개 제품")
            return products_db
        except Exception as e:
            print(f"제품 데이터베이스 로드 오류: {e}")
            return {}
    
    def extract_products_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        텍스트에서 제품명과 수량 추출
        """
        if not text or not text.strip():
            return []
        
        prompt = f"""
다음 텍스트에서 제품명과 수량을 추출해주세요. JSON 형태로 응답해주세요.

텍스트: "{text}"

응답 형식:
[
  {{
    "product_name": "정확한 제품명",
    "quantity": 수량,
    "unit": "단위 (개, 세트, 박스 등)"
  }}
]

규칙:
1. 제품명은 정확하고 완전한 이름으로 추출
2. 수량은 숫자만 (예: "10개" -> 10)
3. 단위는 개, 세트, 박스, ea 등
4. 제품이 없으면 빈 배열 [] 반환
5. JSON만 응답하고 다른 설명은 하지 마세요
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 제품명과 수량을 정확히 추출하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱
            try:
                # JSON 부분만 추출 (```json ... ``` 형태일 수 있음)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                products = json.loads(content)
                
                # 유효성 검증
                if isinstance(products, list):
                    valid_products = []
                    for product in products:
                        if isinstance(product, dict) and "product_name" in product and "quantity" in product:
                            valid_products.append(product)
                    return valid_products
                else:
                    return []
                    
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 내용: {content}")
                return []
                
        except Exception as e:
            print(f"GPT API 오류: {e}")
            return []
    
    def match_product_to_code(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        제품명을 품목코드와 매칭 (브랜드별)
        """
        if not self.products_db:
            return None
        
        # 먼저 정확한 매칭 시도
        for brand_name, brand_products in self.products_db.items():
            for product_code, product_full_name in brand_products.items():
                if product_full_name.strip().lower() == product_name.strip().lower():
                    return {
                        "품목코드": product_code,
                        "제품명": product_full_name,
                        "브랜드": brand_name,
                        "confidence": 100
                    }
        
        # GPT를 사용한 유사 매칭
        prompt = f"""
다음 제품명과 가장 유사한 제품을 찾아주세요.

찾을 제품명: "{product_name}"

제품 데이터베이스 (브랜드별):
{json.dumps(self.products_db, ensure_ascii=False, indent=2)}

응답 형식:
{{
  "품목코드": "매칭된 품목코드",
  "제품명": "매칭된 제품명",
  "브랜드": "브랜드명",
  "confidence": "매칭 신뢰도 (0-100)"
}}

규칙:
1. 정확히 일치하는 제품이 있으면 그것을 선택
2. 유사한 제품이 있으면 가장 유사한 것을 선택
3. 신뢰도가 50 미만이면 null 반환
4. JSON만 응답하고 다른 설명은 하지 마세요
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 제품명 매칭 전문가입니다. 정확한 매칭을 우선시하세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                result = json.loads(content)
                
                # null 체크
                if result is None or result.get("품목코드") is None:
                    return None
                
                # 신뢰도 체크
                confidence = result.get("confidence", 0)
                if isinstance(confidence, str):
                    try:
                        confidence = float(confidence)
                    except ValueError:
                        confidence = 0
                if confidence < 50:
                    return None
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"매칭 결과 JSON 파싱 오류: {e}")
                print(f"응답 내용: {content}")
                return None
                
        except Exception as e:
            print(f"제품 매칭 API 오류: {e}")
            return None
    
    def generate_summary(self, message_text: str, products: List[Dict[str, Any]]) -> str:
        """
        메시지 내용을 바탕으로 적요 생성
        """
        if not message_text:
            return "출고 처리"
        
        prompt = f"""
다음 메시지 내용을 바탕으로 간단한 적요를 생성해주세요.

메시지: "{message_text[:200]}"
추출된 제품: {len(products)}개

규칙:
1. 10자 이내로 간단하게
2. 출고 관련 내용이면 "출고" 포함
3. 특별한 내용이 없으면 "출고 처리"
4. 텍스트만 응답하고 다른 설명은 하지 마세요
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 간단한 요약문을 생성하는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            summary = response.choices[0].message.content.strip()
            return summary[:10]  # 10자 제한
            
        except Exception as e:
            print(f"적요 생성 오류: {e}")
            return "출고 처리"
    
    def process_message_thread(self, message_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        메시지 스레드 전체를 처리하여 제품 정보 추출
        """
        results = []
        
        # 원본 메시지 처리
        original_message = message_data.get("original_message", {})
        message_text = original_message.get("text", "")
        
        if message_text:
            print(f"원본 메시지 처리: {message_text[:50]}...")
            products = self.extract_products_from_text(message_text)
            
            for product in products:
                # 품목코드 매칭
                match_result = self.match_product_to_code(product["product_name"])
                if match_result:
                    results.append({
                        "product_name": product["product_name"],
                        "quantity": product["quantity"],
                        "unit": product.get("unit", "개"),
                        "품목코드": match_result["품목코드"],
                        "매칭된_제품명": match_result["제품명"],
                        "브랜드": match_result["브랜드"],
                        "confidence": match_result["confidence"],
                        "source": "original_message",
                        "message_text": message_text[:100]
                    })
        
        # 스레드 댓글 처리
        replies = message_data.get("thread_replies", [])
        for reply in replies:
            reply_text = reply.get("text", "")
            if reply_text:
                print(f"댓글 처리: {reply_text[:50]}...")
                products = self.extract_products_from_text(reply_text)
                
                for product in products:
                    match_result = self.match_product_to_code(product["product_name"])
                    if match_result:
                        results.append({
                            "product_name": product["product_name"],
                            "quantity": product["quantity"],
                            "unit": product.get("unit", "개"),
                            "품목코드": match_result["품목코드"],
                            "매칭된_제품명": match_result["제품명"],
                            "브랜드": match_result["브랜드"],
                            "confidence": match_result["confidence"],
                            "source": "reply",
                            "message_text": reply_text[:100]
                        })
        
        # 적요 생성
        if results:
            all_text = message_text + " " + " ".join([reply.get("text", "") for reply in replies])
            summary = self.generate_summary(all_text, results)
            for result in results:
                result["적요"] = summary
        
        return results

if __name__ == "__main__":
    # 테스트 실행
    matcher = GPTMatcher()
    
    # 테스트 텍스트
    test_text = "탐뷰티 더 클라우드 컨실러 4홋수 각 10개씩, 시그니처 세트 1ea & 쇼핑백 1ea"
    
    products = matcher.extract_products_from_text(test_text)
    print(f"추출된 제품: {products}")
    
    for product in products:
        match = matcher.match_product_to_code(product["product_name"])
        print(f"매칭 결과: {match}")
