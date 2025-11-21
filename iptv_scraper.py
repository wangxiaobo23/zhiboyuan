# iptv_scraper.py
import asyncio
from playwright.async_api import async_playwright
import re
import time
import requests
from urllib.parse import urlparse
import os

# ================== 配置区域（无需修改）==================
SEARCH_URL = "http://tonkiang.us/"
TIMEOUT = 10  # 测速超时
TARGET_CHANNELS = [
    "CCTV-1", "CCTV-2", "CCTV-3", "CCTV-4", "CCTV-5", "CCTV-5+", "CCTV-6",
    "CCTV-7", "CCTV-8", "CCTV-9", "CCTV-10", "CCTV-11", "CCTV-12", "CCTV-13",
    "CCTV-14", "CCTV-15", "CCTV-17", "CCTV-4K", "凤凰卫视", "凤凰中文台", "凤凰资讯台",
    "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "北京卫视", "广东卫视",
    "深圳卫视", "四川卫视", "湖北卫视", "山东卫视", "河南卫视", "辽宁卫视",
    "安徽卫视", "陕西卫视", "山西卫视", "河北卫视", "黑龙江卫视", "吉林卫视",
    "内蒙古卫视", "新疆卫视", "西藏卫视", "香港卫视", "香港开电视", "HOY TV",
    "翡翠台", "明珠台", "J2", "无线新闻台"
]

MAX_LINKS_PER_CHANNEL = 8
MIN_LINKS_PER_CHANNEL = 2
# ========================================================

def normalize_name(name):
    name = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", "", name)
    mapping = {
        "cctv1": "CCTV-1", "cctv2": "CCTV-2", "cctv3": "CCTV-3", "cctv4": "CCTV-4",
        "cctv5": "CCTV-5", "cctv5p": "CCTV-5+", "cctv5plus": "CCTV-5+", "cctv6": "CCTV-6",
        "cctv7": "CCTV-7", "cctv8": "CCTV-8", "cctv9": "CCTV-9", "cctv10": "CCTV-10",
        "cctv11": "CCTV-11", "cctv12": "CCTV-12", "cctv13": "CCTV-13", "cctv14": "CCTV-14",
        "cctv15": "CCTV-15", "cctv17": "CCTV-17", "cctv4k": "CCTV-4K",
        "凤凰卫视": "凤凰卫视", "凤凰中文台": "凤凰中文台", "凤凰资讯台": "凤凰资讯台",
        "湖南": "湖南卫视", "浙江": "浙江卫视", "江苏": "江苏卫视", "东方": "东方卫视",
        "北京": "北京卫视", "广东": "广东卫视", "深圳": "深圳卫视", "四川": "四川卫视",
        "湖北": "湖北卫视", "山东": "山东卫视", "河南": "河南卫视", "辽宁": "辽宁卫视",
        "安徽": "安徽卫视", "陕西": "陕西卫视", "山西": "山西卫视", "河北": "河北卫视",
        "黑龙江": "黑龙江卫视", "吉林": "吉林卫视", "内蒙古": "内蒙古卫视",
        "新疆": "新疆卫视", "西藏": "西藏卫视", "香港卫视": "香港卫视",
        "开电视": "香港开电视", "hoy": "HOY TV", "翡翠": "翡翠台", "明珠": "明珠台",
        "j2": "J2", "新闻台": "无线新闻台"
    }
    for key in mapping:
        if key in name.lower():
            return mapping[key]
    return None

async def fetch_links(page, keyword):
    await page.goto(SEARCH_URL)
    await page.fill("input[name='q']", keyword)
    await page.click("input[type='submit']")
    await page.wait_for_timeout(3000)

    links = set()
    for _ in range(3):  # 最多翻3页
        hrefs = await page.eval_on_selector_all("div#table a", "nodes => nodes.map(n => n.href)")
        for href in hrefs:
            if "watch" in href:
                try:
                    await page.goto(href, timeout=10000)
                    await page.wait_for_timeout(2000)
                    srcs = await page.eval_on_selector_all("video source, video", """
                        elements => elements.map(el => {
                            const src = el.src || el.children[0]?.src;
                            return src ? src.trim() : '';
                        }).filter(Boolean)
                    """)
                    links.update([s for s in srcs if s.startswith("http") and "m3u8" in s.lower()])
                except:
                    pass
                await page.go_back(timeout=10000)
                await page.wait_for_timeout(2000)
        try:
            next_btn = page.locator("a:has-text('Next')")
            if await next_btn.is_visible():
                await next_btn.click()
                await page.wait_for_timeout(3000)
            else:
                break
        except:
            break
    return list(links)

def test_url_speed(url):
    try:
        start = time.time()
        resp = requests.head(url, timeout=TIMEOUT, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            return time.time() - start
        else:
            resp = requests.get(url, timeout=TIMEOUT, stream=True, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200:
                return time.time() - start
    except:
        return float('inf')
    return float('inf')

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        all_channels = {}

        for channel in TARGET_CHANNELS:
            print(f"🔍 搜索: {channel}")
            links = await fetch_links(page, channel)
            valid_links = []
            for link in set(links):
                delay = test_url_speed(link)
                if delay < float('inf'):
                    valid_links.append((link, delay))
                    print(f"✅ 有效: {link[:60]}... | 延迟: {delay:.2f}s")
            # 按速度排序
            valid_links.sort(key=lambda x: x[1])
            # 限制数量
            selected = valid_links[:MAX_LINKS_PER_CHANNEL]
            if len(selected) >= MIN_LINKS_PER_CHANNEL:
                all_channels[channel] = selected
            else:
                print(f"⚠️  {channel} 有效源不足 {MIN_LINKS_PER_CHANNEL} 个，跳过")
            await page.wait_for_timeout(10