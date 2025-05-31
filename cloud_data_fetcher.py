#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货持仓分析系统 - 云端数据获取模块
专门解决Streamlit Cloud环境下的数据获取问题
作者：7haoge
邮箱：953534947@qq.com
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

class CloudDataFetcher:
    """云端数据获取器 - 专门处理云端环境的数据获取问题"""
    
    def __init__(self):
        self.session = self.create_session()
        self.max_retries = 3
        self.timeout = 30
        self.delay_between_requests = 2  # 请求间隔
        
    def create_session(self):
        """创建优化的请求会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        return session
    
    def safe_akshare_call(self, func, *args, **kwargs):
        """安全的akshare调用，包含重试机制和超时控制"""
        for attempt in range(self.max_retries):
            try:
                # 添加延迟避免请求过快
                if attempt > 0:
                    time.sleep(self.delay_between_requests * attempt)
                
                # 使用更短的超时时间，特别是对于广期所
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("请求超时")
                
                # 设置超时信号（仅在非Windows系统）
                try:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(20)  # 20秒超时
                except:
                    pass  # Windows系统不支持SIGALRM
                
                result = func(*args, **kwargs)
                
                # 取消超时信号
                try:
                    signal.alarm(0)
                except:
                    pass
                
                if result is not None:
                    return result
                    
            except TimeoutError:
                st.warning(f"请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    st.error("多次超时，跳过此数据源")
                continue
                
            except Exception as e:
                error_msg = str(e)
                if attempt == self.max_retries - 1:
                    st.warning(f"数据获取失败 (尝试 {attempt + 1}/{self.max_retries}): {error_msg}")
                else:
                    st.info(f"重试中... (尝试 {attempt + 1}/{self.max_retries})")
                
                # 特定错误的处理
                if "timeout" in error_msg.lower():
                    time.sleep(5)  # 超时错误等待更长时间
                elif "rate limit" in error_msg.lower():
                    time.sleep(10)  # 频率限制等待更长时间
                elif "connection" in error_msg.lower():
                    time.sleep(3)  # 连接错误等待
                    
        return None
    
    def fetch_position_data_with_fallback(self, trade_date: str, progress_callback=None) -> bool:
        """获取持仓数据，包含备用方案"""
        
        # 尝试导入akshare
        try:
            import akshare as ak
        except ImportError:
            st.error("akshare未安装，请联系管理员")
            return False
        
        success_count = 0
        total_exchanges = 5
        
        # 交易所配置 - 按成功率排序，广期所放在最后
        exchanges = [
            {
                "name": "大商所",
                "func": ak.futures_dce_position_rank,
                "filename": "大商所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "中金所", 
                "func": ak.get_cffex_rank_table,
                "filename": "中金所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "郑商所",
                "func": ak.get_czce_rank_table,
                "filename": "郑商所持仓.xlsx", 
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "上期所",
                "func": ak.get_shfe_rank_table,
                "filename": "上期所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "广期所",
                "func": ak.futures_gfex_position_rank,
                "filename": "广期所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 15  # 广期所使用更短的超时时间
            }
        ]
        
        # 确保数据目录存在
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        for i, exchange in enumerate(exchanges):
            if progress_callback:
                progress = i / total_exchanges * 0.6
                progress_callback(f"正在获取 {exchange['name']} 数据...", progress)
            
            try:
                st.info(f"🔄 正在获取 {exchange['name']} 数据...")
                
                # 特殊处理广期所
                if exchange['name'] == '广期所':
                    st.warning("⚠️ 广期所数据获取可能较慢，正在尝试...")
                    
                    # 使用更短的超时和更少的重试次数
                    original_retries = self.max_retries
                    self.max_retries = 2  # 广期所只重试2次
                
                # 使用安全调用
                start_time = time.time()
                data_dict = self.safe_akshare_call(exchange['func'], **exchange['args'])
                end_time = time.time()
                
                # 恢复原始重试次数
                if exchange['name'] == '广期所':
                    self.max_retries = original_retries
                
                if data_dict:
                    # 保存数据
                    save_path = os.path.join(data_dir, exchange['filename'])
                    with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                        for sheet_name, df in data_dict.items():
                            # 清理sheet名称
                            clean_name = sheet_name[:31].replace("/", "-").replace("*", "")
                            df.to_excel(writer, sheet_name=clean_name, index=False)
                    
                    st.success(f"✅ {exchange['name']} 数据获取成功 (耗时: {end_time - start_time:.1f}秒)")
                    success_count += 1
                else:
                    if exchange['name'] == '广期所':
                        st.warning(f"⚠️ {exchange['name']} 数据获取失败（云端环境限制），但不影响分析")
                    else:
                        st.warning(f"⚠️ {exchange['name']} 数据获取失败，但不影响其他交易所")
                    
            except Exception as e:
                error_msg = str(e)
                if exchange['name'] == '广期所':
                    st.warning(f"⚠️ {exchange['name']} 数据获取失败（云端环境限制）: {error_msg}")
                else:
                    st.warning(f"⚠️ {exchange['name']} 数据获取失败: {error_msg}")
                continue
            
            # 添加请求间隔，广期所后等待更长时间
            if exchange['name'] == '广期所':
                time.sleep(self.delay_between_requests * 2)
            else:
                time.sleep(self.delay_between_requests)
        
        if progress_callback:
            progress_callback("持仓数据获取完成", 0.6)
        
        # 如果至少有3个交易所成功，就认为成功
        if success_count >= 3:
            st.info(f"✅ 成功获取 {success_count}/{total_exchanges} 个交易所数据，可以进行分析")
            return True
        elif success_count > 0:
            st.warning(f"⚠️ 仅获取到 {success_count}/{total_exchanges} 个交易所数据，分析结果可能不完整")
            return True
        else:
            st.error("❌ 所有交易所数据获取失败")
            return False
    
    def fetch_price_data_with_fallback(self, trade_date: str, progress_callback=None) -> pd.DataFrame:
        """获取期货行情数据，包含智能自动跳过功能"""
        
        try:
            import akshare as ak
        except ImportError:
            st.error("akshare未安装，请联系管理员")
            return pd.DataFrame()
        
        # 行情数据交易所配置 - 包含所有交易所，增强超时处理
        price_exchanges = [
            {"market": "DCE", "name": "大商所", "timeout": 30},
            {"market": "CFFEX", "name": "中金所", "timeout": 30},
            {"market": "CZCE", "name": "郑商所", "timeout": 30},
            {"market": "SHFE", "name": "上期所", "timeout": 30},
            {"market": "GFEX", "name": "广期所", "timeout": 15},  # 广期所使用更短超时，遇到问题自动跳过
        ]
        
        all_data = []
        success_count = 0
        
        for i, exchange in enumerate(price_exchanges):
            if progress_callback:
                progress = 0.6 + (i / len(price_exchanges)) * 0.2
                progress_callback(f"正在获取 {exchange['name']} 行情数据...", progress)
            
            try:
                st.info(f"🔄 正在获取 {exchange['name']} 行情数据...")
                
                # 记录开始时间
                start_time = time.time()
                
                # 对广期所使用增强的超时控制
                if exchange['name'] == '广期所':
                    st.info("⚠️ 广期所数据获取中，如遇问题将自动跳过...")
                    
                    try:
                        # 使用线程和严格超时控制
                        import threading
                        import queue
                        
                        result_queue = queue.Queue()
                        
                        def fetch_gfex_data():
                            try:
                                result = self.safe_akshare_call(
                                    ak.get_futures_daily,
                                    start_date=trade_date,
                                    end_date=trade_date,
                                    market=exchange["market"]
                                )
                                result_queue.put(('success', result))
                            except Exception as e:
                                result_queue.put(('error', str(e)))
                        
                        # 启动获取线程
                        fetch_thread = threading.Thread(target=fetch_gfex_data)
                        fetch_thread.daemon = True
                        fetch_thread.start()
                        
                        # 等待结果，使用配置的超时时间
                        fetch_thread.join(timeout=exchange.get('timeout', 15))
                        
                        if fetch_thread.is_alive():
                            # 超时了，自动跳过
                            st.warning(f"⚠️ {exchange['name']} 数据获取超时({exchange.get('timeout', 15)}秒)，自动跳过")
                            continue
                        
                        # 获取结果
                        try:
                            status, df = result_queue.get_nowait()
                            if status == 'error':
                                raise Exception(df)
                        except queue.Empty:
                            st.warning(f"⚠️ {exchange['name']} 数据获取无响应，自动跳过")
                            continue
                            
                    except Exception as e:
                        st.warning(f"⚠️ {exchange['name']} 数据获取失败，自动跳过: {str(e)}")
                        continue
                else:
                    # 其他交易所使用标准获取方式
                    df = self.safe_akshare_call(
                        ak.get_futures_daily,
                        start_date=trade_date,
                        end_date=trade_date,
                        market=exchange["market"]
                    )
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                if df is not None and not df.empty:
                    df['exchange'] = exchange["name"]
                    all_data.append(df)
                    st.success(f"✅ {exchange['name']} 行情数据获取成功 (耗时: {elapsed_time:.1f}秒)")
                    success_count += 1
                else:
                    st.warning(f"⚠️ {exchange['name']} 行情数据为空，跳过")
                    
            except Exception as e:
                error_msg = str(e)
                elapsed_time = time.time() - start_time if 'start_time' in locals() else 0
                st.warning(f"⚠️ {exchange['name']} 行情数据获取失败，跳过: {error_msg}")
                continue
            
            # 添加请求间隔
            time.sleep(self.delay_between_requests)
        
        if progress_callback:
            progress_callback("行情数据获取完成", 0.8)
        
        # 显示获取结果统计
        total_exchanges = len(price_exchanges)
        if success_count >= 3:
            st.info(f"✅ 成功获取 {success_count}/{total_exchanges} 个交易所行情数据")
        elif success_count > 0:
            st.warning(f"⚠️ 仅获取到 {success_count}/{total_exchanges} 个交易所行情数据")
        else:
            st.warning("⚠️ 未能获取到任何行情数据，将使用基础分析")
        
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    
    def create_demo_data(self, trade_date: str) -> bool:
        """创建演示数据（当所有数据源都失败时）"""
        st.warning("⚠️ 所有数据源都无法访问，正在创建演示数据...")
        
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        # 创建演示持仓数据
        demo_contracts = ['螺纹钢2501', '铁矿石2501', '豆粕2501', '玉米2501', '白糖2501']
        
        for exchange_name in ['大商所', '中金所', '郑商所', '上期所', '广期所']:
            filename = f"{exchange_name}持仓.xlsx"
            save_path = os.path.join(data_dir, filename)
            
            # 创建演示数据
            demo_data = {}
            for contract in demo_contracts:
                # 生成随机但合理的持仓数据
                np.random.seed(hash(contract + trade_date) % 2**32)
                
                data = []
                for i in range(20):  # 前20名
                    data.append({
                        'long_party_name': f'期货公司{i+1}',
                        'long_open_interest': np.random.randint(1000, 50000),
                        'long_open_interest_chg': np.random.randint(-5000, 5000),
                        'short_party_name': f'期货公司{i+1}',
                        'short_open_interest': np.random.randint(1000, 50000),
                        'short_open_interest_chg': np.random.randint(-5000, 5000),
                    })
                
                demo_data[contract] = pd.DataFrame(data)
            
            # 保存演示数据
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                for sheet_name, df in demo_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        st.info("✅ 演示数据创建完成，您可以体验系统功能")
        return True
    
    def diagnose_network_issues(self):
        """诊断网络问题"""
        st.subheader("🔍 网络诊断")
        
        # 测试基本网络连接
        test_urls = [
            ("百度", "https://www.baidu.com"),
            ("新浪", "https://www.sina.com.cn"),
            ("akshare官网", "https://akshare.akfamily.xyz")
        ]
        
        for name, url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    st.success(f"✅ {name} 连接正常")
                else:
                    st.warning(f"⚠️ {name} 连接异常 (状态码: {response.status_code})")
            except Exception as e:
                st.error(f"❌ {name} 连接失败: {str(e)}")
        
        # 测试akshare导入
        try:
            import akshare as ak
            st.success(f"✅ akshare 导入成功 (版本: {getattr(ak, '__version__', '未知')})")
        except ImportError:
            st.error("❌ akshare 导入失败")
        
        # 提供解决建议
        st.markdown("""
        ### 💡 解决建议
        
        如果数据获取失败，可能的原因和解决方案：
        
        1. **网络限制**: Streamlit Cloud可能限制某些外部API访问
           - 解决方案: 使用演示数据体验功能
        
        2. **API频率限制**: akshare的数据源可能有访问频率限制
           - 解决方案: 等待几分钟后重试
        
        3. **数据源维护**: 交易所数据源可能在维护
           - 解决方案: 选择其他交易日期
        
        4. **云端环境限制**: 某些云端环境对外部请求有限制
           - 解决方案: 本地运行或使用演示模式
        """)

    def fetch_position_data_skip_gfex(self, trade_date: str, progress_callback=None) -> bool:
        """获取持仓数据，跳过广期所（云端环境专用）"""
        
        # 尝试导入akshare
        try:
            import akshare as ak
        except ImportError:
            st.error("akshare未安装，请联系管理员")
            return False
        
        success_count = 0
        total_exchanges = 4  # 不包含广期所
        
        # 交易所配置 - 不包含广期所
        exchanges = [
            {
                "name": "大商所",
                "func": ak.futures_dce_position_rank,
                "filename": "大商所持仓.xlsx",
                "args": {"date": trade_date}
            },
            {
                "name": "中金所", 
                "func": ak.get_cffex_rank_table,
                "filename": "中金所持仓.xlsx",
                "args": {"date": trade_date}
            },
            {
                "name": "郑商所",
                "func": ak.get_czce_rank_table,
                "filename": "郑商所持仓.xlsx", 
                "args": {"date": trade_date}
            },
            {
                "name": "上期所",
                "func": ak.get_shfe_rank_table,
                "filename": "上期所持仓.xlsx",
                "args": {"date": trade_date}
            }
        ]
        
        # 确保数据目录存在
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        st.info("🚀 使用快速模式：跳过广期所数据获取")
        
        for i, exchange in enumerate(exchanges):
            if progress_callback:
                progress = i / total_exchanges * 0.6
                progress_callback(f"正在获取 {exchange['name']} 数据...", progress)
            
            try:
                st.info(f"🔄 正在获取 {exchange['name']} 数据...")
                
                # 使用安全调用
                start_time = time.time()
                data_dict = self.safe_akshare_call(exchange['func'], **exchange['args'])
                end_time = time.time()
                
                if data_dict:
                    # 保存数据
                    save_path = os.path.join(data_dir, exchange['filename'])
                    with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                        for sheet_name, df in data_dict.items():
                            # 清理sheet名称
                            clean_name = sheet_name[:31].replace("/", "-").replace("*", "")
                            df.to_excel(writer, sheet_name=clean_name, index=False)
                    
                    st.success(f"✅ {exchange['name']} 数据获取成功 (耗时: {end_time - start_time:.1f}秒)")
                    success_count += 1
                else:
                    st.warning(f"⚠️ {exchange['name']} 数据获取失败，但不影响其他交易所")
                    
            except Exception as e:
                st.warning(f"⚠️ {exchange['name']} 数据获取失败: {str(e)}")
                continue
            
            # 添加请求间隔
            time.sleep(self.delay_between_requests)
        
        # 创建空的广期所文件以保持兼容性
        gfex_path = os.path.join(data_dir, "广期所持仓.xlsx")
        empty_data = {'空数据': pd.DataFrame({'说明': ['广期所数据已跳过']})}
        with pd.ExcelWriter(gfex_path, engine='openpyxl') as writer:
            for sheet_name, df in empty_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        if progress_callback:
            progress_callback("持仓数据获取完成（已跳过广期所）", 0.6)
        
        if success_count >= 3:
            st.success(f"✅ 成功获取 {success_count}/{total_exchanges} 个主要交易所数据（已跳过广期所）")
            return True
        elif success_count > 0:
            st.warning(f"⚠️ 仅获取到 {success_count}/{total_exchanges} 个交易所数据")
            return True
        else:
            st.error("❌ 所有交易所数据获取失败")
            return False

    def fetch_position_data_with_auto_skip(self, trade_date: str, progress_callback=None) -> bool:
        """获取持仓数据，自动跳过超时的交易所"""
        
        # 尝试导入akshare
        try:
            import akshare as ak
        except ImportError:
            st.error("akshare未安装，请联系管理员")
            return False
        
        success_count = 0
        total_exchanges = 5
        
        # 交易所配置 - 广期所设置更短的超时时间
        exchanges = [
            {
                "name": "大商所",
                "func": ak.futures_dce_position_rank,
                "filename": "大商所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "中金所", 
                "func": ak.get_cffex_rank_table,
                "filename": "中金所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "郑商所",
                "func": ak.get_czce_rank_table,
                "filename": "郑商所持仓.xlsx", 
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "上期所",
                "func": ak.get_shfe_rank_table,
                "filename": "上期所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 30
            },
            {
                "name": "广期所",
                "func": ak.futures_gfex_position_rank,
                "filename": "广期所持仓.xlsx",
                "args": {"date": trade_date},
                "timeout": 20  # 广期所使用更短的超时时间
            }
        ]
        
        # 确保数据目录存在
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        
        for i, exchange in enumerate(exchanges):
            if progress_callback:
                progress = i / total_exchanges * 0.6
                progress_callback(f"正在获取 {exchange['name']} 数据...", progress)
            
            try:
                st.info(f"🔄 正在获取 {exchange['name']} 数据...")
                
                # 记录开始时间
                start_time = time.time()
                
                # 特殊处理广期所 - 使用更严格的超时控制
                if exchange['name'] == '广期所':
                    st.info("⚠️ 广期所数据获取中，如超时将自动跳过...")
                    
                    # 使用更短的超时和更少的重试次数
                    original_retries = self.max_retries
                    self.max_retries = 1  # 广期所只尝试1次
                    
                    try:
                        # 使用线程和超时控制
                        import threading
                        import queue
                        
                        result_queue = queue.Queue()
                        
                        def fetch_data():
                            try:
                                result = self.safe_akshare_call(exchange['func'], **exchange['args'])
                                result_queue.put(('success', result))
                            except Exception as e:
                                result_queue.put(('error', str(e)))
                        
                        # 启动获取线程
                        fetch_thread = threading.Thread(target=fetch_data)
                        fetch_thread.daemon = True
                        fetch_thread.start()
                        
                        # 等待结果，最多等待20秒
                        fetch_thread.join(timeout=20)
                        
                        if fetch_thread.is_alive():
                            # 超时了，自动跳过
                            st.warning("⚠️ 广期所数据获取超时，自动跳过以避免卡顿")
                            self.max_retries = original_retries
                            
                            # 创建空的广期所文件以保持兼容性
                            gfex_path = os.path.join(data_dir, exchange['filename'])
                            empty_data = {'跳过说明': pd.DataFrame({'说明': ['广期所数据获取超时，已自动跳过']})}
                            with pd.ExcelWriter(gfex_path, engine='openpyxl') as writer:
                                for sheet_name, df in empty_data.items():
                                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                            
                            continue
                        
                        # 获取结果
                        try:
                            status, data_dict = result_queue.get_nowait()
                            if status == 'error':
                                raise Exception(data_dict)
                        except queue.Empty:
                            st.warning("⚠️ 广期所数据获取无响应，自动跳过")
                            self.max_retries = original_retries
                            continue
                            
                    finally:
                        self.max_retries = original_retries
                else:
                    # 其他交易所使用正常的获取方式
                    data_dict = self.safe_akshare_call(exchange['func'], **exchange['args'])
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                if data_dict:
                    # 保存数据
                    save_path = os.path.join(data_dir, exchange['filename'])
                    with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                        for sheet_name, df in data_dict.items():
                            # 清理sheet名称
                            clean_name = sheet_name[:31].replace("/", "-").replace("*", "")
                            df.to_excel(writer, sheet_name=clean_name, index=False)
                    
                    st.success(f"✅ {exchange['name']} 数据获取成功 (耗时: {elapsed_time:.1f}秒)")
                    success_count += 1
                else:
                    if exchange['name'] == '广期所':
                        st.warning(f"⚠️ {exchange['name']} 数据获取失败，已自动跳过")
                    else:
                        st.warning(f"⚠️ {exchange['name']} 数据获取失败，但不影响其他交易所")
                    
            except Exception as e:
                error_msg = str(e)
                elapsed_time = time.time() - start_time
                
                if exchange['name'] == '广期所':
                    st.warning(f"⚠️ {exchange['name']} 数据获取失败，已自动跳过: {error_msg}")
                    
                    # 创建空的广期所文件
                    gfex_path = os.path.join(data_dir, exchange['filename'])
                    empty_data = {'跳过说明': pd.DataFrame({'说明': [f'广期所数据获取失败: {error_msg}']})}
                    with pd.ExcelWriter(gfex_path, engine='openpyxl') as writer:
                        for sheet_name, df in empty_data.items():
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    st.warning(f"⚠️ {exchange['name']} 数据获取失败: {error_msg}")
                continue
            
            # 添加请求间隔
            time.sleep(self.delay_between_requests)
        
        if progress_callback:
            progress_callback("持仓数据获取完成", 0.6)
        
        # 如果至少有3个交易所成功，就认为成功
        if success_count >= 3:
            st.info(f"✅ 成功获取 {success_count}/{total_exchanges} 个交易所数据，可以进行分析")
            return True
        elif success_count > 0:
            st.warning(f"⚠️ 仅获取到 {success_count}/{total_exchanges} 个交易所数据，分析结果可能不完整")
            return True
        else:
            st.error("❌ 所有交易所数据获取失败")
            return False

# 全局实例
cloud_fetcher = CloudDataFetcher() 