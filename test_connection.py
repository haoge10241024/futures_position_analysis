#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货持仓分析系统连接测试脚本
用于诊断网络连接和数据获取问题
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta

def test_network_connection():
    """测试网络连接"""
    print("=" * 50)
    print("1. 测试网络连接")
    print("=" * 50)
    
    test_urls = [
        "https://www.baidu.com",
        "https://akshare.akfamily.xyz",
        "https://www.sina.com.cn"
    ]
    
    for url in test_urls:
        try:
            print(f"测试连接: {url}")
            start_time = time.time()
            response = requests.get(url, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                print(f"✅ 连接成功 - 响应时间: {end_time - start_time:.2f}秒")
            else:
                print(f"❌ 连接失败 - 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 连接失败 - 错误: {str(e)}")
        print()

def test_akshare_import():
    """测试akshare导入"""
    print("=" * 50)
    print("2. 测试akshare导入")
    print("=" * 50)
    
    try:
        import akshare as ak
        print("✅ akshare导入成功")
        print(f"akshare版本: {ak.__version__ if hasattr(ak, '__version__') else '未知'}")
    except ImportError as e:
        print(f"❌ akshare导入失败: {str(e)}")
        print("请运行: pip install akshare")
        return False
    except Exception as e:
        print(f"❌ akshare导入异常: {str(e)}")
        return False
    
    return True

def test_data_directory():
    """测试数据目录"""
    print("=" * 50)
    print("3. 测试数据目录")
    print("=" * 50)
    
    data_dir = "data"
    
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"✅ 创建数据目录: {os.path.abspath(data_dir)}")
        else:
            print(f"✅ 数据目录已存在: {os.path.abspath(data_dir)}")
        
        # 测试写入权限
        test_file = os.path.join(data_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print("✅ 数据目录写入权限正常")
        
    except Exception as e:
        print(f"❌ 数据目录测试失败: {str(e)}")
        return False
    
    return True

def test_simple_data_fetch():
    """测试简单数据获取"""
    print("=" * 50)
    print("4. 测试数据获取")
    print("=" * 50)
    
    try:
        import akshare as ak
        
        # 获取昨天的日期
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print(f"测试日期: {yesterday}")
        
        # 测试获取大商所数据
        print("正在测试大商所数据获取...")
        start_time = time.time()
        
        try:
            dce_data = ak.futures_dce_position_rank(date=yesterday)
            end_time = time.time()
            
            if dce_data:
                print(f"✅ 大商所数据获取成功 - 耗时: {end_time - start_time:.2f}秒")
                print(f"   获取到 {len(dce_data)} 个品种的数据")
                
                # 显示第一个品种的数据样本
                first_key = list(dce_data.keys())[0]
                first_df = dce_data[first_key]
                print(f"   样本品种: {first_key}")
                print(f"   数据行数: {len(first_df)}")
                print(f"   数据列: {list(first_df.columns)}")
            else:
                print("❌ 大商所数据为空")
                
        except Exception as e:
            print(f"❌ 大商所数据获取失败: {str(e)}")
            
        # 测试获取期货行情数据
        print("\n正在测试期货行情数据获取...")
        start_time = time.time()
        
        try:
            price_data = ak.get_futures_daily(start_date=yesterday, end_date=yesterday, market="DCE")
            end_time = time.time()
            
            if not price_data.empty:
                print(f"✅ 期货行情数据获取成功 - 耗时: {end_time - start_time:.2f}秒")
                print(f"   获取到 {len(price_data)} 条记录")
                print(f"   数据列: {list(price_data.columns)}")
            else:
                print("❌ 期货行情数据为空")
                
        except Exception as e:
            print(f"❌ 期货行情数据获取失败: {str(e)}")
            
    except Exception as e:
        print(f"❌ 数据获取测试失败: {str(e)}")
        return False
    
    return True

def test_futures_position_analysis():
    """测试期货持仓分析模块"""
    print("=" * 50)
    print("5. 测试期货持仓分析模块")
    print("=" * 50)
    
    try:
        from futures_position_analysis import FuturesPositionAnalyzer
        print("✅ 期货持仓分析模块导入成功")
        
        # 创建分析器实例
        data_dir = "data"
        analyzer = FuturesPositionAnalyzer(data_dir)
        print("✅ 分析器实例创建成功")
        
        # 测试数据获取（使用昨天的日期）
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        print(f"测试分析日期: {yesterday}")
        
        print("正在进行完整分析测试...")
        start_time = time.time()
        
        results = analyzer.fetch_and_analyze(yesterday)
        end_time = time.time()
        
        if results:
            print(f"✅ 完整分析成功 - 耗时: {end_time - start_time:.2f}秒")
            print(f"   分析了 {len(results)} 个合约")
            
            # 显示第一个合约的分析结果
            first_contract = list(results.keys())[0]
            first_result = results[first_contract]
            print(f"   样本合约: {first_contract}")
            print(f"   策略数量: {len(first_result['strategies'])}")
            
            for strategy_name, strategy_result in first_result['strategies'].items():
                print(f"     {strategy_name}: {strategy_result['signal']}")
        else:
            print("❌ 完整分析失败 - 返回结果为空")
            
    except ImportError as e:
        print(f"❌ 期货持仓分析模块导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 期货持仓分析测试失败: {str(e)}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("期货持仓分析系统 - 连接测试")
    print("测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()
    
    # 运行所有测试
    tests = [
        test_network_connection,
        test_akshare_import,
        test_data_directory,
        test_simple_data_fetch,
        test_futures_position_analysis
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试 {test_func.__name__} 出现异常: {str(e)}")
            results.append(False)
        print()
    
    # 总结
    print("=" * 50)
    print("测试总结")
    print("=" * 50)
    
    test_names = [
        "网络连接测试",
        "akshare导入测试", 
        "数据目录测试",
        "数据获取测试",
        "完整分析测试"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n总体结果: {success_count}/{total_count} 项测试通过")
    
    if success_count == total_count:
        print("🎉 所有测试通过！系统应该可以正常运行。")
    elif success_count >= 3:
        print("⚠️  大部分测试通过，系统可能可以运行，但可能会有一些功能受限。")
    else:
        print("❌ 多项测试失败，请检查网络连接和环境配置。")
    
    print("\n建议:")
    if not results[0]:  # 网络连接失败
        print("- 检查网络连接")
        print("- 检查防火墙设置")
    if not results[1]:  # akshare导入失败
        print("- 安装akshare: pip install akshare")
        print("- 更新akshare: pip install --upgrade akshare")
    if not results[3]:  # 数据获取失败
        print("- 检查选择的日期是否为交易日")
        print("- 稍后重试，可能是数据源临时不可用")

if __name__ == "__main__":
    main() 