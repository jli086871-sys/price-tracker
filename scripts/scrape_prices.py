"""
材料涨价监测站 · 全品种价格爬虫 V2
覆盖5大交易所22个期货品种+新闻资讯整理

自动更新品种列表：
  SHFE : 铜/铝/锌/铅/镍/锡/螺纹钢/热轧卷板/黄金/白银
  GFEX : 碳酸锂/工业硅
  DCE  : 铁矿石/焦炭/焦煤/乙二醇/PVC/PP/苯乙烯/LPG
  CZCE : PTA/甲醇/纯碱/尿素
  INE  : 原油

运行：每日08:30 / 17:00（GitHub Actions自动触发）
"""

import json
import os
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json")


def load_data():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"data.json not found: {DATA_PATH}")


def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] data.json saved, {len(data['products'])} products")


def find_product(data, pid):
    for p in data["products"]:
        if p["id"] == pid:
            return p
    return None


def update_price(product, new_price):
    if new_price is None or new_price <= 0:
        return False
    today = datetime.now().strftime("%Y-%m-%d")
    old = product.get("price")
    product["prev_close"] = old if old else new_price
    product["price"] = new_price
    if "prices" not in product:
        product["prices"] = []
    if product["prices"] and product["prices"][-1]["date"] == today:
        product["prices"][-1]["price"] = new_price
    else:
        product["prices"].append({"date": today, "price": new_price})
    changef = f"+{(new_price - old)/old*100:.1f}%" if old and old > 0 and new_price > old else \
             f"{(new_price - old)/old*100:.1f}%" if old and old > 0 else ""
    print(f"  [{product['name']}] {old} → {new_price} {changef}")
    return True


# ====================================================================
# 新浪财经免费API （覆盖国内所有期货交易所主力合约实时行情）
# ====================================================================
# 格式: https://hq.sinajs.cn/list=SHFE_cu2508,GFEX_lc2508,...
# 返回: var hq_str_SHFE_cu2508="名称,开盘,最高,最新,最低,昨收,买价,卖价,持仓,成交,日期,时间"

SINA_URL = "https://hq.sinajs.cn/list="

# 品种 → 新浪合约代码映射表
CONTRACTS = {
    "copper":   {"sina": "SHFE_cu2508", "divisor": 1, "unit": "元/吨"},
    "aluminum": {"sina": "SHFE_al2508", "divisor": 1, "unit": "元/吨"},
    "zinc":     {"sina": "SHFE_zn2508", "divisor": 1, "unit": "元/吨"},
    "lead":     {"sina": "SHFE_pb2508", "divisor": 1, "unit": "元/吨"},
    "nickel":   {"sina": "SHFE_ni2509", "divisor": 1, "unit": "元/吨"},
    "tin":      {"sina": "SHFE_sn2507", "divisor": 1, "unit": "元/吨"},
    "rebar":    {"sina": "SHFE_rb2610", "divisor": 1, "unit": "元/吨"},
    "hot_rolled": {"sina": "SHFE_hc2610", "divisor": 1, "unit": "元/吨"},
    "gold":     {"sina": "SHFE_au2508", "divisor": 1, "unit": "元/克"},
    "silver":   {"sina": "SHFE_ag2508", "divisor": 1, "unit": "元/千克"},
    "lithium_carbonate": {"sina": "GFEX_lc2508", "divisor": 1, "unit": "元/吨"},
    "industrial_silicon": {"sina": "GFEX_si2509", "divisor": 1, "unit": "元/吨"},
    "iron_ore": {"sina": "DCE_i2509", "divisor": 1, "unit": "元/吨"},
    "coke":     {"sina": "DCE_j2509", "divisor": 1, "unit": "元/吨"},
    "coking_coal": {"sina": "DCE_jm2509", "divisor": 1, "unit": "元/吨"},
    "eg":       {"sina": "DCE_eg2509", "divisor": 1, "unit": "元/吨"},
    "pvc":      {"sina": "DCE_v2509", "divisor": 1, "unit": "元/吨"},
    "pp":       {"sina": "DCE_pp2509", "divisor": 1, "unit": "元/吨"},
    "styrene":  {"sina": "DCE_eb2509", "divisor": 1, "unit": "元/吨"},
    "lpg":      {"sina": "DCE_pg2509", "divisor": 1, "unit": "元/吨"},
    "pta":      {"sina": "CZCE_TA509", "divisor": 1, "unit": "元/吨"},
    "methanol": {"sina": "CZCE_MA509", "divisor": 1, "unit": "元/吨"},
    "soda_ash": {"sina": "CZCE_SA509", "divisor": 1, "unit": "元/吨"},
    "urea":     {"sina": "CZCE_UR509", "divisor": 1, "unit": "元/吨"},
    "crude_oil": {"sina": "INE_sc2508", "divisor": 1, "unit": "元/桶"},
}


