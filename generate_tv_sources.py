import requests
import time
import concurrent.futures
from datetime import datetime

class TVSourceGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 预定义的稳定直播源
        self.tv_sources = {
            # 央视频道
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
                "http://ivi.bupt.edu.cn/hls/cctv3hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225498/index.m3u8"
            ],
            "CCTV4": [
                "http://ivi.bupt.edu.cn/hls/cctv4hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225499/index.m3u8"
            ],
            "CCTV5": [
                "http://ivi.bupt.edu.cn/hls/cctv5hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225500/index.m3u8"
            ],
            "CCTV5+": [
                "http://ivi.bupt.edu.cn/hls/cctv5phd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225501/index.m3u8"
            ],
            "CCTV6": [
                "http://ivi.bupt.edu.cn/hls/cctv6hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225502/index.m3u8"
            ],
            "CCTV7": [
                "http://ivi.bupt.edu.cn/hls/cctv7hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225503/index.m3u8"
            ],
            "CCTV8": [
                "http://ivi.bupt.edu.cn/hls/cctv8hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225504/index.m3u8"
            ],
            "CCTV9": [
                "http://ivi.bupt.edu.cn/hls/cctv9hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225505/index.m3u8"
            ],
            "CCTV10": [
                "http://ivi.bupt.edu.cn/hls/cctv10hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225506/index.m3u8"
            ],
            "CCTV11": [
                "http://ivi.bupt.edu.cn/hls/cctv11hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225507/index.m3u8"
            ],
            "CCTV12": [
                "http://ivi.bupt.edu.cn/hls/cctv12hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225508/index.m3u8"
            ],
            "CCTV13": [
                "http://ivi.bupt.edu.cn/hls/cctv13hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225514/index.m3u8"
            ],
            "CCTV14": [
                "http://ivi.bupt.edu.cn/hls/cctv14hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225515/index.m3u8"
            ],
            "CCTV15": [
                "http://ivi.bupt.edu.cn/hls/cctv15hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225516/index.m3u8"
            ],
            "CCTV16": [
                "http://ivi.bupt.edu.cn/hls/cctv16hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225517/index.m3u8"
            ],
            "CCTV17": [
                "http://ivi.bupt.edu.cn/hls/cctv17hd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225518/index.m3u8"
            ],
            
            # 地方卫视
            "北京卫视": [
                "http://ivi.bupt.edu.cn/hls/beijinghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225530/index.m3u8",
                "http://39.134.65.171/PLTV/88888888/224/3221225530/index.m3u8"
            ],
            "湖南卫视": [
                "http://ivi.bupt.edu.cn/hls/hunanhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225561/index.m3u8",
                "http://39.134.65.171/PLTV/88888888/224/3221225561/index.m3u8"
            ],
            "浙江卫视": [
                "http://ivi.bupt.edu.cn/hls/zhejianghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225567/index.m3u8",
                "http://39.134.65.171/PLTV/88888888/224/3221225567/index.m3u8"
            ],
            "江苏卫视": [
                "http://ivi.bupt.edu.cn/hls/jiangsuhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225559/index.m3u8",
                "http://39.134.65.171/PLTV/88888888/224/3221225559/index.m3u8"
            ],
            "东方卫视": [
                "http://ivi.bupt.edu.cn/hls/dongfanghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225553/index.m3u8",
                "http://39.134.65.171/PLTV/88888888/224/3221225553/index.m3u8"
            ],
            "安徽卫视": [
                "http://ivi.bupt.edu.cn/hls/anhuihd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225529/index.m3u8"
            ],
            "山东卫视": [
                "http://ivi.bupt.edu.cn/hls/shandonghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225565/index.m3u8"
            ],
            "天津卫视": [
                "http://ivi.bupt.edu.cn/hls/tianjinhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225566/index.m3u8"
            ],
            "深圳卫视": [
                "http://ivi.bupt.edu.cn/hls/shenzhenhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225564/index.m3u8"
            ],
            "广东卫视": [
                "http://ivi.bupt.edu.cn/hls/guangdonghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225555/index.m3u8"
            ],
            "湖北卫视": [
                "http://ivi.bupt.edu.cn/hls/hubeihd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225557/index.m3u8"
            ],
            "辽宁卫视": [
                "http://ivi.bupt.edu.cn/hls/liaoninghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225560/index.m3u8"
            ],
            "四川卫视": [
                "http://ivi.bupt.edu.cn/hls/sichuanhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225563/index.m3u8"
            ],
            "重庆卫视": [
                "http://ivi.bupt.edu.cn/hls/chongqinghd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225552/index.m3u8"
            ],
            "贵州卫视": [
                "http://ivi.bupt.edu.cn/hls/guizhouhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225556/index.m3u8"
            ],
            "河南卫视": [
                "http://ivi.bupt.edu.cn/hls/henanhd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225554/index.m3u8"
            ],
            "河北卫视": [
                "http://ivi.bupt.edu.cn/hls/hebeihd.m3u8",
                "http://39.134.66.66/PLTV/88888888/224/3221225551/index.m3u8"
            ],
            
            # 凤凰卫视
            "凤凰中文台": [
                "http://liveali.ifeng.com/live/FHZW.m3u8",
                "http://223.110.243.136/PLTV/3/224/3221227545/index.m3u8",
                "http://223.110.243.155/PLTV/3/224/3221227545/index.m3u8"
            ],
            "凤凰资讯台": [
                "http://liveali.ifeng.com/live/FHZX.m3u8",
                "http://223.110.243.136/PLTV/3/224/3221227544/index.m3u8",
                "http://223.110.243.155/PLTV/3/224/3221227544/index.m3u8"
            ],
            "凤凰香港台": [
                "http://liveali.ifeng.com/live/FHGX.m3u8",
                "http://223.110.243.136/PLTV/3/224/3221227546/index.m3u8"
            ],
            
            # 香港电视台
            "翡翠台": [
                "http://xgtx.zzrbl.com:81/tvbpearl/tvbpearl.m3u8",
                "http://116.199.5.51:8114/index.m3u8?Fsv_chan_hls_se_idx=188&FvSeid=1&Fsv_ctype=LIVES&Fsv_otype=1&Provider_id=0&Pcontent_id=.m3u8"
            ],
            "明珠台": [
                "http://xgtx.zzrbl.com:81/tvbjade/tvbjade.m3u8",
                "http://116.199.5.51:8114/index.m3u8?Fsv_chan_hls_se_idx=187&FvSeid=1&Fsv_ctype=LIVES&Fsv_otype=1&Provider_id=0&Pcontent_id=.m3u8"
            ],
            "香港卫视": [
                "http://zhibo.hkstv.tv/livestream/mutfysrq/playlist.m3u8",
                "http://221.120.163.13:8001/rtmp_live/10/playlist.m3u8"
            ]
        }

    def test_source_speed(self, source_info):
        """测试直播源速度"""
        channel, source = source_info
        try:
            start_time = time.time()
            response = self.session.head(source, timeout=5, allow_redirects=True)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return channel, source, response_time, True
            else:
                return channel, source, response_time, False
                
        except Exception:
            return channel, source, float('inf'), False

    def test_all_sources(self):
        """测试所有直播源的速度和有效性"""
        print("开始测试直播源速度和有效性...")
        
        # 准备测试任务
        test_tasks = []
        for channel, sources in self.tv_sources.items():
            for source in sources:
                test_tasks.append((channel, source))
        
        # 多线程测试
        speed_results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.test_source_speed, task) for task in test_tasks]
            
            completed = 0
            total = len(futures)
            
            for future in concurrent.futures.as_completed(futures):
                channel, source, speed, valid = future.result()
                completed += 1
                
                if valid and speed < 5:  # 只接受5秒内的响应
                    if channel not in speed_results:
                        speed_results[channel] = []
                    speed_results[channel].append((source, speed))
                
                print(f"进度: {completed}/{total} - {channel}: {source} - {'有效' if valid else '无效'} - {speed:.2f}s")
        
        # 按速度排序并限制每个频道2-8个源
        final_sources = {}
        for channel, sources in speed_results.items():
            sources.sort(key=lambda x: x[1])  # 按速度排序
            # 每个频道最少2个，最多8个源
            min_sources = min(2, len(sources))
            max_sources = min(8, len(sources))
            final_sources[channel] = [source for source, speed in sources[:max_sources]]
            # 如果有效源少于2个，尝试保留所有可用源
            if len(final_sources[channel]) < min_sources:
                final_sources[channel] = [source for source, speed in sources]
        
        print(f"测试完成! 有效频道: {len(final_sources)}")
        return final_sources

    def generate_m3u_file(self, sources):
        """生成M3U文件"""
        m3u_content = """#EXTM3U
# Generated by TV Source Generator
# Update Time: {}

""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
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
        print("电视直播源生成开始...")
        
        # 测试所有源
        valid_sources = self.test_all_sources()
        
        if not valid_sources:
            print("警告: 未找到任何有效直播源，使用预定义源")
            valid_sources = self.tv_sources
        
        print("有效源统计:")
        for channel, sources in valid_sources.items():
            print("  {}: {}个源".format(channel, len(sources)))
        
        # 生成合并文件
        m3u_content = self.generate_m3u_file(valid_sources)
        txt_content = self.generate_txt_file(valid_sources)
        
        # 保存文件
        with open("tv_sources.m3u", "w", encoding="utf-8") as f:
            f.write(m3u_content)
        
        with open("tv_sources.txt", "w", encoding="utf-8") as f:
            f.write(txt_content)
        
        # 保存分类文件
        self.save_categorized_files(valid_sources)
        
        # 生成统计信息
        self.generate_stats(valid_sources)
        
        print("所有文件生成完成! 共处理 {} 个频道".format(len(valid_sources)))

if __name__ == "__main__":
    generator = TVSourceGenerator()
    generator.run()