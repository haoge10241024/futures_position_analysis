#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪持仓数据获取器
基于"交易席位"项目的数据获取逻辑
使用 ak.futures_hold_pos_sina() 获取持仓数据
"""

import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time
import random
from typing import Dict, List, Optional, Tuple
import warnings
import os

warnings.filterwarnings('ignore')

# 品种名称映射
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


class SinaPositionFetcher:
    """新浪持仓数据获取器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化数据获取器
        
        Args:
            data_dir: 数据保存目录
        """
        self.data_dir = data_dir
        self.symbol_names = SYMBOL_NAMES
        self.exchange_symbols = EXCHANGE_SYMBOLS
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_main_contract(self, symbol: str, date_str: str) -> Optional[str]:
        """
        获取主力合约（简化版）
        
        Args:
            symbol: 品种代码
            date_str: 日期 YYYYMMDD
            
        Returns:
            主力合约代码
        """
        try:
            # 解析日期
            date = datetime.strptime(date_str, '%Y%m%d')
            current_year = date.year
            current_month = date.month
            
            # 确定主力合约月份（简化逻辑）
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
                # 股指期货使用当前月
                year_suffix = str(current_year)[-2:]
                month_suffix = f"{current_month:02d}"
                return f"{symbol}{year_suffix}{month_suffix}"
            else:
                # 默认使用奇数月
                main_months = ['01', '03', '05', '07', '09', '11']
            
            # 选择最近的主力月份
            year_suffix = str(current_year)[-2:]
            
            # 找到当前月份之后的第一个主力月份
            main_month = None
            for month in main_months:
                if int(month) >= current_month:
                    main_month = month
                    break
            
            if not main_month:
                # 如果当前月份已经过了所有主力月份，使用下一年的第一个月份
                year_suffix = str(current_year + 1)[-2:]
                main_month = main_months[0]
            
            # 构造主力合约
            main_contract = f"{symbol}{year_suffix}{main_month}"
            
            return main_contract
            
        except Exception as e:
            print(f"获取{symbol}主力合约失败: {e}")
            return None
    
    def fetch_single_contract_data(self, contract: str, date_str: str, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        获取单个合约的持仓数据
        
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
            for attempt in range(3):  # 重试3次
                try:
                    df = ak.futures_hold_pos_sina(
                        symbol=position_type,
                        contract=contract,
                        date=date_str
                    )
                    
                    if df is not None and not df.empty:
                        df = df.copy()
                        
                        # 标准化列名
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
                    if attempt == 2:  # 最后一次尝试
                        print(f"  获取{contract} {position_type}失败: {str(e)[:50]}")
                    time.sleep(random.uniform(0.5, 1.0))
        
        return result
    
    def convert_to_exchange_format(self, all_data: List[pd.DataFrame], exchange_name: str) -> Dict[str, pd.DataFrame]:
        """
        将新浪数据转换为按交易所格式（兼容现有系统）
        
        Args:
            all_data: 原始数据列表
            exchange_name: 交易所名称
            
        Returns:
            按品种分组的数据字典
        """
        if not all_data:
            return {}
        
        # 合并所有数据
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # 按品种和类型分组
        result = {}
        
        for symbol in combined_df['symbol'].unique():
            symbol_data = combined_df[combined_df['symbol'] == symbol].copy()
            
            # 为每个品种创建一个sheet
            symbol_name = self.symbol_names.get(symbol, symbol)
            sheet_name = f"{symbol_name}({symbol})"
            
            # 按持仓类型分组，创建统一的表格
            # 格式：排名 | 会员简称 | 成交量 | 多单持仓 | 空单持仓 | 持仓变化
            pivot_data = []
            
            # 获取所有会员席位
            all_seats = set()
            for _, row in symbol_data.iterrows():
                all_seats.add(row['会员简称'])
            
            # 为每个席位创建一行数据
            for i, seat in enumerate(sorted(all_seats)[:20], 1):  # 取前20名
                seat_data = {'排名': i, '会员简称': seat}
                
                # 获取成交量
                volume_row = symbol_data[
                    (symbol_data['会员简称'] == seat) & 
                    (symbol_data['position_type'] == '成交量')
                ]
                seat_data['成交量'] = int(volume_row['成交量'].iloc[0]) if not volume_row.empty else 0
                
                # 获取多单持仓
                long_row = symbol_data[
                    (symbol_data['会员简称'] == seat) & 
                    (symbol_data['position_type'] == '多单持仓')
                ]
                seat_data['多单持仓'] = int(long_row['持仓量'].iloc[0]) if not long_row.empty else 0
                seat_data['多单变化'] = int(long_row['比上交易增减'].iloc[0]) if not long_row.empty else 0
                
                # 获取空单持仓
                short_row = symbol_data[
                    (symbol_data['会员简称'] == seat) & 
                    (symbol_data['position_type'] == '空单持仓')
                ]
                seat_data['空单持仓'] = int(short_row['持仓量'].iloc[0]) if not short_row.empty else 0
                seat_data['空单变化'] = int(short_row['比上交易增减'].iloc[0]) if not short_row.empty else 0
                
                pivot_data.append(seat_data)
            
            if pivot_data:
                result[sheet_name] = pd.DataFrame(pivot_data)
        
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
        print(f"\n正在获取{exchange_name}数据...")
        
        if exchange_name not in self.exchange_symbols:
            print(f"未知交易所: {exchange_name}")
            return {}
        
        symbols = self.exchange_symbols[exchange_name]
        all_data = []
        success_count = 0
        
        for symbol in symbols:
            try:
                # 获取主力合约
                main_contract = self.get_main_contract(symbol, trade_date)
                
                if not main_contract:
                    continue
                
                print(f"  {symbol} ({self.symbol_names.get(symbol, symbol)}) - {main_contract}...", end="")
                
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
        
        print(f"{exchange_name}数据获取完成: {success_count}/{len(symbols)} 个品种成功")
        
        # 转换为交易所格式
        return self.convert_to_exchange_format(all_data, exchange_name)
    
    def save_to_excel(self, data_dict: Dict[str, pd.DataFrame], filename: str):
        """
        保存数据到Excel文件
        
        Args:
            data_dict: 数据字典
            filename: 文件名
        """
        if not data_dict:
            print(f"  {filename}: 无数据，跳过保存")
            return
        
        save_path = os.path.join(self.data_dir, filename)
        
        try:
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                for sheet_name, df in data_dict.items():
                    # 清理sheet名称
                    clean_name = sheet_name[:31].replace("/", "-").replace("*", "")
                    df.to_excel(writer, sheet_name=clean_name, index=False)
            
            print(f"  ✅ {filename}: 已保存 {len(data_dict)} 个品种")
        except Exception as e:
            print(f"  ❌ {filename}: 保存失败 - {e}")


def demo_sina_fetcher():
    """演示新浪数据获取器"""
    
    print("=" * 80)
    print("新浪持仓数据获取器演示")
    print("=" * 80)
    
    fetcher = SinaPositionFetcher()
    
    # 测试获取大商所数据
    trade_date = datetime.now().strftime('%Y%m%d')
    print(f"\n测试日期: {trade_date}")
    
    data = fetcher.fetch_exchange_data("大商所", trade_date)
    
    if data:
        print(f"\n成功获取 {len(data)} 个品种的数据")
        print("\n品种列表:")
        for sheet_name in data.keys():
            print(f"  - {sheet_name}")
        
        # 保存数据
        fetcher.save_to_excel(data, "大商所持仓.xlsx")
    else:
        print("\n未获取到数据")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_sina_fetcher()