def fetch_sina_quotes():
    """批量抓取新浪财经行情——一次请求获取所有品种"""
    symbols = [cfg["sina"] for cfg in CONTRACTS.values()]
    # 分批请求（避免URL过长），每批10个
    results = {}
    batch_size = 10
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]
        url = SINA_URL + ",".join(batch)
        try:
            hs = {**HEADERS, "Referer": "https://finance.sina.com.cn"}
            r = requests.get(url, headers=hs, timeout=15)
            r.encoding = "gbk"
            for line in r.text.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                # 解析格式: var hq_str_SHFE_cu2508="..."
                m = re.search(r'var hq_str_(\w+)="(.+)"', line)
                if m:
                    sid = m.group(1)
                    parts = m.group(2).split(",")
                    if len(parts) >= 9:
                        name = parts[0]
                        open_p = try_float(parts[1])
                        high = try_float(parts[2]) if parts[2] else None
                        latest = try_float(parts[3]) if parts[3] else None
                        prev_close = try_float(parts[5]) if parts[5] else None
                        volume = parts[8]
                        date = parts[-2] if len(parts) >= 11 else ""
                        time_ = parts[-1] if len(parts) >= 12 else ""
                        if latest and latest > 0:
                            results[sid] = {
                                "price": latest, "prev_close": prev_close,
                                "volume": volume, "time": f"{date} {time_}"
                            }
            time.sleep(0.1)  # 批次间隔防封
        except Exception as e:
            print(f"  [WARN] 新浪行情批次请求失败: {e}")
    return results


def try_float(v):
    try:
        return float(v) if v else None
    except (ValueError, TypeError):
        return None


# ====================================================================
# 公开网页爬虫 —— 生意社 / 百川盈孚公开报价
# 这些品种的公开页面无需登录，可直接抓取
# ====================================================================

