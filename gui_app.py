# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import json
import os
from slack_fetcher import SlackFetcher
from aggregator import DataAggregator
from excel_generator import ExcelGenerator

class SlackOrderProcessorGUI:
    def __init__(self):
        """GUI 애플리케이션 초기화"""
        self.root = tk.Tk()
        self.root.title("Slack 출고 데이터 처리 자동화")
        self.root.geometry("800x600")
        
        # 모듈 초기화
        self.slack_fetcher = SlackFetcher()
        self.aggregator = DataAggregator()
        self.excel_generator = ExcelGenerator()
        
        # 데이터 저장
        self.processed_data = None
        self.aggregated_data = None
        
        # GUI 구성
        self.setup_gui()
        
    def setup_gui(self):
        """GUI 구성 요소 설정"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = ttk.Label(main_frame, text="Slack 출고 데이터 처리 자동화", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 날짜 선택 섹션
        self.setup_date_section(main_frame)
        
        # 버튼 섹션
        self.setup_button_section(main_frame)
        
        # 진행 상황 섹션
        self.setup_progress_section(main_frame)
        
        # 결과 미리보기 섹션
        self.setup_preview_section(main_frame)
        
        # 상태바
        self.setup_status_bar(main_frame)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
    
    def setup_date_section(self, parent):
        """날짜 선택 섹션 설정"""
        date_frame = ttk.LabelFrame(parent, text="날짜 선택", padding="10")
        date_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 자동 날짜 계산 옵션
        self.auto_date_var = tk.BooleanVar(value=True)
        auto_check = ttk.Checkbutton(date_frame, text="자동 날짜 계산 (직전 날짜, 월요일이면 금~일)", 
                                   variable=self.auto_date_var, command=self.toggle_date_inputs)
        auto_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 수동 날짜 입력
        ttk.Label(date_frame, text="시작일:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(date_frame, textvariable=self.start_date_var, width=12)
        self.start_date_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(date_frame, text="종료일:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        self.end_date_var = tk.StringVar()
        self.end_date_entry = ttk.Entry(date_frame, textvariable=self.end_date_var, width=12)
        self.end_date_entry.grid(row=1, column=3, sticky=tk.W)
        
        # 날짜 형식 힌트
        hint_label = ttk.Label(date_frame, text="날짜 형식: YYYY-MM-DD (예: 2025-10-17)", 
                              font=("Arial", 8), foreground="gray")
        hint_label.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # 초기값 설정
        self.update_auto_dates()
    
    def setup_button_section(self, parent):
        """버튼 섹션 설정"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 데이터 수집 버튼
        self.fetch_button = ttk.Button(button_frame, text="데이터 수집", 
                                      command=self.start_data_collection)
        self.fetch_button.grid(row=0, column=0, padx=(0, 10))
        
        # Excel 생성 버튼
        self.excel_button = ttk.Button(button_frame, text="Excel 생성", 
                                      command=self.generate_excel, state="disabled")
        self.excel_button.grid(row=0, column=1, padx=(0, 10))
        
        # 결과 저장 버튼
        self.save_button = ttk.Button(button_frame, text="결과 저장", 
                                     command=self.save_results, state="disabled")
        self.save_button.grid(row=0, column=2)
    
    def setup_progress_section(self, parent):
        """진행 상황 섹션 설정"""
        progress_frame = ttk.LabelFrame(parent, text="진행 상황", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 상태 텍스트
        self.status_var = tk.StringVar(value="대기 중...")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        progress_frame.columnconfigure(0, weight=1)
    
    def setup_preview_section(self, parent):
        """결과 미리보기 섹션 설정"""
        preview_frame = ttk.LabelFrame(parent, text="결과 미리보기", padding="10")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 트리뷰 생성
        columns = ("품목코드", "제품명", "수량", "신뢰도")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=10)
        
        # 컬럼 설정
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 그리드 배치
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
    
    def setup_status_bar(self, parent):
        """상태바 설정"""
        self.status_bar = ttk.Label(parent, text="준비 완료", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def toggle_date_inputs(self):
        """날짜 입력 필드 활성화/비활성화"""
        if self.auto_date_var.get():
            self.start_date_entry.config(state="disabled")
            self.end_date_entry.config(state="disabled")
            self.update_auto_dates()
        else:
            self.start_date_entry.config(state="normal")
            self.end_date_entry.config(state="normal")
    
    def update_auto_dates(self):
        """자동 날짜 업데이트"""
        if self.auto_date_var.get():
            start_date, end_date = self.slack_fetcher.get_date_range()
            self.start_date_var.set(start_date)
            self.end_date_var.set(end_date)
    
    def start_data_collection(self):
        """데이터 수집 시작 (별도 스레드에서 실행)"""
        self.fetch_button.config(state="disabled")
        self.progress_var.set(0)
        self.status_var.set("데이터 수집 시작...")
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self.collect_data_thread)
        thread.daemon = True
        thread.start()
    
    def collect_data_thread(self):
        """데이터 수집 스레드"""
        try:
            # 날짜 범위 확인
            if self.auto_date_var.get():
                start_date, end_date = self.slack_fetcher.get_date_range()
            else:
                start_date = self.start_date_var.get()
                end_date = self.end_date_var.get()
            
            if not start_date or not end_date:
                messagebox.showerror("오류", "날짜를 입력해주세요.")
                return
            
            # 1단계: Slack 데이터 수집
            self.root.after(0, lambda: self.status_var.set("Slack 메시지 수집 중..."))
            self.root.after(0, lambda: self.progress_var.set(20))
            
            messages = self.slack_fetcher.fetch_messages(start_date, end_date)
            processed_messages = self.slack_fetcher.process_messages_with_threads(messages)
            
            # 2단계: 데이터 집계
            self.root.after(0, lambda: self.status_var.set("데이터 집계 중..."))
            self.root.after(0, lambda: self.progress_var.set(60))
            
            self.aggregated_data = self.aggregator.aggregate_products(processed_messages)
            
            # 3단계: 결과 표시
            self.root.after(0, lambda: self.status_var.set("결과 표시 중..."))
            self.root.after(0, lambda: self.progress_var.set(80))
            
            self.update_preview()
            
            # 완료
            self.root.after(0, lambda: self.status_var.set("데이터 수집 완료"))
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self.excel_button.config(state="normal"))
            self.root.after(0, lambda: self.save_button.config(state="normal"))
            
        except Exception as e:
            error_msg = f"데이터 수집 중 오류 발생: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("오류", error_msg))
            self.root.after(0, lambda: self.status_var.set("오류 발생"))
        
        finally:
            self.root.after(0, lambda: self.fetch_button.config(state="normal"))
    
    def update_preview(self):
        """미리보기 업데이트"""
        if not self.aggregated_data:
            return
        
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 새 데이터 추가
        products = self.aggregated_data.get("aggregated_products", [])
        for product in products:
            self.tree.insert("", "end", values=(
                product["품목코드"],
                product["제품명"],
                product["총_수량"],
                f"{product['신뢰도']}%"
            ))
    
    def generate_excel(self):
        """Excel 파일 생성"""
        if not self.aggregated_data:
            messagebox.showerror("오류", "먼저 데이터를 수집해주세요.")
            return
        
        # 파일 저장 대화상자
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Excel 파일 저장"
        )
        
        if filename:
            try:
                success = self.excel_generator.generate_excel_with_summary(
                    self.aggregated_data, filename
                )
                
                if success:
                    messagebox.showinfo("성공", f"Excel 파일이 생성되었습니다:\n{filename}")
                    self.status_bar.config(text=f"Excel 파일 생성 완료: {os.path.basename(filename)}")
                else:
                    messagebox.showerror("오류", "Excel 파일 생성에 실패했습니다.")
                    
            except Exception as e:
                messagebox.showerror("오류", f"Excel 생성 중 오류 발생: {str(e)}")
    
    def save_results(self):
        """결과 데이터 저장"""
        if not self.aggregated_data:
            messagebox.showerror("오류", "저장할 데이터가 없습니다.")
            return
        
        # 파일 저장 대화상자
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="결과 데이터 저장"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.aggregated_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("성공", f"결과 데이터가 저장되었습니다:\n{filename}")
                self.status_bar.config(text=f"데이터 저장 완료: {os.path.basename(filename)}")
                
            except Exception as e:
                messagebox.showerror("오류", f"데이터 저장 중 오류 발생: {str(e)}")
    
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()

if __name__ == "__main__":
    app = SlackOrderProcessorGUI()
    app.run()


