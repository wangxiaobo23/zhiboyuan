import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import time
import json
import re

class IPTVCollector:
    def __init__(self):
        self.base_url = "http://tonkiang.us/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with open('channels.json', 'r', encoding='utf-8') as f:
            self.channel_categories = json.load(f)
        self.valid_sources = {category: [] for category in self.channel_categories.keys()}

    def search_tonkiang(self, keyword):
        try:
            encoded_keyword = requests.utils.quote(keyword)
            search_url = f"{self.base_url}?s={encoded_keyword}"
            response = self.session.get(search_url, timeout=10)
            response.encoding = 'utf-8'
            if response.status_code != 200:
                print(f"搜索失败: {keyword}")
                return []
            return self.parse_search_results(response.text, keyword)
        except Exception as e:
            print(f"搜索 {keyword} 时出错: {e}")
            return []

    def parse_search_results(self, html, keyword):
        soup = BeautifulSoup(html, 'html.parser')
        sources = []
        for item in soup.find_all('div', class_='result'):
            try:
                link = item.find('a', href=True)
                if link:
                    url = link['href']
                    text = link.get_text().strip()
                    if self.is_live_url(url):
                        name = text if text else f"{keyword}"
                        sources.append({'name': name, 'url': url, 'group': keyword})
            except Exception:
                continue
        print(f"为频道 '{keyword}' 找到 {len(sources)} 个潜在源")
        return sources

    def is_live_url(self, url):
        live_indicators = ['.m3u8', '.flv', 'rtmp://', '/live/', '.ts']
        return any(indicator in url.lower() for indicator in live_indicators)

    async def test_single_source(self, session, source):
        start_time = time.time()
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with session.get(source['url'], timeout=timeout) as response:
                if response.status == 200:
                    elapsed = (time.time() - start_time) * 1000
                    return {**source, 'speed': elapsed, 'status': 'Valid'}
        except Exception:
            return {**source, 'speed': float('inf'), 'status': 'Invalid'}

    async def test_all_sources(self, all_sources):
        connector = aiohttp.TCPConnector(limit=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.test_single_source(session, source) for source in all_sources]
            results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r['status'] == 'Valid']
        valid_results.sort(key=lambda x: x['speed'])
        return valid_results

    def generate_combined_m3u(self):
        content = ['#EXTM3U']
        for category, sources in self.valid_sources.items():
            for source in sources:
                content.append(f"#EXTINF:-1 group-title=\"{category}\",{source['name']}")
                content.append(source['url'])
        return '\n'.join(content)

    def generate_combined_txt(self):
        content = []
        for category, sources in self.valid_sources.items():
            content.append(f"{category},#genre#")
            for source in sources:
                content.append(f"{source['name']},{source['url']}")
        return '\n'.join(content)

    def save_combined_files(self):
        m3u_content = self.generate_combined_m3u()
        with open('combined_sources.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        txt_content = self.generate_combined_txt()
        with open('combined_sources.txt', 'w', encoding='utf-8') as f:
            f.write(txt_content)
        print("已合并保存 M3U 和 TXT 文件")

    async def run(self):
        print("开始收集直播源...")
        all_sources_to_test = []
        for category, keywords in self.channel_categories.items():
            for keyword in keywords:
                sources = self.search_tonkiang(keyword)
                all_sources_to_test.extend(sources)
                await asyncio.sleep(1)
        print(f"共找到 {len(all_sources_to_test)} 个直播源，开始测试...")
        tested_sources = await self.test_all_sources(all_sources_to_test)
        for source in tested_sources:
            for category, keywords in self.channel_categories.items():
                if source['group'] in keywords:
                    self.valid_sources[category].append(source)
        for category in self.valid_sources:
            self.valid_sources[category].sort(key=lambda x: x['speed'])
            self.valid_sources[category] = self.valid_sources[category][:8]
        self.save_combined_files()
        total_valid = sum(len(sources) for sources in self.valid_sources.values())
        print(f"完成! 共找到 {total_valid} 个有效直播源")

if __name__ == "__main__":
    collector = IPTVCollector()
    asyncio.run(collector.run())