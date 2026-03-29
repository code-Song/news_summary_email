# -*- coding: utf-8 -*-
"""
google.genai (최신 SDK)를 이용한 뉴스 요약 모듈
- 네이버 / 구글 뉴스를 별도 함수로 분리하여 각각 요약
"""
import logging
from itertools import groupby
from typing import List

from config import GEMINI_API_KEY, GEMINI_MODEL
from news_fetcher import NewsItem

logger = logging.getLogger(__name__)

SAFETY_OFF = None  # 아래 _safety() 함수에서 생성


def _safety():
    from google.genai import types
    return [
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT",        threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH",       threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
    ]


def _call_gemini(prompt: str) -> str:
    """Gemini API 호출 공통 함수."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=8192,
            temperature=0.4,
            safety_settings=_safety(),
        ),
    )
    import re
    result = response.text.strip()
    
    # 정규식으로 더 안전하게 마크업 제거 (```html ... ```)
    result = re.sub(r"^```(?:html)?\s*", "", result, flags=re.IGNORECASE)
    result = re.sub(r"\s*```$", "", result)
    
    return result.strip()


def _build_news_text(items: List[NewsItem]) -> str:
    """뉴스 목록을 프롬프트용 텍스트로 변환."""
    text = ""
    for i, n in enumerate(items, 1):
        text += (
            f"[{i}] 키워드/주제: {n.keyword}\n"
            f"제목: {n.title}\n"
            f"설명: {n.description[:250]}\n"
            f"링크: {n.link}\n\n"
        )
    return text


def _base_prompt(source_label: str, news_text: str, count: int) -> str:
    return f"""당신은 한국어 뉴스 큐레이터입니다. 아래 {source_label} 뉴스 {count}건을 바탕으로 이메일용 HTML 본문을 작성하세요.

[출력 규칙 - 반드시 준수]
- 순수 HTML만 출력하세요. ```html 코드블록 사용 금지.
- <html>, <head>, <body> 태그는 포함하지 마세요.
- 아래 구조를 정확히 따르세요:

<h3>키워드/주제명</h3>
<ul>
  <li><strong>기사 제목</strong><br>2~3문장 요약.<br><a href="링크">[원문 보기]</a></li>
  ... (해당 키워드의 모든 기사)
</ul>
... (다른 키워드/주제들 반복)

<h2>📌 핵심 트렌드</h2>
<ol>
  <li><strong>트렌드 제목</strong>: 2~3문장 설명.</li>
  <li><strong>트렌드 제목</strong>: 2~3문장 설명.</li>
</ol>

[중요 - 반드시 끝까지 작성하세요]
- 모든 {count}건의 기사를 빠짐없이 요약하세요. 중간에 절대로 멈추거나 생략하지 마세요.
- 요약은 한국어로, 원문 그대로 복사하지 말고 의역하세요.
- href에는 반드시 원본 URL을 넣으세요.
- 끝에 반드시 "<h2>📌 핵심 트렌드</h2>" 섹션을 작성하여 HTML이 완벽하게 닫히도록 하세요. 전혀 잘리면 안 됩니다.

=== {source_label} 뉴스 ({count}건) ===
{news_text}"""


# ------------------------------------------------------------------ #
#  공개 API
# ------------------------------------------------------------------ #

def summarize_naver(news_list: List[NewsItem]) -> str:
    """네이버 뉴스만 요약하여 HTML 반환."""
    items = [n for n in news_list if n.source == "NAVER"]
    if not items:
        return "<p>네이버 뉴스가 없습니다.</p>"

    if not GEMINI_API_KEY:
        return _plain_html(items)

    try:
        prompt = _base_prompt("네이버", _build_news_text(items), len(items))
        html = _call_gemini(prompt)
        logger.info("네이버 요약 완료 (%d자)", len(html))
        return html
    except Exception as exc:
        logger.error("네이버 요약 실패: %s", exc)
        return _plain_html(items) + f"<p><b>⚠ 요약 실패: {exc}</b></p>"


def summarize_google(news_list: List[NewsItem]) -> str:
    """구글 뉴스만 요약하여 HTML 반환."""
    items = [n for n in news_list if n.source == "GOOGLE"]
    if not items:
        return "<p>Google 뉴스가 없습니다.</p>"

    if not GEMINI_API_KEY:
        return _plain_html(items)

    try:
        prompt = _base_prompt("Google", _build_news_text(items), len(items))
        html = _call_gemini(prompt)
        logger.info("구글 요약 완료 (%d자)", len(html))
        return html
    except Exception as exc:
        logger.error("구글 요약 실패: %s", exc)
        return _plain_html(items) + f"<p><b>⚠ 요약 실패: {exc}</b></p>"


def _plain_html(items: List[NewsItem]) -> str:
    """Gemini 없이 제목 목록만 HTML로 반환."""
    items_sorted = sorted(items, key=lambda x: x.keyword)
    html = ""
    for kw, group in groupby(items_sorted, key=lambda x: x.keyword):
        html += f"<h3>{kw}</h3><ul>"
        for n in group:
            html += (
                f'<li><strong>{n.title}</strong><br>'
                f'{n.description[:150]}<br>'
                f'<a href="{n.link}">[원문 보기]</a></li>'
            )
        html += "</ul>"
    return html
