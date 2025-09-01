import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
# ВАЖНО: загружаем .env до импорта менеджеров БД
from config import settings as _settings  # noqa: F401
from app.api.limits import router as limits_router
from app.api.bible import router as bible_router
from app.api.ai import router as ai_router
from app.api.chat import router as chat_router
from app.api.chat import router_compat as chat_router_compat
from app.api.bookmarks import router as bookmarks_router
from app.api.plans import router as plans_router
from app.api.topics import router as topics_router
from app.api.local_bible import router as local_bible_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gospel Backend",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://bible-plus-ai.ru",
            "https://www.bible-plus-ai.ru",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8080",
            "http://localhost",
            "http://127.0.0.1",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health under /api to match Nginx proxy, and /health for local direct access
    @app.get("/api/health")
    async def health_api():
        return {"status": "ok"}

    @app.get("/health")
    async def health_root():
        return {"status": "ok"}

    @app.on_event("startup")
    async def on_startup():
        """Инициализация менеджера БД и лог типа подключения"""
        try:
            from database.universal_manager import universal_db_manager as db
            await db.initialize()
            db_type = "Supabase" if db.is_supabase else (
                "PostgreSQL" if db.is_postgres else "SQLite")
            logging.getLogger(__name__).info(
                f"[Backend] БД инициализирована: {db_type}")
        except Exception as e:
            logging.getLogger(__name__).error(
                f"[Backend] Ошибка инициализации БД: {e}")

    # Routers
    app.include_router(limits_router)
    app.include_router(bible_router)
    app.include_router(ai_router)
    app.include_router(chat_router)
    app.include_router(chat_router_compat)
    app.include_router(bookmarks_router)
    app.include_router(plans_router)
    app.include_router(topics_router)
    app.include_router(local_bible_router)

    return app


app = create_app()


