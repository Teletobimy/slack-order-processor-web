# -*- coding: utf-8 -*-
import pandas as pd
import openpyxl
from typing import Dict, List, Any, Optional
import os

class ExcelParser:
    def __init__(self):
        """Excel 파싱 클래스 초기화"""
        pass
    
    def parse_excel_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Excel 파일을 파싱하여 제품명과 수량 추출
        """
        if not os.path.exists(filepath):
            print(f"파일이 존재하지 않습니다: {filepath}")
            return []
        
        try:
            # Excel 파일 읽기
            df = pd.read_excel(filepath, engine='openpyxl')
            
            # 컬럼명 확인 및 정규화
            df.columns = df.columns.str.strip()  # 공백 제거
            
            print(f"Excel 파일 컬럼: {list(df.columns)}")
            
            # model과 quantity 컬럼 찾기
            model_col = None
            quantity_col = None
            
            # 정확한 컬럼명 찾기
            for col in df.columns:
                col_lower = col.lower()
                if 'model' in col_lower or '제품' in col or '품목' in col:
                    model_col = col
                elif 'quantity' in col_lower or '수량' in col or 'qty' in col_lower:
                    quantity_col = col
            
            if not model_col or not quantity_col:
                print(f"필수 컬럼을 찾을 수 없습니다. model: {model_col}, quantity: {quantity_col}")
                print(f"사용 가능한 컬럼: {list(df.columns)}")
                return []
            
            print(f"사용할 컬럼 - 제품명: {model_col}, 수량: {quantity_col}")
            
            # 데이터 추출
            products = []
            for index, row in df.iterrows():
                product_name = str(row[model_col]).strip()
                quantity = row[quantity_col]
                
                # 빈 값이나 NaN 제외
                if pd.isna(product_name) or product_name == '' or product_name.lower() == 'nan':
                    continue
                
                if pd.isna(quantity) or quantity == '':
                    continue
                
                # 수량을 숫자로 변환
                try:
                    quantity_num = float(quantity)
                    if quantity_num <= 0:
                        continue
                except (ValueError, TypeError):
                    continue
                
                products.append({
                    "product_name": product_name,
                    "quantity": quantity_num,
                    "row_index": index + 2,  # Excel 행 번호 (헤더 제외)
                    "source_file": os.path.basename(filepath)
                })
            
            print(f"추출된 제품 수: {len(products)}개")
            return products
            
        except Exception as e:
            print(f"Excel 파싱 오류: {e}")
            return []
    
    def parse_multiple_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        여러 Excel 파일을 파싱
        """
        all_products = []
        
        for filepath in file_paths:
            print(f"파일 파싱 중: {os.path.basename(filepath)}")
            products = self.parse_excel_file(filepath)
            all_products.extend(products)
        
        return all_products
    
    def validate_excel_structure(self, filepath: str) -> bool:
        """
        Excel 파일 구조 검증
        """
        try:
            df = pd.read_excel(filepath, engine='openpyxl')
            df.columns = df.columns.str.strip()
            
            # 필수 컬럼 확인
            has_model = any('model' in col.lower() or '제품' in col or '품목' in col for col in df.columns)
            has_quantity = any('quantity' in col.lower() or '수량' in col or 'qty' in col.lower() for col in df.columns)
            
            return has_model and has_quantity
            
        except Exception as e:
            print(f"파일 구조 검증 오류: {e}")
            return False
    
    def get_excel_summary(self, filepath: str) -> Dict[str, Any]:
        """
        Excel 파일 요약 정보 반환
        """
        try:
            df = pd.read_excel(filepath, engine='openpyxl')
            
            return {
                "filename": os.path.basename(filepath),
                "rows": len(df),
                "columns": list(df.columns),
                "file_size": os.path.getsize(filepath),
                "is_valid": self.validate_excel_structure(filepath)
            }
            
        except Exception as e:
            return {
                "filename": os.path.basename(filepath),
                "error": str(e),
                "is_valid": False
            }

if __name__ == "__main__":
    # 테스트 실행
    parser = ExcelParser()
    
    # 테스트용 파일이 있다면
    test_file = "test.xlsx"
    if os.path.exists(test_file):
        products = parser.parse_excel_file(test_file)
        print(f"파싱 결과: {len(products)}개 제품")
        for product in products[:5]:  # 처음 5개만 출력
            print(f"  - {product['product_name']}: {product['quantity']}개")
    else:
        print("테스트 파일이 없습니다.")
