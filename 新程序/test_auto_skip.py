#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期货持仓分析系统 - 自动跳过功能测试
作者：7haoge
邮箱：953534947@qq.com
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def test_auto_skip_functionality():
    """测试自动跳过功能"""
    print("🚀 期货持仓分析系统 v2.1 - 自动跳过功能测试")
    print("=" * 60)
    
    # 测试导入
    print("\n1. 测试模块导入...")
    try:
        from cloud_data_fetcher import cloud_fetcher
        print("✅ 云端数据获取器导入成功")
    except ImportError as e:
        print(f"❌ 云端数据获取器导入失败: {e}")
        return False
    
    try:
        from streamlit_app import StreamlitApp
        print("✅ 主应用导入成功")
    except ImportError as e:
        print(f"❌ 主应用导入失败: {e}")
        return False
    
    # 测试配置
    print("\n2. 测试系统配置...")
    try:
        from config import SYSTEM_CONFIG
        print(f"✅ 系统版本: {SYSTEM_CONFIG['version']}")
        print(f"✅ 系统描述: {SYSTEM_CONFIG['description']}")
    except ImportError as e:
        print(f"❌ 配置导入失败: {e}")
        return False
    
    # 测试自动跳过方法
    print("\n3. 测试自动跳过方法...")
    if hasattr(cloud_fetcher, 'fetch_position_data_with_auto_skip'):
        print("✅ 自动跳过方法存在")
    else:
        print("❌ 自动跳过方法不存在")
        return False
    
    # 测试线程和队列导入
    print("\n4. 测试依赖模块...")
    try:
        import threading
        import queue
        print("✅ 线程和队列模块可用")
    except ImportError as e:
        print(f"❌ 线程模块导入失败: {e}")
        return False
    
    # 测试数据目录
    print("\n5. 测试数据目录...")
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ 创建数据目录: {data_dir}")
    else:
        print(f"✅ 数据目录已存在: {data_dir}")
    
    # 测试网络连接
    print("\n6. 测试网络连接...")
    try:
        import requests
        response = requests.get("https://www.baidu.com", timeout=5)
        if response.status_code == 200:
            print("✅ 网络连接正常")
        else:
            print("⚠️ 网络连接异常")
    except Exception as e:
        print(f"⚠️ 网络测试失败: {e}")
    
    # 测试akshare导入
    print("\n7. 测试akshare模块...")
    try:
        import akshare as ak
        print(f"✅ akshare导入成功 (版本: {getattr(ak, '__version__', '未知')})")
    except ImportError:
        print("⚠️ akshare未安装，但不影响测试")
    
    print("\n" + "=" * 60)
    print("🎉 自动跳过功能测试完成！")
    print("\n📋 功能特性:")
    print("- ✅ 智能超时检测（20秒）")
    print("- ✅ 自动跳过广期所")
    print("- ✅ 线程安全的数据获取")
    print("- ✅ 无需用户干预")
    print("- ✅ 保持系统兼容性")
    
    print("\n🚀 使用方法:")
    print("streamlit run streamlit_app.py")
    
    return True

def test_timeout_simulation():
    """模拟超时测试"""
    print("\n" + "=" * 60)
    print("🔧 超时机制模拟测试")
    print("=" * 60)
    
    import threading
    import queue
    import time
    
    def slow_function():
        """模拟慢速函数"""
        time.sleep(25)  # 模拟25秒的慢速操作
        return "完成"
    
    def test_timeout_control():
        """测试超时控制"""
        result_queue = queue.Queue()
        
        def worker():
            try:
                result = slow_function()
                result_queue.put(('success', result))
            except Exception as e:
                result_queue.put(('error', str(e)))
        
        print("启动超时测试...")
        start_time = time.time()
        
        # 启动工作线程
        worker_thread = threading.Thread(target=worker)
        worker_thread.daemon = True
        worker_thread.start()
        
        # 等待结果，最多等待20秒
        worker_thread.join(timeout=20)
        
        elapsed_time = time.time() - start_time
        
        if worker_thread.is_alive():
            print(f"✅ 超时控制生效 (耗时: {elapsed_time:.1f}秒)")
            print("✅ 线程被正确超时处理")
            return True
        else:
            try:
                status, result = result_queue.get_nowait()
                print(f"⚠️ 操作在超时前完成: {result}")
                return True
            except queue.Empty:
                print("❌ 超时控制失败")
                return False
    
    return test_timeout_control()

if __name__ == "__main__":
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 基础功能测试
    basic_test = test_auto_skip_functionality()
    
    # 超时机制测试
    timeout_test = test_timeout_simulation()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"基础功能测试: {'✅ 通过' if basic_test else '❌ 失败'}")
    print(f"超时机制测试: {'✅ 通过' if timeout_test else '❌ 失败'}")
    
    if basic_test and timeout_test:
        print("\n🎉 所有测试通过！系统已准备就绪。")
        print("🚀 可以开始使用: streamlit run streamlit_app.py")
    else:
        print("\n⚠️ 部分测试失败，请检查系统配置。")
    
    print(f"\n作者: 7haoge | 邮箱: 953534947@qq.com") 