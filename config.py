# -*- coding: utf-8 -*-
"""설정값 로드 - .env 파일 또는 환경변수에서 읽습니다."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# --- Gemini ---
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL: str   = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# --- 네이버 ---
NAVER_CLIENT_ID:     str = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET: str = os.environ.get("NAVER_CLIENT_SECRET", "")

# --- Gmail ---
EMAIL_SENDER:   str = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD: str = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECEIVER: str = os.environ.get("EMAIL_RECEIVER", "")

# --- 스케줄 ---
DAILY_HOUR:   int = int(os.environ.get("DAILY_HOUR", "6"))
DAILY_MINUTE: int = int(os.environ.get("DAILY_MINUTE", "0"))

# --- 뉴스 수집 ---
NAVER_KEYWORDS: list[str] = [
    k.strip() for k in os.environ.get("NAVER_KEYWORDS", "속보,IT,경제").split(",") if k.strip()
]
GOOGLE_TOPICS: list[str] = [
    t.strip() for t in os.environ.get("GOOGLE_TOPICS", "TECHNOLOGY,BUSINESS,WORLD").split(",") if t.strip()
]
MAX_NEWS_PER_SOURCE: int = int(os.environ.get("MAX_NEWS_PER_SOURCE", "5"))
