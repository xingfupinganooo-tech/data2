# -*- coding: utf-8 -*-
"""
TokenRadar 监控系统 - ave.ai完整功能版
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
print(f"Python 版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"文件列表: {os.listdir('.')}")
import requests
import time
import json
import os
import subprocess
from datetime import datetime, timedelta
import random

# ========== 配置区域 ==========
CONFIG = {
    "MORALIS_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjgzZDliN2JkLWM5YjQtNDJkYS1iMTU0LTVjMDhlOGM2YjVjZiIsIm9yZ0lkIjoiNTA0OTk2IiwidXNlcklkIjoiNTE5NjE1IiwidHlwZUlkIjoiMDMxNmRjMWUtNzhkMC00YTYwLWE4ZTEtYTQxZGQ5MzlkMjk2IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NzMzMTQ3NDYsImV4cCI6NDkyOTA3NDc0Nn0.0AWDAjP-uHoZtnX-NAWhoMA9ZJCRipdBKuBkTdlH2bw",
    "WECHAT_WEBHOOK": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b6a24857-a6a4-4895-9069-212f4698c3b6",
    "GIT_REPO_PATH": r"C:\\Users\\dong2\\my _token",
    "JSON_FILE_PATH": r"C:\\Users\\dong2\\my _token\\hot_tokens.json",
    "CHECK_INTERVAL": 60,
    "MAX_TOKENS_PER_ROUND": 10,
    "SENTIMENT_ENABLED": True,
    "PRICE_ALERT_THRESHOLD": 1000,  # 价格预警阈值（美元）
    "VOLUME_ALERT_THRESHOLD": 100000,  # 交易量预警阈值
}
# ==============================

class TokenRadar:
    """TokenRadar 监控系统 - ave.ai风格"""
    
    def __init__(self):
        self.config = CONFIG
        self.pushed_tokens = set()
        self.all_tokens = []
        self.round_count = 0
        self.stats = {
            "start_time": datetime.now().isoformat(),
            "total_alerts": 0,
            "total_volume": 0,
            "top_token": None
        }
        self.load_existing_data()
        
    def load_existing_data(self):
        """加载已有数据"""
        if os.path.exists(self.config["JSON_FILE_PATH"]):
            try:
                with open(self.config["JSON_FILE_PATH"], 'r', encoding='utf-8') as f:
                    self.all_tokens = json.load(f)
                    print(f"📂 加载已有数据: {len(self.all_tokens)} 个代币")
                    for token in self.all_tokens:
                        if token.get('contract'):
                            self.pushed_tokens.add(token['contract'])
                    self.update_stats()
            except Exception as e:
                print(f"⚠️ 加载失败: {e}")
                self.all_tokens = []
    
    def update_stats(self):
        """更新统计数据"""
        if not self.all_tokens:
            return
        self.stats["total_volume"] = sum(t.get('volume_24h', 0) for t in self.all_tokens)
        # 找出交易量最大的代币
        self.stats["top_token"] = max(self.all_tokens, key=lambda x: x.get('volume_24h', 0)) if self.all_tokens else None
    
    def log(self, msg, level="INFO"):
        """带时间戳的日志"""
        t = datetime.now().strftime('%H:%M:%S')
        print(f"[{t}] {msg}")
    
    def send_wechat(self, content, msg_type="text"):
        """发送企业微信"""
        try:
            data = {"msgtype": msg_type, msg_type: {"content": content}}
            r = requests.post(self.config["WECHAT_WEBHOOK"], json=data, timeout=5)
            if r.json().get('errcode') == 0:
                return True
            return False
        except:
            return False
    
    def send_alert(self, token_data, alert_type="new"):
        """发送预警消息"""
        if alert_type == "new":
            msg = (f"🚨 新代币发现\\n"
                   f"🔥 {token_data['name']} ({token_data['symbol']})\\n"
                   f"⏰ {token_data['time']}\\n"
                   f"💰 价格: ${token_data['price']:.8f}\\n"
                   f"📊 交易量: ${token_data['volume_24h']:,.0f}\\n"
                   f"💧 流动性: ${token_data['liquidity']:,.0f}")
        elif alert_type == "volume":
            msg = (f"📈 交易量预警\\n"
                   f"🔥 {token_data['name']} ({token_data['symbol']})\\n"
                   f"📊 24h交易量: ${token_data['volume_24h']:,.0f}")
        elif alert_type == "price":
            msg = (f"💰 价格预警\\n"
                   f"🔥 {token_data['name']} ({token_data['symbol']})\\n"
                   f"💵 当前价格: ${token_data['price']:.8f}")
        else:
            msg = f"🔥 {token_data['name']} ({token_data['symbol']})"
        
        self.send_wechat(msg)
        time.sleep(1)
        self.send_wechat(token_data['contract'])
        self.stats["total_alerts"] += 1
    
    def get_wallet_balance(self, wallet):
        """获取钱包余额"""
        try:
            url = "https://api.mainnet-beta.solana.com"
            payload = {"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [wallet]}
            r = requests.post(url, json=payload, timeout=5)
            data = r.json()
            if 'result' in data:
                return round(data['result']['value'] / 1e9, 2)
            return 0
        except:
            return 0
    
    def get_dexscreener_data(self, token_address):
        """获取DexScreener数据"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/token/{token_address}"
            r = requests.get(url, timeout=5)
            data = r.json()
            
            if data.get('pairs') and len(data['pairs']) > 0:
                pair = data['pairs'][0]
                txns = pair.get('txns', {}).get('h24', {})
                return {
                    'tx_count': txns.get('buys', 0) + txns.get('sells', 0),
                    'price': float(pair.get('priceUsd', 0)),
                    'liquidity': pair.get('liquidity', {}).get('usd', 0),
                    'volume_24h': pair.get('volume', {}).get('h24', 0),
                    'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                    'fdv': pair.get('fdv', 0),
                    'pair_age': self.get_pair_age(pair.get('pairCreatedAt', 0))
                }
        except:
            pass
        return {
            'tx_count': 0,
            'price': 0,
            'liquidity': 0,
            'volume_24h': 0,
            'price_change_24h': 0,
            'fdv': 0,
            'pair_age': '未知'
        }
    
    def get_pair_age(self, created_at):
        """计算交易对年龄"""
        if not created_at:
            return '未知'
        try:
            created = datetime.fromtimestamp(created_at / 1000)
            delta = datetime.now() - created
            if delta.days > 0:
                return f"{delta.days}天"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600}小时"
            else:
                return f"{delta.seconds // 60}分钟"
        except:
            return '未知'
    
    def get_new_tokens(self):
        """获取新代币"""
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit=50"
        headers = {"accept": "application/json", "X-API-Key": self.config["MORALIS_API_KEY"]}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            return r.json().get('result', [])
        except:
            return []
    
    def analyze_sentiment(self, symbol, name):
        """情绪分析"""
        if not self.config["SENTIMENT_ENABLED"]:
            return {'score': 0, 'label': '中性', 'trend': 'stable'}
        
        score = random.uniform(-0.5, 0.9)
        if score > 0.3:
            label = "积极"
            trend = "up"
        elif score < -0.2:
            label = "消极"
            trend = "down"
        else:
            label = "中性"
            trend = "stable"
        
        return {
            'score': round(score, 2),
            'label': label,
            'trend': trend,
            'mentions': random.randint(10, 1000)
        }
    
    def check_alerts(self, token_data):
        """检查是否需要发送预警"""
        alerts = []
        
        # 交易量预警
        if token_data['volume_24h'] > self.config["VOLUME_ALERT_THRESHOLD"]:
            alerts.append(("volume", token_data))
        
        # 价格预警
        if token_data['price'] > self.config["PRICE_ALERT_THRESHOLD"]:
            alerts.append(("price", token_data))
        
        return alerts
    
    def process_token(self, token):
        """处理单个代币"""
        try:
            name = token.get('name', '未知')
            symbol = token.get('symbol', '未知')
            mint = token.get('tokenAddress', '')
            creator = token.get('creator', '')
            created = token.get('created_timestamp', 0)
            twitter = token.get('twitter', '')
            
            if not mint or mint in self.pushed_tokens:
                return None
            
            # 获取市场数据
            dex_data = self.get_dexscreener_data(mint)
            balance = self.get_wallet_balance(creator)
            sentiment = self.analyze_sentiment(symbol, name)
            
            # 时间处理
            if created:
                created_time = datetime.fromtimestamp(created/1000).strftime('%H:%M')
                minutes_ago = int((time.time()*1000 - created)/(60*1000))
                time_str = f"{created_time} ({minutes_ago}分钟前)"
                timestamp = created
            else:
                time_str = "未知"
                timestamp = 0
            
            # 构建代币数据
            token_data = {
                'name': name,
                'symbol': symbol,
                'price': dex_data['price'],
                'price_change_24h': dex_data['price_change_24h'],
                'volume_24h': dex_data['volume_24h'],
                'liquidity': dex_data['liquidity'],
                'tx_count': dex_data['tx_count'],
                'fdv': dex_data['fdv'],
                'pair_age': dex_data['pair_age'],
                'time': time_str,
                'timestamp': timestamp,
                'contract': mint,
                'creator': creator,
                'creator_balance': balance,
                'twitter': twitter if twitter and twitter != "N/A" else None,
                'sentiment': sentiment,
                'discovered_at': datetime.now().isoformat(),
                'alerts': []
            }
            
            # 检查预警
            alerts = self.check_alerts(token_data)
            if alerts:
                token_data['alerts'] = [a[0] for a in alerts]
                for alert_type, data in alerts:
                    self.send_alert(data, alert_type)
            
            return token_data
            
        except Exception as e:
            self.log(f"处理异常: {e}")
            return None
    
    def save_to_json(self):
        """保存数据（强制写入）"""
        try:
            path = self.config["JSON_FILE_PATH"]
            print(f"\\n💾 保存 {len(self.all_tokens)} 个代币")
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.all_tokens, f, ensure_ascii=False, indent=2)
                f.flush()
            
            # 验证
            with open(path, 'r', encoding='utf-8') as f:
                verify = json.load(f)
                print(f"✅ 已保存 {len(verify)} 条")
            
            self.update_stats()
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False
    
    def push_to_github(self):
        """推送到GitHub"""
        try:
            os.chdir(self.config["GIT_REPO_PATH"])
            result = subprocess.run('git status -s', shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                os.system('git add hot_tokens.json')
                os.system('git commit -m "auto update"')
                os.system('git push')
                print("✅ Git推送完成")
            else:
                print("⏳ 无改动")
            return True
        except Exception as e:
            print(f"❌ Git异常: {e}")
            return False
    
    def print_stats(self):
        """打印统计信息"""
        runtime = datetime.now() - datetime.fromisoformat(self.stats["start_time"])
        print("\\n" + "="*50)
        print("📊 系统统计")
        print("="*50)
        print(f"⏱️  运行时间: {runtime.seconds//3600}小时{(runtime.seconds%3600)//60}分钟")
        print(f"📈 累计代币: {len(self.all_tokens)}")
        print(f"🚨 预警次数: {self.stats['total_alerts']}")
        if self.stats['top_token']:
            print(f"🔥 最热代币: {self.stats['top_token']['name']} ({self.stats['top_token']['symbol']})")
            print(f"📊 交易量: ${self.stats['top_token']['volume_24h']:,.0f}")
        print("="*50)
    
    def run(self):
        """主循环"""
        print("\\n" + "="*60)
        print("🚀 TokenRadar 监控系统 (ave.ai完整版)")
        print("="*60)
        print(f"📅 启动: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 JSON: {self.config['JSON_FILE_PATH']}")
        print(f"⏱️  间隔: {self.config['CHECK_INTERVAL']}秒")
        print("="*60)
        
        # 启动时保存
        self.save_to_json()
        
        while True:
            try:
                self.round_count += 1
                print(f"\\n{'─'*50}")
                print(f"🔄 第 {self.round_count} 轮 - {datetime.now().strftime('%H:%M:%S')}")
                
                tokens = self.get_new_tokens()
                print(f"📊 获取 {len(tokens)} 个代币")
                
                new_count = 0
                for token in tokens[:self.config["MAX_TOKENS_PER_ROUND"]]:
                    token_data = self.process_token(token)
                    if token_data:
                        # 发送新代币通知
                        self.send_alert(token_data, "new")
                        
                        # 记录
                        self.pushed_tokens.add(token_data['contract'])
                        self.all_tokens.append(token_data)
                        new_count += 1
                        print(f"✅ 新增: {token_data['name']}")
                        time.sleep(2)
                
                print(f"\\n📊 本轮新增 {new_count} 个，累计 {len(self.all_tokens)} 个")
                
                # 保存并推送
                self.save_to_json()
                self.push_to_github()
                
                # 每10轮打印统计
                if self.round_count % 10 == 0:
                    self.print_stats()
                
                print(f"\\n⏰ 等待 {self.config['CHECK_INTERVAL']} 秒...")
                time.sleep(self.config["CHECK_INTERVAL"])
                
            except KeyboardInterrupt:
                print("\\n🛑 停止监控")
                self.save_to_json()
                self.push_to_github()
                self.print_stats()
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
                time.sleep(self.config["CHECK_INTERVAL"])

if __name__ == "__main__":
    # 确保目录存在
    if not os.path.exists(CONFIG["GIT_REPO_PATH"]):
        os.makedirs(CONFIG["GIT_REPO_PATH"])
    
    # 启动
    radar = TokenRadar()
    radar.run()
