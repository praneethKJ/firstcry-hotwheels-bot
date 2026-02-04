import time
import json
import requests
from playwright.sync_api import sync_playwright

# =========================
# TELEGRAM CONFIG
# =========================
BOT_TOKEN = "8020019116:AAEmHUxTFROVZENc6Que_-FNPiZzCVWf98s"
CHAT_ID = "639347587"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=10
        )
        time.sleep(0.8)  # prevent Telegram rate-limit
    except Exception as e:
        print("Telegram error:", e)


# =========================
# FIRSTCRY CONFIG
# =========================
URL = "https://www.firstcry.com/search.aspx?q=hot+wheels"
DATA_FILE = "seen.json"
CHECK_INTERVAL = 120  # 2 minutes


# =========================
# FILTER LISTS
# =========================
REAL_BRANDS = [
    "ferrari","porsche","mazda","honda","toyota","nissan","bmw",
    "mercedes","audi","volkswagen","vw","ford","chevrolet","chevy",
    "lamborghini","pagani","bugatti","mclaren","aston martin",
    "alfa romeo","subaru","mitsubishi","dodge","jeep","pontiac",
    "volvo","renault","bentley","koenigsegg","jaguar","land rover",
    "maserati","lexus","acura","mini"
]

FANTASY_KEYWORDS = [
    "twin mill","bone shaker","street wiener","pixel shaker",
    "madfast","ain't fare","quick bite","power rocket",
    "layin low","driftn break","cruise bruiser",
    "el viento","feline lucky","shark","dragon","skull"
]

BIKE_KEYWORDS = [
    "bike","motorcycle","moto","vfr","ducati",
    "kawasaki","yamaha","triumph","harley","motocompo"
]


# =========================
# STORAGE
# =========================
def load_seen():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_seen(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# =========================
# FILTER LOGIC
# =========================
def is_valid_product(title: str) -> bool:
    t = title.lower()

    if "hot wheels" not in t:
        return False

    if any(f in t for f in FANTASY_KEYWORDS):
        return False

    if any(b in t for b in BIKE_KEYWORDS):
        return False

    if not any(b in t for b in REAL_BRANDS):
        return False

    return True


# =========================
# CORE CHECK (NEW ITEMS ONLY)
# =========================
def check():
    seen = load_seen()
    first_run = len(seen) == 0
    new_items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(URL, timeout=60000)
        page.wait_for_timeout(8000)

        # Scroll to load products
        for _ in range(5):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2000)

        links = page.query_selector_all("a[href]")
        print("Total links found:", len(links))

        for a in links:
            title = a.get_attribute("title")
            href = a.get_attribute("href")

            if not title or not href:
                continue

            if not is_valid_product(title):
                continue

            if href.startswith("/"):
                href = "https://www.firstcry.com" + href

            # FIRST RUN → SAVE ONLY
            if first_run:
                seen[href] = True
                continue

            # NEW LISTING
            if href not in seen:
                seen[href] = True
                new_items.append(f"{title}\n{href}")

        browser.close()

    save_seen(seen)

    # SEND ALERTS ONLY AFTER FIRST RUN
    if not first_run and new_items:
        send_telegram("🆕 NEW Hot Wheels Listing:\n\n" + "\n\n".join(new_items[:10]))

    print(
        "Baseline run completed (no alerts)"
        if first_run else
        f"New items found: {len(new_items)}"
    )


# =========================
# LOOP
# =========================
if __name__ == "__main__":
    send_telegram("🤖 Hot Wheels NEW listing bot started")

    while True:
        try:
            check()
        except Exception as e:
            print("ERROR:", e)

        time.sleep(CHECK_INTERVAL)
