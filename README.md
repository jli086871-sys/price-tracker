# 📊 材料涨价监测站

第一时间发现金属 + 电子特气 + 化工材料的涨价机会。

## 🔗 在线访问

GitHub Pages 开启后：`https://<你的用户名>.github.io/price-tracker/`

## 📁 文件结构

```
price-tracker/
├── index.html              # 主页面（可直接浏览器打开）
├── data.json               # 价格数据（核心——改这个文件更新数据）
├── scripts/
│   └── scrape_prices.py    # 🐍 爬虫脚本（自动抓取期货数据）
├── .github/workflows/
│   └── scrape.yml          # ⏰ GitHub Actions 定时器（工作日 08:30/17:00）
└── README.md
```

## 🚀 快速部署（5分钟）

### 方案A：GitHub Pages（推荐）

1. 在 GitHub 新建仓库：`price-tracker`（公开仓库）
2. 把本目录所有文件 push 上去
3. 进入仓库 Settings → Pages → 选 `main` 分支 `/root` → Save
4. ✅ 等2分钟，访问 `https://<你的用户名>.github.io/price-tracker/`

### 方案B：本地直接打开

直接用浏览器打开 `index.html`——不需要任何服务器，`data.json` 在同目录即可。

### 方案C：部署到其它免费托管

| 平台 | 操作 |
|:----|:----|
| **Vercel** | 导入 GitHub 仓库 → 自动部署，自动 HTTPS |
| **Cloudflare Pages** | 连 GitHub 仓库 → 免费全球 CDN |
| **Netlify** | 拖拽文件夹上传即可 |

## 📝 数据更新方式

### ✅ 期货自动更新（免费）
- 碳酸锂（广期所）、电解铜/铝（上期所）
- **爬虫自动化**：push 到 GitHub 后，`.github/workflows/scrape.yml` 会每天北京时间 **08:30 和 17:00** 自动运行
- 手动触发：GitHub 仓库 → Actions → Scrape Futures Prices → Run workflow

### ✏️ 特气手动更新
- WF₆、NF₃、6N氦气、硅烷、无水氟化氢等 → **因为百川盈孚/隆众无免费API**
- 直接在 GitHub 网页上编辑 `data.json` → 找到对应品种的 `price` 字段 → 改数字 → commit
- 网站自动刷新（GitHub Pages 通常 1-2 分钟生效）
- ⏰ 建议更新频次：**每周一更新一次**（5分钟搞定）

### 手动更新示例
```json
{
  "id": "wf6_6n",
  "name": "六氟化钨 (6N)",
  "price": 420,       ← 改成最新价格
  "prev_close": 380,
  "week_ago": 375,
  "month_ago": 120
}
```

## 📊 当前追踪品种

| 品种 | 数据源 | 更新方式 |
|:-----|:-------|:--------|
| 碳酸锂 (电池级) | 广期所主力合约 | ✅ 自动 |
| 电解铜 | 上期所主力合约 | ✅ 自动 |
| A00铝 | 上期所主力合约 | ✅ 自动 |
| 六氟化钨 (6N) | 百川盈孚 | ✏️ 手动 |
| 三氟化氮 (NF₃) | 百川盈孚 | ✏️ 手动 |
| 6N氦气 | 隆众资讯 | ✏️ 手动 |
| 钨精矿 | 生意社 | ✏️ 手动 |
| 无水氟化氢 | 百川盈孚 | ✏️ 手动 |
| 硅烷 (电子级) | 百川盈孚 | ✏️ 手动 |

## ⚙️ 添加新品种

1. 打开 `data.json`
2. 在 `products` 数组中添加一个新对象，格式参考现有品种
3. 包含字段：`id` / `name` / `category` / `unit` / `price` / `prices`(历史)
4. 前端自动渲染，无需改代码

## ⚠️ 说明

- 数据仅供研究参考，不构成投资建议
- 特气类数据依赖手动更新，频次决定实用性
- 期货数据为前一交易日收盘价，非实时行情
- 建议每周花5分钟更新特气数据，保持监测价值
