from cx_Freeze import setup, Executable
import sys
import os

# 빌드 옵션 설정
build_exe_options = {
    "packages": [
        "openpyxl", "requests", "openai", "pandas", "xlrd",
        "slack_fetcher", "aggregator", "excel_generator", 
        "excel_parser", "gpt_matcher"
    ],
    "include_files": [
        ("config.json", "config.json"), 
        ("products_map.json", "products_map.json"), 
        ("Template_json_with_rows_columns.json", "Template_json_with_rows_columns.json")
    ],
    "excludes": [
        "tkinter", "matplotlib", "scipy", "IPython", "jupyter",
        "distutils", "setuptools", "pkg_resources"
    ],
    "optimize": 2,
    "zip_include_packages": "*",
    "zip_exclude_packages": "",
}

# Windows에서 콘솔 애플리케이션으로 설정
base = None
if sys.platform == "win32":
    base = "Console"

setup(
    name="SlackOrderProcessor",
    version="1.0",
    description="Slack 주문서 처리 시스템",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main_exe_clean.py",
            base=base,
            target_name="SlackOrderProcessor.exe"
        )
    ]
)


