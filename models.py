from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
import json

@dataclass
class ArbitrageStep:
    """套利步骤"""
    step_number: int
    from_token: str
    to_token: str
    input_amount: float
    output_amount: float
    price_impact: float
    route: str
    
    def to_dict(self) -> Dict:
        return {
            'step_number': self.step_number,
            'from_token': self.from_token,
            'to_token': self.to_token,
            'input_amount': self.input_amount,
            'output_amount': self.output_amount,
            'price_impact': self.price_impact,
            'route': self.route
        }

@dataclass
class ArbitrageResult:
    """套利结果"""
    initial_amount: float
    final_amount: float
    profit_loss: float
    profit_percentage: float
    annualized_return: float
    steps: list[ArbitrageStep]
    calculation_time: datetime
    
    @property
    def is_profitable(self) -> bool:
        return self.profit_loss > 0
    
    @property
    def formatted_profit_loss(self) -> str:
        """格式化盈亏显示"""
        if self.is_profitable:
            return f"🟢 {self.profit_loss:.3f} USDT ({self.profit_percentage:.2f}%)"
        else:
            return f"🔴 {abs(self.profit_loss):.3f} USDT ({self.profit_percentage:.2f}%)"
    
    def to_dict(self) -> Dict:
        return {
            'initial_amount': self.initial_amount,
            'final_amount': self.final_amount,
            'profit_loss': self.profit_loss,
            'profit_percentage': self.profit_percentage,
            'annualized_return': self.annualized_return,
            'steps': [step.to_dict() for step in self.steps],
            'calculation_time': self.calculation_time.isoformat(),
            'is_profitable': self.is_profitable
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
    
    def format_telegram_message(self) -> str:
        """格式化Telegram消息"""
        message = f"""📊 SusDE 套利年化收益率报告

💰 初始金额: {self.initial_amount:,.0f} USDT
💵 最终金额: {self.final_amount:,.3f} USDT
📈 收益/损失: {self.formatted_profit_loss}
🚀 年化收益率: {self.annualized_return:.2f}%

🔄 套利路径:"""
        
        for step in self.steps:
            emoji = "1️⃣" if step.step_number == 1 else "2️⃣" if step.step_number == 2 else "3️⃣"
            
            if step.step_number == 2:  # SUSDE -> USDE (解质押)
                message += f"""
{emoji} {step.from_token} → {step.to_token} (解质押)
   💱 {step.input_amount:,.0f} {step.from_token} → {step.output_amount:,.3f} {step.to_token}
   📋 解质押比率: {step.output_amount/step.input_amount:.4f}"""
            else:
                message += f"""
{emoji} {step.from_token} → {step.to_token}
   💱 {step.input_amount:,.0f} {step.from_token} → {step.output_amount:,.3f} {step.to_token}
   📈 价格影响: {step.price_impact:.2f}%
   🛣️ 路由: {step.route}"""
        
        message += f"""

⏰ 计算时间: {self.calculation_time.strftime('%Y/%m/%d %H:%M:%S')}"""
        
        return message
