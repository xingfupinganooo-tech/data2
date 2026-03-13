# -*- coding: utf-8 -*-
import os
import sys
import json
import requests
import time
import random
from datetime import datetime

# ========== 密钥直接写死（已填好）==========
MORALIS_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjgzZDliN2JkLWM5YjQtNDJkYS1iMTU0LTVjMDhlOGM2YjVjZiIsIm9yZ0lkIjoiNTA0OTk2IiwidXNlcklkIjoiNTE5NjE1IiwidHlwZUlkIjoiMDMxNmRjMWUtNzhkMC00YTYwLWE4ZTEtYTQxZGQ5MzlkMjk2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzMzMTQ3NDYsImV4cCI6NDkyOTA3NDc0Nn0.0AWDAjP-uHoZtnX-NAWhoMA9ZJCRipdBKuBkTdlH2bw"
WECHAT_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b6a24857-a6a4-4895-9069-212f4698c3b6"
# ==========================================

print("✅ 密钥已加载，开始运行监控程序...")

# ========== 其他配置 ==========
JSON_PATH = "hot_tokens.json"
CHECK_INTERVAL = 60  # 检查间隔（秒）
MAX_TOKENS_PER_ROUND = 20  # 每轮最多处理代币数
# ==============================

# 全局变量
pushed_tokens = set()  # 已推送的合约地址
all_tokens = []  # 所有筛选出的代币


# ---------- 辅助函数 ----------
def send_wechat(contract, category=""):
    """推送合约地址到微信"""
    try:
        msg = f"【{category}】\\n{contract}" if category else contract
        data = {"msgtype": "text", "text": {"content": msg}}
        r = requests.post(WECHAT_URL, json=data, timeout=5)
        if r.json().get('errcode') == 0:
            print(f"✅ 微信推送 [{category}] {contract[:10]}...")
        else:
            print(f"⚠️ 微信推送失败: {r.text}")
    except Exception as e:
        print(f"❌ 微信推送异常: {e}")


def get_new_tokens():
    """从Moralis获取最新代币"""
    url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit=50"
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        tokens = data.get('result', [])
        print(f"📊 获取到 {len(tokens)} 个新代币")
        return tokens
    except Exception as e:
        print(f"❌ 获取代币失败: {e}")
        return []


def get_dex_data(token_address):
    """从DexScreener获取交易数据"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/token/{token_address}"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get('pairs') and len(data['pairs']) > 0:
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
    except Exception as e:
        print(f"⚠️ DexScreener获取失败: {e}")
    return {'tx': 0, 'liq': 0, 'price': 0, 'vol': 0, 'image': ''}


def classify_token(token, dex):
    """给代币分类（你可以自由修改这里的规则）"""
    name = token.get('name', '')
    symbol = token.get('symbol', '')
    twitter = token.get('twitter', '')
    created = token.get('created_timestamp', 0)
    now = int(time.time() * 1000)
    minutes = int((now - created) / 60000) if created else 999

    has_twitter = twitter and twitter != "N/A"
    category = None
    reason = []

    # 分类规则（按需调整）
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
        # 模拟推特转发数（后期可接入真实API）
        retweets = random.randint(10, 300)
        if retweets > 100 and dex['price'] < 0.001:
            category = "⭐潜力"
            reason.append("社区热度")

    return category, ", ".join(reason)


def process_token(token):
    """处理单个代币：判断是否合格，合格则保存并推送"""
    addr = token.get('tokenAddress')
    if not addr or addr in pushed_tokens:
        return None

    dex = get_dex_data(addr)
    category, reason = classify_token(token, dex)

    if not category:
        return None  # 不符合任何分类，忽略

    # 组装数据
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

    # 推送合约地址到微信
    send_wechat(addr, category)

    # 记录已推送
    pushed_tokens.add(addr)
    return token_data


def save_json():
    """保存数据到JSON（供网页读取）"""
    try:
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(all_tokens, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 已保存，共 {len(all_tokens)} 条")
    except Exception as e:
        print(f"❌ JSON保存失败: {e}")


def main():
    """主循环"""
    print("=" * 50)
    print("🚀 TokenRadar 监控系统启动")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    global all_tokens, pushed_tokens

    # 启动时保存一次空数据（确保文件存在）
    save_json()

    round_count = 0
    while True:
        try:
            round_count += 1
            print(f"\\n🔄 第 {round_count} 轮检查 - {datetime.now().strftime('%H:%M:%S')}")

            # 获取新代币
            tokens = get_new_tokens()
            if not tokens:
                time.sleep(CHECK_INTERVAL)
                continue

            new_count = 0
            for token in tokens[:MAX_TOKENS_PER_ROUND]:
                token_data = process_token(token)
                if token_data:
                    all_tokens.append(token_data)
                    new_count += 1
                    print(f"✅ 新增: {token_data['name']} ({token_data['symbol']}) - {token_data['category']}")
                    time.sleep(1)  # 避免推送太快

            if new_count > 0:
                print(f"📊 本轮新增 {new_count} 个代币，累计 {len(all_tokens)} 个")
                save_json()
            else:
                print("⏳ 本轮无合格代币")

            print(f"⏰ 等待 {CHECK_INTERVAL} 秒...")
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\\n🛑 用户中断，保存数据后退出")
            save_json()
            break
        except Exception as e:
            print(f"❌ 主循环异常: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()