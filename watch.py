import time
import requests
import os

WEBHOOK_URL = os.environ["https://discord.com/api/webhooks/1460146496870813852/njrYGkDQvdLqGNmi7x3nW0c-FCnkv3GlveNcr_G5USexOolxEnkqAUEpIho_i9jQoSMj"]

WALLETS = [
    "0x8def9f50456c6c4e37fa5d3d57f108ed23992dae",
    "0xA399F378380DdDb1fbb72e935B0111d7a4D16A52"
]

CHECK_INTERVAL = 60
NOTIFY_COOLDOWN = 600

last_positions = {}
last_notify = {}

def send_discord(msg):
    requests.post(WEBHOOK_URL, json={"content": msg})

def fetch_positions(wallet):
    url = "https://api.hyperliquid.xyz/info"
    payload = {
        "type": "userState",
        "user": wallet
    }
    r = requests.post(url, json=payload, timeout=10)
    data = r.json()

    positions = {}
    for p in data.get("assetPositions", []):
        pos = p["position"]
        size = float(pos["szi"])
        if size == 0:
            continue
        coin = pos["coin"]
        side = "LONG" if size > 0 else "SHORT"
        positions[f"{coin}_{side}"] = abs(size)

    return positions

while True:
    for wallet in WALLETS:
        current = fetch_positions(wallet)
        prev = last_positions.get(wallet, {})

        for key, size in current.items():
            prev_size = prev.get(key)
            now = time.time()
            notify_key = f"{wallet}_{key}"

            if prev_size is None:
                event = "建て"
            elif size > prev_size:
                event = "増し"
            elif size < prev_size:
                event = "解消"
            else:
                continue

            if now - last_notify.get(notify_key, 0) > NOTIFY_COOLDOWN:
                coin, side = key.split("_")
                send_discord(
                    f"[Hyperliquid]\nWallet: {wallet}\nEvent: {event}\nCoin: {coin}\nSide: {side}\nSize: {prev_size} → {size}"
                )
                last_notify[notify_key] = now

        for key in prev:
            if key not in current:
                now = time.time()
                notify_key = f"{wallet}_{key}"
                if now - last_notify.get(notify_key, 0) > NOTIFY_COOLDOWN:
                    coin, side = key.split("_")
                    send_discord(
                        f"[Hyperliquid]\nWallet: {wallet}\nEvent: 全解消\nCoin: {coin}\nSide: {side}"
                    )
                    last_notify[notify_key] = now

        last_positions[wallet] = current

    time.sleep(CHECK_INTERVAL)
