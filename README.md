# 🚀 期货持仓分析系统 v2.1

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)

> 🎯 **智能期货持仓分析系统，助您洞察市场先机**
> 
> 基于多维度数据分析的期货持仓策略系统，支持云端部署，具备智能容错和性能优化功能。

## ✨ 核心特性

### 🧠 智能分析策略
- **多空力量变化策略**：基于持仓变化分析市场趋势
- **蜘蛛网策略**：知情者与非知情者持仓对比分析
- **家人席位反向操作策略**：基于特定席位的反向操作信号

### 🚀 v2.1 新特性：增强超时处理机制
- **智能跳过功能**：遇到问题自动跳过，不影响整体流程
- **差异化超时设置**：广期所15秒，其他交易所30秒
- **线程+队列控制**：精确的超时控制和错误处理
- **最大化数据获取**：尝试获取所有5个交易所数据

### 📊 数据源覆盖
- **大商所**：大连商品交易所持仓数据
- **中金所**：中国金融期货交易所数据
- **郑商所**：郑州商品交易所数据
- **上期所**：上海期货交易所数据
- **广期所**：广州期货交易所数据（智能跳过）

### 🎨 可视化分析
- **期限结构分析**：期货合约价格结构可视化
- **持仓变化图表**：多维度持仓数据展示
- **策略信号面板**：实时策略信号显示
- **共振分析**：多策略信号共振识别

### ⚡ 性能优化
- **智能缓存系统**：Streamlit原生缓存 + 文件缓存
- **并发数据获取**：多线程并发处理
- **网络连接优化**：连接池复用 + 智能重试
- **增强超时处理**：精确超时控制，避免卡顿

## 🚀 快速开始

