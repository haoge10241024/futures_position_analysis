#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成数据获取器 - 完整集成"交易席位"项目的数据获取逻辑
同时保持与现有分析系统的兼容性
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '交易席位'))

import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time
import random
from typing import Dict, List, Optional
import warnings

warnings.filterwarnings('ignore')

# 从交易席位项目导入核心模块
try:
    from 交易席位.positioning_data_fetcher import PositioningDataFetcher, SYMBOL_NAMES
    from 交易席位.positioning_data_processor import PositioningDataProcessor
    from 交易席位.positioning_data_storage import PositioningDataStorage
except ImportError:
    print("警告: 无法导入交易席位模块，将使用本地实现")
    SYMBOL_NAMES = {
        'A': '豆一', 'AG': '白银', 'AL': '沪铝', 'AU': '黄金', 'B': '豆二',
        'BU': '沥青', 'C': '玉米', 'CF': '棉花', 'CU': '沪铜', 'CY': '棉纱',
        'EB': '苯乙烯', 'EG': '乙二醇', 'FG': '玻璃', 'FU': '燃油', 'HC': '热卷',
        'I': '铁矿石', 'J': '焦炭', 'JD': '鸡蛋', 'JM': '焦煤', 'L': '聚乙烯',
        'LC': '碳酸锂', 'LH': '生猪', 'LU': '低硫燃料油', 'M': '豆粕', 'MA': '甲醇',
        'NI': '镍', 'NR': '20号胶', 'OI': '菜籽油', 'P': '棕榈油', 'PB': '铅',
        'PF': '短纤', 'PG': '液化石油气', 'PP': '聚丙烯', 'PR': '瓶片', 'PS': '多晶硅',
        'PX': '对二甲苯', 'RB': '螺纹钢', 'RM': '菜籽粕', 'RU': '天然橡胶', 'SA': '纯碱',
        'SF': '硅铁', 'SI': '工业硅', 'SM': '锰硅', 'SN': '锡', 'SP': '纸浆',
        'SR': '白糖', 'SS': '不锈钢', 'TA': 'PTA', 'UR': '尿素', 'V': 'PVC',
        'Y': '豆油', 'ZN': '锌'
    }

# 交易所品种映射
EXCHANGE_SYMBOLS = {
    "大商所": ['A', 'B', 'C', 'M', 'Y', 'P', 'I', 'J', 'JM', 'JD', 'L', 'PP', 'V', 'EB', 'EG', 'PG', 'LH'],
    "郑商所": ['CF', 'CY', 'FG', 'MA', 'OI', 'RM', 'SA', 'SF', 'SI', 'SM', 'SR', 'TA', 'UR', 'PF'],
    "上期所": ['AL', 'AU', 'AG', 'BU', 'CU', 'FU', 'HC', 'NI', 'PB', 'RB', 'RU', 'SN', 'SP', 'SS', 'ZN', 'NR', 'LU'],
    "中金所": ['IC', 'IF', 'IH', 'IM', 'T', 'TF', 'TS', 'TL'],
    "广期所": ['LC', 'SI']
}


