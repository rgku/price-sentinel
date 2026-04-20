#!/usr/bin/env python3
"""
Price Sentinel - Monitor de Promoções Automático
Monitors websites and Telegram channels for price drops/discounts.
"""

import json
import os
import hashlib
import asyncio
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright as pw
from deep_translator import GoogleTranslator
import google.genai as genai
import requests

CONFIG_FILE = "queries.json"
DB_FILE = "history.db"
LOG_FILE = "sentinel.log"

TELEGRAM_CHANNEL_LANG = {
    "amazon.es": "es",
    "continente.pt": "pt",
    "canal:@chollos": "es",
    "canal:@descuentos": "es",
    "canal:@ganga24": "es",
    "canal:@ofertacash": "es",
    "canal:@wolf_ofertas": "pt",
    "canal:@portugalgeek": "pt",
    "canal:@linguica_das_promocoes": "pt",
    "canal:@economizzandodg": "pt",
    "canal:@viajerospiratas": "es",
    "canal:@guidellowcost": "es",
    "google_shopping": "en",
    "rss:": "pt",
}

TELEGRAM_BOT_VERSION = "python-telegram-bot"


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


def load_queries() -> list:
    if not os.path.exists(CONFIG_FILE):
        log(f"ERRO: {CONFIG_FILE} nao encontrado!")
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("queries", [])
    except Exception as e:
        log(f"ERRO ler queries: {e}")
        return []


def load_env() -> dict:
    return {
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN", ""),
        "CHAT_ID": os.getenv("CHAT_ID", ""),
        "TELEGRAM_API_ID": os.getenv("TELEGRAM_API_ID", ""),
        "TELEGRAM_API_HASH": os.getenv("TELEGRAM_API_HASH", ""),
    }


def translate_term(term: str, target_lang: str) -> str:
    if target_lang == "pt":
        return term
    try:
        translator = GoogleTranslator(source="auto", target=target_lang)
        translated = translator.translate(term)
        log(f"Traducao: '{term}' -> '{translated}' ({target_lang})")
        return translated
    except Exception as e:
        log(f"ERRO traducao: {e}. A usar termo original.")
        return term


def get_source_lang(source: str) -> str:
    for src, lang in TELEGRAM_CHANNEL_LANG.items():
        if src in source:
            return lang
    if ".es" in source:
        return "es"
    elif ".pt" in source:
        return "pt"
    return "es"


