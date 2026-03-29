# -*- coding: utf-8 -*-
"""
뉴스 수집 모듈
- 네이버 뉴스 검색 API
- Google News RSS
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List

import feedparser
import requests

from config import (
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET,
    NAVER_KEYWORDS, GOOGLE_TOPICS,
    MAX_NEWS_PER_SOURCE,
)

logger = logging.getLogger(__name__)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


@dataclass
class NewsItem:
    source: str          # "NAVER" | "GOOGLE"
    keyword: str         # 검색 키워드 또는 주제
    title: str
    link: str
    description: str = ""
    pub_date: str = ""


# ------------------------------------------------------------------ #
#  네이버 뉴스
# ------------------------------------------------------------------ #

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_naver_news() -> List[NewsItem]:
    """네이버 검색 API를 이용해 키워드별 최신 뉴스를 가져옵니다."""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        logger.warning("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 미설정 → 네이버 뉴스 건너뜀")
        return []

    results: List[NewsItem] = []
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id":     NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }

    for keyword in NAVER_KEYWORDS:
        try:
            resp = requests.get(
                url,
                headers=headers,
                params={"query": keyword, "display": MAX_NEWS_PER_SOURCE, "sort": "date"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                results.append(NewsItem(
                    source="NAVER",
                    keyword=keyword,
                    title=_strip_html(item.get("title", "")),
                    link=item.get("link", ""),
                    description=_strip_html(item.get("description", "")),
                    pub_date=item.get("pubDate", ""),
                ))

            logger.info("네이버 [%s]: %d건 수집", keyword, len(data.get("items", [])))
        except Exception as exc:
            logger.error("네이버 뉴스 오류 [%s]: %s", keyword, exc)

    return results


# ------------------------------------------------------------------ #
#  Google News RSS
# ------------------------------------------------------------------ #

def fetch_google_news() -> List[NewsItem]:
    """Google News RSS를 주제별로 파싱합니다."""
    results: List[NewsItem] = []

    for topic in GOOGLE_TOPICS:
        rss_url = (
            f"https://news.google.com/rss/headlines/section/topic/{topic.upper()}"
            "?hl=ko&gl=KR&ceid=KR:ko"
        )
        try:
            feed = feedparser.parse(rss_url)
            count = 0
            for entry in feed.entries:
                if count >= MAX_NEWS_PER_SOURCE:
                    break
                results.append(NewsItem(
                    source="GOOGLE",
                    keyword=topic,
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    description=_strip_html(entry.get("summary", "")),
                    pub_date=entry.get("published", ""),
                ))
                count += 1

            logger.info("Google News [%s]: %d건 수집", topic, count)
        except Exception as exc:
            logger.error("Google News 오류 [%s]: %s", topic, exc)

    return results


# ------------------------------------------------------------------ #
#  통합 수집
# ------------------------------------------------------------------ #

def fetch_all_news() -> List[NewsItem]:
    """네이버 + 구글 뉴스 통합 수집."""
    naver_news  = fetch_naver_news()
    google_news = fetch_google_news()
    all_news = naver_news + google_news
    logger.info("총 수집 뉴스: %d건 (네이버 %d건, 구글 %d건)",
                len(all_news), len(naver_news), len(google_news))
    return all_news
