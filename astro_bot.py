import requests
from bs4 import BeautifulSoup
import os
import sys

# 출력 실시간 확인 설정
sys.stdout.reconfigure(encoding='utf-8')

KEYWORDS = ["2600", "OAG", "필터", "EFW", "174", "220", "정리", "불용품"]
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL = "https://astromart.co.kr/market/?category1=%ED%8C%90%EB%A7%A4&mod=list&pageid=1"
DB_FILE = "notified_ids.txt"

def send_telegram(message):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(api_url, params={'chat_id': CHAT_ID, 'text': message})

def check_market():
    print("🚀 [1단계] 감시 로봇 엔진 가동!")
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            notified_ids = f.read().splitlines()
    else:
        notified_ids = []

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 게시글 행(Row)을 더 넓은 범위로 찾습니다.
        rows = soup.select('.kboard-list tbody tr')
        
        # 공지사항 제외 필터링 (번호가 '공지'라고 적힌 행 건너뛰기)
        real_posts = []
        for r in rows:
            uid_text = r.select_one('.kboard-list-uid').text.strip() if r.select_one('.kboard-list-uid') else ""
            if uid_text and '공지' not in uid_text:
                real_posts.append(r)

        print(f"🔎 실제 매물 {len(real_posts)}개 발견. 상위 5개를 검사합니다.")

        for row in real_posts[:5]:
            # 2. 제목 찾기 (더 유연하게)
            # 클래스가 없어도 'a' 태그 내부의 텍스트를 가져옵니다.
            title_el = row.select_one('.kboard-list-title a')
            uid_el = row.select_one('.kboard-list-uid')
            
            if not title_el or not uid_el:
                print("⚠️ 특정 행에서 제목이나 ID를 찾지 못해 건너뜁니다.")
                continue

            post_id = uid_el.text.strip()
            # 제목 내부의 '새글' 아이콘 등을 제외하고 텍스트만 추출
            title = title_el.get_text(strip=True)
            link = "https://astromart.co.kr" + title_el['href']
            
            print(f"📝 확인 중: [{post_id}] {title}") # 이제 로그에 이게 찍혀야 합니다!

            has_keyword = any(kw.lower() in title.lower() for kw in KEYWORDS)
            is_new = post_id not in notified_ids
            
            if has_keyword and is_new:
                send_telegram(f"✨ [새 매물] {title}\n링크: {link}")
                print(f"✅ 알림 전송: {title}")
                notified_ids.append(post_id)
            elif not has_keyword:
                print(f"   ㄴ 키워드 없음")
            elif not is_new:
                print(f"   ㄴ 이미 보낸 글")
        
        with open(DB_FILE, "w") as f:
            f.write("\n".join(notified_ids[-20:]))
        print("💾 기억장치 업데이트 완료.")
                
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    check_market()
