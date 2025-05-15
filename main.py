import requests
import json
import random
import time
import uuid
import os
from colorama import Fore, Style, init
from prettytable import PrettyTable

init(autoreset=True)

CLAIM_URL = "https://testnet.humanity.org/api/rewards/daily/claim"
BALANCE_URL = "https://testnet.humanity.org/api/rewards/balance"
TOKEN_FILE = "tokens.txt"
PROXY_FILE = "proxy.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

def load_resources():
    tokens = []
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tokens = [line.strip() for line in f if line.strip()]
    
    proxies = []
    if os.path.exists(PROXY_FILE):
        with open(PROXY_FILE) as f:
            proxies = [line.strip() for line in f if line.strip()]
    
    return tokens, proxies

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Request-ID": str(uuid.uuid4()),
        "X-Client-Signature": f"v1:{uuid.uuid4().hex}",
        "Referer": "https://testnet.humanity.org/dashboard"
    }

def get_proxy(proxy_str):
    if proxy_str.startswith("http"):
        return {"http": proxy_str, "https": proxy_str}
    return {"http": f"http://{proxy_str}", "https": f"http://{proxy_str}"}

def extract_balance(response_data):
    balance_paths = [
        ['data', 'balance'],
        ['balance'],
        ['result', 'balance'],
        ['account', 'total'],
        ['wallet', 'available'],
        ['availableBalance'],
        ['response', 'balance']
    ]
    
    for path in balance_paths:
        try:
            current = response_data
            for key in path:
                if isinstance(current, list):
                    current = current[int(key)] if str(key).isdigit() else current[key]
                else:
                    current = current.get(str(key))
                if current is None:
                    break
            if current is not None:
                return str(current)
        except (KeyError, IndexError, TypeError):
            continue
    return "Format tidak dikenali"

def process_claim(token, proxy=None):
    headers = get_headers(token)
    result = {
        "token": f"{token[:10]}...{token[-6:]}",
        "claim_status": None,
        "balance": None,
        "error": None,
        "proxy": proxy.split('@')[-1] if proxy else "No Proxy"
    }
    
    try:
        claim_resp = requests.post(
            CLAIM_URL,
            headers=headers,
            json={"daily_reward": True},
            proxies=proxy,
            timeout=20
        )
        result["claim_status"] = claim_resp.status_code
        
        balance_resp = requests.get(
            BALANCE_URL,
            headers=headers,
            proxies=proxy,
            timeout=15
        )
        
        if balance_resp.status_code == 200:
            try:
                balance_data = balance_resp.json()
                result["balance"] = extract_balance(balance_data)
                with open("balance_debug.log", "a") as f:
                    f.write(f"Token: {result['token']}\n")
                    f.write(f"Response: {json.dumps(balance_data, indent=2)}\n")
                    f.write(f"Balance Extracted: {result['balance']}\n\n")
            except json.JSONDecodeError:
                result["balance"] = "Invalid JSON"
        else:
            result["balance"] = f"Error {balance_resp.status_code}"
            result["error"] = balance_resp.text[:50]
            
    except requests.exceptions.RequestException as e:
        result["error"] = f"Network Error: {str(e)}"
    except Exception as e:
        result["error"] = f"System Error: {str(e)}"
    
    return result

def colored_token(token):
    return Fore.CYAN + token + Style.RESET_ALL

def colored_proxy(proxy):
    return Fore.MAGENTA + proxy + Style.RESET_ALL

def colored_error(error):
    if error == "-" or error is None:
        return "-"
    return Fore.RED + error + Style.RESET_ALL

def colored_balance(balance):
    if balance is None:
        return "-"
    if balance.isdigit():
        return Fore.GREEN + balance + Style.RESET_ALL
    else:
        return Fore.YELLOW + balance + Style.RESET_ALL

def colored_claim_status(status):
    if status == 200:
        return Fore.GREEN + f"✅ {status}" + Style.RESET_ALL
    elif status is None:
        return Fore.YELLOW + "N/A" + Style.RESET_ALL
    else:
        return Fore.RED + f"❌ {status}" + Style.RESET_ALL

def create_pretty_table(results):
    table = PrettyTable()
    table.field_names = ["No", "Token", "Claim Status", "Balance", "Proxy", "Error"]
    table.align["Token"] = "l"
    table.align["Proxy"] = "l"
    table.align["Error"] = "l"
    table.align["Claim Status"] = "r"
    table.align["Balance"] = "r"

    for idx, res in enumerate(results, 1):
        table.add_row([
            idx,
            colored_token(res["token"]),
            colored_claim_status(res["claim_status"]),
            colored_balance(res["balance"]),
            colored_proxy(res["proxy"]),
            colored_error(res["error"])
        ])
    return table

def main():
    tokens, proxies = load_resources()
    if not tokens:
        print(f"{Fore.RED}❌ Tidak ada token yang ditemukan!")
        return

    results = []
    for idx, token in enumerate(tokens):
        proxy = None
        if proxies:
            proxy_str = random.choice(proxies)
            proxy = get_proxy(proxy_str)

        result = process_claim(token, proxy)
        results.append(result)

        os.system('cls' if os.name == 'nt' else 'clear')
        print(create_pretty_table(results))

        delay = random.uniform(1.5, 3.5) + (idx * 0.1)
        time.sleep(delay)

if __name__ == "__main__":
    try:
        while True:
            main()
            print(f"\n{Fore.YELLOW}🔄 Akan menjalankan kembali dalam 6 jam...")
            time.sleep(6 * 3600)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}⏹ Program dihentikan oleh pengguna")
