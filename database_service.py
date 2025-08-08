#!/usr/bin/env python3
"""
Supabase数据库服务模块

处理套利数据的存储和查询
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import json

from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
from models import ArbitrageResult

logger = logging.getLogger(__name__)

class DatabaseService:
    """Supabase数据库服务"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.supabase: Optional[Client] = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """连接到Supabase"""
        try:
            if not SUPABASE_URL or not SUPABASE_ANON_KEY:
                logger.warning("Supabase配置不完整，数据库功能将被禁用")
                return
            
            # 优先使用服务角色密钥，否则使用匿名密钥
            key = SUPABASE_SERVICE_ROLE_KEY if SUPABASE_SERVICE_ROLE_KEY else SUPABASE_ANON_KEY
            
            self.supabase = create_client(SUPABASE_URL, key)
            self.connected = True
            logger.info("成功连接到Supabase数据库")
            
            # 测试连接
            self._test_connection()
            
        except Exception as e:
            logger.error(f"连接Supabase失败: {e}")
            self.connected = False
    
    def _test_connection(self):
        """测试数据库连接"""
        try:
            if self.supabase:
                # 尝试查询arbitrage_checks表
                result = self.supabase.table('arbitrage_checks').select('*').limit(1).execute()
                logger.info("数据库连接测试成功")
        except Exception as e:
            logger.warning(f"数据库连接测试失败: {e}")
    
    def save_arbitrage_result(self, result: ArbitrageResult, check_type: str = "scheduled") -> bool:
        """保存套利检查结果"""
        if not self.connected or not self.supabase:
            logger.warning("数据库未连接，跳过保存")
            return False
        
        try:
            # 从steps中提取价格信息
            usdt_to_susde_price = None
            susde_to_usde_rate = None
            usde_to_usdt_price = None
            execution_steps = []
            
            for step in result.steps:
                execution_steps.append(f"{step.from_token} -> {step.to_token}")
                
                if step.from_token == "USDT" and step.to_token == "SUSDE":
                    usdt_to_susde_price = step.output_amount / step.input_amount if step.input_amount > 0 else None
                elif step.from_token == "SUSDE" and step.to_token == "USDE":
                    susde_to_usde_rate = step.output_amount / step.input_amount if step.input_amount > 0 else None
                elif step.from_token == "USDE" and step.to_token == "USDT":
                    usde_to_usdt_price = step.output_amount / step.input_amount if step.input_amount > 0 else None
            
            # 准备数据
            data = {
                'timestamp': datetime.now().isoformat(),
                'check_type': check_type,  # 'scheduled', 'manual', 'alert'
                'amount': result.initial_amount,
                'usdt_to_susde_price': usdt_to_susde_price,
                'susde_to_usde_rate': susde_to_usde_rate,
                'usde_to_usdt_price': usde_to_usdt_price,
                'profit_loss': result.profit_loss,
                'profit_percentage': result.profit_percentage,
                'annualized_return': result.annualized_return,
                'is_profitable': result.is_profitable,
                'execution_steps': execution_steps,
                'market_data': {
                    'usdt_to_susde_price': usdt_to_susde_price,
                    'susde_to_usde_rate': susde_to_usde_rate,
                    'usde_to_usdt_price': usde_to_usdt_price,
                    'steps': [step.to_dict() for step in result.steps]
                }
            }
            
            # 插入数据
            response = self.supabase.table('arbitrage_checks').insert(data).execute()
            
            if response.data:
                logger.info(f"成功保存套利结果 - 年化收益率: {result.annualized_return:.2f}%")
                return True
            else:
                logger.error("保存套利结果失败：无返回数据")
                return False
                
        except Exception as e:
            logger.error(f"保存套利结果时出错: {e}")
            return False
    
    def save_alert(self, alert_data: Dict[str, Any]) -> bool:
        """保存告警记录"""
        if not self.connected or not self.supabase:
            logger.warning("数据库未连接，跳过保存告警")
            return False
        
        try:
            # 准备告警数据
            data = {
                'timestamp': alert_data.get('timestamp', datetime.now().isoformat()),
                'alert_type': alert_data.get('alert_type', 'opportunity'),
                'message': alert_data.get('message', ''),
                'arbitrage_data': alert_data.get('result', {}),
                'is_opportunity': alert_data.get('alert_type') == 'opportunity'
            }
            
            # 插入告警数据
            response = self.supabase.table('alerts').insert(data).execute()
            
            if response.data:
                logger.info(f"成功保存告警记录: {alert_data.get('alert_type')}")
                return True
            else:
                logger.error("保存告警记录失败：无返回数据")
                return False
                
        except Exception as e:
            logger.error(f"保存告警记录时出错: {e}")
            return False
    
    def get_recent_checks(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """获取最近的检查记录"""
        if not self.connected or not self.supabase:
            return []
        
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            response = (self.supabase.table('arbitrage_checks')
                       .select('*')
                       .gte('timestamp', cutoff_time)
                       .order('timestamp', desc=True)
                       .limit(limit)
                       .execute())
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"查询最近检查记录时出错: {e}")
            return []
    
    def get_recent_alerts(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """获取最近的告警记录"""
        if not self.connected or not self.supabase:
            return []
        
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            response = (self.supabase.table('alerts')
                       .select('*')
                       .gte('timestamp', cutoff_time)
                       .order('timestamp', desc=True)
                       .limit(limit)
                       .execute())
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"查询最近告警记录时出错: {e}")
            return []
    
    def get_profitable_opportunities(self, days: int = 7, min_apy: float = 20.0) -> List[Dict]:
        """获取盈利机会记录"""
        if not self.connected or not self.supabase:
            return []
        
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = (self.supabase.table('arbitrage_checks')
                       .select('*')
                       .gte('timestamp', cutoff_time)
                       .eq('is_profitable', True)
                       .gte('annualized_return', min_apy)
                       .order('annualized_return', desc=True)
                       .execute())
            
            return response.data or []
            
        except Exception as e:
            logger.error(f"查询盈利机会时出错: {e}")
            return []
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """获取统计数据"""
        if not self.connected or not self.supabase:
            return {}
        
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 获取总检查次数
            total_checks_response = (self.supabase.table('arbitrage_checks')
                                   .select('id', count='exact')
                                   .gte('timestamp', cutoff_time)
                                   .execute())
            
            # 获取盈利机会次数
            profitable_response = (self.supabase.table('arbitrage_checks')
                                 .select('id', count='exact')
                                 .gte('timestamp', cutoff_time)
                                 .eq('is_profitable', True)
                                 .execute())
            
            # 获取最高年化收益率
            max_apy_response = (self.supabase.table('arbitrage_checks')
                              .select('annualized_return')
                              .gte('timestamp', cutoff_time)
                              .order('annualized_return', desc=True)
                              .limit(1)
                              .execute())
            
            # 获取平均年化收益率
            avg_apy_response = (self.supabase.rpc('avg_annualized_return', {
                'start_time': cutoff_time
            }).execute())
            
            total_checks = total_checks_response.count or 0
            profitable_count = profitable_response.count or 0
            max_apy = max_apy_response.data[0]['annualized_return'] if max_apy_response.data else 0
            avg_apy = avg_apy_response.data if avg_apy_response.data else 0
            
            return {
                'period_days': days,
                'total_checks': total_checks,
                'profitable_opportunities': profitable_count,
                'success_rate': (profitable_count / total_checks * 100) if total_checks > 0 else 0,
                'max_apy': max_apy,
                'avg_apy': avg_apy
            }
            
        except Exception as e:
            logger.error(f"获取统计数据时出错: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> bool:
        """清理旧数据"""
        if not self.connected or not self.supabase:
            return False
        
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 删除旧的检查记录
            checks_response = (self.supabase.table('arbitrage_checks')
                             .delete()
                             .lt('timestamp', cutoff_time)
                             .execute())
            
            # 删除旧的告警记录
            alerts_response = (self.supabase.table('alerts')
                             .delete()
                             .lt('timestamp', cutoff_time)
                             .execute())
            
            logger.info(f"成功清理{days}天前的旧数据")
            return True
            
        except Exception as e:
            logger.error(f"清理旧数据时出错: {e}")
            return False

# 全局数据库服务实例
db_service = DatabaseService()
