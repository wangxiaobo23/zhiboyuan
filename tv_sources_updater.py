import requests
import re
import time
import concurrent.futures
from urllib.parse import quote, urljoin
import os
from datetime import datetime
import random
from bs4 import BeautifulSoup
import json

class TVSourceUpdater:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 定义要搜索的电视台列表
        self.tv_channels = [
            # 央视频道
            "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7", 
            "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15",
            "CCTV16", "CCTV17",
            
            # 地方卫视
            "北京卫视", "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "安徽卫视",
            "山东卫视", "天津卫视", "深圳卫视", "广东卫视", 
            
            # 凤凰卫视
            "凤凰中文", "凤凰资讯", "凤凰香港",
            
            # 香港电视台
            "翡翠台", "明珠台", "香港卫视"
        ]
        
        # 备用搜索关键词
        self.channel_keywords = {
            "CCTV1": ["CCTV-1", "CCTV1综合", "CCTV 1"],
            "CCTV2": ["CCTV-2", "CCTV2财经", "CCTV 2"],
            "CCTV5": ["CCTV-5", "CCTV5体育", "CCTV 5"],
            "CCTV5+": ["CCTV-5+", "CCTV5plus", "CCTV5+"],
            "CCTV13": ["CCTV-13", "CCTV13新闻", "CCTV 13"],
            "北京卫视": ["北京电视台", "BTV", "北京卫视"],
            "湖南卫视": ["湖南电视台", "Hunan TV"],
            "凤凰中文": ["凤凰中文台", "凤凰卫视频道"],
            "凤凰资讯": ["凤凰资讯台", "凤凰信息台"],
            "翡翠台": ["TVB翡翠", "TVB"],
            "明珠台": ["TVB明珠", "Pearl"],
        }
        
        self.valid_sources = {}
        self.found_sources_count = 0

    def get_search_urls(self, channel):
        """生成多个搜索URL"""
        base_urls = [
            f"https://tonkiang.us/?s={quote(channel)}",
            f"https://tonkiang.us/hotellist.html?s={quote(channel)}",
            f"https://tonkiang.us/tv.html?t={quote(channel)}",
        ]
        
        # 添加关键词变体
        if channel in self.channel_keywords:
            for keyword in self.channel_keywords[channel]:
                base_urls.append(f"https://tonkiang.us/?s={quote(keyword)}")
        
        return base_urls

    def search_tv_sources(self, channel):
        """搜索电视直播源 - 改进版本"""
        all_sources = []
        
        for search_url in self.get_search_urls(channel):
            try:
                print(f"搜索URL: {search_url}")
                response = self.session.get(search_url, timeout=15)
                response.encoding = 'utf-8'
                
                if response.status_code != 200:
                    continue
                
                # 使用多种方法提取源
                sources = self.extract_sources_advanced(response.text, channel)
                all_sources.extend(sources)
                
                # 避免请求过快
                time.sleep(1)
                
            except Exception as e:
                print(f"搜索 {channel} 时出错: {e}")
                continue
        
        # 去重
        unique_sources = list(set(all_sources))
        print(f"频道 {channel} 找到 {len(unique_sources)} 个唯一源")
        return channel, unique_sources[:8]  # 最多取8个

    def extract_sources_advanced(self, html, channel):
        """使用多种方法提取直播源"""
        sources = []
        
        # 方法1: 直接匹配m3u8链接
        m3u8_patterns = [
            r'https?://[^\s"<>]+\.m3u8(?:\?[^\s"<>]*)?',
            r'https?://[^\s"<>]+\.m3u(?:\?[^\s"<>]*)?',
            r'http[^\s"<>]+\.m3u8[^\s"<>]*',
            r'http[^\s"<>]+\.m3u[^\s"<>]*',
        ]
        
        for pattern in m3u8_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            sources.extend(matches)
        
        # 方法2: 从JavaScript变量中提取
        js_patterns = [
            r'var\s+[^=]*=\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'source\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
            r'url\s*:\s*["\'](https?://[^"\']+\.m3u8[^"\']*)["\']',
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            sources.extend(matches)
        
        # 方法3: 从HTML属性中提取
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找可能的播放链接
        for tag in soup.find_all(['a', 'div', 'span']):
            text = tag.get_text()
            if channel in text or any(keyword in text for keyword in self.channel_keywords.get(channel, [])):
                # 在附近查找m3u8链接
                parent_html = str(tag.parent)
                m3u_matches = re.findall(r'https?://[^\s"<>]+\.m3u8[^\s"<>]*', parent_html, re.IGNORECASE)
                sources.extend(m3u_matches)
        
        # 方法4: 查找包含频道名的div中的链接
        for div in soup.find_all('div', string=re.compile(channel)):
            div_html = str(div)
            m3u_matches = re.findall(r'https?://[^\s"<>]+\.m3u8[^\s"<>]*', div_html, re.IGNORECASE)
            sources.extend(m3u_matches)
        
        # 过滤和清理
        filtered_sources = []
        for source in sources:
            source = source.strip()
            if self.is_valid_source(source):
                # 确保URL格式正确
                if source.startswith('http'):
                    filtered_sources.append(source)
        
        return list(set(filtered_sources))

    def is_valid_source(self, url):
        """验证直播源URL"""
        invalid_keywords = [
            'example.com', 'test.com', 'localhost', '127.0.0.1',
            'google', 'baidu', 'tonkiang.us', 'javascript:',
            '.jpg', '.png', '.gif', '.css', '.js'
        ]
        
        valid_keywords = ['.m3u8', '.m3u']
        
        # 必须包含有效关键词
        if not any(keyword in url.lower() for keyword in valid_keywords):
            return False
            
        # 不能包含无效关键词
        if any(keyword in url.lower() for keyword in invalid_keywords):
            return False
            
        return True

    def test_source_speed(self, source):
        """测试直播源速度和有效性 - 改进版本"""
        try:
            start_time = time.time()
            
            # 只请求头部，设置较短超时
            response = self.session.head(
                source, 
                timeout=3, 
                allow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # 额外检查内容类型
                content_type = response.headers.get('content-type', '').lower()
                if 'video' in content_type or 'application' in content_type or 'octet-stream' in content_type:
                    return source, response_time, True
                else:
                    # 对于m3u8文件，可能没有特定的content-type，所以也接受
                    if '.m3u8' in source or '.m3u' in source:
                        return source, response_time, True
            
            return source, response_time, False
                
        except Exception as e:
            return source, float('inf'), False

    def process_channel(self, channel):
        """处理单个频道"""
        print(f"\n=== 正在处理: {channel} ===")
        
        # 搜索源
        channel_name, sources = self.search_tv_sources(channel)
        
        if not sources:
            print(f"未找到 {channel} 的源")
            return channel_name, []
        
        print(f"找到 {len(sources)} 个源，开始测试...")
        
        # 测试所有源的速度
        speed_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_source = {
                executor.submit(self.test_source_speed, source): source 
                for source in sources
            }
            
            for future in concurrent.futures.as_completed(future_to_source):
                source, speed, valid = future.result()
                if valid and speed < 5:  # 只接受响应时间小于5秒的源
                    speed_results.append((source, speed))
                    print(f"有效源: {source} (响应时间: {speed:.2f}s)")
        
        # 按速度排序
        speed_results.sort(key=lambda x: x[1])
        
        # 只保留最快的8个有效源
        final_sources = [source for source, _ in speed_results[:8]]
        
        print(f"{channel} 完成测试，有效源: {len(final_sources)} 个")
        return channel_name, final_sources

    def add_backup_sources(self):
        """添加备用直播源"""
        backup_sources = {
            "CCTV1": [
                "http://ivi.bupt.edu.cn/hls/cctv1hd.m3u8",
                "https://cctvcnch5c.v.wscdns.com/live/cctv1_2/playlist.m3u8"
            ],
            "CCTV5": [
                "http://ivi.bupt.edu.cn/hls/cctv5hd.m3u8",
                "https://cctvcnch5c.v.wscdns.com/live/cctv5_2/playlist.m3u8"
            ],
            "湖南卫视": [
                "http://ivi.bupt.edu.cn/hls/hunanhd.m3u8",
                "https://hnws.tvpal.com/hunanstv/04.m3u8"
            ],
            "浙江卫视": [
                "http://ivi.bupt.edu.cn/hls/zhejianghd.m3u8"
            ],
            "江苏卫视": [
                "http://ivi.bupt.edu.cn/hls/jiangsuhd.m3u8"
            ],
            "北京卫视": [
                "http://ivi.bupt.edu.cn/hls/beijinghd.m3u8"
            ],
            "东方卫视": [
                "http://ivi.bupt.edu.cn/hls/dongfanghd.m3u8"
            ]
        }
        
        for channel, sources in backup_sources.items():
            if channel in self.valid_sources:
                # 合并备用源
                existing_sources = self.valid_sources[channel]
                all_sources = existing_sources + [s for s in sources if s not in existing_sources]
                self.valid_sources[channel] = all_sources[:8]
            else:
                self.valid_sources[channel] = sources[:8]

    def generate_m3u_file(self):
        """生成M3U文件"""
        m3u_content = "#EXTM3U\n# Generated by TV Source Updater\n# Update Time: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n"
        
        for channel, sources in self.valid_sources.items():
            for i, source in enumerate(sources):
                m3u_content += f'#EXTINF:-1 tvg-id="{channel}" tvg-name="{channel}" tvg-logo="" group-title="直播",{channel} 源{i+1}\n'
                m3u_content += f"{source}\n"
        
        return m3u_content

    def generate_txt_file(self):
        """生成TXT文件"""
        txt_content = f"# 电视直播源更新于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        txt_content += "# 格式: 频道名称,直播源URL\n\n"
        
        for channel, sources in self.valid_sources.items():
            if sources:
                txt_content += f"# {channel}\n"
                for source in sources:
                    txt_content += f"{source}\n"
                txt_content += "\n"
        
        return txt_content

    def save_categorized_files(self):
        """保存分类文件"""
        categories = {
            "央视": [],
            "卫视": [],
            "凤凰": [],
            "香港": [],
            "其他": []
        }
        
        # 分类频道
        for channel, sources in self.valid_sources.items():
            if "CCTV" in channel:
                categories["央视"].append((channel, sources))
            elif "卫视" in channel:
                categories["卫视"].append((channel, sources))
            elif "凤凰" in channel:
                categories["凤凰"].append((channel, sources))
            elif any(hk in channel for hk in ["翡翠", "明珠", "香港"]):
                categories["香港"].append((channel, sources))
            else:
                categories["其他"].append((channel, sources))
        
        # 为每个分类生成文件
        for category, channels in categories.items():
            if channels:
                # M3U文件
                m3u_content = "#EXTM3U\n"
                for channel, sources in channels:
                    for i, source in enumerate(sources):
                        m3u_content += f'#EXTINF:-1 tvg-id="{channel}" tvg-name="{channel}" group-title="{category}",{channel} 源{i+1}\n'
                        m3u_content += f"{source}\n"
                
                with open(f"tv_sources_{category}.m3u", "w", encoding="utf-8") as f:
                    f.write(m3u_content)
                
                # TXT文件
                txt_content = f"# {category}直播源\n"
                txt_content += f"# 更新于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                for channel, sources in channels:
                    txt_content += f"# {channel}\n"
                    for source in sources:
                        txt_content += f"{source}\n"
                    txt_content += "\n"
                
                with open(f"tv_sources_{category}.txt", "w", encoding="utf-8") as f:
                    f.write(txt_content)

    def run(self):
        """主运行函数"""
        print("开始抓取电视直播源...")
        print("=" * 50)
        
        # 使用多线程处理所有频道
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(self.process_channel, self.tv_channels))
        
        # 整理结果
        for channel_name, sources in results:
            if sources:
                self.valid_sources[channel_name] = sources
        
        print("\n" + "=" * 50)
        print(f"初步完成！共获取 {len(self.valid_sources)} 个频道的有效直播源")
        
        # 添加备用源
        print("添加备用直播源...")
        self.add_backup_sources()
        
        print(f"最终获取 {len(self.valid_sources)} 个频道的直播源")
        
        # 生成合并文件
        m3u_content = self.generate_m3u_file()
        txt_content = self.generate_txt_file()
        
        # 保存文件
        with open("tv_sources.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        
        with open("tv_sources.txt", "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        # 保存分类文件
        self.save_categorized_files()
        
        # 生成统计信息
        self.generate_stats()
        
        print("所有文件已生成完成！")

    def generate_stats(self):
        """生成统计信息"""
        total_sources = sum(len(sources) for sources in self.valid_sources.values())
        
        stats_content = f"""# 电视直播源统计
更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 频道统计
- 总频道数: {len(self.valid_sources)}
- 总源数量: {total_sources}

## 各频道源数量
"""
        for channel, sources in sorted(self.valid_sources.items()):
            stats_content += f"- {channel}: {len(sources)} 个源\n"
        
        with open("STATS.md", "w", encoding="utf-8") as f:
            f.write(stats_content)

if __name__ == "__main__":
    updater = TVSourceUpdater()
    updater.run()