# -*- coding: utf-8 -*-
import os
import requests
import time
import json
import hmac
import hashlib
from datetime import datetime

# ========== 从环境变量读取配置 ==========
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')print(f"🔍 调试: BINANCE_API_KEY 是否存在: {'BINANCE_API_KEY' in os.environ}")
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')print(f"🔍 调试: BINANCE_SECRET_KEY 是否存在: {'BINANCE_SECRET_KEY' in os.environ}")
WECHAT_URL = os.getenv('WECHAT_URL')print(f"🔍 调试: WECHAT_URL 是否存在: {'WECHAT_URL' in os.environ}")

if not all([BINANCE_API_KEY, BINANCE_SECRET_KEY, WECHAT_URL]):
    print("❌ 请设置环境变量: BINANCE_API_KEY, BINANCE_SECRET_KEY, WECHAT_URL", flush=True)
    exit(1)
# ======================================

print("🔥 币安Alpha监控启动...", flush=True)
pushed_tokens = set()

def send_wechat_markdown(msg):
    """发送企业微信Markdown消息"""
    try:
        data = {"msgtype": "markdown", "markdown": {"content": msg}}
        r = requests.post(WECHAT_URL, json=data, timeout=5)
        if r.json().get('errcode') == 0:
            print("✅ 推送成功", flush=True)
            return True
        return False
    except Exception as e:
        print(f"❌ 推送失败: {e}", flush=True)
        return False

def get_binance_alpha_tokens():
    """获取币安Alpha板块所有代币"""
    # 方法1：通过币安API获取Alpha代币列表
    try:
        # 获取交易所信息，从中筛选Alpha代币
        url = "https://api.binance.com/api/v3/exchangeInfo"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            symbols = data.get('symbols', [])
            
            # 筛选USDT交易对，且可能是Alpha的代币（这里需要根据实际规则判断）
            alpha_tokens = []
            for s in symbols:
                if s.get('quoteAsset') == 'USDT' and s.get('status') == 'TRADING':
                    # 这里可以根据实际Alpha规则进一步筛选
                    alpha_tokens.append({
                        'symbol': s.get('baseAsset'),
                        'name': s.get('baseAsset'),  # 币安exchangeInfo没有name字段
                        'contract': '',  # 币安API不提供合约地址
                        'quote_asset': 'USDT'
                    })
            
            print(f"📊 获取到 {len(alpha_tokens)} 个交易对", flush=True)
            return alpha_tokens
    except Exception as e:
        print(f"⚠️ 币安API失败: {e}", flush=True)
    
    # 方法2：备用方案 - 手动维护的Alpha代币列表
    # 根据币安Alpha最近上线的代币（需要定期从公告更新）
    alpha_tokens = [
        {"symbol": "B2", "name": "B2 Network", "contract": "0x0000000000000000000000000000000000000000"},
        {"symbol": "AIOT", "name": "AIOT", "contract": "0x0000000000000000000000000000000000000000"},
        {"symbol": "NIGHT", "name": "NIGHT", "contract": "0x0000000000000000000000000000000000000000"},
        {"symbol": "VINE", "name": "VINE", "contract": "0x0000000000000000000000000000000000000000"},
        {"symbol": "ALPHA", "name": "ALPHA", "contract": "0x0000000000000000000000000000000000000000"},
        {"symbol": "KAT", "name": "Katana", "contract": "0x0000000000000000000000000000000000000000"},
        {"symbol": "CAI", "name": "CharacterX", "contract": "0x0000000000000000000000000000000000000000"},
        {"symbol": "BIRB", "name": "Moonbirds", "contract": "0x0000000000000000000000000000000000000000"},
    ]
    return alpha_tokens

def get_token_details(symbol):
    """通过币安API获取代币详细信息"""
    try:
        # 获取24小时行情
        url = "https://api.binance.com/api/v3/ticker/24hr"
        params = {"symbol": f"{symbol}USDT"}
        r = requests.get(url, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return {
                'price': float(data.get('lastPrice', 0)),
                'volume': float(data.get('volume', 0)),
                'quote_volume': float(data.get('quoteVolume', 0)),
                'price_change': float(data.get('priceChangePercent', 0)),
                'high': float(data.get('highPrice', 0)),
                'low': float(data.get('lowPrice', 0))
            }
    except Exception as e:
        print(f"⚠️ 获取 {symbol} 详情失败: {e}", flush=True)
    return None

def analyze_potential(details):
    """分析代币潜力"""
    if not details:
        return False, []
    
    reasons = []
    score = 0
    
    # 交易量 > $1M
    if details['quote_volume'] > 1_000_000:
        score += 30
        reasons.append(f"交易量 ${details['quote_volume']/1e6:.1f}M")
    
    # 价格波动 > 10%
    if abs(details['price_change']) > 10:
        score += 20
        reasons.append(f"涨跌幅 {details['price_change']:.1f}%")
    
    # 交易量 > $100K 且涨跌 > 5%
    if details['quote_volume'] > 100_000 and abs(details['price_change']) > 5:
        score += 15
        reasons.append("活跃度高")
    
    return score >= 30, reasons

def process_alpha_tokens():
    """处理所有Alpha代币，筛选有潜力的推送"""
    tokens = get_binance_alpha_tokens()
    if not tokens:
        print("⏳ 没有获取到Alpha代币", flush=True)
        return
    
    new_count = 0
    for token in tokens:
        symbol = token.get('symbol')
        if not symbol or symbol in pushed_tokens:
            continue
        
        # 获取详细行情
        details = get_token_details(symbol)
        if not details:
            continue
        
        # 分析潜力
        is_potential, reasons = analyze_potential(details)
        if not is_potential:
            continue
        
        # 构建Markdown消息
        msg = f"<font color=\"blue\">💎 {token.get('name', symbol)} ({symbol})</font>\\n\\n"
        msg += f"⏰ 时间: {datetime.now().strftime('%H:%M')}\\n\\n"
        msg += f"💰 价格: ${details['price']:.8f}\\n"
        msg += f"📊 24h涨跌: {details['price_change']:.2f}%\\n"
        msg += f"📈 24h交易量: ${details['quote_volume']:,.0f}\\n"
        msg += f"🔥 24h最高: ${details['high']:.8f}\\n"
        msg += f"📉 24h最低: ${details['low']:.8f}\\n\\n"
        
        if reasons:
            msg += f"✨ 潜力指标: {', '.join(reasons)}\\n\\n"
        
        # 合约地址（如果有的话）
        contract = token.get('contract', '')
        if contract and contract != '0x0000000000000000000000000000000000000000':
            msg += f"🔗 合约:\\n<font color=\"blue\">{contract}</font>"
        
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
    while True:
        try:
            round_count += 1
            print(f"\\n🔄 第 {round_count} 轮检查 - {datetime.now().strftime('%H:%M:%S')}", flush=True)
            
            process_alpha_tokens()
            time.sleep(60 * 5)  # 每5分钟检查一次
            
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