def scrape_100ppi_price(url, name):
    """爬取生意社（100ppi.com）公开报价页面的现货价格"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        # 尝试多种价格选择器
        for sel in [".price-today .strong", ".newprice", ".price_num",
                    ".hq_price", ".hq_price_span", ".price_value",
                    "span[class*='price']", "td[class*='price']"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                nums = re.findall(r'\d+\.?\d*', text.replace(",", ""))
                if nums:
                    price = float(nums[0])
                    print(f"  [100ppi] {name}: → {price}")
                    return price
        # 备用：搜所有常见价格标签
        for tag in ["strong", "span", "b", "div"]:
            for el in soup.find_all(tag):
                text = el.get_text(strip=True)
                if re.search(r'^\s*\d+[\.\d]*\s*(元|万|吨)', text):
                    nums = re.findall(r'\d+\.?\d*', text)
                    if nums:
                        price = float(nums[0])
                        print(f"  [100ppi] {name} (fn): → {price}")
                        return price
        print(f"  [100ppi] {name}: 未找到价格元素")
        return None
    except Exception as e:
        print(f"  [WARN] 100ppi {name} 爬取失败: {e}")
        return None


def scrape_smm_price(url, name):
    """爬取上海有色网（SMM）公开现货报价"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        # SMM 公开页面常用结构
        for sel in [".price", ".current-price", ".value", ".price-value",
                    "span[class*='price']", "div[class*='price']"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                nums = re.findall(r'\d+\.?\d*', text.replace(",", ""))
                if nums:
                    price = float(nums[0])
                    print(f"  [SMM] {name}: → {price}")
                    return price
        print(f"  [SMM] {name}: 未找到价格元素")
        return None
    except Exception as e:
        print(f"  [WARN] SMM {name} 爬取失败: {e}")
        return None


# 手动品种的公开爬虫配置
# 格式: { "品种id": ("url", "爬取函数", "描述") }
MANUAL_SCRAPERS = {
    "tungsten": (
        "https://www.100ppi.com/price/detail-1429.html",
        scrape_100ppi_price,
        "钨精矿"
    ),
    "anhydrous_hf": (
        "https://www.100ppi.com/price/detail-1008.html",
        scrape_100ppi_price,
        "无水氟化氢"
    ),
    "fluorspar": (
        "https://www.100ppi.com/price/detail-1441.html",
        scrape_100ppi_price,
        "萤石"
    ),
}


def run_manual_scrapers(data):
    """运行手动品种的公开网页爬虫"""
    print(f"\n[手动品种公开爬虫] 目标: {len(MANUAL_SCRAPERS)} 个")
    updated = 0
    for pid, (url, scraper_fn, name) in MANUAL_SCRAPERS.items():
        prod = find_product(data, pid)
        if not prod:
            print(f"  [SKIP] {name}: 未在data.json中找到")
            continue
        price = scraper_fn(url, name)
        if price and update_price(prod, price):
            updated += 1
    return updated


def main():
    print("=" * 55)
    print(f"材料涨价监测站 · 全品种价格爬虫 V2")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标品种: {len(CONTRACTS)} 个")
    print("=" * 55)

    data = load_data()
    quotes = fetch_sina_quotes()
    print(f"\n新浪行情返回: {len(quotes)} 个有效报价")
    if quotes:
        sample = list(quotes.items())[:3]
        for sid, q in sample:
            print(f"  例: {sid} → {q['price']} (昨收 {q['prev_close']})")

    updated = 0
    succeeded = []
    failed = []

    for pid, cfg in CONTRACTS.items():
        sid = cfg["sina"]
        q = quotes.get(sid)
        if q:
            price = q["price"] / cfg["divisor"] if cfg["divisor"] > 1 else q["price"]
            prod = find_product(data, pid)
            if prod:
                price = round(price, 2)
                if update_price(prod, price):
                    updated += 1
                    succeeded.append(pid)
                else:
                    failed.append(f"{pid}(无效价格)")
            else:
                failed.append(f"{pid}(未在data.json中找到)")
        else:
            failed.append(f"{pid}(新浪未返回数据)")

    # 运行公开网页爬虫（钨精矿/无水氟化氢/萤石）
    manual_updated = run_manual_scrapers(data)
    updated += manual_updated

    # 更新全局时间
    data["update_time"] = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*55}")
    print(f"更新统计: 成功 {updated}/{len(CONTRACTS) + len(MANUAL_SCRAPERS)} 个品种")
    if succeeded:
        print(f"✅ 期货自动: {', '.join(succeeded[:10])}{'...' if len(succeeded)>10 else ''}")
    if manual_updated:
        print(f"✅ 公开网页: 钨精矿/氟化氢/萤石 共 {manual_updated} 个已更新")
    if failed:
        print(f"❌ 未更新: {', '.join(failed[:8])}{'...' if len(failed)>8 else ''}")
    print(f"下次自动更新: 工作日 08:30 / 17:00 (UTC+8)")
    print(f"仍需手动维护: WF₆ / NF₃ / 6N氦气 / 硅烷（百川盈孚/隆众需付费会员）")
    print(f"{'='*55}")

    if updated > 0:
        save_data(data)
    else:
        print("[WARN] 本次无任何品种更新")


if __name__ == "__main__":
    main()
