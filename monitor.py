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
    """Solscan 公开 API - 获取最新代币"""
    url = "https://api.solscan.io/token/list"
    params = {
        "sort_by": "created_time",
        "sort_order": "desc",
        "limit": 50
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://solscan.io/"
    }
    try:
        print(f"🔍 请求 Solscan API: {url}", flush=True)
        r = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"🔍 API 返回状态码: {r.status_code}", flush=True)
        
        if r.status_code == 200:
            data = r.json()
            print(f"📦 API 返回数据结构: {type(data)}", flush=True)
            
            # Solscan 返回的数据可能有多种格式，尝试不同路径
            tokens = []
            if isinstance(data, dict):
                if 'data' in data:
                    tokens = data['data']
                elif 'result' in data:
                    tokens = data['result']
                elif 'tokens' in data:
                    tokens = data['tokens']
                elif 'list' in data:
                    tokens = data['list']
            
            print(f"📊 获取到 {len(tokens)} 个原始代币", flush=True)
            
            formatted_tokens = []
            for token in tokens[:50]:
                # 尝试不同的字段名
                addr = (token.get('address') or 
                       token.get('tokenAddress') or 
                       token.get('token_addr') or 
                       token.get('mint') or 
                       token.get('id'))
                
                if not addr:
                    continue
                
                # 获取创建时间
                created = (token.get('createdTime') or 
                          token.get('created_at') or 
                          token.get('createTime') or 
                          token.get('timestamp') or 0)
                
                formatted_tokens.append({
                    'name': token.get('name', '未知'),
                    'symbol': token.get('symbol', '未知'),
                    'tokenAddress': addr,
                    'created_timestamp': created,
                    'twitter': token.get('twitter', ''),
                    'website': token.get('website', '')
                })
            
            print(f"✅ 格式化后获得 {len(formatted_tokens)} 个代币", flush=True)
            return formatted_tokens
        else:
            print(f"❌ API 返回错误: {r.status_code}", flush=True)
            print(f"📄 错误内容: {r.text[:200]}", flush=True)
            return []
    except Exception as e:
        print(f"❌ 获取代币失败: {e}", flush=True)
        return []

def get_dex_data(addr):
    """从 DexScreener 获取交易数据"""
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/token/{addr}", timeout=5)
        if r.status_code == 200:
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
    msg += "⚡️ TIP: Solscan 实验版"
    
    send_wechat(msg)
    pushed_tokens.add(mint)
    print(f"✅ 推送: {token.get('name')} - {minutes_ago}分钟前", flush=True)
    return True

def main():
    print("="*50, flush=True)
    print("🔬 Solscan 实验版（正在调试）", flush=True)
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
