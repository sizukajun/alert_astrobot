import requests
from bs4 import BeautifulSoup
import os
import sys

# 로그 실시간 확인 설정
sys.stdout.reconfigure(encoding='utf-8')

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
    print("🚀 [1단계] 감시 로봇 엔진 가동!")
    
    # 기억장치 읽기
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            notified_ids = f.read().splitlines()
        print(f"📌 기존 기억장치에서 {len(notified_ids)}개 기록 로드.")
    else:
        notified_ids = []
        print("📌 새로운 기억장치 생성.")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ✅ 작동이 확인되었던 '공지사항 제외' 선택 방식입니다.
        rows = soup.select('.kboard-list tbody tr:not(.kboard-list-notice)')
        
        print(f"🔎 실제 매물 후보 {len(rows)}개 발견. 상위 5개를 검사합니다.")

        for row in rows[:5]:
            uid_el = row.select_one('.kboard-list-uid')
            # 제목과 링크가 있는 a 태그를 찾습니다.
            title_el = row.select_one('.kboard-list-title a')
            
            if not uid_el or not title_el:
                continue

            post_id = uid_el.get_text(strip=True)
            title = title_el.get_text(strip=True)
            link = "https://astromart.co.kr" + title_el['href']
            
            print(f"📝 확인 중: [{post_id}] {title}")

            # 키워드 검사 및 중복 검사
            has_keyword = any(kw.lower() in title.lower() for kw in KEYWORDS)
            is_new = post_id not in notified_ids
            
            if has_keyword and is_new:
                send_telegram(f"✨ [새 매물] {title}\n링크: {link}")
                print(f"   ✅ 알림 전송 성공!")
                notified_ids.append(post_id)
            elif not has_keyword:
                print(f"   ㄴ 키워드 없음 (패스)")
            elif not is_new:
                print(f"   ㄴ 이미 알림 보낸 글 (패스)")
        
        # 기억장치 업데이트 (최근 20개만 보관)
        with open(DB_FILE, "w") as f:
            f.write("\n".join(notified_ids[-20:]))
        print("💾 기억장치 업데이트 완료.")
                
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    check_market()
    print("🏁 로봇 작업 종료.")
