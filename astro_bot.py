import requests
from bs4 import BeautifulSoup
import os
import sys
import re # 숫자 추출을 위한 라이브러리 추가

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
    print("🚀 [1단계] 고유 ID 인식 모드로 로봇 엔진 가동!")
    
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            notified_ids = f.read().splitlines()
    else:
        notified_ids = []

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 공지사항 제외 행 추출
        rows = soup.select('.kboard-list tbody tr:not(.kboard-list-notice)')
        print(f"🔎 매물 후보 {len(rows)}개 발견.")

        for row in rows[:5]:
            cols = row.find_all('td')
            if len(cols) < 2: continue

            # 제목 칸(두 번째 td)에서 링크를 찾습니다.
            link_el = cols[1].find('a')
            if not link_el: continue

            title = link_el.get_text(strip=True)
            raw_link = link_el['href']
            full_link = "https://astromart.co.kr" + raw_link
            
            # 💡 핵심 수정: 링크 주소에서 'uid=숫자' 부분을 찾아 고유 ID로 사용합니다.
            uid_match = re.search(r'uid=(\d+)', raw_link)
            post_id = uid_match.group(1) if uid_match else raw_link # 못 찾으면 링크 전체를 ID로 사용
            
            print(f"📝 검사 중: [ID:{post_id}] {title}")

            has_keyword = any(kw.lower() in title.lower() for kw in KEYWORDS)
            is_new = post_id not in notified_ids
            
            if has_keyword and is_new:
                send_telegram(f"✨ [새 매물] {title}\n링크: {full_link}")
                print(f"   ✅ 알림 전송!")
                notified_ids.append(post_id)
            elif not has_keyword:
                print(f"   ㄴ 키워드 없음")
            elif not is_new:
                print(f"   ㄴ 이미 알림 보낸 고유 ID")
        
        # 기억장치 저장
        with open(DB_FILE, "w") as f:
            f.write("\n".join(notified_ids[-30:])) # 최근 30개 기억
        print("💾 기억장치 업데이트 완료.")
                
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    check_market()
