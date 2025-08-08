#!/usr/bin/env python3
"""
SusDE套利监控后端服务

提供HTTP API接口和定期监控任务
"""

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import threading
import logging
import os
import json
from typing import Dict, List, Optional

from arbitrage_calculator import ArbitrageCalculator
from models import ArbitrageResult
from config import PORT, CHECK_INTERVAL_HOURS, ALERT_THRESHOLD

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 全局变量
calculator = ArbitrageCalculator()
scheduler = BackgroundScheduler()
monitoring_enabled = False
last_check_time = None
last_result = None
alert_history = []
monitoring_config = {
    'cron_expression': '0 * * * *',  # 默认每小时检查一次
    'alert_threshold': ALERT_THRESHOLD,  # 年化收益率阈值
    'amount': 100000  # 默认检查金额
}

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alert_threshold = ALERT_THRESHOLD
        self.alert_history = []
        self.max_history = 100
    
    def check_alert_condition(self, result: ArbitrageResult) -> bool:
        """检查是否满足告警条件"""
        return (result.is_profitable and 
                result.annualized_return >= self.alert_threshold)
    
    def add_alert(self, result: ArbitrageResult, message: str):
        """添加告警记录"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'result': result.to_dict(),
            'message': message,
            'alert_type': 'opportunity' if result.is_profitable else 'check'
        }
        
        self.alert_history.append(alert)
        
        # 保持历史记录在合理大小
        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)
        
        logger.info(f"告警: {message}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """获取最近的告警记录"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        return [alert for alert in self.alert_history 
                if alert['timestamp'] >= cutoff_str]

alert_manager = AlertManager()

def perform_arbitrage_check():
    """执行套利检查"""
    global last_check_time, last_result
    
    try:
        logger.info("开始定期套利检查")
        last_check_time = datetime.now()
        
        # 计算套利机会
        result = calculator.calculate_arbitrage(monitoring_config['amount'])
        last_result = result
        
        if result:
            # 检查是否需要告警
            if alert_manager.check_alert_condition(result):
                message = (f"🚀 发现套利机会!\n"
                          f"年化收益率: {result.annualized_return:.2f}%\n"
                          f"预期利润: {result.profit_loss:.2f} USDT")
                alert_manager.add_alert(result, message)
            else:
                message = f"定期检查完成，年化收益率: {result.annualized_return:.2f}%"
                alert_manager.add_alert(result, message)
            
            logger.info(f"套利检查完成 - 年化收益率: {result.annualized_return:.2f}%")
        else:
            message = "套利检查失败"
            logger.error(message)
    
    except Exception as e:
        logger.error(f"定期检查时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

# API路由定义

@app.route("/", methods=["GET"])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "SusDE Arbitrage Monitor API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "monitoring_enabled": monitoring_enabled,
        "endpoints": {
            "/": "健康检查",
            "/arbitrage/check": "手动检查套利机会",
            "/arbitrage/status": "获取监控状态",
            "/monitoring/start": "启动定期监控",
            "/monitoring/stop": "停止定期监控", 
            "/monitoring/config": "配置监控参数",
            "/alerts/recent": "获取最近告警",
            "/alerts/history": "获取告警历史"
        }
    })

@app.route("/arbitrage/check", methods=["GET", "POST"])
def manual_check():
    """手动检查套利机会"""
    try:
        # 获取参数
        if request.method == "POST":
            data = request.get_json() or {}
            amount = data.get("amount", 100000)
        else:
            amount = request.args.get("amount", 100000, type=float)
        
        logger.info(f"手动检查套利机会，金额: {amount}")
        
        # 计算套利
        result = calculator.calculate_arbitrage(amount)
        
        if result:
            # 添加到历史记录
            message = f"手动检查 - 年化收益率: {result.annualized_return:.2f}%"
            alert_manager.add_alert(result, message)
            
            return jsonify({
                "success": True,
                "data": result.to_dict(),
                "message": result.format_telegram_message(),
                "is_opportunity": alert_manager.check_alert_condition(result)
            })
        else:
            return jsonify({
                "success": False,
                "error": "无法计算套利机会"
            }), 500
    
    except Exception as e:
        logger.error(f"手动检查失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/arbitrage/status", methods=["GET"])
