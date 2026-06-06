#!/usr/bin/env python3
"""
데일리 뉴스 브리핑 자동 생성 스크립트
GitHub Actions에서 매일 실행되어 index.html을 업데이트합니다.
"""

import os
import datetime
import subprocess
import feedparser
import google.generativeai as genai

KST = datetime.timezone(datetime.timedelta(hours=9))

FEEDS = {
    "politics": [
        ("연합뉴스", "https://www.yna.co.kr/RSS/politics.xml"),
        ("뉴시스", "https://www.newsis.com/RSS/politics.xml"),
    ],
    "economy": [
        ("연합뉴스", "https://www.yna.co.kr/RSS/economy.xml"),
        ("뉴시스", "https://www.newsis.com/RSS/economy.xml"),
    ],
    "society": [
        ("연합뉴스", "https://www.yna.co.kr/RSS/society.xml"),
        ("뉴시스", "https://www.newsis.com/RSS/society.xml"),
    ],
}

CSS = """* { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif; background: #F2F2F7; color: #1D1D1F; line-height: 1.6; }
        .topbar { position: sticky; top: 0; z-index: 100; background: rgba(255,255,255,0.78); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border-bottom: 0.5px solid rgba(0,0,0,0.12); padding: 14px 24px; }
        .topbar-inner { max-width: 760px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
        .topbar-title { font-size: 16px; font-weight: 600; }
        .topbar-date { font-size: 13px; color: #6E6E73; background: #F2F2F7; padding: 4px 12px; border-radius: 20px; }
        .container { max-width: 760px; margin: 0 auto; padding: 36px 20px 60px; }
        .hero { text-align: center; margin-bottom: 40px; }
        .hero h1 { font-size: 36px; font-weight: 700; letter-spacing: -0.8px; margin-bottom: 8px; }
        .hero p { font-size: 17px; color: #6E6E73; }
        .section { margin-bottom: 36px; }
        .section-label { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
        .section-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
        .politics .section-icon { background: #EEF2FF; }
        .economy .section-icon { background: #F0FDF4; }
        .society .section-icon { background: #FFF7ED; }
        .section-name { font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }
        .card { background: #fff; border-radius: 20px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 12px; }
        .issue-num { font-size: 12px; font-weight: 700; color: #8E8E93; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 8px; }
        .issue-title { font-size: 20px; font-weight: 700; letter-spacing: -0.3px; margin-bottom: 12px; }
        .summary-box { background: #F2F2F7; border-radius: 12px; border-left: 3px solid #007AFF; padding: 12px 16px; font-size: 15px; color: #3A3A3C; margin-bottom: 18px; }
        .bg-label { font-size: 11px; font-weight: 700; color: #8E8E93; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px; }
        .bg-text { font-size: 15px; color: #3A3A3C; line-height: 1.7; margin-bottom: 20px; }
        .perspectives { border: 1px solid #E5E5EA; border-radius: 14px; overflow: hidden; margin-bottom: 16px; }
        .prow { display: flex; align-items: flex-start; gap: 14px; padding: 14px 16px; border-bottom: 1px solid #F2F2F7; }
        .prow:last-child { border-bottom: none; }
        .badge { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; white-space: nowrap; min-width: 68px; justify-content: center; }
        .badge-c { background: #EFF6FF; color: #1D4ED8; }
        .badge-p { background: #FEF2F2; color: #DC2626; }
        .badge-n { background: #F3F4F6; color: #374151; }
        .ptext { font-size: 14px; color: #3A3A3C; line-height: 1.65; flex: 1; padding-top: 2px; }
        .keytip { display: flex; align-items: flex-start; gap: 8px; background: #F2F2F7; border-radius: 12px; padding: 14px 16px; font-size: 14px; color: #1D1D1F; margin-bottom: 16px; }
        .keytip-label { color: #007AFF; font-weight: 600; white-space: nowrap; }
        .related { margin-top: 4px; }
        .related-label { font-size: 11px; font-weight: 700; color: #8E8E93; letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 8px; }
        .related-links { display: flex; flex-direction: column; gap: 6px; }
        .related-link { display: flex; align-items: center; gap: 8px; text-decoration: none; color: #007AFF; font-size: 14px; padding: 8px 12px; background: #F2F8FF; border-radius: 10px; transition: background 0.15s; }
        .related-link:hover { background: #E5F0FF; }
        .related-link-source { font-size: 12px; color: #8E8E93; margin-left: auto; white-space: nowrap; }
        .vocab-card { background: #fff; border-radius: 20px; padding: 24px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .vocab-title { font-size: 20px; font-weight: 700; margin-bottom: 18px; }
        .vitem { padding: 13px 0; border-bottom: 1px solid #F2F2F7; }
        .vitem:last-child { border-bottom: none; padding-bottom: 0; }
        .vterm { font-size: 15px; font-weight: 600; margin-bottom: 3px; }
        .vdef { font-size: 14px; color: #6E6E73; line-height: 1.55; }
        .footer { text-align: center; margin-top: 48px; font-size: 13px; color: #8E8E93; }"""

