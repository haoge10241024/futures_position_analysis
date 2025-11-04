#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的代码
"""

import sys
import os

def test_imports():
    """测试导入"""
    try:
        import streamlit as st
        print("✅ streamlit导入成功")
        
        from futures_analyzer import FuturesAnalysisEngine
        print("✅ FuturesAnalysisEngine导入成功")
        
        from cloud_data_fetcher import cloud_fetcher
        print("✅ cloud_fetcher导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_analysis_flow():
    """测试分析流程"""
    try:
        from futures_analyzer import FuturesAnalysisEngine
        from cloud_data_fetcher import cloud_fetcher
        
        # 创建分析引擎
        engine = FuturesAnalysisEngine()
        print("✅ 分析引擎创建成功")
        
        # 测试数据加载方法
        position_data = engine.data_manager.load_position_data()
        print(f"✅ 数据加载方法可用，当前数据: {len(position_data)} 个文件")
        
        # 测试分析方法
        if position_data:
            results = engine._analyze_positions(position_data)
            print(f"✅ 分析方法可用，分析了 {len(results)} 个合约")
        else:
            print("ℹ️ 暂无数据文件，跳过分析测试")
        
        return True
    except Exception as e:
        print(f"❌ 分析流程测试失败: {e}")
        return False

def main():
    print("🔧 测试修复后的代码...")
    print("=" * 50)
    
    # 测试导入
    print("1. 测试模块导入...")
    import_ok = test_imports()
    
    # 测试分析流程
    print("\n2. 测试分析流程...")
    flow_ok = test_analysis_flow()
    
    print("\n" + "=" * 50)
    if import_ok and flow_ok:
        print("🎉 所有测试通过！修复成功。")
        print("💡 建议：现在可以重新运行Streamlit应用")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    return import_ok and flow_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 