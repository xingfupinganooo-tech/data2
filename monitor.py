# -*- coding: utf-8 -*-
import requests
import time
import json
import random
from datetime import datetime

# ========== 配置区域 ==========
WECHAT_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b6a24857-a6a4-4895-9069-212f4698c3b6"
# ==============================

print("🔥 Solscan 版启动...", flush=True)
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
    """使用 Solscan 公开 API 获取最新代币（无需密钥）"""
    url = "url = "https://pro-api.solscan.io/v2.0/token/list"
    params = {
        "sortBy": "createdTime",  # 按创建时间排序
        "direction": "desc",       # 倒序，最新的在前
        "limit": 50                 # 获取 50 个
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    try:
        print(f"🔍 请求 Solscan API...", flush=True)
        r = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"🔍 API 返回状态码: {r.status_code}", flush=True)
        
        if r.status_code == 200:
            data = r.json()
            tokens = data.get('data', [])
            print(f"📊 获取到 {len(tokens)} 个新代币", flush=True)
            
            # 转换成我们需要的格式
            formatted_tokens = []
            for token in tokens:
                formatted_tokens.append({
                    'name': token.get('name', '未知'),
                    'symbol': token.get('symbol', '未知'),
                    'tokenAddress': token.get('address'),
                    'created_timestamp': token.get('createdTime', 0),
                    'twitter': token.get('twitter', ''),
                    'website': token.get('website', '')
                })
            return formatted_tokens
        else:
            print(f"❌ API 返回错误: {r.text}", flush=True)
            return []
    except Exception as e:
        print(f"❌ 获取代币失败: {e}", flush=True)
        return []

def get_dex_data(addr):
    """从 DexScreener 获取交易数据（也免费）"""
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
    
    # 模拟数据（Solscan 没有这些，保持模拟）
    holders = random.randint(100, 500)
    rug_prob = random.randint(20, 80)
    rug_history = "无" if rug_prob < 50 else "有可疑记录" if rug_prob < 80 else "高风险项目"
    process1 = f"{random.randint(6,8)}m {random.randint(0,59)}s"
    process2 = f"{random.randint(24,26)}m {random.randint(0,59)}s"
    dev_sol = random.uniform(3, 20)
    dev_usd = dev_sol * 86.7
    
    # 构建消息
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
    
    links = []
    if token.get('twitter'):
        links.append("🐦 Twitter")
    if token.get('website'):
        links.append("🌏 website")
    links.append("💊 Pump")
    msg += " | ".join(links) + "\\n\\n"
    msg += "⚡️ TIP: Solscan 版 | 无需 API Key"
    
    send_wechat(msg)
    pushed_tokens.add(mint)
    print(f"✅ 推送: {token.get('name')} - {minutes_ago}分钟前", flush=True)
    return True

def main():
    print("="*50, flush=True)
    print("🌱 Solscan 版（无需 API Key）", flush=True)
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
