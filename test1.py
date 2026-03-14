import os
import sys
import requests
import time
import json
from datetime import datetime

# ========== 从环境变量读取配置 ==========
A = os.getenv('A')
B = os.getenv('B')
C = os.getenv('C')

print("="*50, flush=True)
print("🔍 环境变量检查", flush=True)
print(f"A 长度: {len(A) if A else 0}", flush=True)
print(f"B 长度: {len(B) if B else 0}", flush=True)
print(f"C 长度: {len(C) if C else 0}", flush=True)
print("="*50, flush=True)

if not A or not B or not C:
    print("❌ 缺少环境变量", flush=True)
    sys.exit(1)

print("✅ 环境变量读取成功，开始运行...", flush=True)
print("="*50, flush=True)
# ======================================

pushed_tokens = set()

def send_wechat_markdown(msg):
    """发送企业微信Markdown消息"""
    try:
        data = {"msgtype": "markdown", "markdown": {"content": msg}}
        r = requests.post(C, json=data, timeout=5)
        if r.status_code == 200 and r.json().get('errcode') == 0:
            print("✅ 推送成功", flush=True)
            return True
        return False
    except Exception as e:
        print(f"❌ 推送失败: {e}", flush=True)
        return False

def get_binance_alpha_tokens():
    """获取币安Alpha板块所有代币"""
    try:
        url = "https://api.binance.com/api/v3/exchangeInfo"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            symbols = data.get('symbols', [])
            alpha_tokens = []
            for s in symbols:
                if s.get('quoteAsset') == 'USDT' and s.get('status') == 'TRADING':
                    alpha_tokens.append({
                        'symbol': s.get('baseAsset'),
                        'name': s.get('baseAsset')
                    })
            print(f"📊 获取到 {len(alpha_tokens)} 个USDT交易对", flush=True)
            return alpha_tokens
    except Exception as e:
        print(f"⚠️ 币安API失败: {e}", flush=True)
    return []

def get_token_details(symbol):
    """通过币安API获取代币详细信息"""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        params = {"symbol": f"{symbol}USDT"}
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                'price': float(data.get('lastPrice', 0)),
                'quote_volume': float(data.get('quoteVolume', 0)),
                'price_change': float(data.get('priceChangePercent', 0))
            }
    except Exception as e:
        print(f"⚠️ 获取 {symbol} 详情失败: {e}", flush=True)
    return None

def analyze_potential(details):
    """分析代币潜力"""
    if not details:
        return False, []
    reasons = []
    if details['quote_volume'] > 1_000_000:
        reasons.append(f"交易量 ${details['quote_volume']/1e6:.1f}M")
    if abs(details['price_change']) > 10:
        reasons.append(f"涨跌幅 {details['price_change']:.1f}%")
    return len(reasons) > 0, reasons

def process_alpha_tokens():
    """处理所有Alpha代币，筛选有潜力的推送"""
    print("🔥 开始本轮代币筛选...", flush=True)
    tokens = get_binance_alpha_tokens()
    if not tokens:
        print("⏳ 没有获取到代币", flush=True)
        return
    
    new_count = 0
    for token in tokens[:10]:
        symbol = token.get('symbol')
        if not symbol or symbol in pushed_tokens:
            continue
        
        details = get_token_details(symbol)
        is_potential, reasons = analyze_potential(details)
        if not is_potential:
            continue
        
        msg = f"<font color=\"blue\">💎 {symbol}</font>\\n\\n"
        msg += f"⏰ 时间: {datetime.now().strftime('%H:%M')}\\n\\n"
        msg += f"💰 价格: ${details['price']:.8f}\\n"
        msg += f"📊 24h涨跌: {details['price_change']:.2f}%\\n"
        msg += f"📈 24h交易量: ${details['quote_volume']:,.0f}\\n"
        if reasons:
            msg += f"\\n✨ {' '.join(reasons)}\\n"
        
        send_wechat_markdown(msg)
        pushed_tokens.add(symbol)
        new_count += 1
        print(f"✅ 推送: {symbol}", flush=True)
        time.sleep(2)
    
    print(f"📊 本轮推送 {new_count} 个潜力代币", flush=True)

def main():
    print("="*50, flush=True)
    print("🔥 币安Alpha潜力代币监控", flush=True)
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("="*50, flush=True)
    
    round_count = 0
    print("🚀 进入无限循环，每5分钟检查一次...", flush=True)
    
    while True:
        try:
            round_count += 1
            print(f"\\n{'='*50}", flush=True)
            print(f"🔄 第 {round_count} 轮检查 - {datetime.now().strftime('%H:%M:%S')}", flush=True)
            print(f"{'='*50}", flush=True)
            
            process_alpha_tokens()
            
            print(f"\\n✅ 第 {round_count} 轮执行完成", flush=True)
            print(f"⏰ 等待5分钟后进入第 {round_count+1} 轮...", flush=True)
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\\n🛑 用户中断，程序停止", flush=True)
            break
        except Exception as e:
            print(f"\\n❌ 错误: {e}", flush=True)
            print("⏰ 等待1分钟后重试...", flush=True)
            time.sleep(60)

if __name__ == "__main__":
    main()
