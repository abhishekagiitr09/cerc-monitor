import urllib.request
from html.parser import HTMLParser
import json
import os
import smtplib
from email.mime.text import MIMEText

# ------------------------------
# CONFIGURATION
# ------------------------------
URL = "http://cercind.gov.in/Current_reg.html"  # Use HTTP (important fix)
DATA_FILE = "cerc_updates.json"

EMAIL_SENDER = "abhishekag.iitr09@gmail.com"
EMAIL_PASSWORD = "Abhishek@123"
EMAIL_RECEIVER = "abhishek.agarwal@feplglobal.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ------------------------------
# HTML PARSER
# ------------------------------
class CERCParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.current_row = []
        self.data = []
        self.current_link = ""

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.in_td = True
        
        if tag == "a":
            for attr in attrs:
                if attr[0] == "href":
                    self.current_link = attr[1]

    def handle_endtag(self, tag):
        if tag == "td":
            self.in_td = False
        
        if tag == "tr":
            if len(self.current_row) >= 2:
                entry = {
                    "date": self.current_row[0].strip(),
                    "description": self.current_row[1].strip(),
                    "link": self.current_link
                }

                if entry["link"] and not entry["link"].startswith("http"):
                    entry["link"] = "http://cercind.gov.in/" + entry["link"]

                self.data.append(entry)

            self.current_row = []
            self.current_link = ""

    def handle_data(self, data):
        if self.in_td:
            text = data.strip()
            if text:  # avoid blank entries
                self.current_row.append(text)

# ------------------------------
# FETCH WEBSITE DATA
# ------------------------------

def fetch_updates():
    print("Fetching website...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Connection": "keep-alive"
    }

    req = urllib.request.Request(URL, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode('utf-8', errors='ignore')

    except Exception as e:
        print("Retrying with HTTP fallback...")
        
        # fallback attempt
        import time
        time.sleep(2)

        with urllib.request.urlopen(req, timeout=20) as response:
            html = response.read().decode('utf-8', errors='ignore')

    parser = CERCParser()
    parser.feed(html)

    return parser.data

# ------------------------------
# LOAD PREVIOUS DATA
# ------------------------------
def load_old_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

# ------------------------------
# FIND NEW ENTRIES (by LINK)
# ------------------------------
def get_new_entries(new_data, old_data):
    if not new_data:
        return[]
    
    latest = new_data[0]

    if not old_data:
        return[latest]
    
    old_latest=old_data[0]

    if latest["link"]!=old_latest["link"]:
        return[latest]
    # old_links = set(item["link"] for item in old_data)

    # new_entries = []
    # for item in new_data:
        # if item["link"] not in old_links:
            # new_entries.append(item)

    return []

# ------------------------------
# SAVE DATA
# ------------------------------
def save_data(data):
    if data:
        with open(DATA_FILE, "w") as f:
            json.dump([data[0]], f, indent=2)

# ------------------------------
# SEND EMAIL (OUTLOOK)
# ------------------------------
def send_email(new_entries):
    if not new_entries:
        print("No new updates found.")
        return

    body = "New CERC Updates:\n\n"

    for item in new_entries:
        body += f"Date: {item['date']}\n"
        body += f"Description: {item['description']}\n"
        body += f"Link: {item['link']}\n\n"

    msg = MIMEText(body)
    msg["Subject"] = "CERC New Upload Alert"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email failed:", e)

# ------------------------------
# MAIN FUNCTION
# ------------------------------
def main():
    print("Checking for new updates...")

    try:
        new_data = fetch_updates()
    except Exception as e:
        print("❌ Fetch failed:", e)
        return

    old_data = load_old_data()

    new_entries = get_new_entries(new_data, old_data)

    print(f"New entries found: {len(new_entries)}")

    send_email(new_entries)
    save_data(new_data)

# ------------------------------
# RUN
# ------------------------------
main()