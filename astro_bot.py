import requests
from bs4 import BeautifulSoup
import os
import sys

# 출력을 강제로 즉시 보여주게 설정 (버퍼링 방지)
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
    print("🚀 [1단계] 아스트로마트 감시 로봇을 시작합니다!") # 로그에 무조건 찍혀야 함
    
    # 1. 시크릿 값 확인 (보안상 앞부분만)
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ 에러: 텔레그램 토큰이나 챗 ID가 시크릿에 설정되지 않았습니다!")
        return
    print(f"✅ 설정 확인: Token(앞자리 {TELEGRAM_TOKEN[:5]}), ID({CHAT_ID[:3]}...)")

    # 2. 기억장치 파일 확인
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            notified_ids = f.read().splitlines()
        print(f"📌 기억된 ID 개수: {len(notified_ids)}개")
    else:
        notified_ids = []
        print("📌 새로운 기억장치를 생성합니다.")

    # 3. 사이트 접속
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    try:
        print(f"🌐 사이트 접속 중: {URL}")
        response = requests.get(URL, headers=headers, timeout=20)
        print(f"📡 응답 코드: {response.status_code}") # 200이 나와야 함
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('.kboard-list tbody tr:not(.kboard-list-notice)')
        
        if not rows:
            print("⚠️ 경고: 게시글 목록을 찾지 못했습니다. 사이트 구조가 바뀌었을 수 있습니다.")
            # 사이트 HTML 일부를 출력해서 확인 (디버깅용)
            return

        print(f"🔎 상위 {len(rows[:5])}개 글을 검사합니다...")
        
        for row in rows[:5]:
            uid_el = row.select_one('.kboard-list-uid')
            title_el = row.select_one('.kboard-default-cut-strings')
            
            if uid_el and title_el:
                post_id = uid_el.text.strip()
                title = title_el.text.strip()
                
                print(f"📝 확인 중: [{post_id}] {title}")
                
                # 키워드 체크
                has_keyword = any(kw.lower() in title.lower() for kw in KEYWORDS)
                is_new = post_id not in notified_ids
                
                if has_keyword and is_new:
                    link = "https://astromart.co.kr" + row.select_one('.kboard-list-title a')['href']
                    send_telegram(f"✨ [새 매물] {title}\n링크: {link}")
                    print(f"✅ 알림 전송 성공: {title}")
                    notified_ids.append(post_id)
                elif not has_keyword:
                    pass # 키워드 없는 건 조용히 패스
                elif not is_new:
                    print(f"⏭️ 이미 보낸 글입니다: {post_id}")
        
        # 4. 파일 업데이트
        with open(DB_FILE, "w") as f:
            f.write("\n".join(notified_ids[-20:]))
        print("💾 기억장치 업데이트 완료.")
                
    except Exception as e:
        print(f"❌ 치명적 오류 발생: {str(e)}")

if __name__ == "__main__":
    check_market()
    print("🏁 로봇 작업 종료.")
