# pip install beautifulsoup4 requests schedule python-telegram-bot
import requests, schedule, time, os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from telegram import Bot
from dotenv import load_dotenv
import pytz

# == KONFIGURASI TELEGRAM ==
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# == KATA KUNCI ==
keywords = [
    "akuisisi perusahaan", "akuisisi", "merger",
    "perusahaan IPO", "sahamnya dibeli",
    "sahamnya diborong", "rencana IPO", "backdoor listing"
]

# == WEBSITE BISNIS ==
sites = {
    'Bisnis': 'https://www.bisnis.com',
    'Detik': 'https://finance.detik.com',
    'CNBC': 'https://www.cnbcindonesia.com/market',
    'Kontan': 'https://investasi.kontan.co.id',
    'IDX Channel': 'https://www.idxchannel.com'
}

# == GOOGLE ADVANCED SEARCH ==
def search_google(keyword):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.google.com/search?q={keyword}+site:bisnis.com+OR+site:detik.com+OR+site:cnbcindonesia.com+OR+site:kontan.co.id+OR+site:idxchannel.com&hl=id&gl=id&tbs=qdr:d"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    results = soup.select('.tF2Cxc')
    data = []
    for result in results:
        title = result.select_one('h3')
        link = result.select_one('a')['href']
        if title:
            data.append((keyword, title.text, link))
    return data

# == SCRAPE SITUS FINANSIAL ==
def scrape_sites():
    findings = []
    for name, base_url in sites.items():
        try:
            r = requests.get(base_url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            articles = soup.find_all('a')
            for a in articles:
                title = a.text.strip()
                href = a.get('href', '')
                if any(kw.lower() in title.lower() for kw in keywords):
                    link = href if href.startswith('http') else base_url + href
                    findings.append((title, name, link))
        except Exception:
            continue
    return findings

# == FUNGSI UTAMA ==
def run_monitor():
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.now(tz)
    start_time = now - timedelta(days=1)

    # Format waktu
    time_range = f"{start_time.strftime('%d %B %Y %H:%M')} - {now.strftime('%d %B %Y %H:%M')}"
    message = f"🗓️ Pengecekan: {now.strftime('%d %B %Y %H:%M')}\n🕒 Rentang: {time_range}\n\n[GOOGLE SEARCH]\n"

    # Google Search Result
    for kw in keywords:
        results = search_google(kw)
        if results:
            for keyword, title, link in results[:3]:  # Batasi 3 hasil per keyword
                message += f"🔍 Kata Kunci: \"{keyword}\"\n✅ Judul: {title}\n🔗 Sumber: {link}\n\n"
        else:
            message += f"🔍 Kata Kunci: \"{kw}\"\n❌ Not found\n\n"

    # Website Crawl
    message += "[WEBSITE CRAWL]\n"
    site_results = scrape_sites()
    if site_results:
        for title, source, link in site_results[:5]:  # Batasi 5 hasil dari website
            message += f"✅ Judul: {title} - {source}\n🔗 {link}\n\n"
    else:
        message += "❌ Not found\n"

    # Kirim ke Telegram
    bot.send_message(chat_id=CHAT_ID, text=message)

# == JADWAL ==
schedule.every().day.at("01:00").do(run_monitor)  # 08:00 WIB
schedule.every().day.at("13:00").do(run_monitor)  # 20:00 WIB

# == JALANKAN LOOP ==
print("🚀 Monitor berjalan... Menunggu jam 08:00 dan 20:00")
while True:
    schedule.run_pending()
    time.sleep(60)