def get_status():
    """获取监控状态"""
    global last_check_time, last_result
    
    status = {
        "monitoring_enabled": monitoring_enabled,
        "cron_expression": monitoring_config['cron_expression'],
        "alert_threshold": monitoring_config['alert_threshold'],
        "check_amount": monitoring_config['amount'],
        "last_check_time": last_check_time.isoformat() if last_check_time else None,
        "last_result": last_result.to_dict() if last_result else None,
        "recent_alerts_count": len(alert_manager.get_recent_alerts(24)),
        "scheduler_running": scheduler.running if hasattr(scheduler, 'running') else False
    }
    
    return jsonify(status)

@app.route("/monitoring/start", methods=["POST"])
def start_monitoring():
    """启动定期监控"""
    global monitoring_enabled
    
    try:
        data = request.get_json() or {}
        
        # 更新配置
        if 'cron_expression' in data:
            monitoring_config['cron_expression'] = data['cron_expression']
        if 'alert_threshold' in data:
            monitoring_config['alert_threshold'] = float(data['alert_threshold'])
        if 'amount' in data:
            monitoring_config['amount'] = float(data['amount'])
        
        # 移除现有任务
        if scheduler.get_jobs():
            scheduler.remove_all_jobs()
        
        # 添加新任务
        scheduler.add_job(
            func=perform_arbitrage_check,
            trigger=CronTrigger.from_crontab(monitoring_config['cron_expression']),
            id='arbitrage_monitor',
            name='SusDE Arbitrage Monitor',
            replace_existing=True
        )
        
        if not scheduler.running:
            scheduler.start()
        
        monitoring_enabled = True
        
        logger.info(f"定期监控已启动 - Cron: {monitoring_config['cron_expression']}")
        
        return jsonify({
            "success": True,
            "message": "定期监控已启动",
            "config": monitoring_config
        })
    
    except Exception as e:
        logger.error(f"启动监控失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/monitoring/stop", methods=["POST"])
def stop_monitoring():
    """停止定期监控"""
    global monitoring_enabled
    
    try:
        if scheduler.get_jobs():
            scheduler.remove_all_jobs()
        
        monitoring_enabled = False
        
        logger.info("定期监控已停止")
        
        return jsonify({
            "success": True,
            "message": "定期监控已停止"
        })
    
    except Exception as e:
        logger.error(f"停止监控失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/monitoring/config", methods=["GET", "POST"])
def monitoring_config_endpoint():
    """获取或更新监控配置"""
    global monitoring_config
    
    if request.method == "GET":
        return jsonify({
            "success": True,
            "config": monitoring_config,
            "cron_examples": {
                "每分钟": "* * * * *",
                "每小时": "0 * * * *", 
                "每天9点": "0 9 * * *",
                "工作日9点": "0 9 * * 1-5",
                "每30分钟": "*/30 * * * *"
            }
        })
    
    try:
        data = request.get_json()
        
        # 验证cron表达式
        if 'cron_expression' in data:
            CronTrigger.from_crontab(data['cron_expression'])  # 验证有效性
            monitoring_config['cron_expression'] = data['cron_expression']
        
        if 'alert_threshold' in data:
            monitoring_config['alert_threshold'] = float(data['alert_threshold'])
        
        if 'amount' in data:
            monitoring_config['amount'] = float(data['amount'])
        
        # 更新告警管理器阈值
        alert_manager.alert_threshold = monitoring_config['alert_threshold']
        
        return jsonify({
            "success": True,
            "message": "配置已更新",
            "config": monitoring_config
        })
    
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route("/alerts/recent", methods=["GET"])
def get_recent_alerts():
    """获取最近的告警"""
    hours = request.args.get("hours", 24, type=int)
    alerts = alert_manager.get_recent_alerts(hours)
    
    return jsonify({
        "success": True,
        "alerts": alerts,
        "count": len(alerts),
        "hours": hours
    })

@app.route("/alerts/history", methods=["GET"])
def get_alert_history():
    """获取告警历史"""
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    alerts = alert_manager.alert_history[start_idx:end_idx]
    
    return jsonify({
        "success": True,
        "alerts": alerts,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(alert_manager.alert_history),
            "has_more": end_idx < len(alert_manager.alert_history)
        }
    })

@app.route("/alerts/clear", methods=["POST"])
def clear_alerts():
    """清空告警历史"""
    alert_manager.alert_history.clear()
    
    return jsonify({
        "success": True,
        "message": "告警历史已清空"
    })

if __name__ == "__main__":
    logger.info("启动SusDE套利监控后端服务")
    
    # 启动调度器
    scheduler.start()
    logger.info("任务调度器已启动")
    
    # 启动Flask应用
    port = int(os.environ.get("PORT", PORT))
    app.run(host="0.0.0.0", port=port, debug=False)
