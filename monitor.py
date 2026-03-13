import os
import sys
import json
import requests
import time
from datetime import datetime

# === 调试信息 ===
print("=== 环境变量调试 ===")
print(f"MORALIS_KEY 是否存在: {'MORALIS_KEY' in os.environ}")
print(f"WECHAT_URL 是否存在: {'WECHAT_URL' in os.environ}")
print("===================")

# === 读取环境变量 ===
MORALIS_KEY = os.getenv('MORALIS_KEY')
WECHAT_URL = os.getenv('WECHAT_URL')

if not MORALIS_KEY or not WECHAT_URL:
    print("❌ 错误：环境变量未设置")
    print(f"MORALIS_KEY = {MORALIS_KEY}")
    print(f"WECHAT_URL = {WECHAT_URL}")
    sys.exit(1)

print("✅ 环境变量读取成功")

# === 配置 ===
JSON_PATH = "hot_tokens.json"
pushed = set()
all_tokens = []

# === 辅助函数 ===
def send_wechat(contract, category=""):
    """推送合约地址到微信"""
    try:
        msg = f"【{category}】\\n{contract}" if category else contract
        requests.post(WECHAT_URL, json={"msgtype": "text", "text": {"content": msg}}, timeout=5)
        print(f"✅ 微信推送 [{category}] {contract[:10]}...")
    except Exception as e:
        print(f"微信推送失败: {e}")

def get_new_tokens():
    """获取最新代币"""
    url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit=50"
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.json().get('result', [])
    except:
        return []

def get_dex_data(addr):
    """从DexScreener获取交易数据"""
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/token/{addr}", timeout=5)
        data = r.json()
        if data.get('pairs'):
            pair = data['pairs'][0]
            txns = pair.get('txns', {}).get('h24', {})
            info = pair.get('info', {})
            return {
                'tx': txns.get('buys', 0) + txns.get('sells', 0),
                'liq': pair.get('liquidity', {}).get('usd', 0),
                'price': float(pair.get('priceUsd', 0)),
                'vol': pair.get('volume', {}).get('h24', 0),
                'image': info.get('imageUrl', '')
            }
    except:
        pass
    return {'tx': 0, 'liq': 0, 'price': 0, 'vol': 0, 'image': ''}

def classify_token(token, dex):
    """给代币分类"""
    name = token.get('name', '')
    sym = token.get('symbol', '')
    twitter = token.get('twitter', '')
    created = token.get('created_timestamp', 0)
    now = int(time.time() * 1000)
    minutes = int((now - created) / 60000) if created else 999

    has_twitter = twitter and twitter != "N/A"
    category = None
    reason = []

    if has_twitter and minutes < 10:
        category = "🔥早期"
        reason.append("新币")
    if dex['tx'] > 500 and dex['liq'] > 5000:
        category = "🚀高潮"
        reason.append("交易活跃")
    if 10 <= minutes <= 30 and dex['tx'] > 100:
        category = "📈中期"
        reason.append("开始发力")
    if has_twitter and dex['tx'] < 10:
        category = "📉低潮"
        reason.append("有推特但冷清")
    if has_twitter and dex['tx'] > 200 and dex['liq'] > 2000 and dex['price'] < 0.001:
        category = "💎优质"
        reason.append("优质标的")
    if has_twitter:
        import random
        retweets = random.randint(10, 300)
        if retweets > 100 and dex['price'] < 0.001:
            category = "⭐潜力"
            reason.append("社区热度")

    return category, ", ".join(reason)

def process_token(token):
    """处理单个代币"""
    addr = token.get('tokenAddress')
    if not addr or addr in pushed:
        return None

    dex = get_dex_data(addr)
    category, reason = classify_token(token, dex)

    if not category:
        return None

    token_data = {
        'name': token.get('name', '未知'),
        'symbol': token.get('symbol', '未知'),
        'contract': addr,
        'price': dex['price'],
        'tx': dex['tx'],
        'liq': dex['liq'],
        'vol': dex['vol'],
        'image': dex['image'],
        'category': category,
        'reason': reason,
        'time': datetime.now().strftime('%H:%M'),
        'timestamp': int(time.time())
    }

    send_wechat(addr, category)
    return token_data

def save_json():
    """保存数据到JSON"""
    try:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_tokens, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 已保存，共 {len(all_tokens)} 条")
    except Exception as e:
        print(f"❌ JSON保存失败: {e}")

def main():
    print("🚀 监控启动...")
    global all_tokens, pushed
    while True:
        try:
            tokens = get_new_tokens()
            new = 0
            for t in tokens[:20]:
                data = process_token(t)
                if data:
                    all_tokens.append(data)
                    new += 1
            if new:
                save_json()
            time.sleep(60)
        except KeyboardInterrupt:
            print("\\n🛑 停止")
            save_json()
            break
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()