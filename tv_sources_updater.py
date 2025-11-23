import requests
import re
import time
import concurrent.futures
import json
from datetime import datetime
import os
import random

class MultiSourceTVUpdater:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.tv_channels = [
            "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV5+", "CCTV6", "CCTV7", 
            "CCTV8", "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", 
            "CCTV15", "CCTV16", "CCTV17",
            "北京卫视", "湖南卫视", "浙江卫视", "江苏卫视", "东方卫视", "安徽卫视",
            "山东卫视", "天津卫视", "深圳卫视", "广东卫视", "湖北卫视", "辽宁卫视",
            "四川卫视", "重庆卫视", "贵州卫视", "河南卫视", "河北卫视",
            "凤凰中文", "凤凰资讯", "凤凰香港",
            "翡翠台", "明珠台", "香港卫视"
        ]
        
        self.valid_sources = {}

    def get_sources_from_github(self):
        """从GitHub上的公开直播源项目获取"""
        print("尝试从GitHub获取直播源...")
        
        github_sources = [
            "https://raw.githubusercontent.com/iptv-org/iptv/master/channels/cn.m3u",
            "https://raw.githubusercontent.com/ImMarcos/iptv/master/canais",
            "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/global.m3u",
            "https://raw.githubusercontent.com/YanG-1989/m3u/main/Adult.m3u",
        ]
        
        all_sources = []
        
        for url in github_sources:
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    sources = self.parse_m3u_content(response.text)
                    all_sources.extend(sources)
                    print(f"从 {url} 获取到 {len(sources)} 个源")
            except Exception as e:
                print(f"从GitHub获取失败: {e}")
        
        return all_sources

    def get_sources_from_public_apis(self):
        """从公开API获取直播源"""
        print("尝试从公开API获取直播源...")
        
        apis = [
            "https://iptv-org.github.io/iptv/channels.json",
            "https://api.github.com/repos/iptv-org/iptv/contents/channels",
        ]
        
        all_sources = []
        
        for api_url in apis:
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    if api_url.endswith('.json'):
                        data = response.json()
                        # 解析JSON数据提取源
                        sources = self.parse_json_sources(data)
                        all_sources.extend(sources)
            except Exception as e:
                print(f"从API获取失败: {e}")
        
        return all_sources

    def parse_m3u_content(self, content):
        """解析M3U内容"""
        sources = []
        lines = content.split('\n')
        
        for i in range(len(lines)):
            if lines[i].startswith('#EXTINF'):
                if i + 1 < len(lines) and lines[i + 1].startswith('http'):
                    source = lines[i + 1].strip()
                    if self.is_valid_source(source):
                        sources.append(source)
        
        return sources

    def parse_json_sources(self, data):
        """解析JSON数据提取源"""
        sources = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'url' in item:
                    url = item['url']
                    if self.is_valid_source(url):
                        sources.append(url)
        
        return sources

    def get_sources_from_static_list(self):
        """使用静态直播源列表"""
        print("使用静态直播源列表...")
        
        static_sources = {
            "CCTV1": [
                "http://ivi.bupt.edu.cn/hls/cctv1hd.m3u8",
                "https://cctvcnch5c.v.wscdns.com/live/cctv1_2/playlist.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225496/index.m3u8",
                "http://39.134.65.171/PLTV/88888888/224/3221225496/index.m3u8"
            ],
            "CCTV2": [
                "http://ivi.bupt.edu.cn/hls/cctv2hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225497/index.m3u8"
            ],
            "CCTV3": [
                "http://ivi.bupt.edu.cn/hls/cctv3hd.m3u8"
            ],
            "CCTV4": [
                "http://ivi.bupt.edu.cn/hls/cctv4hd.m3u8"
            ],
            "CCTV5": [
                "http://ivi.bupt.edu.cn/hls/cctv5hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225500/index.m3u8"
            ],
            "CCTV5+": [
                "http://ivi.bupt.edu.cn/hls/cctv5phd.m3u8"
            ],
            "CCTV6": [
                "http://ivi.bupt.edu.cn/hls/cctv6hd.m3u8"
            ],
            "CCTV7": [
                "http://ivi.bupt.edu.cn/hls/cctv7hd.m3u8"
            ],
            "CCTV8": [
                "http://ivi.bupt.edu.cn/hls/cctv8hd.m3u8"
            ],
            "CCTV9": [
                "http://ivi.bupt.edu.cn/hls/cctv9hd.m3u8"
            ],
            "CCTV10": [
                "http://ivi.bupt.edu.cn/hls/cctv10hd.m3u8"
            ],
            "CCTV11": [
                "http://ivi.bupt.edu.cn/hls/cctv11hd.m3u8"
            ],
            "CCTV12": [
                "http://ivi.bupt.edu.cn/hls/cctv12hd.m3u8"
            ],
            "CCTV13": [
                "http://ivi.bupt.edu.cn/hls/cctv13hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225514/index.m3u8"
            ],
            "CCTV14": [
                "http://ivi.bupt.edu.cn/hls/cctv14hd.m3u8"
            ],
            "CCTV15": [
                "http://ivi.bupt.edu.cn/hls/cctv15hd.m3u8"
            ],
            "CCTV16": [
                "http://ivi.bupt.edu.cn/hls/cctv16hd.m3u8"
            ],
            "CCTV17": [
                "http://ivi.bupt.edu.cn/hls/cctv17hd.m3u8"
            ],
            "北京卫视": [
                "http://ivi.bupt.edu.cn/hls/beijinghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225530/index.m3u8"
            ],
            "湖南卫视": [
                "http://ivi.bupt.edu.cn/hls/hunanhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225561/index.m3u8"
            ],
            "浙江卫视": [
                "http://ivi.bupt.edu.cn/hls/zhejianghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225567/index.m3u8"
            ],
            "江苏卫视": [
                "http://ivi.bupt.edu.cn/hls/jiangsuhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225559/index.m3u8"
            ],
            "东方卫视": [
                "http://ivi.bupt.edu.cn/hls/dongfanghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225553/index.m3u8"
            ],
            "安徽卫视": [
                "http://ivi.bupt.edu.cn/hls/anhuihd.m3u8"
            ],
            "山东卫视": [
                "http://ivi.bupt.edu.cn/hls/shandonghd.m3u8"
            ],
            "天津卫视": [
                "http://ivi.bupt.edu.cn/hls/tianjinhd.m3u8"
            ],
            "深圳卫视": [
                "http://ivi.bupt.edu.cn/hls/shenzhenhd.m3u8"
            ],
            "广东卫视": [
                "http://ivi.bupt.edu.cn/hls/guangdonghd.m3u8"
            ],
            "湖北卫视": [
                "http://ivi.bupt.edu.cn/hls/hubeihd.m3u8"
            ],
            "辽宁卫视": [
                "http://ivi.bupt.edu.cn/hls/liaoninghd.m3u8"
            ],
            "四川卫视": [
                "http://ivi.bupt.edu.cn/hls/sichuanhd.m3u8"
            ],
            "重庆卫视": [
                "http://ivi.bupt.edu.cn/hls/chongqinghd.m3u8"
            ],
            "贵州卫视": [
                "http://ivi.bupt.edu.cn/hls/guizhouhd.m3u8"
            ],
            "河南卫视": [
                "http://ivi.bupt.edu.cn/hls/henanhd.m3u8"
            ],
            "河北卫视": [
                "http://ivi.bupt.edu.cn/hls/hebeihd.m3u8"
            ],
            "凤凰中文": [
                "http://liveali.ifeng.com/live/FHZW.m3u8",
                "http://223.110.243.136/PLTV/3/224/3221227545/index.m3u8"
            ],
            "凤凰资讯": [
                "http://liveali.ifeng.com/live/FHZX.m3u8",
                "http://223.110.243.136/PLTV/3/224/3221227544/index.m3u8"
            ],
            "凤凰香港": [
                "http://liveali.ifeng.com/live/FHGX.m3u8"
            ],
            "翡翠台": [
                "http://www.stream-link.org/stream/jade.php",
                "http://146.196.80.53/live/tvbjade.m3u8"
            ],
            "明珠台": [
                "http://www.stream-link.org/stream/pearl.php"
            ],
            "香港卫视": [
                "http://zhibo.hkstv.tv/livestream/mutfysrq/playlist.m3u8"
            ]
        }
        
        return static_sources

    def is_valid_source(self, url):
        """验证直播源URL"""
        if not url or not url.startswith('http'):
            return False
            
        invalid_keywords = [
            'example.com', 'test.com', 'localhost', '127.0.0.1',
            'google', 'baidu', 'javascript:', '.jpg', '.png', '.gif'
        ]
        
        valid_keywords = ['.m3u8', '.m3u', 'rtmp://', 'rtsp://']
        
        # 必须包含有效关键词
        if not any(keyword in url.lower() for keyword in valid_keywords):
            return False
            
        # 不能包含无效关键词
        if any(keyword in url.lower() for keyword in invalid_keywords):
            return False
            
        return True

    def test_source_speed(self, source_info):
        """测试直播源速度"""
        channel, source = source_info
        try:
            start_time = time.time()
            response = self.session.head(source, timeout=3, allow_redirects=True)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return channel, source, response_time, True
            else:
                return channel, source, response_time, False
                
        except Exception as e:
            return channel, source, float('inf'), False

    def collect_all_sources(self):
        """收集所有来源的直播源"""
        print("开始收集直播源...")
        
        # 方法1: 静态源列表
        static_sources = self.get_sources_from_static_list()
        
        # 方法2: GitHub源
        github_sources = self.get_sources_from_github()
        
        # 方法3: 公开API
        api_sources = self.get_sources_from_public_apis()
        
        # 合并所有源到频道分类
        all_channel_sources = {}
        
        # 添加静态源
        for channel, sources in static_sources.items():
            all_channel_sources[channel] = sources
        
        # 处理GitHub源 (简单按关键词分类)
        for source in github_sources:
            for channel in self.tv_channels:
                if channel.lower() in source.lower():
                    if channel not in all_channel_sources:
                        all_channel_sources[channel] = []
                    all_channel_sources[channel].append(source)
                    break
        
        print(f"收集到 {len(all_channel_sources)} 个频道的源")
        return all_channel_sources

    def test_all_sources(self, all_sources):
        """测试所有源的速度和有效性"""
        print("开始测试直播源速度...")
        
        # 准备测试任务
        test_tasks = []
        for channel, sources in all_sources.items():
            for source in sources:
                test_tasks.append((channel, source))
        
        # 多线程测试
        speed_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.test_source_speed, task) for task in test_tasks]
            
            for future in concurrent.futures.as_completed(futures):
                channel, source, speed, valid = future.result()
                
                if valid and speed < 5:  # 只接受5秒内的响应
                    if channel not in speed_results:
                        speed_results[channel] = []
                    speed_results[channel].append((source, speed))
        
        # 按速度排序并限制数量
        final_sources = {}
        for channel, sources in speed_results.items():
            sources.sort(key=lambda x: x[1])  # 按速度排序
            final_sources[channel] = [source for source, speed in sources[:8]]  # 取最快8个
        
        return final_sources

    def generate_m3u_file(self, sources):
        """生成M3U文件"""
        m3u_content = """#EXTM3U
# Generated by TV Source Updater
# Update Time: {}\n\n""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        for channel, channel_sources in sources.items():
            for i, source in enumerate(channel_sources):
                m3u_content += '#EXTINF:-1 tvg-id="{}" tvg-name="{}" group-title="直播",{} 源{}\n'.format(
                    channel, channel, channel, i+1)
                m3u_content += source + '\n'
        
        return m3u_content

    def generate_txt_file(self, sources):
        """生成TXT文件"""
        txt_content = "# 电视直播源更新于: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        txt_content += "# 格式: 频道名称,直播源URL\n\n"
        
        for channel, channel_sources in sources.items():
            if channel_sources:
                txt_content += "# {}\n".format(channel)
                for source in channel_sources:
                    txt_content += source + '\n'
                txt_content += "\n"
        
        return txt_content

    def save_categorized_files(self, sources):
        """保存分类文件"""
        categories = {
            "央视": [],
            "卫视": [],
            "凤凰": [],
            "香港": []
        }
        
        # 分类频道
        for channel, channel_sources in sources.items():
            if channel.startswith('CCTV'):
                categories["央视"].append((channel, channel_sources))
            elif "卫视" in channel:
                categories["卫视"].append((channel, channel_sources))
            elif "凤凰" in channel:
                categories["凤凰"].append((channel, channel_sources))
            elif any(hk in channel for hk in ["翡翠", "明珠", "香港"]):
                categories["香港"].append((channel, channel_sources))
        
        # 为每个分类生成文件
        for category, channels in categories.items():
            if channels:
                # M3U文件
                m3u_content = "#EXTM3U\n"
                for channel, channel_sources in channels:
                    for i, source in enumerate(channel_sources):
                        m3u_content += '#EXTINF:-1 tvg-id="{}" tvg-name="{}" group-title="{}",{} 源{}\n'.format(
                            channel, channel, category, channel, i+1)
                        m3u_content += source + '\n'
                
                with open("tv_sources_{}.m3u".format(category), "w", encoding="utf-8") as f:
                    f.write(m3u_content)
                
                # TXT文件
                txt_content = "# {}直播源\n".format(category)
                txt_content += "# 更新于: {}\n\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                for channel, channel_sources in channels:
                    txt_content += "# {}\n".format(channel)
                    for source in channel_sources:
                        txt_content += source + '\n'
                    txt_content += "\n"
                
                with open("tv_sources_{}.txt".format(category), "w", encoding="utf-8") as f:
                    f.write(txt_content)

    def generate_stats(self, sources):
        """生成统计信息"""
        total_sources = sum(len(s) for s in sources.values())
        
        stats_content = """# 电视直播源统计
