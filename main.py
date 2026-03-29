# -*- coding: utf-8 -*-
"""
메인 실행 파일
- 매일 지정 시각에 네이버/구글 뉴스를 각각 수집·요약·이메일 발송
- python main.py --now  → 즉시 1회 테스트
- python main.py       → 스케줄러 대기 (매일 DAILY_HOUR:DAILY_MINUTE)
"""
import logging
import sys
import time
from datetime import datetime

import schedule

from config import DAILY_HOUR, DAILY_MINUTE
from email_sender import send_email
from news_fetcher import fetch_all_news
from summarizer import summarize_naver, summarize_google

# ------------------------------------------------------------------ #
#  로깅 설정
# ------------------------------------------------------------------ #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("news_email.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


# ------------------------------------------------------------------ #
#  핵심 작업
# ------------------------------------------------------------------ #
def run_daily_job():
    logger.info("=" * 60)
    logger.info("뉴스 이메일 작업 시작: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    today = datetime.now().strftime("%Y년 %m월 %d일")

    # ── 1. 뉴스 수집 ──────────────────────────────────────────────
    logger.info("[1/5] 뉴스 수집 중...")
    news_list = fetch_all_news()
    if not news_list:
        logger.warning("수집된 뉴스가 없습니다. 종료합니다.")
        return

    # ── 2. 네이버 뉴스 요약 ────────────────────────────────────────
    logger.info("[2/5] 네이버 뉴스 Gemini 요약 중...")
    naver_html = summarize_naver(news_list)

    # ── 3. 네이버 뉴스 이메일 발송 ──────────────────────────────────
    logger.info("[3/5] 네이버 뉴스 이메일 발송 중...")
    naver_body = f"<h2>📰 네이버 뉴스</h2>\n{naver_html}"
    ok1 = send_email(
        html_body=naver_body,
        subject=f"📰 [네이버 뉴스] 오늘의 요약 - {today}",
    )

    # ── 4. 구글 뉴스 요약 ──────────────────────────────────────────
    logger.info("[4/5] Google 뉴스 Gemini 요약 중...")
    google_html = summarize_google(news_list)

    # ── 5. 구글 뉴스 이메일 발송 ────────────────────────────────────
    logger.info("[5/5] Google 뉴스 이메일 발송 중...")
    google_body = f"<h2>🌐 Google 뉴스</h2>\n{google_html}"
    ok2 = send_email(
        html_body=google_body,
        subject=f"🌐 [Google 뉴스] 오늘의 요약 - {today}",
    )

    # ── 결과 ───────────────────────────────────────────────────────
    if ok1 and ok2:
        logger.info("✅ 작업 완료! (네이버 + 구글 이메일 2건 발송)")
    elif ok1:
        logger.warning("⚠ 네이버 이메일만 발송 성공, 구글 이메일 실패")
    elif ok2:
        logger.warning("⚠ 구글 이메일만 발송 성공, 네이버 이메일 실패")
    else:
        logger.error("❌ 두 이메일 모두 발송 실패. 설정을 확인해주세요.")


# ------------------------------------------------------------------ #
#  스케줄러
# ------------------------------------------------------------------ #
def main():
    send_time = f"{DAILY_HOUR:02d}:{DAILY_MINUTE:02d}"
    logger.info("뉴스 이메일 서비스 시작")
    logger.info("발송 예정 시각: 매일 %s (로컬 시간)", send_time)
    logger.info("발송 구성: 네이버 뉴스 이메일 + Google 뉴스 이메일 (총 2통)")

    # 즉시 1회 실행
    if "--now" in sys.argv:
        logger.info("--now 플래그 감지: 즉시 1회 실행 후 종료합니다.")
        run_daily_job()
        sys.exit(0)

    # 스케줄 등록
    schedule.every().day.at(send_time).do(run_daily_job)
    logger.info("스케줄 등록 완료. 대기 중... (Ctrl+C로 종료)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("서비스 종료.")


if __name__ == "__main__":
    main()