def url_hash(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def init_db():
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_hash TEXT UNIQUE,
            url TEXT,
            query_name TEXT,
            last_price REAL,
            last_discount REAL,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_price(url: str, query_name: str, price: float, discount: float):
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO prices (url_hash, url, query_name, last_price, last_discount, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (url_hash(url), url, query_name, price, discount, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_last_discount(url: str) -> Optional[float]:
    import sqlite3
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT last_discount FROM prices WHERE url_hash = ?", (url_hash(url),))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


async def scrape_website(url: str) -> str:
    try:
        async with pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set user agent to look like a real browser
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)  # Wait for JS to load
            
            content = await page.content()
            await browser.close()
            
            # Debug: log content length
            log(f"Scraped {len(content)} chars from {url}")
            
            return content
    except Exception as e:
        log(f"ERRO scraping {url}: {e}")
        return ""


def extract_prices_regex(text: str, query_name: str) -> list:
    """Fallback: extract prices directly from HTML using regex."""
    import re
    
    # Common price patterns: €XX.XX, XX,XX€, $XX.XX
    patterns = [
        r'[€$]?\s*(\d+[.,]\d{2})\s*€?',  # 19.99, 19,99
        r'[€$]?\s*(\d+)\s*€?(?:\s*€|\s*$)',  # 19€
    ]
    
    results = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                price = float(match.replace(',', '.'))
                if 1 < price < 1000:  # Reasonable price range
                    results.append({
                        "produto": f"Produto encontrado ({query_name})",
                        "preco": price,
                        "preco_original": price * 1.3,  # Estimate original as 30% higher
                        "desconto_percent": 23,  # Assume reasonable discount
                        "source": "regex"
                    })
            except:
                pass
    
    return results[:3]  # Return top 3


async def scrape_google_shopping(query: str, target_lang: str) -> list:
    """Usar Google Shopping para encontrar produtos."""
    import requests
    
    results = []
    
    # Traduzir query para inglês se necessário
    if target_lang != "en":
        from deep_translator import GoogleTranslator
        query_en = GoogleTranslator(source="auto", target="en").translate(query)
    else:
        query_en = query
    
    try:
        # Usar pesquisa web simples (sem API paga)
        url = f"https://www.google.com/search?q={query_en.replace(' ', '+')}+price"
        
        async with pw() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            
            content = await page.content()
            await browser.close()
            
            if content:
                results.append({
                    "url": url,
                    "content": content,
                    "source": "google_shopping",
                })
                log(f"Google Shopping: {len(content)} chars")
                
    except Exception as e:
        log(f"ERRO Google Shopping: {e}")
    
    return results


async def scrape_search(source: str, search_term: str) -> list:
    results = []
    lang = get_source_lang(source)
    translated = translate_term(search_term, lang)

    if "amazon.es" in source:
        url = f"https://www.amazon.es/s?k={translated.replace(' ', '+')}"
        log(f"Pesquisar Amazon ES: {search_term}")
        content = await scrape_website(url)
        if content:
            results.append({"url": url, "content": content, "source": source})

    elif "continente.pt" in source:
        encoded = translated.replace(' ', '%20')
        url = f"https://www.continente.pt/pesquisar?q={encoded}"
        log(f"Pesquisar Continente PT: {search_term}")
        content = await scrape_website(url)
        if content:
            results.append({"url": url, "content": content, "source": source})

    elif "google" in source:
        # Google Shopping / Search
        results = await scrape_google_shopping(search_term, lang)
        return results
    
    elif "rss:" in source:
        # RSS Feed
        feed_url = source.replace("rss:", "")
        results = await fetch_rss_feed(feed_url, search_term)
        return results

    return results


async def fetch_rss_feed(url: str, search_term: str) -> list:
    """Ler RSS feeds de promoções."""
    import feedparser
    
    results = []
    
    try:
        feed = feedparser.parse(url)
        
        if feed.entries:
            for entry in feed.entries[:20]:  # Latest 20 items
                title = entry.get("title", "").lower()
                summary = entry.get("summary", "").lower()
                
                if search_term.lower() in title or search_term.lower() in summary:
                    content = f"{entry.get('title', '')}\n{entry.get('summary', '')}"
                    results.append({
                        "url": entry.get("link", url),
                        "content": content,
                        "source": f"rss:{url}",
                    })
            
            log(f"RSS: {len(feed.entries)} itens de {url}")
        else:
            log(f"RSS vazio ou inválido: {url}")
            
    except Exception as e:
        log(f"ERRO RSS {url}: {e}")
    
    return results


# RSS Feeds populares de promoções
RSS_FEEDS = {
    "amazon_deals": "https://www.amazon.de/giftcard-todayonly/rss/11188470031/ref=as_li_ss_tw?pf_rd_r=2NM6XDWDAGKR6M2G6G4R&pf_rd_p=c4be4b3a-062e-49ac-929e-aabb5a7c0de0&pf_rd_s=toprs&pf_rd_t=1&pf_rd_i=giftcards&linkCode=ll",
    "chollos_rss": "https://chollometro.com/feed",
    "descuentos.es": "https://www.descuentoses/feed",
}


async def fetch_telegram_channel_api(channel_username: str, search_term: str) -> list:
    """Ler mensagens de canal Telegram via API oficial (Telethon)."""
    from telethon import TelegramClient
    from telethon.errors import ApiIdInvalidError, UsernameNotOccupiedError
    
    results = []
    channel = channel_username.replace("canal:", "")
    
    # Carregar credentials do Telegram
    api_id = os.getenv("TELEGRAM_API_ID", "")
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    
    if not api_id or not api_hash:
        log("ERRO: TELEGRAM_API_ID ou TELEGRAM_API_HASH não definidos")
        return results
    
    try:
        client = TelegramClient('sentinel_session', int(api_id), api_hash)
        
        async with client:
            # Obter mensagens do canal
            try:
                entity = await client.get_entity(channel)
                messages = await client.get_messages(entity, limit=50)
                
                for msg in messages:
                    if msg.text and search_term.lower() in msg.text.lower():
                        # Tentar extrair preço do texto
                        results.append({
                            "url": f"https://t.me/{channel}/{msg.id}",
                            "content": msg.text,
                            "source": channel_username,
                            "message": msg.text
                        })
                        
            except UsernameNotOccupiedError:
                log(f"Canal não encontrado: {channel}")
            except Exception as e:
                log(f"ERRO a ler canal {channel}: {e}")
        
        log(f"Telegram API: {len(results)} mensagens encontradas em @{channel}")
        
    except ApiIdInvalidError:
        log("ERRO: API_ID ou API_HASH inválidos")
    except Exception as e:
        log(f"ERRO Telegram API: {e}")
    
    return results


async def fetch_telegram_channel_html(channel_username: str) -> list:
    """Fallback: usar HTML público (menos fiável)."""
    results = []
    channel = channel_username.replace("canal:", "")
    url = f"https://t.me/s/{channel}"
    
    try:
        content = await scrape_website(url)
        if content:
            results.append({
                "url": f"https://t.me/{channel}",
                "content": content,
                "source": channel_username,
            })
    except Exception as e:
        log(f"ERRO Telegram {channel_username}: {e}")
    
    return results


def extract_with_openrouter(api_key: str, text: str, query_name: str) -> Optional[dict]:
    """Fallback: usar OpenRouter API quando Gemini falha."""
    import requests
    
    if not api_key:
        return None
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-3.2-11b-vision-instruct",
                "messages": [{
                    "role": "user",
                    "content": f"""Extrai o preco e desconto deste texto de promocao.
Responde APENAS em JSON: {{"produto": "nome", "preco": numero, "preco_original": numero, "desconto_percent": numero}}

Texto: {text[:2000]}"""
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Parse JSON response
            import re
            match = re.search(r'\{[^}]+\}', content)
            if match:
                data = json.loads(match.group())
                log(f"OpenRouter retornou: {data}")
                return data
                
    except Exception as e:
        log(f"ERRO OpenRouter: {e}")
    
    return None


def extract_with_gemini(api_key: str, text: str, query_name: str) -> Optional[dict]:
    if not api_key:
        log("ERRO: GEMINI_API_KEY nao definida")
        return None

    try:
        client = genai.Client(api_key=api_key)
        model = "gemini-2.0-flash-001"

        prompt = f"""
Analisa este texto e extrai informacao de preco.
Se houver preco, calcula o desconto baseado em precos originais mencionados.
Se nao houver desconto, usa preco_original = preco e desconto_percent = 0.
Responde APENAS em JSON valido:
{{"produto": "nome do produto", "preco": preco atual (numero), "preco_original": preco sem desconto (numero), "desconto_percent": desconto em numero}}

Texto:
{text[:3000]}
"""
        response = client.models.generate_content(model=model, contents=prompt)
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        data = json.loads(response_text)
        log(f"Gemini retornou: {data}")
        return data

    except Exception as e:
        log(f"ERRO Gemini: {e}")
        log(f"Resposta: {response_text if 'response_text' in dir() else 'N/A'}")
        return None


def send_telegram_alert(token: str, chat_id: str, alert: dict):
    if not token or not chat_id:
        log("ERRO: TELEGRAM_TOKEN ou CHAT_ID nao definido")
        return

    try:
        from telegram import Bot
        bot = Bot(token=token)
        
        discount = alert.get("desconto_percent", 0)
        emoji = "🔥" if discount >= 50 else "📉" if discount >= 30 else "💰"

        message = f"""
{emoji} Promocao Detetada!

Query: {alert['query_name']}
Produto: {alert['produto']}
Preco: EUR {alert['preco']:.2f}
Original: EUR {alert['preco_original']:.2f}
Desconto: {discount:.0f}%

Ver produto: {alert['url']}
"""
        bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        log(f"Alerta enviado: {alert['produto']} - {discount}% desconto")

    except Exception as e:
        log(f"ERRO enviar alerta: {e}")


async def process_query(api_key: str, telegram_token: str, chat_id: str, query: dict):
    query_name = query.get("name", "")
    search_term = query.get("search_term", "")
    source = query.get("source", "")
    min_discount = query.get("min_discount_percent", 20)
    max_price = query.get("max_price")  # Novo filtro por preço máximo

    log(f"A processar: {query_name} ({source})")

    all_results = []

    if "canal:" in source:
        # Try Telegram API first, fallback to HTML
        results = await fetch_telegram_channel_api(source, search_term)
        if not results:
            log(f"Telegram API falhou, a tentar HTML...")
            results = await fetch_telegram_channel_html(source)
        all_results.extend(results)
    else:
        results = await scrape_search(source, search_term)
        all_results.extend(results)

    if not all_results:
        log(f"Sem resultados para: {query_name}")
        return

    for item in all_results:
        content = item.get("content", "")
        log(f"Content preview: {content[:500]}...")
        
        data = extract_with_gemini(api_key, content, query_name)

        # Fallback 1: OpenRouter if Gemini failed
        if not data or not data.get("preco"):
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
            if openrouter_key:
                log(f"Gemini failed, tentando OpenRouter...")
                data = extract_with_openrouter(openrouter_key, content, query_name)

        # Fallback 2: regex if both AIs failed
        if not data or not data.get("preco"):
            log(f"Todas as AIs falharam, tentando regex fallback...")
            regex_results = extract_prices_regex(content, query_name)
            if regex_results:
                data = regex_results[0]
                log(f"Regex found: {data}")

        if not data:
            continue

        # Filtro por desconto mínimo
        discount = data.get("desconto_percent") or 0
        if discount < min_discount:
            log(f"Descarto {query_name}: {discount}% < {min_discount}%")
            continue

        # Filtro por preço máximo
        price = data.get("preco") or 0
        if max_price and price > max_price:
            log(f"Descarto {query_name}: {price} > {max_price}")
            continue

        url = item.get("url", "")
        last_discount = get_last_discount(url)

        if last_discount and discount <= last_discount:
            log(f"Descarto {query_name}: sem melhoria (era {last_discount}%)")
            continue

        save_price(url, query_name, data.get("preco") or 0, discount)

        alert = {
            "query_name": query_name,
            "produto": data.get("produto", ""),
            "preco": data.get("preco", 0),
            "preco_original": data.get("preco_original", 0),
            "desconto_percent": discount,
            "url": url,
            "source": source,
        }

        send_telegram_alert(telegram_token, chat_id, alert)


async def main():
    log("=" * 50)
    log("Price Sentinel iniciado")

    init_db()
    queries = load_queries()

    if not queries:
        log("Nenhuma query para processar")
        return

    env = load_env()
    api_key = env["GEMINI_API_KEY"]
    telegram_token = env["TELEGRAM_TOKEN"]
    chat_id = env["CHAT_ID"]

    for query in queries:
        await process_query(api_key, telegram_token, chat_id, query)
        await asyncio.sleep(3)

    log("Price Sentinel terminado")


if __name__ == "__main__":
    asyncio.run(main())