更新时间: {}

## 频道统计
- 总频道数: {}
- 总源数量: {}

## 各频道源数量
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), len(sources), total_sources)

        for channel, channel_sources in sorted(sources.items()):
            stats_content += "- {}: {} 个源\n".format(channel, len(channel_sources))
        
        with open("STATS.md", "w", encoding="utf-8") as f:
            f.write(stats_content)

    def run(self):
        """主运行函数"""
        print("电视直播源更新开始...")
        
        # 收集所有源
        all_sources = self.collect_all_sources()
        
        if not all_sources:
            print("警告: 未找到任何直播源，使用备用方案")
            all_sources = self.get_sources_from_static_list()
        
        # 测试源速度
        valid_sources = self.test_all_sources(all_sources)
        
        print("有效源统计:")
        for channel, sources in valid_sources.items():
            print("  {}: {}个源".format(channel, len(sources)))
        
        # 生成文件
        m3u_content = self.generate_m3u_file(valid_sources)
        txt_content = self.generate_txt_file(valid_sources)
        
        with open("tv_sources.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        
        with open("tv_sources.txt", "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        # 保存分类文件
        self.save_categorized_files(valid_sources)
        
        # 生成统计
        self.generate_stats(valid_sources)
        
        print("更新完成! 共处理 {} 个频道".format(len(valid_sources)))

if __name__ == "__main__":
    updater = MultiSourceTVUpdater()
    updater.run()