def _home_html() -> str:
    return """
<!doctype html>
<html lang=ru>
<head>
  <meta charset=utf-8>
  <meta name=viewport content="width=device-width, initial-scale=1">
  <title>Gospel Bot — ИИ‑помощник</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,'Noto Sans',sans-serif;margin:0;background:#f7f7f8;color:#111}
    .wrap{max-width:960px;margin:0 auto;padding:24px}
    .hero{background:#fff;border:1px solid #e7e7ea;border-radius:12px;padding:20px}
    .tg-btn{display:inline-block;background:#24A1DE;color:#fff;text-decoration:none;padding:10px 14px;border-radius:8px}
    #chat{margin-top:14px}
    #chatLog{min-height:180px;max-height:50vh}
    button{cursor:pointer}
  </style>
  <meta name="description" content="Православный ИИ‑помощник: диалог, ссылки на Писание, молитвы.">
  <meta name="robots" content="noindex">
  <meta name="referrer" content="same-origin">
</head>
<body>
  <div class=wrap>
    <section class=hero>
      <h1 style=\"margin:0 0 6px\">Gospel Bot</h1>
      <p style=\"margin:0 0 12px\">Православный ИИ‑помощник: беседа, разбор Писания, подбор молитв.</p>
      <div style=\"margin:12px 0;display:flex;gap:10px;flex-wrap:wrap\">
        <a class=\"tg-btn\" href=\"https://t.me/bedrik12345_bot\" target=\"_blank\" rel=\"noopener\">Открыть в Telegram</a>
        <a class=\"tg-btn\" style=\"background:#16a34a\" href=\"/api/docs\" target=\"_blank\" rel=\"noopener\">API Docs</a>
      </div>

      <div id=\"chat\" style=\"max-width:860px;border:1px solid #ddd;border-radius:10px;padding:12px;background:#fbfbfc\">
        <div style=\"display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap\">
          <input id=\"userId\" type=\"number\" placeholder=\"Ваш user_id\" style=\"width:180px;padding:6px;border:1px solid #d9d9de;border-radius:8px\">
          <button id=\"startBtn\">Начать диалог</button>
          <button id=\"resetBtn\" disabled>Сбросить</button>
        </div>
        <div id=\"chatLog\" style=\"padding:8px;background:#fff;border:1px solid #eee;border-radius:8px;overflow:auto\"></div>
        <div style=\"display:flex;gap:8px;margin-top:8px\">
          <input id=\"msg\" type=\"text\" placeholder=\"Напишите вопрос...\" style=\"flex:1;padding:8px;border:1px solid #d9d9de;border-radius:8px\">
          <button id=\"sendBtn\" disabled>Отправить</button>
        </div>
      </div>
    </section>
  </div>

<script>
(function(){
  const API = '/api';
  const startBtn = document.getElementById('startBtn');
  const resetBtn = document.getElementById('resetBtn');
  const sendBtn  = document.getElementById('sendBtn');
  const msgInput = document.getElementById('msg');
  const chatLog  = document.getElementById('chatLog');
  const userIdEl = document.getElementById('userId');

  let conversationId = null;
  let userId = null;

  function appendMessage(role, text, verseRefs){
    const wrapper = document.createElement('div');
    wrapper.style.margin='10px 0';
    const who = document.createElement('div');
    who.textContent = role==='user'?'Вы:':'Ассистент:';
    who.style.fontWeight='600';
    wrapper.appendChild(who);

    const body = document.createElement('div');
    body.textContent = text || '';
    wrapper.appendChild(body);

    if (Array.isArray(verseRefs) && verseRefs.length){
      const kb = document.createElement('div');
      kb.style.display='flex';kb.style.flexWrap='wrap';kb.style.gap='6px';kb.style.marginTop='6px';
      verseRefs.slice(0,5).forEach(ref=>{
        const btn=document.createElement('button');
        btn.textContent=ref; btn.style.padding='4px 6px';
        btn.onclick=async()=>{
          try{
            const r=await fetch(`${API}/v1/bible/reference?`+new URLSearchParams({ref}));
            const data=await r.json();
            const text=data.text||'Не удалось получить текст';
            const block=document.createElement('div');
            block.style.whiteSpace='pre-wrap';
            block.style.marginTop='6px';
            block.style.padding='8px';
            block.style.background='#fff';
            block.style.border='1px solid #eee';
            block.style.borderRadius='6px';
            block.textContent=text;
            wrapper.appendChild(block);
            wrapper.scrollIntoView({behavior:'smooth',block:'end'});
          }catch(e){console.error(e)}
        };
        kb.appendChild(btn);
      });
      wrapper.appendChild(kb);
    }

    chatLog.appendChild(wrapper);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  async function start(){
    userId = parseInt(userIdEl.value||'0',10);
    if(!userId){ alert('Введите ваш user_id'); return; }
    startBtn.disabled=true;
    try{
      const r=await fetch(`${API}/v1/ai/chat/start`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId})});
      const data=await r.json();
      conversationId=data.conversation_id; resetBtn.disabled=false; sendBtn.disabled=false;
      appendMessage('assistant','Диалог запущен. Задайте свой вопрос.');
    }catch(e){console.error(e); startBtn.disabled=false;}
  }

  async function reset(){
    if(!conversationId||!userId) return; resetBtn.disabled=true;
    try{
      await fetch(`${API}/v1/ai/chat/reset`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId,conversation_id:conversationId})});
      const r=await fetch(`${API}/v1/ai/chat/start`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId})});
      const data=await r.json();
      conversationId=data.conversation_id; chatLog.innerHTML='';
      appendMessage('assistant','Контекст очищен. Напишите новый вопрос.');
    }catch(e){console.error(e);} finally{ resetBtn.disabled=false; }
  }

  async function send(){
    const text=msgInput.value.trim(); if(!text||!conversationId||!userId) return;
    msgInput.value=''; appendMessage('user',text); sendBtn.disabled=true;
    try{
      const r=await fetch(`${API}/v1/ai/chat/message`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:userId,conversation_id:conversationId,message:text})});
      const data=await r.json();
      appendMessage('assistant',data.text||'',data.verse_refs||[]);
    }catch(e){console.error(e); appendMessage('assistant','Ошибка при обращении к ИИ. Попробуйте позже.');}
    finally{ sendBtn.disabled=false; }
  }

  document.getElementById('startBtn').onclick=start;
  document.getElementById('resetBtn').onclick=reset;
  document.getElementById('sendBtn').onclick=send;
  document.getElementById('msg').addEventListener('keydown',e=>{ if(e.key==='Enter') send(); });
})();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home_page():
    return _home_html()


@app.get("/chat", response_class=HTMLResponse)
async def chat_page():
    return _home_html()
