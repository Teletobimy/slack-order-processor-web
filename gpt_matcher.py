# -*- coding: utf-8 -*-
import openai
import json
from typing import Dict, List, Any, Optional
import re
import os

class GPTMatcher:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """GPT 매칭 클래스 초기화"""
        if config is None:
            # 환경 변수에서 설정 로드
            config = {
                "openai_api_key": os.getenv("OPENAI_API_KEY"),
                "products_db": "products_map.json"
            }
        
        if not config.get("openai_api_key"):
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        # OpenAI API 설정
        openai.api_key = config['openai_api_key']
        self.client = openai.OpenAI(api_key=config['openai_api_key'])
        
        # 제품 데이터베이스 로드
        self.products_db = self.load_products_db(config.get('products_db', 'products_map.json'))
        
        # 담당자-브랜드 매핑 (우선순위 낮음, 참고용 힌트만)
        self.user_brand_mapping = {
            "김다연": "바루랩",
            "이유주": "탐뷰티",
            "이승학": "피더린"
        }
        
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
    
    def extract_brand_hint_from_text(self, text: str) -> Optional[str]:
        """
        텍스트에서 브랜드 힌트 추출
        """
        # 브랜드명이 직접 언급된 경우
        brands = ["피더린", "바루랩", "탐뷰티", "탐 뷰티"]
        for brand in brands:
            if brand in text:
                return brand
        
        return None
    
    def match_products_with_context(self, full_text: str, message_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        RAG 방식: 전체 메시지 문맥을 활용한 제품 매칭
        """
        # 1. 브랜드 힌트 추출
        brand_hint = self.extract_brand_hint_from_text(full_text)
        
        # 2. 담당자 브랜드 힌트 추출 (우선순위 낮음)
        user_hint = None
        if "user" in message_info:
            user_name = message_info["user"].get("real_name", "")
            if user_name in self.user_brand_mapping:
                user_hint = self.user_brand_mapping[user_name]
        
        # 3. 제품 데이터베이스 필터링
        relevant_products = {}
        if brand_hint and brand_hint in self.products_db:
            relevant_products[brand_hint] = self.products_db[brand_hint]
        else:
            relevant_products = self.products_db
        
        # 4. GPT 매칭 프롬프트 생성
        brand_filter = ""
        if brand_hint:
            brand_filter = f"\n⚠️ 중요: 이 메시지에서 '{brand_hint}' 브랜드가 명시되었습니다. 반드시 '{brand_hint}' 브랜드 내에서만 매칭해주세요."
        if user_hint and user_hint != brand_hint:
            brand_filter += f"\n참고: 담당자는 '{user_hint}' 브랜드를 맡습니다. (우선순위 낮음)"
        
        prompt = f"""
다음 메시지 스레드에서 요청된 제품들을 추출하고, 제품 데이터베이스에서 매칭해주세요.

메시지: "{full_text}"

참고: 이 메시지는 원본 메시지와 댓글이 포함된 전체 문맥입니다.
댓글에서 "앰플재고 부족으로", "재고 상황에 따라" 등의 이유를 제시하며 제품과 수량을 수정/조정한 내용이 있다면,
전체 문맥을 종합적으로 고려하여 최종 요청사항을 판단해주세요.

제품 데이터베이스:
{json.dumps(relevant_products, ensure_ascii=False, indent=2)}

응답 형식:
{{
  "products": [
    {{
      "product_name": "제품명 (용량 포함)",
      "quantity": 수량,
      "unit": "단위",
      "capacity": "용량 (예: 1ml, 30ml, 150g 등)",
      "품목코드": "매칭된 품목코드",
      "제품명": "데이터베이스의 정확한 제품명",
      "브랜드": "브랜드명",
      "confidence": 신뢰도 (0-100),
      "matched_capacity": true/false
    }}
  ],
  "ambiguous": [모호한 제품들이 있다면 배열로 반환]
}}

규칙:
1. "각 제품별 X개" 패턴을 정확히 처리:
   - "클렌저, 토너, 앰플, 크림 - 각 제품별 5개" → 클렌저 5개, 토너 5개, 앰플 5개, 크림 5개 (4개 항목)
   - "앰플, 마스크 3종(얼굴,손,발) - 각 제품별 1개" → 앰플 1개, 얼굴마스크 1개, 손마스크 1개, 발마스크 1개 (4개 항목)
   - "마스크 3종(얼굴,손,발) - 각 제품별 1개" → 얼굴마스크 1개, 손마스크 1개, 발마스크 1개 (3개 항목)

2. 제품명과 수량을 정확히 추출
3. 용량 정보가 있으면 반드시 포함 (예: 1ml, 30ml, 150g)
4. 용량이 데이터베이스와 일치하면 matched_capacity=true, 아니면 false
5. 용량이 다르면 confidence를 50 미만으로 설정
6. 브랜드가 명시되면 해당 브랜드만 검색
7. 모호한 경우 모든 가능한 후보를 ambiguous 배열에 추가
{brand_filter}
8. JSON만 응답하고 다른 설명은 하지 마세요
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "당신은 제품 매칭 전문가입니다. 문맥을 정확히 이해하고 매칭해주세요."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # JSON 파싱
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                
                result = json.loads(content)
                
                # 결과 정제
                matched_products = result.get("products", [])
                ambiguous_products = result.get("ambiguous", [])
                
                # 각 제품에 ambiguous 플래그 추가
                for product in matched_products:
                    product["ambiguous"] = any(
                        amb.get("product_name") == product.get("product_name")
                        for amb in ambiguous_products
                    )
                
                return matched_products
                
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 내용: {content}")
                return []
                
        except Exception as e:
            print(f"RAG 매칭 API 오류: {e}")
            return []
    
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
