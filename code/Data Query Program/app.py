from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import mysql.connector

app = FastAPI()

def get_connection(db_name):
    return mysql.connector.connect(
"enter your detail"
    )

def query_chatbot_logic(text: str) -> str:
    conn = get_connection('examination_standard_db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT standard_title, standard_content 
        FROM examination_standards 
        WHERE standard_title LIKE %s OR standard_content LIKE %s 
        LIMIT 3
    """, (f'%{text}%', f'%{text}%'))
    standard_results = cursor.fetchall()
    cursor.close()
    conn.close()
    if standard_results:
        resp = []
        for title, content in standard_results:
            resp.append(f"[{title}] {content[:120]}...")
        return "다음 심사기준을 찾았습니다:\n" + "\n\n".join(resp)

    conn = get_connection('paper')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, authors, abstract 
        FROM arxiv_play 
        WHERE title LIKE %s OR authors LIKE %s OR abstract LIKE %s 
        LIMIT 3
    """, (f'%{text}%', f'%{text}%', f'%{text}%'))
    paper_results = cursor.fetchall()
    cursor.close()
    conn.close()
    if paper_results:
        resp = []
        for title, authors, abstract in paper_results:
            abstract = abstract if abstract else ""
            resp.append(f"논문 제목: {title}\n저자: {authors}\n요약: {abstract[:120]}...")
        return "다음 논문을 찾았습니다:\n" + "\n\n".join(resp)

    conn = get_connection('test10')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT application_number, invention_title, filing_date, legal_status, abstract 
        FROM patents 
        WHERE invention_title LIKE %s 
        LIMIT 3
    """, (f'%{text}%',))
    patent_results = cursor.fetchall()
    cursor.close()
    conn.close()
    if patent_results:
        texts = []
        for app_num, title, filing_date, status, abstract in patent_results:
            abstract_text = abstract if abstract else ""
            texts.append(
                f"출원번호: {app_num}, 발명명: {title}, 출원일: {filing_date}, 상태: {status}\n요약: {abstract_text[:100]}..."
            )
        return "다음 특허를 찾았습니다:\n" + "\n\n".join(texts)

    return "관련 정보를 찾을 수 없습니다."


@app.get("/", response_class=HTMLResponse)
async def home():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
      <title>특허 챗봇</title>
      <style>
        body { font-family: Arial, sans-serif; }
        #chatbox { width: 80%%; height: 400px; border: 1px solid #ccc; overflow-y: auto; padding: 10px; margin-bottom: 10px; }
        .user { color: blue; margin-bottom: 8px; }
        .bot { color: green; margin-bottom: 8px; }
      </style>
    </head>
    <body>
      <h2>특허 챗봇</h2>
      <div id="chatbox"></div>
      <input type="text" id="input" placeholder="질문(심사기준/논문 제목/특허 키워드 등)을 입력하세요" style="width: 80%%;" />
      <button onclick="sendMessage()">전송</button>

      <script>
        let chatbox = document.getElementById('chatbox');
        let input = document.getElementById('input');

        function appendMessage(sender, msg) {
          let div = document.createElement('div');
          div.className = sender;
          div.textContent = sender + ': ' + msg;
          chatbox.appendChild(div);
          chatbox.scrollTop = chatbox.scrollHeight;
        }

        async function sendMessage() {
          let message = input.value.trim();
          if (!message) return;
          appendMessage('User', message);
          input.value = '';

          const response = await fetch('/chatbot', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: message})
          });
          const data = await response.json();
          appendMessage('Bot', data.answer);
        }
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/chatbot")
async def chatbot_endpoint(request: Request):
    data = await request.json()
    query = data.get('query', '')
    answer = query_chatbot_logic(query)
    return JSONResponse({"answer": answer})
