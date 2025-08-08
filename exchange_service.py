from web3 import Web3
import requests
import re
import time
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright
from config import INFURA_URL, ONEINCH_URLS, SUSDE_ABI, TokenConfig
from models import ArbitrageStep
import traceback
import asyncio
import threading

class ExchangeService:
    """交易所服务类"""
    
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(INFURA_URL))
        if not self.web3.is_connected():
            raise Exception("无法连接到以太坊节点")
    
    def clean_number_string(self, number_str: str) -> Optional[float]:
        """清理数字字符串"""
        if not number_str:
            return None
        
        try:
            number_str = re.sub(r'\s', '', number_str)
            match = re.search(r'(\d+[.,]?\d*)', number_str)
            if match:
                clean_str = match.group(1).replace(',', '.')
                return float(clean_str)
            return None
        except Exception as e:
            print(f"解析数字字符串时出错: {e}")
            return None
    
    def get_1inch_exchange_rate(self, url: str, input_amount: float) -> Optional[Dict[str, Any]]:
        """使用Playwright获取1inch兑换率"""
        try:
            print(f"获取1inch兑换率: {url}, 输入金额: {input_amount}")
            
            with sync_playwright() as p:
                # 切换回无头模式，提高性能
                browser = p.chromium.launch(headless=True, slow_mo=500)
                page = browser.new_page()
                
                # 设置更长的超时时间
                page.set_default_timeout(30000)
                
                print("正在访问页面...")
                page.goto(url, timeout=30000)
                
                # 等待页面完全加载 - 分步骤等待
                print("等待页面DOM加载...")
                page.wait_for_load_state("domcontentloaded", timeout=3000)
                
                print("等待页面网络空闲...")
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except:
                    print("网络空闲等待超时，继续...")
                    pass
                
                # 额外等待确保页面完全渲染
                print("等待页面渲染完成...")
                page.wait_for_timeout(3000)
                
                # 查找输入框 - 使用确认有效的选择器
                try:
                    print("查找输入框...")
                    
                    # 使用已确认有效的选择器
                    selector = '.token-amount-input input'
                    print(f"使用选择器: {selector}")
                    page.wait_for_selector(selector, timeout=10000)
                    elements = page.query_selector_all(selector)
                    
                    input_field = None
                    if elements:
                        # 寻找第一个可见且可编辑的输入框
                        for elem in elements:
                            is_visible = elem.is_visible()
                            is_enabled = elem.is_enabled()
                            if is_visible and is_enabled:
                                input_field = elem
                                print(f"找到可用输入框")
                                break
                    
                    if not input_field:
                        print("未找到可用输入框")
                        # 截图以便调试
                        page.screenshot(path=f"no_input_found_{input_amount}.png")
                        browser.close()
                        return None
                    
                    # 多步骤输入金额，确保成功
                    print(f"输入金额: {input_amount}")
                    
                    # 方法1: 点击并清空
                    input_field.click()
                    page.wait_for_timeout(1000)
                    
                    # 方法2: 选择所有并删除
                    is_mac = page.evaluate("() => navigator.platform.indexOf('Mac') !== -1")
                    if is_mac:
                        page.keyboard.press("Meta+A")
                    else:
                        page.keyboard.press("Control+A")
                    page.keyboard.press("Delete")
                    page.wait_for_timeout(500)
                    
                    # 方法3: 逐字符输入
                    amount_str = str(input_amount)
                    for char in amount_str:
                        page.keyboard.type(char)
                        page.wait_for_timeout(100)
                    
                    current_value = input_field.get_attribute('value')
                    print(f"输入完成，当前值: {current_value}")
                    
                    # 等待计算完成
                    print("等待计算结果...")
                    page.wait_for_timeout(3000)
                    
                    # 获取输出金额 - 借鉴Selenium成功的方法
                    output_amount = None
                    
                    # 方法1: 获取所有输入框的值，找到非输入金额的那个
                    all_inputs = page.query_selector_all('input')
                    visible_inputs = [inp for inp in all_inputs if inp.is_visible() and inp.is_enabled()]
                    print(f"找到 {len(visible_inputs)} 个可见输入框")
                    
                    for i, inp in enumerate(visible_inputs):
                        # 尝试多种方式获取值
                        value1 = inp.get_attribute("value")
                        value2 = inp.evaluate("el => el.value")
                        value3 = inp.input_value() if hasattr(inp, 'input_value') else None
                        
                        print(f"输入框 {i+1}: attribute={value1}, evaluate={value2}, input_value={value3}")
                        
                        # 选择最有效的值
                        value = value2 or value1 or value3
                        
                        if value and value != "0" and value != "":
                            # 清理数字字符串进行比较
                            clean_value = re.sub(r'[^\d.]', '', str(value))  # 移除空格和其他字符
                            clean_input = str(input_amount)
                            
                            # 如果清理后的值不等于输入金额，则可能是输出金额
                            if clean_value != clean_input:
                                try:
                                    # 检查是否是合理的输出金额
                                    num_value = float(clean_value)
                                    # 根据您的输出，1000.231745 vs 1000 的比例是合理的
                                    if 0.1 <= num_value / float(input_amount) <= 2.0:
                                        output_amount = clean_value
                                        print(f"✅ 从输入框 {i+1} 获取输出金额: {output_amount} (原始值: {value})")
                                        break
                                except Exception as e:
                                    print(f"解析输入框 {i+1} 值时出错: {e}")
                                    continue
                    
                    # 方法2: 如果输入框方法失败，使用JavaScript扫描页面
                    if not output_amount:
                        print("尝试JavaScript方法获取输出金额...")
                        try:
                            # 借鉴Selenium的JavaScript方法，寻找包含大数字的元素
                            result_numbers = page.evaluate("""
                                () => {
                                    const elements = Array.from(document.querySelectorAll('*'));
                                    const candidates = [];
                                    
                                    elements.forEach(el => {
                                        if (!el.offsetParent) return; // 跳过不可见元素
                                        
                                        const text = el.textContent || el.innerText || '';
                                        const value = el.value || '';
                                        
                                        // 检查文本内容和输入值
                                        [text, value].forEach(content => {
                                            if (!content) return;
                                            
                                            // 匹配类似 842.062532 的数字格式
                                            const matches = content.match(/\\b\\d{1,4}\\.\\d{6}\\b/g);
                                            if (matches) {
                                                matches.forEach(match => {
                                                    const num = parseFloat(match);
                                                    if (num > 100 && num < 10000) { // 合理范围
                                                        candidates.push(match);
                                                    }
                                                });
                                            }
                                            
                                            // 也匹配较短的小数
                                            const shortMatches = content.match(/\\b\\d{2,4}\\.\\d{1,6}\\b/g);
                                            if (shortMatches) {
                                                shortMatches.forEach(match => {
                                                    const num = parseFloat(match);
                                                    if (num > 100 && num < 10000 && num !== """ + str(input_amount) + """) {
                                                        candidates.push(match);
                                                    }
                                                });
                                            }
                                        });
                                    });
                                    
                                    return candidates;
                                }
                            """)
                            
                            if result_numbers:
                                # 选择最可能的输出金额（最长或最精确的）
                                best_candidate = max(result_numbers, key=lambda x: len(x.split('.')[-1]) if '.' in x else 0)
                                output_amount = best_candidate
                                print(f"✅ JavaScript方法找到输出金额: {output_amount}")
                        
                        except Exception as e:
                            print(f"JavaScript方法失败: {e}")
                    
                    # 方法3: 最后手段 - 触发输入事件重新计算
                    if not output_amount:
                        print("尝试重新触发计算...")
                        try:
                            # 重新点击输入框并触发输入事件
                            input_field.click()
                            page.keyboard.press('End')  # 移动到末尾
                            page.keyboard.press('Backspace')  # 删除最后一个字符
                            page.keyboard.type('0')  # 重新输入
                            page.wait_for_timeout(3000)  # 等待重新计算
                            
                            # 再次尝试获取输出
                            for i, inp in enumerate(visible_inputs):
                                value = inp.evaluate("el => el.value")
                                if value and value != str(input_amount) and value != "0":
                                    try:
                                        num_value = float(value.replace(',', ''))
                                        if 100 <= num_value <= 2000:  # 基于您截图的合理范围
                                            output_amount = value
                                            print(f"✅ 重新计算后获取输出金额: {output_amount}")
                                            break
                                    except:
                                        continue
                        except Exception as e:
                            print(f"重新触发计算失败: {e}")
                    
                    # 方法3: 截图并手动检查（调试用）
                    if not output_amount:
                        print("截图保存，便于调试...")
                        page.screenshot(path=f"debug_1inch_{input_amount}.png")
                        print("未能自动获取输出金额，请检查截图")
                        browser.close()
                        return None
                    
                    numeric_output = self.clean_number_string(output_amount)
                    if numeric_output is None:
                        print(f"无法解析输出金额: {output_amount}")
                        browser.close()
                        return None
                    
                    # 合理性检查
                    rate = numeric_output / float(input_amount)
                    if rate > 5 or rate < 0.1:  # 汇率不应该超过5倍或小于0.1倍
                        print(f"汇率异常: {rate}, 输入: {input_amount}, 输出: {numeric_output}")
                        browser.close()
                        return None
                    
                    print(f"解析成功 - 输入: {input_amount}, 输出: {numeric_output}, 汇率: {rate}")
                    browser.close()
                    
                    return {
                        'input_amount': float(input_amount),
                        'output_amount': numeric_output,
                        'exchange_rate': rate
                    }
                
                except Exception as e:
                    print(f"操作页面时出错: {e}")
                    page.screenshot(path=f"error_1inch_{input_amount}.png")
                    browser.close()
                    return None
        
        except Exception as e:
            print(f"获取1inch兑换率失败: {e}")
            return None
    
    def get_usdt_to_susde(self, usdt_amount: float) -> Optional[ArbitrageStep]:
        """USDT转换为SUSDE"""
        result = self.get_1inch_exchange_rate(ONEINCH_URLS['USDT_TO_SUSDE'], usdt_amount)
        if not result:
            return None
        
        price_impact = -0.05  # 估算价格影响
        
        return ArbitrageStep(
            step_number=1,
            from_token="USDT",
            to_token="SUSDE", 
            input_amount=usdt_amount,
            output_amount=result['output_amount'],
            price_impact=price_impact,
            route="Uniswap V3"
        )
    
    def get_susde_to_usde(self, susde_amount: float) -> Optional[ArbitrageStep]:
        """SUSDE解质押为USDE"""
        try:
            # 获取合约实例
            susde_contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(TokenConfig.SUSDE['address']),
                abi=SUSDE_ABI
            )
            
            # 将金额转换为wei
            shares_amount_in_wei = self.web3.to_wei(susde_amount, 'ether')
            
            # 调用预览赎回方法
            assets_amount = susde_contract.functions.previewRedeem(shares_amount_in_wei).call()
            
            # 转换回USDE单位
            usde_amount = self.web3.from_wei(assets_amount, 'ether')
            
            return ArbitrageStep(
                step_number=2,
                from_token="SUSDE",
                to_token="USDE",
                input_amount=susde_amount,
                output_amount=float(usde_amount),
                price_impact=0.0,  # 解质押无价格影响
                route="解质押"
            )
        
        except Exception as e:
            print(f"获取SUSDE解质押失败: {e}")
            return None
    
    def get_usde_to_usdt(self, usde_amount: float) -> Optional[ArbitrageStep]:
        """USDE转换为USDT"""
        result = self.get_1inch_exchange_rate(ONEINCH_URLS['USDE_TO_USDT'], usde_amount)
        if not result:
            return None
        
        price_impact = -0.03  # 估算价格影响
        
        return ArbitrageStep(
            step_number=3,
            from_token="USDE",
            to_token="USDT",
            input_amount=usde_amount,
            output_amount=result['output_amount'],
            price_impact=price_impact,
            route="Uniswap V3"
        )
