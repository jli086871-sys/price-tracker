# 📊 材料涨价监测站

第一时间发现金属 + 能源 + 化工 + 电子特气涨价机会。

## 🔗 在线访问

**https://jli086871-sys.github.io/price-tracker/**

## 📁 文件结构

```
price-tracker/
├── index.html               # 主页面（三大板块：价格监控 / 资讯摘要 / 涨幅排行）
├── data.json                # 价格数据库（27个品种 + 22条新闻资讯）
├── scripts/
│   └── scrape_prices.py     # 🐍 全品种爬虫（5大交易所 22品种 自动抓取）
├── .github/workflows/
│   └── scrape.yml           # ⏰ 定时器（工作日 08:30 + 17:00 自动运行）
└── README.md
```

## 📊 追踪品种一览

### ✅ 自动更新（免费 · 每日自动抓取）

| 交易所 | 品种 |
|:------|:-----|
| **上期所 (SHFE)** | 沪铜、沪铝、沪锌、沪铅、沪镍、沪锡、螺纹钢、热轧卷板、沪金、沪银 |
| **广期所 (GFEX)** | 碳酸锂、工业硅 |
| **大商所 (DCE)** | 铁矿石、焦炭、焦煤、乙二醇、PVC、PP、苯乙烯、LPG |
| **郑商所 (CZCE)** | PTA、甲醇、纯碱、尿素 |
| **上海能源中心 (INE)** | 原油 |

### ✏️ 手动更新（建议一周一次）

| 品类 | 品种 | 来源 | 原因 |
|:----|:-----|:----|:----|
| 电子特气 | **六氟化钨 (6N)**、**三氟化氮**、**6N氦气**、硅烷 | 百川盈孚/隆众 | 需付费会员，无公开API |

**手动方法：** GitHub网页上编辑 data.json → 找到品种的 `price` 字段 → 改数字 → Commit changes（5分钟搞定）

## 🚀 部署说明

```bash
git clone https://github.com/jli086871-sys/price-tracker.git
cd price-tracker
# 本地测试
python -m http.server 8080
# 浏览器访问 http://localhost:8080
```

推送至 GitHub 后，GitHub Pages 自动部署，爬虫自动运行。

## 📝 手动更新特气数据

在 GitHub 网页上编辑 `data.json`，找到对应品种的 `price` 字段，改数字 → **Commit changes**。
- 建议频次：每周一更新一次（5分钟）

## ⚠️ 说明

- 期货数据为前一交易日收盘价，数据源自新浪财经公开行情
- 特气/化工现货数据需手动编辑，百川盈孚/隆众无免费 API
- 所有数据仅供研究参考，不构成投资建议
