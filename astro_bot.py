import requests
from bs4 import BeautifulSoup
import os

# --- 설정 ---
KEYWORDS = ["2600", "OAG", "필터", "EFW", "174", "220", "정리", "불용품"]
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL = "https://astromart.co.kr/market/?category1=%ED%8C%90%EB%A7%A4&mod=list&pageid=1"
DB_FILE = "notified_ids.txt"

def send_telegram(message):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.get(api_url, params={'chat_id': CHAT_ID, 'text': message})

def check_market():
    # 1. 이미 알림 보낸 ID 목록 불러오기
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            notified_ids = f.read().splitlines()
    else:
        notified_ids = []

    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('.kboard-list tbody tr:not(.kboard-list-notice)')
        
        new_ids = []
        for row in rows[:5]:
            uid_el = row.select_one('.kboard-list-uid')
            title_el = row.select_one('.kboard-default-cut-strings')
            if not uid_el or not title_el: continue
            
            post_id = uid_el.text.strip()
            title = title_el.text.strip()
            link = "https://astromart.co.kr" + row.select_one('.kboard-list-title a')['href']
            
            # 2. 키워드가 있고 + 아직 알림 안 보낸 글인 경우만!
            if any(kw.lower() in title.lower() for kw in KEYWORDS):
                if post_id not in notified_ids:
                    msg = f"✨ [새 매물] {title}\n링크: {link}"
                    send_telegram(msg)
                    print(f"새 알림 전송: {title}")
                    notified_ids.append(post_id)
        
        # 3. 최신 상태를 파일에 저장 (최근 20개만 유지)
        with open(DB_FILE, "w") as f:
            f.write("\n".join(notified_ids[-20:]))
                
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    check_market()