### 在线体验
🌐 **Streamlit Cloud**: [https://your-app-url.streamlit.app](https://your-app-url.streamlit.app)

### 本地部署

#### 1. 环境准备
```bash
# 克隆项目
git clone https://github.com/yourusername/futures-analysis.git
cd futures-analysis

# 安装依赖
pip install -r requirements.txt
```

#### 2. 启动应用
```bash
# 方式1：直接启动
streamlit run streamlit_app.py

# 方式2：使用启动脚本
python app.py
```

#### 3. 访问应用
打开浏览器访问：`http://localhost:8501`

## 📋 系统要求

### 基础环境
- **Python**: 3.8 或更高版本
- **内存**: 建议 2GB 以上
- **网络**: 稳定的互联网连接

### 核心依赖
```
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.21.0
plotly>=5.0.0
akshare>=1.13.0
openpyxl>=3.0.0
xlsxwriter>=3.0.0
requests>=2.28.0
```

## 🔧 配置说明

### 家人席位配置
在 `config.py` 中自定义家人席位：
```python
STRATEGY_CONFIG = {
    "家人席位反向操作策略": {
        "default_retail_seats": [
            "永安期货", "国泰君安", "海通期货", 
            "申银万国", "华泰期货", "中信期货"
        ]
    }
}
```

### 超时设置配置
系统自动配置差异化超时：
```python
price_exchanges = [
    {"market": "DCE", "name": "大商所", "timeout": 30},
    {"market": "CFFEX", "name": "中金所", "timeout": 30},
    {"market": "CZCE", "name": "郑商所", "timeout": 30},
    {"market": "SHFE", "name": "上期所", "timeout": 30},
    {"market": "GFEX", "name": "广期所", "timeout": 15},  # 智能跳过
]
```

## 📊 使用指南

### 基本操作流程

1. **选择交易日期**：在侧边栏选择要分析的交易日
2. **配置家人席位**：根据需要调整家人席位列表
3. **开始分析**：点击"开始分析"按钮
4. **查看结果**：在主界面查看分析结果和可视化图表

### 高级功能

#### 性能监控
- 在侧边栏查看缓存状态
- 监控数据获取成功率
- 查看系统性能指标

#### 错误处理
- 系统自动处理网络超时
- 智能跳过问题交易所
- 详细的错误提示信息

## 🎯 核心算法

### 多空力量变化策略
```python
def analyze_power_change(data):
    long_chg = data['total_long_chg']
    short_chg = data['total_short_chg']
    
    if long_chg > 0 and short_chg < 0:
        return "看多"
    elif long_chg < 0 and short_chg > 0:
        return "看空"
    else:
        return "中性"
```

### 家人席位反向操作策略
```python
def analyze_retail_reverse(data, retail_seats):
    # 看多信号：所有家人席位的空单持仓量变化为正，且多单持仓量变化为负或0
    # 看空信号：所有家人席位的多单持仓量变化为正，且空单持仓量变化为负或0
    
    for seat in active_seats:
        long_chg = seat['long_chg']
        short_chg = seat['short_chg']
        
        # 判断信号条件
        long_condition = short_chg > 0 and long_chg <= 0
        short_condition = long_chg > 0 and short_chg <= 0
```

### 增强超时处理机制
```python
def fetch_with_timeout(exchange, timeout=15):
    import threading, queue
    
    result_queue = queue.Queue()
    
    def fetch_data():
        try:
            result = api_call(exchange)
            result_queue.put(('success', result))
        except Exception as e:
            result_queue.put(('error', str(e)))
    
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        return None  # 超时，自动跳过
    
    return result_queue.get_nowait()
```

## 🔍 故障排除

### 常见问题

#### 1. 数据获取失败
**现象**：显示"数据获取失败"
**解决方案**：
- 检查网络连接
- 等待几分钟后重试
- 使用演示数据体验功能

#### 2. 广期所卡顿
**现象**：系统在广期所处停留过久
**解决方案**：
- v2.1版本已自动解决（15秒超时）
- 系统会自动跳过并继续分析

#### 3. 性能问题
**现象**：运行速度较慢
**解决方案**：
- 首次运行较慢属正常现象
- 后续运行会显著加速（缓存机制）
- 清理缓存可释放存储空间

### 技术支持

如遇到问题，请：
1. 查看 [故障排除文档](docs/TROUBLESHOOTING.md)
2. 提交 [GitHub Issue](https://github.com/yourusername/futures-analysis/issues)
3. 联系开发者：953534947@qq.com

## 📈 性能指标

### v2.1 性能提升

| 指标 | v1.0 | v2.0 | v2.1 | 改进幅度 |
|------|------|------|------|----------|
| 首次运行时间 | 3-5分钟 | 1-3分钟 | 1-2分钟 | 60%+ |
| 重复运行时间 | 3-5分钟 | 10-30秒 | 5-20秒 | 90%+ |
| 数据完整性 | 4/5交易所 | 4/5交易所 | 4-5/5交易所 | +25% |
| 系统稳定性 | 良好 | 优秀 | 卓越 | 显著提升 |

### 云端适配优化
- ✅ **智能超时控制**：15秒精确超时
- ✅ **自动容错处理**：遇到问题自动跳过
- ✅ **用户友好提示**：详细的状态信息
- ✅ **最大化数据获取**：尝试获取所有交易所数据

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式
1. **报告问题**：提交 Bug 报告或功能请求
2. **代码贡献**：提交 Pull Request
3. **文档改进**：完善文档和示例
4. **功能建议**：提出新功能想法

### 开发流程
```bash
# 1. Fork 项目
# 2. 创建功能分支
git checkout -b feature/your-feature

# 3. 提交更改
git commit -m "Add your feature"

# 4. 推送分支
git push origin feature/your-feature

# 5. 创建 Pull Request
```

详细信息请查看 [贡献指南](CONTRIBUTING.md)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 👨‍💻 作者信息

**7haoge**
- 📧 邮箱：953534947@qq.com
- 🐙 GitHub：[@yourusername](https://github.com/yourusername)
- 💼 专业：量化交易系统开发

## 🙏 致谢

感谢以下开源项目的支持：
- [Streamlit](https://streamlit.io/) - 优秀的Web应用框架
- [akshare](https://akshare.akfamily.xyz/) - 强大的金融数据接口
- [Plotly](https://plotly.com/) - 专业的数据可视化库
- [Pandas](https://pandas.pydata.org/) - 高效的数据处理工具

## 📊 项目统计

![GitHub stars](https://img.shields.io/github/stars/yourusername/futures-analysis?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/futures-analysis?style=social)
![GitHub issues](https://img.shields.io/github/issues/yourusername/futures-analysis)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/futures-analysis)

---

<div align="center">

**🚀 期货持仓分析系统 v2.1 - 智能分析，精准决策！**

[⭐ Star](https://github.com/yourusername/futures-analysis) | [🍴 Fork](https://github.com/yourusername/futures-analysis/fork) | [📝 Issues](https://github.com/yourusername/futures-analysis/issues) | [📖 Docs](docs/)

</div> 