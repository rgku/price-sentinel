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
import google.generativeai as genai
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
            await page.goto(url, timeout=30000, wait_until="networkidle")
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        log(f"ERRO scraping {url}: {e}")
        return ""


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

    return results


async def fetch_telegram_channel_html(channel_username: str) -> list:
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


def extract_with_gemini(api_key: str, text: str, query_name: str) -> Optional[dict]:
    if not api_key:
        log("ERRO: GEMINI_API_KEY nao definida")
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = f"""
Extrai o preco e desconto deste texto de promocao.
Responde APENAS em JSON valido (sem texto extra):
{{"produto": "string", "preco": float, "preco_original": float, "desconto_percent": float}}

Texto (ate 3000 caracteres):
{text[:3000]}
"""
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        data = json.loads(response_text)
        return data

    except Exception as e:
        log(f"ERRO Gemini: {e}")
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
        results = await fetch_telegram_channel_html(source)
        all_results.extend(results)
    else:
        results = await scrape_search(source, search_term)
        all_results.extend(results)

    if not all_results:
        log(f"Sem resultados para: {query_name}")
        return

    for item in all_results:
        data = extract_with_gemini(api_key, item.get("content", ""), query_name)

        if not data:
            continue

        # Filtro por desconto mínimo
        discount = data.get("desconto_percent", 0)
        if discount < min_discount:
            log(f"Descarto {query_name}: {discount}% < {min_discount}%")
            continue

        # Filtro por preço máximo
        price = data.get("preco", 0)
        if max_price and price > max_price:
            log(f"Descarto {query_name}: {price} > {max_price}")
            continue

        url = item.get("url", "")
        last_discount = get_last_discount(url)

        if last_discount and discount <= last_discount:
            log(f"Descarto {query_name}: sem melhoria (era {last_discount}%)")
            continue

        save_price(url, query_name, data.get("preco", 0), discount)

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