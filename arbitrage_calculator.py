from datetime import datetime
from typing import Optional, List
from models import ArbitrageResult, ArbitrageStep
from exchange_service import ExchangeService
from config import MonitorConfig
import traceback

class ArbitrageCalculator:
    """套利计算器"""
    
    def __init__(self):
        self.exchange_service = ExchangeService()
        self.config = MonitorConfig()
    
    def calculate_arbitrage(self, initial_amount: float = None) -> Optional[ArbitrageResult]:
        """计算套利机会"""
        if initial_amount is None:
            initial_amount = self.config.initial_amount
        
        try:
            print(f"开始计算套利，初始金额: {initial_amount} USDT")
            
            steps = []
            current_amount = initial_amount
            
            # 第一步：USDT → SUSDE
            step1 = self.exchange_service.get_usdt_to_susde(current_amount)
            if not step1:
                print("第一步USDT → SUSDE失败")
                return None
            
            steps.append(step1)
            current_amount = step1.output_amount
            print(f"第一步完成: {step1.input_amount} USDT → {step1.output_amount} SUSDE")
            
            # 第二步：SUSDE → USDE (解质押)
            step2 = self.exchange_service.get_susde_to_usde(current_amount)
            if not step2:
                print("第二步SUSDE → USDE失败")
                return None
            
            steps.append(step2)
            current_amount = step2.output_amount
            print(f"第二步完成: {step2.input_amount} SUSDE → {step2.output_amount} USDE")
            
            # 第三步：USDE → USDT
            step3 = self.exchange_service.get_usde_to_usdt(current_amount)
            if not step3:
                print("第三步USDE → USDT失败")
                return None
            
            steps.append(step3)
            final_amount = step3.output_amount
            print(f"第三步完成: {step3.input_amount} USDE → {step3.output_amount} USDT")
            
            # 计算收益
            profit_loss = final_amount - initial_amount
            profit_percentage = (profit_loss / initial_amount) * 100
            
            # 计算年化收益率 (基于7天期收益)
            # 公式: (收益 / 7 * 365) / 初始金额 * 100
            annualized_return = (profit_loss / 7 * 365) / initial_amount * 100
            
            result = ArbitrageResult(
                initial_amount=initial_amount,
                final_amount=final_amount,
                profit_loss=profit_loss,
                profit_percentage=profit_percentage,
                annualized_return=annualized_return,
                steps=steps,
                calculation_time=datetime.now()
            )
            
            print(f"套利计算完成:")
            print(f"初始: {initial_amount} USDT")
            print(f"最终: {final_amount} USDT") 
            print(f"收益: {profit_loss:.3f} USDT ({profit_percentage:.2f}%)")
            print(f"年化收益率: {annualized_return:.2f}%")
            
            return result
            
        except Exception as e:
            print(f"计算套利时出错: {e}")
            print(traceback.format_exc())
            return None