CARD_EXAMPLE = """<div class="card">
      <div class="issue-num">이슈 1</div>
      <div class="issue-title">이슈 제목</div>
      <div class="summary-box">한 줄 요약: ...</div>
      <div class="bg-label">배경</div>
      <div class="bg-text">배경 설명 (어려운 용어는 괄호로 쉽게 설명)...</div>
      <div class="perspectives">
        <div class="prow"><span class="badge badge-c">🔵 보수</span><span class="ptext">보수 시각...</span></div>
        <div class="prow"><span class="badge badge-p">🔴 진보</span><span class="ptext">진보 시각...</span></div>
        <div class="prow"><span class="badge badge-n">⚪ 중립</span><span class="ptext">중립 시각...</span></div>
      </div>
      <div class="keytip"><span class="keytip-label">💡 한마디</span><span>핵심 한마디...</span></div>
      <div class="related">
        <div class="related-label">🔗 관련 기사</div>
        <div class="related-links">
          <a href="기사URL" target="_blank" class="related-link">기사 제목 <span class="related-link-source">언론사</span></a>
        </div>
      </div>
    </div>"""


def fetch_articles(feeds_list, max_per_feed=20):
    articles = []
    for source, url in feeds_list:
        try:
            feed = feedparser.parse(url, request_headers={"User-Agent": "Mozilla/5.0"})
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", entry.get("description", "")).strip()
                # feedparser sometimes returns HTML in summary — strip tags crudely
                import re
                summary = re.sub(r"<[^>]+>", "", summary)[:300]
                link = entry.get("link", "")
                if title and link:
                    articles.append({
                        "title": title,
                        "summary": summary,
                        "link": link,
                        "source": source,
                    })
        except Exception as e:
            print(f"피드 수집 실패 ({url}): {e}")
    return articles


def build_articles_text(all_articles):
    lines = []
    cat_names = {"politics": "정치", "economy": "경제", "society": "사회"}
    for category, articles in all_articles.items():
        lines.append(f"\n=== {cat_names[category]} ===")
        for i, a in enumerate(articles, 1):
            lines.append(f"{i}. [{a['source']}] {a['title']}")
            if a["summary"]:
                lines.append(f"   내용: {a['summary']}")
            lines.append(f"   URL: {a['link']}")
    return "\n".join(lines)


