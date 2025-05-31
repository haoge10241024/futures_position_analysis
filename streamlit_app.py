#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货持仓分析系统 - Streamlit Web应用
全新改进版本，整合所有功能，包含性能优化
作者：7haoge
邮箱：953534947@qq.com
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import io
import time
import os
from datetime import datetime, timedelta
from futures_analyzer import FuturesAnalysisEngine, validate_trade_date, get_recent_trade_date
from config import STRATEGY_CONFIG, SYSTEM_CONFIG

# 导入性能优化模块
try:
    from performance_optimizer import optimize_streamlit_performance, show_performance_metrics, FastDataManager
    PERFORMANCE_OPTIMIZATION_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZATION_AVAILABLE = False
    st.warning("性能优化模块未找到，将使用标准模式")

# 导入云端数据获取器
try:
    from cloud_data_fetcher import cloud_fetcher
    CLOUD_FETCHER_AVAILABLE = True
except ImportError:
    CLOUD_FETCHER_AVAILABLE = False
    st.warning("云端数据获取器未找到，将使用标准模式")

# 页面配置
st.set_page_config(
    page_title=f"{SYSTEM_CONFIG['app_name']} v{SYSTEM_CONFIG['version']} - 性能优化版",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .author-info {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .strategy-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .signal-long {
        background-color: #ffe6e6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #ff4444;
    }
    .signal-short {
        background-color: #e6ffe6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #44ff44;
    }
    .resonance-signal {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #ffc107;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    """Streamlit应用主类 - 包含性能优化功能"""
    
    def __init__(self):
        self.init_session_state()
        
        # 启用性能优化
        if PERFORMANCE_OPTIMIZATION_AVAILABLE:
            optimize_streamlit_performance()
            self.fast_data_manager = FastDataManager("data")
        
        # 初始化分析引擎时使用会话状态中的家人席位配置
        self.engine = FuturesAnalysisEngine("data", st.session_state.retail_seats)
    
    def init_session_state(self):
        """初始化会话状态"""
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
        if 'last_analysis_date' not in st.session_state:
            st.session_state.last_analysis_date = None
        if 'analysis_running' not in st.session_state:
            st.session_state.analysis_running = False
        if 'retail_seats' not in st.session_state:
            st.session_state.retail_seats = STRATEGY_CONFIG["家人席位反向操作策略"]["default_retail_seats"].copy()
        if 'performance_mode' not in st.session_state:
            st.session_state.performance_mode = PERFORMANCE_OPTIMIZATION_AVAILABLE
        if 'cloud_fetcher_mode' not in st.session_state:
            st.session_state.cloud_fetcher_mode = CLOUD_FETCHER_AVAILABLE
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            st.header("🔧 系统控制")
            
            # 系统状态
            st.subheader("系统状态")
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            st.success(f"✅ 数据目录: {data_dir}")
            
            # 性能状态
            if PERFORMANCE_OPTIMIZATION_AVAILABLE:
                if st.session_state.performance_mode:
                    st.success("🚀 性能优化已启用")
                    
                    # 显示性能指标
                    with st.expander("📊 性能监控", expanded=False):
                        show_performance_metrics()
                else:
                    st.warning("⚠️ 性能优化未启用")
            else:
                st.info("ℹ️ 标准模式运行")
            
            # 云端模式状态
            if CLOUD_FETCHER_AVAILABLE:
                if st.session_state.cloud_fetcher_mode:
                    st.success("☁️ 云端优化已启用")
                else:
                    st.warning("⚠️ 云端优化未启用")
            
            # 网络测试和诊断
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🌐 测试网络"):
                    self.test_network_connection()
            with col2:
                if st.button("🔍 网络诊断"):
                    if CLOUD_FETCHER_AVAILABLE:
                        cloud_fetcher.diagnose_network_issues()
                    else:
                        st.warning("云端诊断功能不可用")
            
            st.divider()
            
            # 家人席位配置
            st.subheader("👥 家人席位配置")
            st.info("家人席位是指散户投资者集中的期货公司席位")
            
            # 显示当前配置
            st.write("**当前家人席位：**")
            for i, seat in enumerate(st.session_state.retail_seats):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{i+1}. {seat}")
                with col2:
                    if st.button("❌", key=f"remove_{i}", help="删除此席位"):
                        st.session_state.retail_seats.pop(i)
                        st.rerun()
            
            # 添加新席位
            new_seat = st.text_input("添加新席位", placeholder="输入期货公司名称")
            if st.button("➕ 添加席位") and new_seat:
                if new_seat not in st.session_state.retail_seats:
                    st.session_state.retail_seats.append(new_seat)
                    st.success(f"已添加席位：{new_seat}")
                    st.rerun()
                else:
                    st.warning("该席位已存在")
            
            # 重置为默认
            if st.button("🔄 重置为默认"):
                st.session_state.retail_seats = STRATEGY_CONFIG["家人席位反向操作策略"]["default_retail_seats"].copy()
                st.success("已重置为默认配置")
                st.rerun()
            
            st.divider()
            
            # 分析参数
            st.subheader("📊 分析参数")
            
            # 日期选择
            today = datetime.now()
            default_date = today - timedelta(days=1)
            trade_date = st.date_input(
                "选择交易日期",
                value=default_date,
                max_value=today,
                help="选择要分析的交易日期"
            )
            
            # 显示选项
            show_charts = st.checkbox(
                "📈 显示图表",
                value=True,
                help="显示持仓分布图表"
            )
            
            max_display = st.slider(
                "最大显示数量",
                min_value=5,
                max_value=20,
                value=10,
                help="每个策略显示的最大信号数量"
            )
            
            st.divider()
            
            # 分析说明
            performance_info = ""
            if PERFORMANCE_OPTIMIZATION_AVAILABLE and st.session_state.performance_mode:
                performance_info = """
            🚀 **性能优化已启用**
            - 智能缓存系统
            - 并发数据获取
            - 网络连接优化
            
            """
            
            st.info(f"""
            📋 **分析内容**
            - 多空力量变化策略
            - 蜘蛛网策略  
            - 家人席位反向操作策略
            - 期限结构分析
            - 信号共振分析
            
            👥 **当前家人席位数量**: {len(st.session_state.retail_seats)}
            
            {performance_info}⏱️ **预计用时**: {"30秒-2分钟" if PERFORMANCE_OPTIMIZATION_AVAILABLE else "2-5分钟"}
            
            💡 **智能跳过**: 广期所数据获取超时将自动跳过，确保分析流畅进行
            """)
            
            # 分析按钮
            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                self.run_analysis(trade_date, show_charts, max_display)
            
            # 清除缓存按钮
            if st.button("🗑️ 清除缓存", use_container_width=True):
                st.session_state.analysis_results = None
                st.session_state.last_analysis_date = None
                st.success("缓存已清除")
                st.rerun()
    
    def test_network_connection(self):
        """测试网络连接"""
        try:
            import requests
            with st.spinner("测试网络连接..."):
                response = requests.get("https://www.baidu.com", timeout=5)
                if response.status_code == 200:
                    st.success("✅ 网络连接正常")
                else:
                    st.warning("⚠️ 网络连接异常")
        except Exception as e:
            st.error(f"❌ 网络连接失败: {str(e)}")
    
    def run_analysis(self, trade_date, show_charts, max_display):
        """运行分析"""
        trade_date_str = trade_date.strftime("%Y%m%d")
        
        # 检查是否已经分析过相同日期和相同家人席位配置
        if (st.session_state.analysis_results and 
            st.session_state.last_analysis_date == trade_date_str and
            st.session_state.analysis_results['metadata'].get('retail_seats') == st.session_state.retail_seats):
            st.info("使用缓存的分析结果")
            return
        
        # 验证日期
        if not validate_trade_date(trade_date_str):
            st.error("无效的日期格式")
            return
        
        # 更新分析引擎的家人席位配置
        self.engine.update_retail_seats(st.session_state.retail_seats)
        
        # 创建进度显示
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        def progress_callback(message, progress):
            progress_bar.progress(progress)
            status_text.text(message)
        
        try:
            st.session_state.analysis_running = True
            
            # 运行分析
            with st.spinner("正在进行期货持仓分析..."):
                # 如果启用了云端获取器，使用云端获取器的自动跳过功能
                if CLOUD_FETCHER_AVAILABLE:
                    # 使用云端数据获取器的自动跳过功能
                    progress_callback("正在使用云端优化获取数据（自动跳过超时交易所）...", 0.1)
                    
                    position_success = cloud_fetcher.fetch_position_data_with_auto_skip(
                        trade_date_str, progress_callback
                    )
                    
                    if not position_success:
                        st.error("❌ 数据获取失败，请检查网络连接或稍后重试")
                        return
                    
                    # 获取行情数据
                    price_data = cloud_fetcher.fetch_price_data_with_fallback(
                        trade_date_str, progress_callback
                    )
                    
                    # 添加调试信息
                    st.info(f"🔍 调试：行情数据获取完成，数据形状: {price_data.shape}")
                    
                    # 直接进行分析，不再重复获取数据
                    progress_callback("开始分析持仓数据...", 0.8)
                    st.info("🔍 调试：开始加载持仓数据...")
                    
                    # 加载已获取的持仓数据
                    try:
                        position_data = self.engine.data_manager.load_position_data()
                        st.info(f"🔍 调试：持仓数据加载完成，合约数量: {len(position_data)}")
                    except Exception as e:
                        st.error(f"❌ 持仓数据加载失败: {str(e)}")
                        return
                    
                    # 检查是否有数据
                    if not position_data:
                        st.error("❌ 没有找到持仓数据文件")
                        return
                    
                    st.info("🔍 调试：开始分析持仓数据...")
                    try:
                        position_results = self.engine._analyze_positions(position_data, progress_callback)
                        st.info(f"🔍 调试：持仓分析完成，分析了 {len(position_results)} 个合约")
                    except Exception as e:
                        st.error(f"❌ 持仓分析失败: {str(e)}")
                        return
                    
                    # 期限结构分析
                    progress_callback("开始期限结构分析...", 0.9)
                    st.info("🔍 调试：开始期限结构分析...")
                    
                    term_results = []
                    try:
                        if not price_data.empty:
                            term_results = self.engine.term_analyzer.analyze_term_structure(price_data)
                            st.info(f"🔍 调试：期限结构分析完成，结果数量: {len(term_results)}")
                        else:
                            st.info("🔍 调试：行情数据为空，跳过期限结构分析")
                    except Exception as e:
                        st.warning(f"⚠️ 期限结构分析失败: {str(e)}")
                        term_results = []
                    
                    # 构建结果
                    st.info("🔍 调试：构建分析结果...")
                    results = {
                        'position_analysis': position_results,
                        'term_structure': term_results,
                        'summary': {},
                        'metadata': {
                            'trade_date': trade_date_str,
                            'analysis_time': datetime.now().isoformat(),
                            'include_term_structure': True,
                            'retail_seats': st.session_state.retail_seats
                        }
                    }
                    
                    # 生成总结
                    progress_callback("生成分析总结...", 0.95)
                    st.info("🔍 调试：生成分析总结...")
                    
                    try:
                        results['summary'] = self.engine._generate_summary(results)
                        st.info("🔍 调试：分析总结生成完成")
                    except Exception as e:
                        st.error(f"❌ 分析总结生成失败: {str(e)}")
                        return
                    
                    progress_callback("分析完成", 1.0)
                    st.info("🔍 调试：所有分析步骤完成")
                    
                else:
                    # 使用标准分析引擎
                    results = self.engine.full_analysis(trade_date_str, progress_callback)
            
            # 清除进度显示
            progress_bar.empty()
            status_text.empty()
            
            if results:
                st.session_state.analysis_results = results
                st.session_state.last_analysis_date = trade_date_str
                
                st.success(f"✅ 分析完成！共分析了 {results['summary']['statistics']['total_contracts']} 个合约")
                st.rerun()
            else:
                st.error("❌ 分析失败，请检查网络连接或稍后重试")
                
        except Exception as e:
            st.error(f"❌ 分析过程出错: {str(e)}")
            import traceback
            st.error(f"详细错误信息: {traceback.format_exc()}")
            
        finally:
            st.session_state.analysis_running = False
    
    def render_main_content(self):
        """渲染主要内容"""
        # 标题和作者信息
        st.markdown(f'<h1 class="main-header">📊 {SYSTEM_CONFIG["app_name"]} v{SYSTEM_CONFIG["version"]}</h1>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="author-info">
            作者：{SYSTEM_CONFIG["author"]} | 邮箱：{SYSTEM_CONFIG["email"]}
        </div>
        ''', unsafe_allow_html=True)
        
        # 检查是否有分析结果
        if not st.session_state.analysis_results:
            self.render_welcome_page()
            return
        
        results = st.session_state.analysis_results
        
        # 显示分析概览
        self.render_analysis_overview(results)
        
        # 创建标签页
        tabs = st.tabs([
            "📈 多空力量变化策略",
            "🕸️ 蜘蛛网策略", 
            "👥 家人席位反向操作策略",
            "📊 期限结构分析",
            "🎯 策略总结",
            "📋 详细数据"
        ])
        
        # 渲染各个标签页
        self.render_strategy_tabs(tabs, results)
    
    def render_welcome_page(self):
        """渲染欢迎页面"""
        st.markdown("""
        ## 🎯 欢迎使用期货持仓分析系统
        
        ### ✨ 主要功能
        - **多空力量变化策略**: 分析席位持仓增减变化判断市场趋势
        - **蜘蛛网策略**: 基于持仓分布分化程度判断机构资金参与情况  
        - **家人席位反向操作策略**: 基于散户投资者行为特点的反向操作策略
        - **期限结构分析**: 分析同品种不同月份合约价格关系
        - **信号共振分析**: 识别多策略共同看好的品种
        
        ### 🚀 使用说明
        1. 在左侧边栏配置家人席位（可自定义）
        2. 选择交易日期和显示参数
        3. 点击"开始分析"按钮
        4. 等待分析完成，查看结果
        
        ### ⚡ 系统特性
        - 智能缓存机制，避免重复分析
        - 并行数据获取，提高效率
        - 实时进度显示
        - 完整的期限结构分析
        - 可配置的家人席位
        
        ### 📊 家人席位说明
        家人席位是指散户投资者集中的期货公司席位，系统默认监控：
        - 东方财富
        - 平安期货
        - 徽商期货
        
        您可以在左侧边栏自定义添加或删除家人席位。
        
        ---
        **请在左侧边栏配置参数并开始分析**
        """)
    
    def render_analysis_overview(self, results):
        """渲染分析概览"""
        st.subheader("📊 分析概览")
        
        # 基本统计信息
        stats = results['summary']['statistics']
        metadata = results['metadata']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['total_contracts']}</h3>
                <p>分析合约数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['total_long_signals']}</h3>
                <p>看多信号数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['total_short_signals']}</h3>
                <p>看空信号数</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            resonance_total = stats['resonance_long_count'] + stats['resonance_short_count']
            st.markdown(f"""
            <div class="metric-card">
                <h3>{resonance_total}</h3>
                <p>共振信号数</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 分析信息
        retail_seats_str = "、".join(metadata.get('retail_seats', []))
        
        st.info(f"""
        📅 **分析日期**: {metadata['trade_date']}  
        ⏰ **分析时间**: {metadata['analysis_time'][:19]}  
        👥 **家人席位**: {retail_seats_str}
        """)
        
        # 数据来源说明
        with st.expander("📋 数据来源说明"):
            st.markdown("""
            ### 分析概览数据来源
            
            **分析合约数**: 从各大期货交易所获取的持仓数据中包含的合约总数
            - 数据来源：大商所、中金所、郑商所、上期所、广期所
            - 统计方法：成功获取并处理的合约数量
            
            **看多/看空信号数**: 各策略分析后产生的信号总数
            - 多空力量变化策略：基于持仓增减变化产生的信号
            - 蜘蛛网策略：基于MSD指标产生的信号  
            - 家人席位反向操作策略：基于家人席位持仓变化产生的信号
            - 统计方法：所有策略信号的累加总数
            
            **共振信号数**: 多个策略共同看好的品种数量
            - 统计方法：在2个及以上策略中都出现看多/看空信号的品种
            - 意义：提高信号可靠性，降低误判风险
            
            **家人席位**: 当前分析使用的散户席位配置
            - 可在左侧边栏自定义配置
            - 用于家人席位反向操作策略分析
            """)
    
    def render_strategy_tabs(self, tabs, results):
        """渲染策略标签页"""
        strategy_signals = results['summary']['strategy_signals']
        
        # 多空力量变化策略
        with tabs[0]:
            self.render_power_change_strategy(strategy_signals['多空力量变化策略'], results)
        
        # 蜘蛛网策略
        with tabs[1]:
            self.render_spider_web_strategy(strategy_signals['蜘蛛网策略'], results)
        
        # 家人席位反向操作策略
        with tabs[2]:
            self.render_retail_reverse_strategy(results)
        
        # 期限结构分析
        with tabs[3]:
            self.render_term_structure_analysis(results['term_structure'])
        
        # 策略总结
        with tabs[4]:
            self.render_strategy_summary(results['summary'])
        
        # 详细数据
        with tabs[5]:
            self.render_detailed_data(results)
    
    def render_power_change_strategy(self, signals, results):
        """渲染多空力量变化策略"""
        st.header("📈 多空力量变化策略")
        
        st.markdown("""
        <div class="strategy-card">
        <h4>💡 策略原理</h4>
        <p>通过分析席位持仓的增减变化来判断市场趋势。当多头席位大幅增仓而空头席位减仓时，表明市场看多情绪浓厚；反之则产生看空信号。</p>
        </div>
        """, unsafe_allow_html=True)
        
        self.render_signals_display(signals, "多空力量变化", results)
    
    def render_spider_web_strategy(self, signals, results):
        """渲染蜘蛛网策略"""
        st.header("🕸️ 蜘蛛网策略")
        
        st.markdown("""
        <div class="strategy-card">
        <h4>💡 策略原理</h4>
        <p>基于持仓分布的分化程度判断机构资金的参与情况。通过计算MSD指标，衡量各席位持仓与平均持仓的偏离程度，判断知情者的态度。</p>
        </div>
        """, unsafe_allow_html=True)
        
        self.render_signals_display(signals, "蜘蛛网", results)
    
    def render_retail_reverse_strategy(self, results):
        """渲染家人席位反向操作策略"""
        st.header("👥 家人席位反向操作策略")
        
        st.markdown("""
        <div class="strategy-card">
        <h4>💡 策略原理</h4>
        <p>基于散户投资者往往在市场顶部做多、底部做空的特点，采用反向操作思路。监控特定散户席位的持仓变化：</p>
        <ul>
        <li><strong>看多信号</strong>：当所有家人席位的空单持仓量变化为正（增加），且多单持仓量变化为负或0（减少或不变）时</li>
        <li><strong>看空信号</strong>：当所有家人席位的多单持仓量变化为正（增加），且空单持仓量变化为负或0（减少或不变）时</li>
        <li><strong>中性信号</strong>：不满足上述严格条件时</li>
        </ul>
        <p><strong>策略逻辑</strong>：散户在市场底部时往往增加空单（恐慌性做空），此时应该看多；在市场顶部时往往增加多单（追涨），此时应该看空。</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示当前家人席位配置
        retail_seats_str = "、".join(results['metadata'].get('retail_seats', []))
        st.info(f"📊 当前监控的家人席位：{retail_seats_str}")
        
        # 获取家人席位策略的详细信息
        position_analysis = results['position_analysis']
        retail_signals = {'long': [], 'short': []}
        
        for contract, data in position_analysis.items():
            if '家人席位反向操作策略' in data['strategies']:
                strategy_data = data['strategies']['家人席位反向操作策略']
                signal_info = {
                    'contract': contract,
                    'strength': strategy_data['strength'],
                    'reason': strategy_data['reason'],
                    'seat_details': strategy_data.get('seat_details', [])
                }
                
                if strategy_data['signal'] == '看多':
                    retail_signals['long'].append(signal_info)
                elif strategy_data['signal'] == '看空':
                    retail_signals['short'].append(signal_info)
        
        # 按强度排序
        retail_signals['long'].sort(key=lambda x: x['strength'], reverse=True)
        retail_signals['short'].sort(key=lambda x: x['strength'], reverse=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 看多信号")
            if retail_signals['long']:
                for i, signal in enumerate(retail_signals['long'][:10], 1):
                    st.markdown(f"""
                    <div class="signal-long">
                        <strong>{i}. {signal['contract']}</strong><br>
                        强度: {signal['strength']:.4f}<br>
                        {signal['reason']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 显示席位详情
                    if signal['seat_details']:
                        with st.expander(f"查看 {signal['contract']} 家人席位详情"):
                            st.markdown("**家人席位持仓变化：**")
                            for seat in signal['seat_details']:
                                # 改进持仓变化描述
                                long_desc = self._format_position_change(seat['long_chg'], "多单")
                                short_desc = self._format_position_change(seat['short_chg'], "空单")
                                st.markdown(f"- **{seat['seat_name']}**: {long_desc}, {short_desc}")
            else:
                st.info("暂无看多信号")
        
        with col2:
            st.subheader("📉 看空信号")
            if retail_signals['short']:
                for i, signal in enumerate(retail_signals['short'][:10], 1):
                    st.markdown(f"""
                    <div class="signal-short">
                        <strong>{i}. {signal['contract']}</strong><br>
                        强度: {signal['strength']:.4f}<br>
                        {signal['reason']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 显示席位详情
                    if signal['seat_details']:
                        with st.expander(f"查看 {signal['contract']} 家人席位详情"):
                            st.markdown("**家人席位持仓变化：**")
                            for seat in signal['seat_details']:
                                # 改进持仓变化描述
                                long_desc = self._format_position_change(seat['long_chg'], "多单")
                                short_desc = self._format_position_change(seat['short_chg'], "空单")
                                st.markdown(f"- **{seat['seat_name']}**: {long_desc}, {short_desc}")
            else:
                st.info("暂无看空信号")
        
        # 统计信息
        st.markdown("---")
        st.markdown(f"""
        ### 📊 统计信息
        - 看多信号数量: {len(retail_signals['long'])}
        - 看空信号数量: {len(retail_signals['short'])}
        - 总信号数量: {len(retail_signals['long']) + len(retail_signals['short'])}
        
        ### 📋 家人席位说明
        - **东方财富**: 主要散户交易平台
        - **平安期货**: 零售客户较多的期货公司
        - **徽商期货**: 区域性散户集中的期货公司
        
        **策略逻辑**: 当这些席位一致性地增加多单时，往往预示着市场顶部，应该看空；反之亦然。
        """)
    
    def _format_position_change(self, change_value, position_type):
        """格式化持仓变化描述"""
        if change_value > 0:
            return f"{position_type}增加{change_value:.0f}手"
        elif change_value < 0:
            return f"{position_type}减少{abs(change_value):.0f}手"
        else:
            return f"{position_type}无变化"
    
    def render_term_structure_analysis(self, term_structure_data):
        """渲染期限结构分析"""
        st.header("📊 期限结构分析")
        
        st.markdown("""
        <div class="strategy-card">
        <h4>💡 策略原理</h4>
        <p>通过比较同一品种不同交割月份合约的价格关系，判断市场对该品种未来供需的预期。Back结构表明当前供应紧张，Contango结构表明当前供应充足。</p>
        <p><strong>判断标准</strong>：严格按照近月到远月价格的递减/递增关系判断，确保结构的准确性。</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not term_structure_data:
            st.warning("暂无期限结构数据")
            return
        
        # 分类结果
        back_results = [r for r in term_structure_data if r[1] == "back"]
        contango_results = [r for r in term_structure_data if r[1] == "contango"]
        flat_results = [r for r in term_structure_data if r[1] == "flat"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Back结构（近强远弱）")
            if back_results:
                for variety, structure, contracts, closes in back_results:
                    st.markdown(f"**{variety}** - 严格递减结构")
                    
                    # 使用expander显示详细价格信息
                    with st.expander(f"查看 {variety} 合约价格详情"):
                        price_df = pd.DataFrame({
                            '合约': contracts,
                            '收盘价': closes,
                            '价格变化': self._calculate_price_changes(closes)
                        })
                        st.dataframe(price_df, use_container_width=True)
                        
                        # 显示价格趋势
                        st.markdown(f"**价格趋势**: {closes[0]:.2f} → {closes[-1]:.2f} (递减 {((closes[-1]-closes[0])/closes[0]*100):+.2f}%)")
            else:
                st.info("暂无Back结构品种")
        
        with col2:
            st.subheader("📉 Contango结构（近弱远强）")
            if contango_results:
                for variety, structure, contracts, closes in contango_results:
                    st.markdown(f"**{variety}** - 严格递增结构")
                    
                    # 使用expander显示详细价格信息
                    with st.expander(f"查看 {variety} 合约价格详情"):
                        price_df = pd.DataFrame({
                            '合约': contracts,
                            '收盘价': closes,
                            '价格变化': self._calculate_price_changes(closes)
                        })
                        st.dataframe(price_df, use_container_width=True)
                        
                        # 显示价格趋势
                        st.markdown(f"**价格趋势**: {closes[0]:.2f} → {closes[-1]:.2f} (递增 {((closes[-1]-closes[0])/closes[0]*100):+.2f}%)")
            else:
                st.info("暂无Contango结构品种")
        
        # 平坦结构单独显示
        if flat_results:
            st.subheader("📊 平坦结构品种")
            flat_varieties = [r[0] for r in flat_results]
            st.info(f"平坦结构品种 ({len(flat_varieties)}个): {', '.join(flat_varieties)}")
        
        # 统计信息
        st.markdown("---")
        st.markdown(f"""
        ### 📊 统计信息
        - Back结构品种: {len(back_results)} (近强远弱，严格递减)
        - Contango结构品种: {len(contango_results)} (近弱远强，严格递增)
        - 平坦结构品种: {len(flat_results)} (不符合严格递减或递增)
        - 总品种数量: {len(term_structure_data)}
        
        ### 📋 结构判断说明
        - **Back结构**: 近月合约价格到远月合约价格严格递减
        - **Contango结构**: 近月合约价格到远月合约价格严格递增
        - **平坦结构**: 不符合严格递减或递增的价格关系
        """)
        
        # 期限结构图表
        if back_results or contango_results:
            st.subheader("📈 期限结构图表")
            fig = go.Figure()
            
            # 添加Back结构
            for variety, structure, contracts, closes in back_results:
                fig.add_trace(go.Scatter(
                    x=contracts,
                    y=closes,
                    mode='lines+markers',
                    name=f'{variety} (Back)',
                    line=dict(color='red', width=2)
                ))
            
            # 添加Contango结构
            for variety, structure, contracts, closes in contango_results:
                fig.add_trace(go.Scatter(
                    x=contracts,
                    y=closes,
                    mode='lines+markers',
                    name=f'{variety} (Contango)',
                    line=dict(color='green', width=2)
                ))
            
            fig.update_layout(
                title='期限结构分析图',
                xaxis_title='合约',
                yaxis_title='收盘价',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _calculate_price_changes(self, prices):
        """计算价格变化百分比"""
        changes = ['基准']
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                change_pct = ((prices[i] - prices[i-1]) / prices[i-1] * 100)
                changes.append(f'{change_pct:+.2f}%')
            else:
                changes.append('N/A')
        return changes
    
    def render_strategy_summary(self, summary):
        """渲染策略总结"""
        st.header("🎯 策略总结")
        
        # 信号共振分析
        resonance = summary['signal_resonance']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 信号共振看多品种")
            if resonance['long']:
                sorted_long = sorted(resonance['long'].items(), key=lambda x: x[1]['count'], reverse=True)
                for symbol, info in sorted_long:
                    strategies_text = "、".join(info['strategies'])
                    st.markdown(f"""
                    <div class="resonance-signal">
                        <strong>{symbol}</strong> 
                        <span style='color: #666; font-size: 0.9em;'>({info['count']}个策略)</span><br>
                        <span style='font-size: 0.8em; color: #888;'>策略: {strategies_text}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暂无信号共振的看多品种")
        
        with col2:
            st.subheader("🔥 信号共振看空品种")
            if resonance['short']:
                sorted_short = sorted(resonance['short'].items(), key=lambda x: x[1]['count'], reverse=True)
                for symbol, info in sorted_short:
                    strategies_text = "、".join(info['strategies'])
                    st.markdown(f"""
                    <div class="resonance-signal">
                        <strong>{symbol}</strong> 
                        <span style='color: #666; font-size: 0.9em;'>({info['count']}个策略)</span><br>
                        <span style='font-size: 0.8em; color: #888;'>策略: {strategies_text}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("暂无信号共振的看空品种")
        
        # 各策略前十名
        st.markdown("---")
        st.subheader("📋 各策略前十名品种")
        
        strategy_signals = summary['strategy_signals']
        for strategy_name, signals in strategy_signals.items():
            with st.expander(f"📊 {strategy_name}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**看多信号**")
                    for signal in signals['long'][:10]:
                        st.markdown(f"- {signal['contract']} (强度: {signal['strength']:.2f})")
                
                with col2:
                    st.markdown("**看空信号**")
                    for signal in signals['short'][:10]:
                        st.markdown(f"- {signal['contract']} (强度: {signal['strength']:.2f})")
        
        # 下载功能
        st.markdown("---")
        st.subheader("💾 下载分析结果")
        
        # 准备Excel数据
        excel_data = self.prepare_excel_data(summary, resonance)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📊 下载Excel报告",
                data=excel_data,
                file_name=f"futures_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            # 准备文本数据
            text_data = self.prepare_text_data(summary, resonance)
            st.download_button(
                label="📝 下载文本报告",
                data=text_data,
                file_name=f"futures_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    def render_detailed_data(self, results):
        """渲染详细数据"""
        st.header("📋 详细数据")
        
        position_analysis = results['position_analysis']
        
        # 合约选择
        contract_names = list(position_analysis.keys())
        selected_contract = st.selectbox("选择合约", contract_names)
        
        if selected_contract:
            contract_data = position_analysis[selected_contract]
            
            # 显示策略结果
            st.subheader(f"📊 {selected_contract} 策略分析结果")
            
            strategies = contract_data['strategies']
            for strategy_name, strategy_data in strategies.items():
                with st.expander(f"{strategy_name}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("信号", strategy_data['signal'])
                    with col2:
                        st.metric("强度", f"{strategy_data['strength']:.4f}")
                    with col3:
                        st.write("**原因**")
                        st.write(strategy_data['reason'])
                    
                    # 如果是家人席位策略，显示席位详情
                    if strategy_name == '家人席位反向操作策略' and strategy_data.get('seat_details'):
                        st.write("**家人席位详情**")
                        seat_df = pd.DataFrame(strategy_data['seat_details'])
                        st.dataframe(seat_df, use_container_width=True)
            
            # 显示原始数据
            st.subheader(f"📋 {selected_contract} 原始持仓数据")
            raw_data = contract_data['raw_data']
            st.dataframe(raw_data, use_container_width=True)
            
            # 显示汇总数据
            st.subheader(f"📈 {selected_contract} 汇总数据")
            summary_data = contract_data['summary_data']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总多单", f"{summary_data['total_long']:,.0f}")
            with col2:
                st.metric("总空单", f"{summary_data['total_short']:,.0f}")
            with col3:
                st.metric("多单变化", f"{summary_data['total_long_chg']:,.0f}")
            with col4:
                st.metric("空单变化", f"{summary_data['total_short_chg']:,.0f}")
            
            # 生成持仓分布图
            if len(raw_data) > 0:
                st.subheader(f"📊 {selected_contract} 持仓分布图")
                self.create_position_chart(raw_data, selected_contract)
    
    def render_signals_display(self, signals, strategy_type, results=None):
        """渲染信号显示"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 看多信号")
            if signals['long']:
                for signal in signals['long'][:10]:
                    st.markdown(f"""
                    <div class="signal-long">
                        <strong>{signal['contract']}</strong><br>
                        强度: {signal['strength']:.2f}<br>
                        {signal['reason']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 添加查看持仓详情的功能
                    if results and signal['contract'] in results['position_analysis']:
                        with st.expander(f"查看 {signal['contract']} 持仓详情"):
                            contract_data = results['position_analysis'][signal['contract']]
                            raw_data = contract_data['raw_data']
                            
                            # 显示汇总信息
                            summary_data = contract_data['summary_data']
                            col_a, col_b, col_c, col_d = st.columns(4)
                            with col_a:
                                st.metric("总多单", f"{summary_data['total_long']:,.0f}")
                            with col_b:
                                st.metric("总空单", f"{summary_data['total_short']:,.0f}")
                            with col_c:
                                st.metric("多单变化", f"{summary_data['total_long_chg']:,.0f}")
                            with col_d:
                                st.metric("空单变化", f"{summary_data['total_short_chg']:,.0f}")
                            
                            # 显示前20名持仓数据
                            st.markdown("**前20名持仓明细：**")
                            display_data = raw_data.head(20)
                            st.dataframe(display_data, use_container_width=True)
            else:
                st.info("暂无看多信号")
        
        with col2:
            st.subheader("📉 看空信号")
            if signals['short']:
                for signal in signals['short'][:10]:
                    st.markdown(f"""
                    <div class="signal-short">
                        <strong>{signal['contract']}</strong><br>
                        强度: {signal['strength']:.2f}<br>
                        {signal['reason']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 添加查看持仓详情的功能
                    if results and signal['contract'] in results['position_analysis']:
                        with st.expander(f"查看 {signal['contract']} 持仓详情"):
                            contract_data = results['position_analysis'][signal['contract']]
                            raw_data = contract_data['raw_data']
                            
                            # 显示汇总信息
                            summary_data = contract_data['summary_data']
                            col_a, col_b, col_c, col_d = st.columns(4)
                            with col_a:
                                st.metric("总多单", f"{summary_data['total_long']:,.0f}")
                            with col_b:
                                st.metric("总空单", f"{summary_data['total_short']:,.0f}")
                            with col_c:
                                st.metric("多单变化", f"{summary_data['total_long_chg']:,.0f}")
                            with col_d:
                                st.metric("空单变化", f"{summary_data['total_short_chg']:,.0f}")
                            
                            # 显示前20名持仓数据
                            st.markdown("**前20名持仓明细：**")
                            display_data = raw_data.head(20)
                            st.dataframe(display_data, use_container_width=True)
            else:
                st.info("暂无看空信号")
        
        # 统计信息
        st.markdown("---")
        st.markdown(f"""
        ### 📊 {strategy_type}策略统计
        - 看多信号数量: {len(signals['long'])}
        - 看空信号数量: {len(signals['short'])}
        - 总信号数量: {len(signals['long']) + len(signals['short'])}
        """)
        
        # 信号强度图表
        if signals['long'] or signals['short']:
            st.subheader(f"📊 {strategy_type}策略信号强度分布")
            fig = go.Figure()
            
            if signals['long']:
                fig.add_trace(go.Bar(
                    x=[s['contract'] for s in signals['long'][:10]],
                    y=[s['strength'] for s in signals['long'][:10]],
                    name='看多信号',
                    marker_color='red'
                ))
            
            if signals['short']:
                fig.add_trace(go.Bar(
                    x=[s['contract'] for s in signals['short'][:10]],
                    y=[-s['strength'] for s in signals['short'][:10]],
                    name='看空信号',
                    marker_color='green'
                ))
            
            fig.update_layout(
                title=f'{strategy_type}策略信号强度分布',
                xaxis_title='合约',
                yaxis_title='信号强度',
                barmode='relative',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def create_position_chart(self, df, contract_name):
        """创建持仓分布图"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('多空持仓分布', '持仓变化分布'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 多空持仓分布
        fig.add_trace(
            go.Bar(
                x=df['long_party_name'][:10],
                y=df['long_open_interest'][:10],
                name='多单持仓',
                marker_color='red'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=df['short_party_name'][:10],
                y=df['short_open_interest'][:10],
                name='空单持仓',
                marker_color='green'
            ),
            row=1, col=1
        )
        
        # 持仓变化分布
        fig.add_trace(
            go.Bar(
                x=df['long_party_name'][:10],
                y=df['long_open_interest_chg'][:10],
                name='多单变化',
                marker_color='lightcoral',
                showlegend=False
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(
                x=df['short_party_name'][:10],
                y=df['short_open_interest_chg'][:10],
                name='空单变化',
                marker_color='lightgreen',
                showlegend=False
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title=f'{contract_name} 持仓分析图',
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def prepare_excel_data(self, summary, resonance):
        """准备Excel下载数据"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # 策略总结
            summary_data = []
            for strategy_name, signals in summary['strategy_signals'].items():
                for signal in signals['long'][:10]:
                    summary_data.append({
                        '策略': strategy_name,
                        '信号类型': '看多',
                        '合约': signal['contract'],
                        '强度': signal['strength'],
                        '原因': signal['reason']
                    })
                for signal in signals['short'][:10]:
                    summary_data.append({
                        '策略': strategy_name,
                        '信号类型': '看空',
                        '合约': signal['contract'],
                        '强度': signal['strength'],
                        '原因': signal['reason']
                    })
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='策略总结', index=False)
            
            # 共振信号
            resonance_data = []
            for symbol, info in resonance['long'].items():
                resonance_data.append({
                    '品种': symbol,
                    '信号类型': '共同看多',
                    '策略数量': info['count'],
                    '策略列表': '、'.join(info['strategies'])
                })
            for symbol, info in resonance['short'].items():
                resonance_data.append({
                    '品种': symbol,
                    '信号类型': '共同看空',
                    '策略数量': info['count'],
                    '策略列表': '、'.join(info['strategies'])
                })
            
            pd.DataFrame(resonance_data).to_excel(writer, sheet_name='信号共振', index=False)
        
        return output.getvalue()
    
    def prepare_text_data(self, summary, resonance):
        """准备文本下载数据"""
        lines = []
        lines.append("期货持仓分析报告")
        lines.append("=" * 50)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 信号共振
        lines.append("信号共振分析")
        lines.append("-" * 30)
        lines.append("共同看多品种:")
        for symbol, info in resonance['long'].items():
            lines.append(f"  {symbol} ({info['count']}个策略): {', '.join(info['strategies'])}")
        
        lines.append("\n共同看空品种:")
        for symbol, info in resonance['short'].items():
            lines.append(f"  {symbol} ({info['count']}个策略): {', '.join(info['strategies'])}")
        
        # 各策略信号
        lines.append("\n\n各策略信号详情")
        lines.append("-" * 30)
        
        for strategy_name, signals in summary['strategy_signals'].items():
            lines.append(f"\n{strategy_name}:")
            lines.append("  看多信号:")
            for signal in signals['long'][:10]:
                lines.append(f"    {signal['contract']} (强度: {signal['strength']:.2f})")
            
            lines.append("  看空信号:")
            for signal in signals['short'][:10]:
                lines.append(f"    {signal['contract']} (强度: {signal['strength']:.2f})")
        
        return "\n".join(lines)
    
    def run(self):
        """运行应用"""
        self.render_sidebar()
        self.render_main_content()

# 主程序入口
if __name__ == "__main__":
    app = StreamlitApp()
    app.run() 
