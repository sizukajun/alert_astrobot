import requests
from bs4 import BeautifulSoup
import os
import sys


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 제대로 읽어오는지 테스트하는 코드 (보안을 위해 앞부분만 출력)
if not TELEGRAM_TOKEN:
    print("❌ 에러: TELEGRAM_TOKEN 시크릿을 읽어오지 못했습니다!")
else:
    print(f"✅ 토큰 앞부분 확인: {TELEGRAM_TOKEN[:5]}***")
    
# --- 필터링 설정 구간 ---
# 원하는 키워드를 리스트에 넣으세요. (대소문자 구분 안 함)
KEYWORDS = ["2600", "OAG", "필터", "EFW", "174", "220", "장비", "불용품"]

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
URL = "https://astromart.co.kr/market/?category1=%ED%8C%90%EB%A7%A4&mod=list&pageid=1"

def send_telegram(message):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {'chat_id': CHAT_ID, 'text': message}
    
    # 텔레그램 서버의 실제 응답을 확인합니다.
    response = requests.get(api_url, params=params)
    res_json = response.json()
    
    if res_json.get("ok"):
        print("텔레그램 전송 성공!")
    else:
        # 여기가 핵심입니다. 왜 실패했는지 에러 메시지를 로그에 출력합니다.
        print(f"전송 실패! 에러 코드: {res_json.get('error_code')}")
        print(f"에러 내용: {res_json.get('description')}")

def check_market():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 게시글 목록 추출 (공지사항 제외)
        rows = soup.select('.kboard-list tbody tr:not(.kboard-list-notice)')
        
        for row in rows[:5]:  # 상위 5개 글만 확인
            title_el = row.select_one('.kboard-default-cut-strings')
            if not title_el: continue
            
            title = title_el.text.strip()
            link = "https://astromart.co.kr" + row.select_one('.kboard-list-title a')['href']
            
            # 키워드 필터링 로직
            if any(kw.lower() in title.lower() for kw in KEYWORDS):
                msg = f"✨ [맞춤 알림] 아스트로마트\n\n제목: {title}\n링크: {link}"
                send_telegram(msg)
                print(f"알림 전송 완료: {title}")
                return # 하나라도 찾으면 중복 방지를 위해 종료 (혹은 로직 수정)
                
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    check_market()
