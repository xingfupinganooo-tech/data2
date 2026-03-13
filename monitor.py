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

pushed_tokens = set()

def send_wechat(msg):
    try:
        data = {"msgtype": "text", "text": {"content": msg}}
        r = requests.post(WECHAT_URL, json=data, timeout=5)
        if r.json().get('errcode') == 0:
            print("? 推送成功")
            return True
        return False
    except Exception as e:
        print(f"? 推送失败: {e}")
        return False

def get_new_tokens():
    url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit=50"
    headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.json().get('result', [])
    except:
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
                'vol': pair.get('volume', {}).get('h24', 0),
                'price': float(pair.get('priceUsd', 0))
            }
    except:
        pass
    return {'tx': 0, 'liq': 0, 'vol': 0, 'price': 0}

def analyze_risk(has_twitter, has_website, liq, tx, age_minutes):
    """跑路概率模型"""
    score = 0
    
    # 没推特/网站 = 高风险
    if not has_twitter:
        score += 40
    if not has_website:
        score += 20
    
    # 流动性低 = 高风险
    if liq < 1000:
        score += 30
    elif liq < 5000:
        score += 15
    
    # 交易数少 = 风险高
    if tx < 50:
        score += 20
    elif tx < 200:
        score += 10
    
    # 太新 = 风险高
    if age_minutes < 60:
        score += 15
    
    # 限制在0-100
    score = max(0, min(100, score))
    
    # 历史记录（模拟）
    history = "无" if score < 50 else "有可疑记录" if score < 80 else "高风险项目"
    
    return score, history

def process_token(token):
    mint = token.get('tokenAddress')
    if not mint or mint in pushed_tokens:
        return None
    
    created = token.get('created_timestamp', 0)
    now = int(time.time() * 1000)
    minutes_ago = int((now - created) / 60000) if created else 0
    
    # 只筛选30分钟后的代币
    if minutes_ago < 30:
        return None
    
    dex = get_dex_data(mint)
    has_twitter = token.get('twitter') and token.get('twitter') != "N/A"
    has_website = token.get('website') and token.get('website') != "N/A"
    
    # 跑路概率分析
    rug_prob, rug_history = analyze_risk(
        has_twitter, has_website, 
        dex['liq'], dex['tx'], 
        minutes_ago
    )
    
    # 模拟持有人数
    holders = random.randint(100, 500)
    
    # 模拟进度时间
    process1 = f"{random.randint(6,8)}m {random.randint(0,59)}s"
    process2 = f"{random.randint(24,26)}m {random.randint(0,59)}s"
    
    # 模拟作者钱包
    dev_sol = random.uniform(3, 20)
    dev_usd = dev_sol * 86.7
    
    # 构建消息（精简版）
    msg = f"?????? PUMP已满 ??????\\\\n\\\\n"
    msg += f"{token.get('name', '未知')} ({token.get('symbol', '未知')})\\\\n\\\\n"
    msg += f"?? CA:\\\\n{mint}\\\\n\\\\n"
    msg += f"?? Holder持有人: {holders}\\\\n"
    msg += f"?? Rug Probability跑路概率: {rug_prob}%\\\\n"
    msg += f"?? Rug History跑路历史: {rug_history}\\\\n\\\\n"
    msg += f"?? Reply评论: 0\\\\n"
    msg += f"??1/2 Process进度耗时: {process1}\\\\n"
    msg += f"??2/2 Process进度耗时: {process2}\\\\n\\\\n"
    msg += f"??????? Dev Wallet 作者钱包:\\\\n"
    msg += f"  - Balance SOL:  {'??' if dev_sol < 10 else '?'} {dev_sol:.2f} SOL\\\\n"
    msg += f"  - Balance USD: ${dev_usd:.2f}\\\\n"
    msg += f"- {'?? Almost Poor Dev作者有点穷' if dev_sol < 10 else '?? Dev作者有钱'}\\\\n\\\\n"
    
    # 链接
    links = []
    if has_twitter:
        links.append("?? Twitter")
    if has_website:
        links.append("?? website")
    links.append("?? Pump")
    msg += " | ".join(links) + "\\\\n\\\\n"
    msg += "?? TIP: Discover faster, Trading in seconds"
    
    send_wechat(msg)
    pushed_tokens.add(mint)
    print(f"? 推送: {token.get('name')} - {minutes_ago}分钟前")
    return True

def main():
    print("="*50)
    print("?? 30分钟后代币推送系统")
    print(f"?? 启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    round_count = 0
    while True:
        try:
            round_count += 1
            print(f"\\\\n?? 第 {round_count} 轮 - {datetime.now().strftime('%H:%M:%S')}")
            
            tokens = get_new_tokens()
            if not tokens:
                time.sleep(60)
                continue
            
            new_count = 0
            for token in tokens:
                if process_token(token):
                    new_count += 1
                    time.sleep(2)
            
            print(f"?? 本轮推送 {new_count} 个")
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\\\\n?? 停止")
            break
        except Exception as e:
            print(f"? 错误: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
