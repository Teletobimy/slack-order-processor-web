# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict
from excel_parser import ExcelParser
from gpt_matcher import GPTMatcher

class DataAggregator:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """데이터 집계 클래스 초기화"""
        self.excel_parser = ExcelParser()
        self.gpt_matcher = GPTMatcher(config)
        
    def process_excel_files(self, downloaded_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        다운로드된 Excel 파일들을 처리
        """
        excel_products = []
        
        for file_data in downloaded_files:
            filepath = file_data.get("filepath")
            if not filepath:
                continue
            
            print(f"Excel 파일 처리 중: {filepath}")
            
            # Excel 파일 파싱
            products = self.excel_parser.parse_excel_file(filepath)
            
            for product in products:
                # 품목코드 매칭
                match_result = self.gpt_matcher.match_product_to_code(product["product_name"])
                if match_result:
                    excel_products.append({
                        "product_name": product["product_name"],
                        "quantity": product["quantity"],
                        "품목코드": match_result["품목코드"],
                        "매칭된_제품명": match_result["제품명"],
                        "브랜드": match_result["브랜드"],
                        "confidence": match_result["confidence"],
                        "source": "excel_file",
                        "source_file": product["source_file"],
                        "row_index": product["row_index"]
                    })
        
        return excel_products
    
    def aggregate_products(self, processed_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        모든 메시지에서 제품 정보를 집계 (RAG 방식 사용)
        """
        print("제품 정보 집계 시작...")
        
        all_products = []
        ambiguous_products = []
        thread_summaries = []
        
        for i, message_data in enumerate(processed_messages):
            print(f"메시지 처리 중: {i+1}/{len(processed_messages)}")
            
            # RAG 방식: 전체 메시지 문맥 활용
            original_message = message_data.get("original_message", {})
            replies = message_data.get("replies", [])
            
            # 전체 텍스트 조합
            full_text = original_message.get("text", "")
            for reply in replies:
                full_text += " " + reply.get("text", "")
            
            if full_text.strip():
                # RAG 매칭 사용
                rag_products = self.gpt_matcher.match_products_with_context(full_text, original_message.get("user", {}))
                
                for product in rag_products:
                    # ambiguous 분리
                    if product.get("ambiguous", False):
                        ambiguous_products.append(product)
                    else:
                        all_products.append(product)
            
            # Excel 파일 처리 (기존 방식 유지)
            downloaded_files = message_data.get("downloaded_files", [])
            if downloaded_files:
                excel_products = self.process_excel_files(downloaded_files)
                all_products.extend(excel_products)
            
            # 스레드 요약 생성
            if all_products:
                thread_summaries.append({
                    "thread_index": i,
                    "summary": "출고 처리",
                    "product_count": len([p for p in all_products if "thread_index" not in p])
                })
        
        # 브랜드별, 제품별 수량 집계
        aggregated_by_brand = self.aggregate_by_brand_and_product(all_products)
        
        return {
            "aggregated_by_brand": aggregated_by_brand,
            "ambiguous_products": ambiguous_products,
            "thread_summaries": thread_summaries,
            "total_products": len(all_products),
            "unique_products": sum(len(products) for products in aggregated_by_brand.values()),
            "brands": list(aggregated_by_brand.keys())
        }
    
    def aggregate_by_brand_and_product(self, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        브랜드별, 품목코드별로 제품 수량 집계
        """
        # 브랜드별로 그룹화
        brand_groups = defaultdict(lambda: defaultdict(list))
        
        for product in products:
            brand = product.get("브랜드")
            product_code = product.get("품목코드")
            if brand and product_code:
                brand_groups[brand][product_code].append(product)
        
        # 집계된 결과 생성
        aggregated_by_brand = {}
        
        for brand_name, brand_products in brand_groups.items():
            brand_aggregated = []
            
            for product_code, product_list in brand_products.items():
                # 수량을 정수로 변환하여 합산
                total_quantity = sum(int(p["quantity"]) if isinstance(p["quantity"], (int, str)) else 0 for p in product_list)
                
                # 가장 높은 신뢰도의 제품명 사용
                best_match = max(product_list, key=lambda x: x.get("confidence", 0) if isinstance(x.get("confidence"), (int, float)) else 0)
                
                # 출처 정보 수집
                sources = []
                for p in product_list:
                    source_info = f"{p.get('source', 'unknown')}"
                    if p.get('source_file'):
                        source_info += f"({p['source_file']})"
                    sources.append(source_info)
                
                brand_aggregated.append({
                    "품목코드": product_code,
                    "제품명": best_match.get("매칭된_제품명", ""),
                    "총_수량": total_quantity,
                    "신뢰도": best_match.get("confidence", 0),
                    "출처_수": len(product_list),
                    "출처_목록": list(set(sources)),
                    "상세_정보": product_list
                })
            
            # 수량 순으로 정렬
            brand_aggregated.sort(key=lambda x: x["총_수량"], reverse=True)
            aggregated_by_brand[brand_name] = brand_aggregated
        
        return aggregated_by_brand
    
    def validate_aggregation(self, aggregated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        집계 결과 검증 및 통계 생성
        """
        products = aggregated_data.get("aggregated_products", [])
        
        # 통계 계산
        total_quantity = sum(p["총_수량"] for p in products)
        avg_confidence = sum(p["신뢰도"] for p in products) / len(products) if products else 0
        
        # 신뢰도별 분포
        high_confidence = len([p for p in products if p["신뢰도"] >= 80])
        medium_confidence = len([p for p in products if 60 <= p["신뢰도"] < 80])
        low_confidence = len([p for p in products if p["신뢰도"] < 60])
        
        # 출처별 분포
        source_stats = defaultdict(int)
        for p in products:
            for source in p["출처_목록"]:
                source_stats[source] += 1
        
        validation_result = {
            "total_products": len(products),
            "total_quantity": total_quantity,
            "average_confidence": round(avg_confidence, 2),
            "confidence_distribution": {
                "high (80+)": high_confidence,
                "medium (60-79)": medium_confidence,
                "low (<60)": low_confidence
            },
            "source_distribution": dict(source_stats),
            "thread_count": len(aggregated_data.get("thread_summaries", [])),
            "validation_passed": len(products) > 0 and avg_confidence > 50
        }
        
        return validation_result
    
    def save_aggregated_data(self, aggregated_data: Dict[str, Any], filename: str = "aggregated_data.json"):
        """
        집계된 데이터를 JSON 파일로 저장
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, ensure_ascii=False, indent=2)
        print(f"집계 데이터 저장: {filename}")
    
    def get_summary_report(self, aggregated_data: Dict[str, Any]) -> str:
        """
        집계 결과 요약 리포트 생성
        """
        products = aggregated_data.get("aggregated_products", [])
        validation = self.validate_aggregation(aggregated_data)
        
        report = f"""
=== 제품 집계 결과 리포트 ===

📊 기본 통계
- 총 제품 종류: {validation['total_products']}개
- 총 수량: {validation['total_quantity']}개
- 평균 신뢰도: {validation['average_confidence']}%
- 처리된 스레드: {validation['thread_count']}개

🎯 신뢰도 분포
- 높음 (80%+): {validation['confidence_distribution']['high (80+)']}개
- 보통 (60-79%): {validation['confidence_distribution']['medium (60-79)']}개
- 낮음 (60% 미만): {validation['confidence_distribution']['low (<60)']}개

📋 상위 제품 (수량 기준)
"""
        
        for i, product in enumerate(products[:10], 1):
            report += f"{i}. {product['제품명']} (코드: {product['품목코드']}) - {product['총_수량']}개\n"
        
        if validation['validation_passed']:
            report += "\n✅ 검증 통과: 데이터 품질이 양호합니다."
        else:
            report += "\n⚠️ 검증 실패: 데이터 품질을 확인해주세요."
        
        return report

if __name__ == "__main__":
    # 테스트 실행
    aggregator = DataAggregator()
    
    # 테스트용 데이터가 있다면
    test_file = "processed_slack_data.json"
    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            processed_messages = json.load(f)
        
        aggregated_data = aggregator.aggregate_products(processed_messages)
        print(aggregator.get_summary_report(aggregated_data))
        
        aggregator.save_aggregated_data(aggregated_data)
    else:
        print("테스트 데이터가 없습니다.")
