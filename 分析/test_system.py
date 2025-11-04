#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货持仓分析系统 - 系统测试脚本
用于测试系统各个组件的功能
"""

import os
import sys
import time
from datetime import datetime, timedelta
from utils import (
    test_network_connectivity, 
    ensure_directory, 
    get_recent_trading_date,
    validate_date_format,
    logger
)

def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("1. 测试模块导入")
    print("=" * 60)
    
    modules_to_test = [
        ('streamlit', 'streamlit'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('plotly', 'plotly.graph_objects'),
        ('akshare', 'akshare'),
        ('openpyxl', 'openpyxl'),
        ('xlsxwriter', 'xlsxwriter'),
        ('requests', 'requests')
    ]
    
    success_count = 0
    
    for module_name, import_name in modules_to_test:
        try:
            __import__(import_name)
            print(f"✅ {module_name} 导入成功")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module_name} 导入失败: {str(e)}")
        except Exception as e:
            print(f"❌ {module_name} 导入异常: {str(e)}")
    
    print(f"\n导入测试结果: {success_count}/{len(modules_to_test)} 成功")
    return success_count == len(modules_to_test)

def test_network():
    """测试网络连接"""
    print("=" * 60)
    print("2. 测试网络连接")
    print("=" * 60)
    
    try:
        results = test_network_connectivity()
        
        for detail in results['details']:
            url = detail['url']
            if detail['success']:
                print(f"✅ {url} - 响应时间: {detail['response_time']:.2f}秒")
            else:
                error_msg = detail['error'] or "连接失败"
                print(f"❌ {url} - {error_msg}")
        
        print(f"\n网络测试结果: {results['passed_tests']}/{results['total_tests']} 成功")
        return results['success']
        
    except Exception as e:
        print(f"❌ 网络测试异常: {str(e)}")
        return False

def test_data_directory():
    """测试数据目录"""
    print("=" * 60)
    print("3. 测试数据目录")
    print("=" * 60)
    
    data_dir = "data"
    
    try:
        # 测试目录创建
        if ensure_directory(data_dir):
            print(f"✅ 数据目录创建/验证成功: {os.path.abspath(data_dir)}")
        else:
            print(f"❌ 数据目录创建失败")
            return False
        
        # 测试写入权限
        test_file = os.path.join(data_dir, "test_write.txt")
        try:
            with open(test_file, "w", encoding='utf-8') as f:
                f.write("测试写入权限")
            print("✅ 数据目录写入权限正常")
            
            # 清理测试文件
            os.remove(test_file)
            print("✅ 测试文件清理成功")
            
        except Exception as e:
            print(f"❌ 数据目录写入权限测试失败: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 数据目录测试异常: {str(e)}")
        return False

def test_akshare_basic():
    """测试akshare基本功能"""
    print("=" * 60)
    print("4. 测试akshare基本功能")
    print("=" * 60)
    
    try:
        import akshare as ak
        print(f"✅ akshare版本: {getattr(ak, '__version__', '未知')}")
        
        # 测试简单的数据获取
        print("正在测试基础数据获取...")
        
        # 获取最近的交易日
        trade_date = get_recent_trading_date(1)
        print(f"测试日期: {trade_date}")
        
        # 测试获取大商所数据
        try:
            print("正在测试大商所数据获取...")
            start_time = time.time()
            dce_data = ak.futures_dce_position_rank(date=trade_date)
            end_time = time.time()
            
            if dce_data:
                print(f"✅ 大商所数据获取成功 - 耗时: {end_time - start_time:.2f}秒")
                print(f"   获取到 {len(dce_data)} 个品种的数据")
                
                # 显示第一个品种的信息
                first_key = list(dce_data.keys())[0]
                first_df = dce_data[first_key]
                print(f"   样本品种: {first_key}, 数据行数: {len(first_df)}")
            else:
                print("❌ 大商所数据为空")
                return False
                
        except Exception as e:
            print(f"❌ 大商所数据获取失败: {str(e)}")
            return False
        
        return True
        
    except ImportError:
        print("❌ akshare未安装")
        return False
    except Exception as e:
        print(f"❌ akshare测试异常: {str(e)}")
        return False

def test_core_analyzer():
    """测试核心分析器"""
    print("=" * 60)
    print("5. 测试核心分析器")
    print("=" * 60)
    
    try:
        from futures_analyzer import FuturesAnalysisEngine
        print("✅ 核心分析器导入成功")
        
        # 创建分析引擎
        engine = FuturesAnalysisEngine("data")
        print("✅ 分析引擎创建成功")
        
        # 测试快速分析
        trade_date = get_recent_trading_date(1)
        print(f"测试分析日期: {trade_date}")
        
        def progress_callback(message, progress):
            print(f"[{progress*100:.1f}%] {message}")
        
        print("正在进行快速分析测试...")
        start_time = time.time()
        
        results = engine.full_analysis(trade_date, progress_callback)
        
        end_time = time.time()
        
        if results:
            print(f"✅ 核心分析器测试成功 - 耗时: {end_time - start_time:.2f}秒")
            
            stats = results['summary']['statistics']
            print(f"   分析合约数: {stats['total_contracts']}")
            print(f"   看多信号数: {stats['total_long_signals']}")
            print(f"   看空信号数: {stats['total_short_signals']}")
            print(f"   共振信号数: {stats['resonance_long_count'] + stats['resonance_short_count']}")
            
            return True
        else:
            print("❌ 核心分析器返回空结果")
            return False
            
    except ImportError as e:
        print(f"❌ 核心分析器导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 核心分析器测试失败: {str(e)}")
        return False

def test_streamlit_components():
    """测试Streamlit组件"""
    print("=" * 60)
    print("6. 测试Streamlit组件")
    print("=" * 60)
    
    try:
        import streamlit as st
        import plotly.graph_objects as go
        from streamlit_app import StreamlitApp
        
        print("✅ Streamlit组件导入成功")
        
        # 测试应用类创建
        app = StreamlitApp()
        print("✅ Streamlit应用类创建成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ Streamlit组件导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Streamlit组件测试失败: {str(e)}")
        return False

def test_configuration():
    """测试配置文件"""
    print("=" * 60)
    print("7. 测试配置文件")
    print("=" * 60)
    
    try:
        from config import (
            SYSTEM_CONFIG, DATA_CONFIG, EXCHANGE_CONFIG,
            STRATEGY_CONFIG, DISPLAY_CONFIG, UI_CONFIG
        )
        
        print("✅ 配置文件导入成功")
        print(f"   系统名称: {SYSTEM_CONFIG['app_name']}")
        print(f"   系统版本: {SYSTEM_CONFIG['version']}")
        print(f"   数据目录: {DATA_CONFIG['data_dir']}")
        print(f"   启用的交易所: {len([k for k, v in EXCHANGE_CONFIG.items() if v['enabled']])}")
        print(f"   启用的策略: {len([k for k, v in STRATEGY_CONFIG.items() if v['enabled']])}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 配置文件导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 配置文件测试失败: {str(e)}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("期货持仓分析系统 v2.0 - 系统测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("模块导入测试", test_imports),
        ("网络连接测试", test_network),
        ("数据目录测试", test_data_directory),
        ("akshare基本功能测试", test_akshare_basic),
        ("核心分析器测试", test_core_analyzer),
        ("Streamlit组件测试", test_streamlit_components),
        ("配置文件测试", test_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 出现异常: {str(e)}")
            results.append((test_name, False))
        print()
    
    # 测试总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    total_tests = len(results)
    print(f"\n总体结果: {success_count}/{total_tests} 项测试通过")
    
    # 给出建议
    if success_count == total_tests:
        print("\n🎉 所有测试通过！系统可以正常运行。")
        print("\n启动建议:")
        print("1. 运行命令: streamlit run streamlit_app.py")
        print("2. 在浏览器中打开显示的URL")
        print("3. 选择交易日期并开始分析")
    elif success_count >= total_tests * 0.7:
        print("\n⚠️ 大部分测试通过，系统基本可用，但可能有部分功能受限。")
        print("\n建议:")
        failed_tests = [name for name, result in results if not result]
        for test_name in failed_tests:
            if "网络" in test_name:
                print("- 检查网络连接和防火墙设置")
            elif "akshare" in test_name:
                print("- 更新akshare: pip install --upgrade akshare")
            elif "模块" in test_name:
                print("- 安装缺失的依赖: pip install -r requirements.txt")
    else:
        print("\n❌ 多项测试失败，系统可能无法正常运行。")
        print("\n建议:")
        print("1. 检查Python环境和依赖安装")
        print("2. 运行: pip install -r requirements.txt")
        print("3. 检查网络连接")
        print("4. 重新运行测试")
    
    return success_count, total_tests

if __name__ == "__main__":
    try:
        success_count, total_tests = run_all_tests()
        
        # 设置退出码
        if success_count == total_tests:
            sys.exit(0)  # 全部成功
        elif success_count >= total_tests * 0.7:
            sys.exit(1)  # 部分成功
        else:
            sys.exit(2)  # 大部分失败
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(3)
    except Exception as e:
        print(f"\n\n测试过程出现异常: {str(e)}")
        sys.exit(4) 