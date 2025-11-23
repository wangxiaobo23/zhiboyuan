import requests
import re
import time
import concurrent.futures
from urllib.parse import quote
import os
from datetime import datetime

class TVSourceUpdater:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 定义要搜索的电视台列表
        self.tv_channels = [
            # 央视频道
            "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7", 
            "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15",
            "CCTV16", "CCTV17",
            
            # 地方卫视
            "北京卫视", "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "安徽卫视",
            "山东卫视", "天津卫视", "深圳卫视", "广东卫视", "湖北卫视", "辽宁卫视",
            "四川卫视", "重庆卫视", "贵州卫视", "河南卫视", "河北卫视", "黑龙江卫视",
            "吉林卫视", "江西卫视", "广西卫视", "山西卫视", "陕西卫视", "云南卫视",
            "新疆卫视", "西藏卫视", "内蒙古卫视", "宁夏卫视", "青海卫视", "甘肃卫视",
            "海南卫视",
            
            # 凤凰卫视
            "凤凰中文台", "凤凰资讯台", "凤凰香港台",
            
            # 香港电视台
            "翡翠台", "明珠台", "本港台", "国际台", "香港卫视", "TVB", "ATV"
        ]
        
        self.valid_sources = {}
        self.speed_results = {}

    def search_tv_sources(self, channel):
        """搜索电视直播源"""
        try:
            encoded_channel = quote(channel)
            url = f"https://tonkiang.us/?s={encoded_channel}"
            
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            # 提取直播源链接
            sources = self.extract_sources(response.text)
            
            print(f"找到 {channel} 的 {len(sources)} 个源")
            return channel, sources[:8]  # 最多取8个
            
        except Exception as e:
            print(f"搜索 {channel} 时出错: {e}")
            return channel, []

    def extract_sources(self, html):
        """从HTML中提取直播源"""
        sources = []
        
        # 匹配m3u8链接
        m3u8_patterns = [
            r'https?://[^\s<>"]+\.m3u8?[^\s<>"]*',
            r'https?://[^\s<>"]+\.m3u?[^\s<>"]*'
        ]
        
        for pattern in m3u8_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            sources.extend(matches)
        
        # 去重
        unique_sources = list(set(sources))
        
        # 过滤无效链接
        valid_sources = []
        for source in unique_sources:
            if self.is_valid_source(source):
                valid_sources.append(source)
                
        return valid_sources

    def is_valid_source(self, url):
        """初步验证直播源URL"""
        invalid_keywords = [
            'example.com', 'test.com', 'localhost', '127.0.0.1',
            'google', 'baidu', 'tonkiang.us'
        ]
        
        return all(keyword not in url.lower() for keyword in invalid_keywords)

    def test_source_speed(self, source):
        """测试直播源速度和有效性"""
        try:
            start_time = time.time()
            
            # 只请求头部信息来测试响应速度
            response = self.session.head(source, timeout=5, allow_redirects=True)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return source, response_time, True
            else:
                return source, response_time, False
                
        except Exception as e:
            return source, float('inf'), False

    def process_channel(self, channel):
        """处理单个频道"""
        print(f"正在处理: {channel}")
        
        # 搜索源
        channel_name, sources = self.search_tv_sources(channel)
        
        if not sources:
            return channel_name, []
        
        # 测试所有源的速度
        speed_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_source = {
                executor.submit(self.test_source_speed, source): source 
                for source in sources
            }
            
            for future in concurrent.futures.as_completed(future_to_source):
                source, speed, valid = future.result()
                if valid:
                    speed_results.append((source, speed))
        
        # 按速度排序
        speed_results.sort(key=lambda x: x[1])
        
        # 只保留最快的8个有效源
        final_sources = [source for source, _ in speed_results[:8]]
        
        print(f"{channel} 完成测试，有效源: {len(final_sources)} 个")
        return channel_name, final_sources

    def generate_m3u_file(self):
        """生成M3U文件"""
        m3u_content = "#EXTM3U\n"
        
        for channel, sources in self.valid_sources.items():
            for i, source in enumerate(sources):
                m3u_content += f'#EXTINF:-1 tvg-id="{channel}" tvg-name="{channel}{i+1}" group-title="直播",{channel} 源{i+1}\n'
                m3u_content += f"{source}\n"
        
        return m3u_content

    def generate_txt_file(self):
        """生成TXT文件"""
        txt_content = f"# 电视直播源更新于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        txt_content += "# 格式: 频道名称,直播源URL\n\n"
        
        for channel, sources in self.valid_sources.items():
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
            elif any(hk in channel for hk in ["翡翠", "明珠", "本港", "国际", "香港", "TVB", "ATV"]):
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
                        m3u_content += f'#EXTINF:-1 tvg-id="{channel}" tvg-name="{channel}{i+1}" group-title="{category}",{channel} 源{i+1}\n'
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
        
        # 使用多线程处理所有频道
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(self.process_channel, self.tv_channels))
        
        # 整理结果
        for channel_name, sources in results:
            if sources:
                self.valid_sources[channel_name] = sources
        
        print(f"完成！共获取 {len(self.valid_sources)} 个频道的有效直播源")
        
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

    def generate_stats(self):
        """生成统计信息"""
        stats_content = f"""# 电视直播源统计
更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 频道统计
- 总频道数: {len(self.valid_sources)}
- 总源数量: {sum(len(sources) for sources in self.valid_sources.values())}

## 各频道源数量
"""
        for channel, sources in sorted(self.valid_sources.items()):
            stats_content += f"- {channel}: {len(sources)} 个源\n"
        
        with open("STATS.md", "w", encoding="utf-8") as f:
            f.write(stats_content)

if __name__ == "__main__":
    updater = TVSourceUpdater()
    updater.run()