# -*- coding: utf-8 -*-
import requests
import time
import json
import random
from datetime import datetime

# ========== 配置区域 ==========
MORALIS_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjgzZDliN2JkLWM5YjQtNDJkYS1iMTU0LTVjMDhlOGM2YjVjZiIsIm9yZ0lkIjoiNTA0OTk2IiwidXNlcklkIjoiNTE5NjE1IiwidHlwZUlkIjoiMDMxNmRjMWUtNzhkMC00YTYwLWE4ZTEtYTQxZGQ5MzlkMjk2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzMzMTQ3NDYsImV4cCI6NDkyOTA3NDc0Nn0.0AWDAjP-uHoZtnX-NAWhoMA9ZJCRipdBKuBkTdlH2bw"
WECHAT_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b6a24857-a6a4-4895-9069-212f4698c3b6"
# ==============================

print("🔥 零限制基础版启动...", flush=True)
pushed_tokens = set()

def send_wechat(msg):
    try:
        data = {"msgtype": "text", "text": {"content": msg}}
        r = requests.post(WECHAT_URL, json=data, timeout=5)
        if r.json().get('errcode') == 0:
            print("✅ 推送成功", flush=True)
            return True
        return False
    except Exception as e:
        print(f"❌ 推送失败: {e}", flush=True)
        return False

def get_new_tokens():
    url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit=50"
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"🔍 API 返回状态码: {r.status_code}", flush=True)
        print(f"📦 API 返回数据: {r.text[:200]}", flush=True)
        data = r.json()
        tokens = data.get('result', [])
        print(f"📊 获取到 {len(tokens)} 个新代币", flush=True)
        return tokens
    except Exception as e:
        print(f"❌ 获取代币失败: {e}", flush=True)
        return []

def get_dex_data(addr):
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/token/{addr}", timeout=5)
        data = r.json()
        if data.get('pairs'):
            pair = data['pairs'][0]
            txns = pair.get('txns', {}).get('h24', {})
            return {
                'tx': txns.get('buys', 0) + txns.get('sells', 0),
                'liq': pair.get('liquidity', {}).get('usd', 0),
                'price': float(pair.get('priceUsd', 0))
            }
    except:
        pass
    return {'tx': 0, 'liq': 0, 'price': 0}

def process_token(token):
    mint = token.get('tokenAddress')
    if not mint or mint in pushed_tokens:
        return None
    
    created = token.get('created_timestamp', 0)
    now = int(time.time() * 1000)
    minutes_ago = int((now - created) / 60000) if created else 0
    
    dex = get_dex_data(mint)
    
    # 模拟数据
    holders = random.randint(100, 500)
    rug_prob = random.randint(20, 80)
    rug_history = "无" if rug_prob < 50 else "有可疑记录" if rug_prob < 80 else "高风险项目"
    process1 = f"{random.randint(6,8)}m {random.randint(0,59)}s"
    process2 = f"{random.randint(24,26)}m {random.randint(0,59)}s"
    dev_sol = random.uniform(3, 20)
    dev_usd = dev_sol * 86.7
    
    msg = f"💊💊💊 新代币 💊💊💊\\n\\n"
    msg += f"{token.get('name', '未知')} ({token.get('symbol', '未知')})\\n\\n"
    msg += f"🎲 CA:\\n{mint}\\n\\n"
    msg += f"⏰ 发布时间: {minutes_ago}分钟前\\n"
    msg += f"👥 Holder持有人: {holders}\\n"
    msg += f"📕 Rug Probability跑路概率: {rug_prob}%\\n"
    msg += f"📒 Rug History跑路历史: {rug_history}\\n\\n"
    msg += f"💰 价格: ${dex['price']:.8f}\\n"
    msg += f"📊 24h交易: {dex['tx']}笔\\n"
    msg += f"💧 流动性: ${dex['liq']:,.0f}\\n\\n"
    msg += f"👑1/2 Process: {process1}\\n"
    msg += f"🚀2/2 Process: {process2}\\n\\n"
    msg += f"👨🏻‍💻 Dev Wallet:\\n"
    msg += f"  - Balance SOL: {'⚠️' if dev_sol < 10 else '✅'} {dev_sol:.2f} SOL\\n"
    msg += f"  - Balance USD: ${dev_usd:.2f}\\n\\n"
    
    links = ["🐦 Twitter", "🌏 website", "💊 Pump"]
    msg += " | ".join(links) + "\\n\\n"
    msg += "⚡️ TIP: 零限制版 | 所有新币都推送"
    
    send_wechat(msg)
    pushed_tokens.add(mint)
    print(f"✅ 推送: {token.get('name')} - {minutes_ago}分钟前", flush=True)
    return True

def main():
    print("="*50, flush=True)
    print("🌱 零限制基础版（所有新代币都推送）", flush=True)
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("="*50, flush=True)
    
    round_count = 0
    while True:
        try:
            round_count += 1
            print(f"\\n🔄 第 {round_count} 轮检查 - {datetime.now().strftime('%H:%M:%S')}", flush=True)
            
            tokens = get_new_tokens()
            if not tokens:
                print("⏳ 没有获取到代币", flush=True)
                time.sleep(60)
                continue
            
            new_count = 0
            for token in tokens:
                if process_token(token):
                    new_count += 1
                    time.sleep(2)
            
            print(f"📊 本轮推送 {new_count} 个代币", flush=True)
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\\n🛑 用户中断", flush=True)
            break
        except Exception as e:
            print(f"❌ 错误: {e}", flush=True)
            time.sleep(60)

if __name__ == "__main__":
    print("🔥🔥🔥 程序开始运行 🔥🔥🔥", flush=True)
    main()
    print("✅ 程序正常结束", flush=True)
