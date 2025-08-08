import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AlertConfig:
    """告警配置"""
    apy_threshold: float = 20.0  # 年化收益率阈值（%）
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    enable_notifications: bool = True

@dataclass
class MonitorConfig:
    """监控配置"""
    check_interval: int = 3600  # 检查间隔（秒），默认1小时
    initial_amount: float = 100000.0  # 初始金额 USDT
    
@dataclass
class TokenConfig:
    """代币配置"""
    USDT = {
        'address': "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        'decimals': 6,
        'symbol': "USDT"
    }
    
    USDE = {
        'address': "0x4c9EDD5852cd905f086C759E8383e09bff1E68B3",
        'decimals': 18,
        'symbol': "USDE"
    }
    
    SUSDE = {
        'address': "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497",
        'decimals': 18,
        'symbol': "SUSDE"
    }

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Telegram机器人配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# 以太坊节点配置 
INFURA_URL = os.getenv('INFURA_URL', 'https://mainnet.infura.io/v3/your_project_id')

# 监控配置
CHECK_INTERVAL_HOURS = float(os.getenv('CHECK_INTERVAL_HOURS', '1'))
ALERT_THRESHOLD = float(os.getenv('ALERT_THRESHOLD', '20.0'))

# Flask配置
PORT = int(os.getenv('PORT', '8081'))

# 1inch URL配置
ONEINCH_URLS = {
    'USDT_TO_SUSDE': "https://app.1inch.io/swap?src=1:USDT&dst=1:sUSDe",
    'USDE_TO_USDT': "https://app.1inch.io/swap?src=1:USDe&dst=1:USDT"
}

# SUSDE合约ABI
SUSDE_ABI = [
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "shares",
                "type": "uint256"
            }
        ],
        "name": "previewRedeem",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
