"""
材料涨价监测站 · 自动价格爬虫
抓取来源：广期所(碳酸锂) + 上期所(铜/铝) + 生意社(钨)
运行方式：GitHub Actions 定时执行 或 本地 python scripts/scrape_prices.py

注意：本脚本只会更新 data.json 中的期货品种字段（price/prev_close/week_ago等）
      特气类品种（WF₆/NF₃/氦气等）需手动更新，因为百川盈孚没有免费 API
"""

import json
import os
import re
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.json")


def load_data():
    """加载现有数据"""
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"data.json 不存在: {DATA_PATH}")


def save_data(data):
    """保存数据"""
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] data.json 已更新，共 {len(data['products'])} 个品种")


def find_product(data, pid):
    """按 id 查找品种"""
    for p in data["products"]:
        if p["id"] == pid:
            return p
    return None


# ========================
#  爬虫函数
# ========================

def scrape_gfex_lithium():
    """广期所碳酸锂主力合约（免费公开数据）"""
    # 广期所行情页面：碳酸锂期货主力合约
    url = "http://www.gfex.com.cn/gfex/trends/quotesDaily.shtml"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        # 尝试从页面提取碳酸锂主力合约价格
        soup = BeautifulSoup(resp.text, "lxml")
        # 寻找碳酸锂2407等主力合约的行
        # 广期所页面结构较为复杂，这里用一个简化方案
        text = resp.text
        # 正则匹配碳酸锂合约价格：lc2507 或 lc2508 等格式
        # 寻找 "lc" + 年份后两位 + 月份 的价格
        matches = re.findall(r'lc\d{4}.*?(\d+\.?\d*)', text, re.IGNORECASE)
        if matches:
            # 取第一个匹配的价格
            price = float(matches[0])
            return price
        # 备用：尝试查询新浪财经接口（广期所公开数据）
        # 碳酸锂主力合约代码：lc2508（根据当前月份动态调整）
        sip = "https://hq.sinajs.cn/list=GFEX_lc2508"
        hs = {**HEADERS, "Referer": "https://finance.sina.com.cn"}
        r = requests.get(sip, headers=hs, timeout=10)
        r.encoding = "gbk"
        # 返回格式: var hq_str_GFEX_lc2508="名称,开盘价,最高价,最新价,...
        if r'var hq_str' in r.text:
            parts = r.text.split(',')
            if len(parts) > 3:
                price = float(parts[3])  # 最新价
                return price
    except Exception as e:
        print(f"[WARN] 广期所爬取失败: {e}")
    return None


def scrape_shfe_copper():
    """上期所沪铜主力合约（免费公开数据）"""
    # 使用新浪财经公开接口
    sip = "https://hq.sinajs.cn/list=SHFE_cu2508"
    try:
        hs = {**HEADERS, "Referer": "https://finance.sina.com.cn"}
        r = requests.get(sip, headers=hs, timeout=10)
        r.encoding = "gbk"
        if r'var hq_str' in r.text:
            parts = r.text.split(',')
            if len(parts) > 3:
                # 期货格式: 名称,开盘,最高,最新,最低,...
                price = float(parts[3]) / 10000  # 元/吨 → 万元/吨
                return round(price, 2)
    except Exception as e:
        print(f"[WARN] 上期所铜爬取失败: {e}")
    return None


def scrape_shfe_aluminum():
    """上期所沪铝主力合约"""
    sip = "https://hq.sinajs.cn/list=SHFE_al2508"
    try:
        hs = {**HEADERS, "Referer": "https://finance.sina.com.cn"}
        r = requests.get(sip, headers=hs, timeout=10)
        r.encoding = "gbk"
        if r'var hq_str' in r.text:
            parts = r.text.split(',')
            if len(parts) > 3:
                price = float(parts[3]) / 10000
                return round(price, 2)
    except Exception as e:
        print(f"[WARN] 上期所铝爬取失败: {e}")
    return None


def scrape_ccmn_tungsten():
    """长江有色金属网/生意社 钨精矿价格"""
    # 生意社——钨精矿公开报价
    url = "https://www.100ppi.com/price/detail-1429.html"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        # 寻找价格元素
        price_el = soup.select_one(".price-today .strong, .newprice, .price_num")
        if price_el:
            text = price_el.get_text(strip=True)
            nums = re.findall(r'\d+\.?\d*', text)
            if nums:
                return float(nums[0])
    except Exception as e:
        print(f"[WARN] 钨精矿爬取失败: {e}")
    return None


def update_product_price(product, new_price):
    """更新品种的当日价格，并维护历史价格序列"""
    if new_price is None or new_price <= 0:
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")

    # 更新当前价
    old_price = product.get("price")
    product["prev_close"] = old_price if old_price else new_price
    product["price"] = new_price

    # 更新历史价格序列
    if "prices" not in product:
        product["prices"] = []

    # 检查是否今天已有记录
    if product["prices"] and product["prices"][-1]["date"] == today_str:
        product["prices"][-1]["price"] = new_price
    else:
        product["prices"].append({"date": today_str, "price": new_price})

    print(f"  [{product['name']}] {old_price} → {new_price} {product.get('unit','')}")
    return True


# ========================
#  主逻辑
# ========================

def main():
    print("=" * 50)
    print(f"材料涨价监测站 · 价格爬虫")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    data = load_data()
    updated_count = 0

    # 1. 碳酸锂 ← 广期所
    print("\n[1/3] 爬取碳酸锂（广期所）...")
    li_price = scrape_gfex_lithium()
    if li_price:
        prod = find_product(data, "lithium_carbonate")
        if prod and update_product_price(prod, li_price):
            updated_count += 1
    else:
        print("  [SKIP] 碳酸锂数据未获取（下次重试）")

    # 2. 电解铜 ← 上期所
    print("\n[2/3] 爬取电解铜（上期所）...")
    cu_price = scrape_shfe_copper()
    if cu_price:
        prod = find_product(data, "copper")
        if prod and update_product_price(prod, cu_price):
            updated_count += 1
    else:
        print("  [SKIP] 铜数据未获取（下次重试）")

    # 3. 电解铝 ← 上期所
    print("\n[3/3] 爬取电解铝（上期所）...")
    al_price = scrape_shfe_aluminum()
    if al_price:
        prod = find_product(data, "aluminum")
        if prod and update_product_price(prod, al_price):
            updated_count += 1
    else:
        print("  [SKIP] 铝数据未获取（下次重试）")

    # 更新全局时间
    data["update_time"] = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*50}")
    print(f"更新完成：{updated_count} 个品种已更新")
    print(f"下次自动更新：工作日 08:30 / 17:00")
    print(f"特气数据（WF₆/NF₃/氦气等）请手动编辑 data.json")
    print(f"{'='*50}")

    if updated_count > 0:
        save_data(data)
    else:
        print("[WARN] 本次无品种更新")


if __name__ == "__main__":
    main()