class IntegratedDataFetcher:
    """
    集成数据获取器
    - 使用"交易席位"项目的数据获取方法
    - 输出与现有系统兼容的格式
    """
    
    def __init__(self, data_dir: str = "data", basis_data_path: str = None):
        """
        初始化集成数据获取器
        
        Args:
            data_dir: 数据保存目录
            basis_data_path: 基差数据路径（用于获取准确的主力合约）
        """
        self.data_dir = data_dir
        self.symbol_names = SYMBOL_NAMES
        self.exchange_symbols = EXCHANGE_SYMBOLS
        self.ensure_data_directory()
        
        # 设置基差数据路径
        if basis_data_path:
            self.basis_data_path = Path(basis_data_path)
        else:
            # 默认路径：交易席位/basis
            default_basis_path = Path(__file__).parent / "交易席位" / "basis"
            if default_basis_path.exists():
                self.basis_data_path = default_basis_path
                print(f"✅ 找到基差数据目录: {self.basis_data_path}")
            else:
                self.basis_data_path = None
                print("⚠️ 未找到基差数据，将使用简化的主力合约推测方法")
        
        print("✅ 集成数据获取器已初始化（使用交易席位数据获取逻辑）")
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_main_contract_from_basis(self, symbol: str, date_str: str) -> Optional[str]:
        """
        从基差数据中获取主力合约（最准确的方法）
        
        Args:
            symbol: 品种代码
            date_str: 日期 YYYYMMDD
            
        Returns:
            主力合约代码
        """
        if not self.basis_data_path:
            return None
        
        basis_file = self.basis_data_path / symbol / "basis_data.csv"
        
        if not basis_file.exists():
            return None
        
        try:
            df = pd.read_csv(basis_file)
            
            if 'date' not in df.columns or 'dominant_contract' not in df.columns:
                return None
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
            target_date = datetime.strptime(date_str, '%Y%m%d')
            
            # 查找对应日期的主力合约
            matching_rows = df[df['date'] == target_date]
            
            if not matching_rows.empty:
                contract = str(matching_rows.iloc[0]['dominant_contract']).strip()
                if contract and contract != 'nan':
                    # 修复合约代码格式
                    contract = self._fix_contract_code(contract, symbol)
                    return contract
            
            return None
            
        except Exception as e:
            return None
    
    def _fix_contract_code(self, contract: str, symbol: str) -> str:
        """
        修复合约代码格式
        如果数字部分只有3位，在前面补2
        
        Args:
            contract: 原始合约代码
            symbol: 品种代码
            
        Returns:
            修复后的合约代码
        """
        if not contract:
            return contract
        
        import re
        match = re.match(r'([A-Za-z]+)(\d+)', contract.upper())
        
        if match:
            prefix = match.group(1)
            digits = match.group(2)
            
            # 如果数字部分只有3位，在前面补2
            if len(digits) == 3:
                return f"{prefix}2{digits}"
            else:
                return contract
        else:
            return contract
    
    def get_main_contract_from_symbol(self, symbol: str, date_str: str) -> Optional[str]:
        """
        获取主力合约（简化版）
        
        Args:
            symbol: 品种代码
            date_str: 日期 YYYYMMDD
            
        Returns:
            主力合约代码
        """
        try:
            date = datetime.strptime(date_str, '%Y%m%d')
            current_year = date.year
            current_month = date.month
            
            # 确定主力合约月份
            if symbol in ['RB', 'HC']:  # 螺纹钢、热卷
                main_months = ['01', '05', '10']
            elif symbol in ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN']:  # 有色金属
                main_months = ['03', '06', '09', '12']
            elif symbol in ['I', 'J', 'JM']:  # 黑色系
                main_months = ['01', '05', '09']
            elif symbol in ['M', 'Y', 'P', 'A']:  # 油脂油料
                main_months = ['01', '05', '09']
            elif symbol in ['CF', 'SR', 'TA']:  # 郑商所主力
                main_months = ['01', '05', '09']
            elif symbol in ['IC', 'IF', 'IH']:  # 股指期货
                year_suffix = str(current_year)[-2:]
                month_suffix = f"{current_month:02d}"
                return f"{symbol}{year_suffix}{month_suffix}"
            else:
                main_months = ['01', '03', '05', '07', '09', '11']
            
            # 选择最近的主力月份
            year_suffix = str(current_year)[-2:]
            
            main_month = None
            for month in main_months:
                if int(month) >= current_month:
                    main_month = month
                    break
            
            if not main_month:
                year_suffix = str(current_year + 1)[-2:]
                main_month = main_months[0]
            
            main_contract = f"{symbol}{year_suffix}{main_month}"
            return main_contract
            
        except Exception as e:
            print(f"  获取{symbol}主力合约失败: {e}")
            return None
    
    def fetch_single_contract_data(self, contract: str, date_str: str, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        获取单个合约的持仓数据（使用交易席位的方法）
        
        Args:
            contract: 合约代码
            date_str: 日期 YYYYMMDD
            symbol: 品种代码
            
        Returns:
            持仓数据字典
        """
        position_types = ["成交量", "多单持仓", "空单持仓"]
        result = {}
        
        for position_type in position_types:
            for attempt in range(3):
                try:
                    df = ak.futures_hold_pos_sina(
                        symbol=position_type,
                        contract=contract,
                        date=date_str
                    )
                    
                    if df is not None and not df.empty:
                        df = df.copy()
                        
                        # 标准化列名（与交易席位项目一致）
                        if len(df.columns) >= 4:
                            if position_type in ["多单持仓", "空单持仓"]:
                                df.columns = ['排名', '会员简称', '持仓量', '比上交易增减']
                            elif position_type == "成交量":
                                df.columns = ['排名', '会员简称', '成交量', '比上交易增减']
                        
                        # 添加元数据
                        df['date'] = date_str
                        df['contract'] = contract
                        df['position_type'] = position_type
                        df['symbol'] = symbol
                        
                        result[position_type] = df
                        break
                    else:
                        time.sleep(random.uniform(0.3, 0.6))
                        
                except Exception as e:
                    if attempt == 2:
                        print(f"    获取{contract} {position_type}失败: {str(e)[:50]}")
                    time.sleep(random.uniform(0.5, 1.0))
        
        return result
    
    def convert_to_exchange_format(self, all_data: List[pd.DataFrame], exchange_name: str) -> Dict[str, pd.DataFrame]:
        """
        将持仓数据转换为按交易所Excel格式（兼容现有分析系统）
        
        Args:
            all_data: 原始数据列表
            exchange_name: 交易所名称
            
        Returns:
            按品种分组的数据字典（用于保存为Excel的多个sheet）
        """
        if not all_data:
            return {}
        
        # 合并所有数据
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 按品种分组
        result = {}
        
        for symbol in combined_df['symbol'].unique():
            symbol_data = combined_df[combined_df['symbol'] == symbol].copy()
            
            # 为每个品种创建一个sheet
            symbol_name = self.symbol_names.get(symbol, symbol)
            sheet_name = f"{symbol_name}({symbol})"
            
            # 获取各类型数据（保持原始排名）
            long_data = symbol_data[symbol_data['position_type'] == '多单持仓'].copy()
            short_data = symbol_data[symbol_data['position_type'] == '空单持仓'].copy()
            volume_data = symbol_data[symbol_data['position_type'] == '成交量'].copy()
            
            # 如果没有任何数据，跳过
            if long_data.empty and short_data.empty and volume_data.empty:
                continue
            
            # 合并数据：以多单持仓为主，补充其他数据
            if not long_data.empty:
                # 使用多单持仓的排名和席位
                merged = long_data[['排名', '会员简称', '持仓量', '比上交易增减']].copy()
                merged.columns = ['排名', '会员简称', '多单持仓', '多单变化']
            elif not short_data.empty:
                # 如果没有多单数据，使用空单数据
                merged = short_data[['排名', '会员简称']].copy()
                merged['多单持仓'] = 0
                merged['多单变化'] = 0
            else:
                # 只有成交量数据
                merged = volume_data[['排名', '会员简称']].copy()
                merged['多单持仓'] = 0
                merged['多单变化'] = 0
            
            # 添加空单持仓数据（通过会员简称匹配）
            if not short_data.empty:
                short_dict = dict(zip(short_data['会员简称'], 
                                     zip(short_data['持仓量'], short_data['比上交易增减'])))
                merged['空单持仓'] = merged['会员简称'].map(lambda x: int(short_dict.get(x, (0, 0))[0]))
                merged['空单变化'] = merged['会员简称'].map(lambda x: int(short_dict.get(x, (0, 0))[1]))
            else:
                merged['空单持仓'] = 0
                merged['空单变化'] = 0
            
            # 添加成交量数据（通过会员简称匹配）
            if not volume_data.empty:
                volume_dict = dict(zip(volume_data['会员简称'], volume_data['成交量']))
                merged['成交量'] = merged['会员简称'].map(lambda x: int(volume_dict.get(x, 0)))
            else:
                merged['成交量'] = 0
            
            # 确保数值类型
            for col in ['多单持仓', '多单变化', '空单持仓', '空单变化', '成交量']:
                if col in merged.columns:
                    merged[col] = pd.to_numeric(merged[col], errors='coerce').fillna(0).astype(int)
            
            # 重新排列列的顺序（与原系统一致）
            column_order = ['排名', '会员简称', '成交量', '多单持仓', '多单变化', '空单持仓', '空单变化']
            existing_cols = [col for col in column_order if col in merged.columns]
            merged = merged[existing_cols]
            
            # 只保留前20行
            merged = merged.head(20)
            
            if len(merged) > 0:
                result[sheet_name] = merged
        
        return result
    
    def fetch_exchange_data(self, exchange_name: str, trade_date: str) -> Dict[str, pd.DataFrame]:
        """
        获取指定交易所的所有品种持仓数据
        
        Args:
            exchange_name: 交易所名称
            trade_date: 交易日期 YYYYMMDD
            
        Returns:
            按品种分组的数据字典
        """
        print(f"\n正在获取{exchange_name}数据（使用交易席位方法）...")
        
        if exchange_name not in self.exchange_symbols:
            print(f"  未知交易所: {exchange_name}")
            return {}
        
        symbols = self.exchange_symbols[exchange_name]
        all_data = []
        success_count = 0
        
        for symbol in symbols:
            try:
                # 优先从基差数据获取主力合约
                main_contract = self.get_main_contract_from_basis(symbol, trade_date)
                
                # 如果基差数据中没有，使用简化推测方法
                if not main_contract:
                    main_contract = self.get_main_contract_from_symbol(symbol, trade_date)
                
                if not main_contract:
                    print(f"  {symbol} ({self.symbol_names.get(symbol, symbol)}) - 无法确定主力合约 ❌")
                    continue
                
                print(f"  {symbol} ({self.symbol_names.get(symbol, symbol)}) - {main_contract}...", end="", flush=True)
                
                # 获取合约数据
                contract_data = self.fetch_single_contract_data(main_contract, trade_date, symbol)
                
                if contract_data:
                    # 将所有类型的数据添加到列表
                    for data_type, df in contract_data.items():
                        all_data.append(df)
                    print(" ✅")
                    success_count += 1
                else:
                    print(" ❌")
                
                # 避免请求过快
                time.sleep(random.uniform(0.5, 1.0))
                
            except Exception as e:
                print(f" ❌ {str(e)[:30]}")
                continue
        
        print(f"  {exchange_name}数据获取完成: {success_count}/{len(symbols)} 个品种成功")
        
        # 转换为交易所Excel格式
        return self.convert_to_exchange_format(all_data, exchange_name)
    
    def save_to_excel(self, data_dict: Dict[str, pd.DataFrame], filename: str):
        """
        保存数据到Excel文件（兼容现有系统格式）
        
        Args:
            data_dict: 数据字典
            filename: 文件名
        """
        if not data_dict:
            print(f"    {filename}: 无数据，跳过保存")
            return
        
        save_path = os.path.join(self.data_dir, filename)
        
        try:
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                for sheet_name, df in data_dict.items():
                    # 清理sheet名称
                    clean_name = sheet_name[:31].replace("/", "-").replace("*", "")
                    df.to_excel(writer, sheet_name=clean_name, index=False)
            
            print(f"    ✅ {filename}: 已保存 {len(data_dict)} 个品种")
        except Exception as e:
            print(f"    ❌ {filename}: 保存失败 - {e}")
    
    def fetch_all_exchanges_data(self, trade_date: str, progress_callback=None) -> bool:
        """
        获取所有交易所的数据
        
        Args:
            trade_date: 交易日期 YYYYMMDD
            progress_callback: 进度回调函数
            
        Returns:
            是否成功
        """
        print("\n" + "=" * 80)
        print("使用集成数据获取器（交易席位方法）")
        print("=" * 80)
        
        exchanges = {
            "大商所": "大商所持仓.xlsx",
            "中金所": "中金所持仓.xlsx",
            "郑商所": "郑商所持仓.xlsx",
            "上期所": "上期所持仓.xlsx",
            "广期所": "广期所持仓.xlsx"
        }
        
        success_count = 0
        total_exchanges = len(exchanges)
        
        for i, (exchange_name, filename) in enumerate(exchanges.items()):
            if progress_callback:
                progress = i / total_exchanges * 0.6
                progress_callback(f"正在获取 {exchange_name} 数据（交易席位方法）...", progress)
            
            try:
                # 获取交易所数据
                data_dict = self.fetch_exchange_data(exchange_name, trade_date)
                
                if data_dict:
                    # 保存数据
                    self.save_to_excel(data_dict, filename)
                    success_count += 1
                else:
                    print(f"    ⚠️ {exchange_name} 数据获取失败")
                    
            except Exception as e:
                print(f"    ❌ {exchange_name} 数据获取失败: {str(e)[:50]}")
                continue
        
        if progress_callback:
            progress_callback("持仓数据获取完成", 0.6)
        
        print(f"\n{'='*80}")
        print(f"数据获取完成: {success_count}/{total_exchanges} 个交易所成功")
        print(f"{'='*80}\n")
        
        return success_count >= 3


def demo_integrated_fetcher():
    """演示集成数据获取器"""
    
    print("=" * 80)
    print("集成数据获取器演示")
    print("=" * 80)
    
    fetcher = IntegratedDataFetcher("test_integrated_data")
    
    # 测试获取大商所数据
    trade_date = input("\n请输入测试日期（YYYYMMDD，例如20241101）: ").strip()
    
    if len(trade_date) != 8 or not trade_date.isdigit():
        print("日期格式不正确")
        return
    
    data = fetcher.fetch_exchange_data("大商所", trade_date)
    
    if data:
        print(f"\n成功获取 {len(data)} 个品种的数据")
        print("\n品种列表:")
        for sheet_name in data.keys():
            print(f"  - {sheet_name}")
        
        # 保存数据
        fetcher.save_to_excel(data, "大商所持仓.xlsx")
        
        # 显示第一个品种的数据示例
        first_sheet = list(data.keys())[0]
        print(f"\n第一个品种 '{first_sheet}' 的数据示例:")
        print(data[first_sheet].head())
    else:
        print("\n未获取到数据")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_integrated_fetcher()

