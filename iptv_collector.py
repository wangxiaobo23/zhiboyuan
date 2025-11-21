import requests
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import time
import json
import re
from urllib.parse import quote

class IPTVCollector:
    def __init__(self):
        self.base_url = "http://tonkiang.us/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 加载频道配置
        with open('channels.json', 'r', encoding='utf-8') as f:
            self.channel_categories = json.load(f)
        
        # 存储有效的直播源
        self.all_valid_sources = []
        
    def search_tonkiang(self, keyword):
        """通过tonkiang搜索直播源"""
        try:
            print(f"正在搜索: {keyword}")
            encoded_keyword = quote(keyword)
            search_url = f"{self.base_url}?s={encoded_keyword}"
            
            response = self.session.get(search_url, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"搜索失败: {keyword}, 状态码: {response.status_code}")
                return []
            
            return self.parse_search_results(response.text, keyword)
            
        except Exception as e:
            print(f"搜索出错 {keyword}: {str(e)}")
            return []
    
    def parse_search_results(self, html, keyword):
        """解析搜索结果"""
        soup = BeautifulSoup(html, 'html.parser')
        sources = []
        
        # 查找所有结果项
        result_items = soup.find_all('div', class_=lambda x: x and 'result' in x)
        
        for item in result_items:
            try:
                # 查找频道名称
                channel_name_elem = item.find(['h2', 'div', 'span'], class_=lambda x: x and ('channel' in str(x) or 'title' in str(x)))
                channel_name = channel_name_elem.get_text().strip() if channel_name_elem else keyword
                
                # 清理频道名称
                channel_name = re.sub(r'[<>:"/\\|?*]', '', channel_name)
                channel_name = channel_name[:50]  # 限制长度
                
                # 查找直播源链接
                links = item.find_all('a', href=True)
                for link in links:
                    url = link['href'].strip()
                    if self.is_valid_live_url(url):
                        # 为每个频道找到的第一个链接创建源
                        source = {
                            'name': channel_name,
                            'url': url,
                            'group': keyword,
                            'category': self.get_category(keyword)
                        }
                        sources.append(source)
                        break  # 每个结果只取第一个有效链接
                        
            except Exception as e:
                continue
        
        print(f"为 '{keyword}' 找到 {len(sources)} 个潜在源")
        return sources
    
    def is_valid_live_url(self, url):
        """验证是否为有效的直播URL"""
        if not url or len(url) < 10:
            return False
            
        live_patterns = [
            r'\.m3u8?($|\?)',
            r'\.flv($|\?)',
            r'\.ts($|\?)',
            r'rtmp://',
            r'rtsp://',
            r'http.*/live/',
            r'http.*\.m3u8',
            r'http.*\.flv'
        ]
        
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in live_patterns)
    
    def get_category(self, keyword):
        """根据关键词确定分类"""
        for category, keywords in self.channel_categories.items():
            if keyword in keywords:
                return category
        return "其他"
    
    async def test_source_speed(self, session, source):
        """测试直播源速度和有效性"""
        start_time = time.time()
        try:
            # 设置超时
            timeout = aiohttp.ClientTimeout(total=8)
            
            async with session.get(source['url'], timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://tonkiang.us/'
            }) as response:
                
                if response.status == 200:
                    # 尝试读取前1KB数据来确认可用性
                    data = await response.content.read(1024)
                    if data:
                        speed = (time.time() - start_time) * 1000  # 毫秒
                        return {
                            **source,
                            'speed': speed,
                            'status': 'Valid',
                            'response_time': f"{speed:.0f}ms"
                        }
                
                return {**source, 'speed': float('inf'), 'status': f'HTTP {response.status}'}
                
        except asyncio.TimeoutError:
            return {**source, 'speed': float('inf'), 'status': 'Timeout'}
        except Exception as e:
            return {**source, 'speed': float('inf'), 'status': f'Error: {str(e)[:50]}'}
    
    async def test_all_sources(self, sources):
        """并发测试所有直播源"""
        print(f"开始测试 {len(sources)} 个直播源...")
        
        # 限制并发数
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.test_source_speed(session, source) for source in sources]
            results = await asyncio.gather(*tasks)
        
        # 过滤有效源并按速度排序
        valid_sources = [r for r in results if r['speed'] < float('inf')]
        valid_sources.sort(key=lambda x: x['speed'])
        
        print(f"测试完成，有效源: {len(valid_sources)} 个")
        return valid_sources
    
    def filter_sources_per_channel(self, all_sources):
        """为每个频道选择2-8个最佳源"""
        filtered_sources = []
        
        # 按频道分组
        channel_groups = {}
        for source in all_sources:
            channel_key = source['group']
            if channel_key not in channel_groups:
                channel_groups[channel_key] = []
            channel_groups[channel_key].append(source)
        
        # 为每个频道选择最佳源
        for channel, sources in channel_groups.items():
            # 按速度排序
            sources.sort(key=lambda x: x['speed'])
            
            # 确保至少2个，最多8个
            min_sources = min(2, len(sources))
            selected_sources = sources[:max(min_sources, min(8, len(sources)))]
            
            filtered_sources.extend(selected_sources)
            print(f"频道 '{channel}': 选择 {len(selected_sources)} 个最佳源")
        
        return filtered_sources
    
    def generate_combined_m3u(self, sources):
        """生成合并的M3U文件内容"""
        content = ['#EXTM3U']
        
        for source in sources:
            content.append(f"#EXTINF:-1 group-title=\"{source['category']}\",{source['name']} [{source['response_time']}]")
            content.append(source['url'])
        
        return '\n'.join(content)
    
    def generate_combined_txt(self, sources):
        """生成合并的TXT文件内容"""
        content = []
        current_category = None
        
        for source in sources:
            if source['category'] != current_category:
                content.append(f"{source['category']},#genre#")
                current_category = source['category']
            
            content.append(f"{source['name']},{source['url']}")
        
        return '\n'.join(content)
    
    def save_files(self, sources):
        """保存M3U和TXT文件"""
        if not sources:
            print("没有有效的直播源可保存")
            return
        
        # 生成文件内容
        m3u_content = self.generate_combined_m3u(sources)
        txt_content = self.generate_combined_txt(sources)
        
        # 保存文件
        with open('all_channels.m3u', 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        with open('all_channels.txt', 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        print(f"已保存 {len(sources)} 个直播源到 all_channels.m3u 和 all_channels.txt")
    
    async def run(self):
        """主运行函数"""
        print("=== IPTV直播源收集开始 ===")
        
        # 收集所有直播源
        all_sources = []
        for category, keywords in self.channel_categories.items():
            for keyword in keywords:
                sources = self.search_tonkiang(keyword)
                all_sources.extend(sources)
                
                # 延迟避免请求过快
                await asyncio.sleep(1.5)
        
        print(f"\n总共找到 {len(all_sources)} 个潜在直播源")
        
        if not all_sources:
            print("没有找到任何直播源，程序结束")
            return
        
        # 测试所有源
        tested_sources = await self.test_all_sources(all_sources)
        
        if not tested_sources:
            print("没有有效的直播源，程序结束")
            return
        
        # 过滤每个频道的最佳源
        final_sources = self.filter_sources_per_channel(tested_sources)
        
        # 保存文件
        self.save_files(final_sources)
        
        # 打印统计信息
        print(f"\n=== 收集完成 ===")
        print(f"总有效直播源: {len(final_sources)}")
        
        category_count = {}
        for source in final_sources:
            category = source['category']
            category_count[category] = category_count.get(category, 0) + 1
        
        for category, count in category_count.items():
            print(f"{category}: {count} 个源")

# 主程序
async def main():
    collector = IPTVCollector()
    await collector.run()

if __name__ == "__main__":
    asyncio.run(main())