def generate_body(genai_module, today_full, articles_text):
    prompt = f"""오늘은 {today_full}입니다. 아래 뉴스 기사들을 바탕으로 데일리 뉴스 브리핑의 HTML body 내용을 생성해주세요.

[오늘 수집된 뉴스]
{articles_text}

[생성 규칙]
- 정치·경제·사회 각 3개 이슈 선택 (총 9개 카드)
- 각 이슈: 제목, 한 줄 요약, 배경(쉬운 말로 + 어려운 용어는 괄호로 설명), 보수/진보/중립 3가지 시각, 핵심 한마디, 관련 기사 링크 2-3개
- 관련 기사 링크는 반드시 위 뉴스 목록의 실제 URL을 사용
- 용어 정리 섹션: 오늘 기사에서 나온 어려운 용어 3개
- 모든 설명은 고등학생도 이해할 수 있게 쉬운 한국어로

[카드 HTML 구조 예시]
{CARD_EXAMPLE}

[전체 출력 구조] - 아래 HTML을 그대로 따르되 내용만 채워주세요:

<div class="topbar">
  <div class="topbar-inner">
    <span class="topbar-title">📰 데일리 뉴스 브리핑</span>
    <span class="topbar-date">{today_full}</span>
  </div>
</div>
<div class="container">
  <div class="hero">
    <h1>오늘의 핵심 뉴스</h1>
    <p>정치 · 경제 · 사회를 다양한 시각으로</p>
  </div>

  <div class="section politics">
    <div class="section-label"><div class="section-icon">🏛</div><span class="section-name">정치</span></div>
    [정치 카드 3개]
  </div>

  <div class="section economy">
    <div class="section-label"><div class="section-icon">💰</div><span class="section-name">경제</span></div>
    [경제 카드 3개]
  </div>

  <div class="section society">
    <div class="section-label"><div class="section-icon">🌐</div><span class="section-name">사회</span></div>
    [사회 카드 3개]
  </div>

  <div class="vocab-card">
    <div class="vocab-title">📚 오늘의 용어 정리</div>
    [vitem 3개]
  </div>

  <div class="footer">매일 오전 8시 자동 업데이트 · 데일리 뉴스 브리핑</div>
</div>

HTML만 출력하세요. ```html 같은 마크다운 없이 <div class="topbar">부터 시작해서 마지막 </div>까지만."""

    model = genai_module.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def assemble_html(today_full, body_html):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>데일리 뉴스 브리핑 — {today_full}</title>
    <style>
        {CSS}
    </style>
</head>
<body>
{body_html}
</body>
</html>"""


def git_push(today_date):
    subprocess.run(["git", "config", "user.email", "github-actions@github.com"], check=True)
    subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
    subprocess.run(["git", "add", "index.html"], check=True)
    diff = subprocess.run(["git", "diff", "--staged", "--quiet"])
    if diff.returncode != 0:
        subprocess.run(["git", "commit", "-m", f"뉴스 자동 업데이트: {today_date}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("GitHub Pages에 푸시 완료")
    else:
        print("변경 없음 — 커밋 건너뜀")


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

    now = datetime.datetime.now(KST)
    weekday = ["월", "화", "수", "목", "금", "토", "일"][now.weekday()]
    today_full = f"{now.year}년 {now.month}월 {now.day}일 {weekday}요일"
    today_date = now.strftime("%Y-%m-%d")

    print(f"뉴스 생성 시작: {today_full}")

    all_articles = {}
    for category, feeds in FEEDS.items():
        articles = fetch_articles(feeds)
        all_articles[category] = articles
        print(f"  {category}: {len(articles)}개 기사 수집")

    articles_text = build_articles_text(all_articles)

    print("Gemini API로 뉴스 브리핑 생성 중...")
    genai.configure(api_key=api_key)
    body_html = generate_body(genai, today_full, articles_text)

    # 마크다운 코드블록 감싸짐 방어
    if body_html.startswith("```"):
        body_html = body_html.split("\n", 1)[1]
    if body_html.endswith("```"):
        body_html = body_html.rsplit("```", 1)[0]
    body_html = body_html.strip()

    html = assemble_html(today_full, body_html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html 저장 완료")

    git_push(today_date)


if __name__ == "__main__":
    main()
