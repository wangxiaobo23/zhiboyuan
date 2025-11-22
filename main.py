import requests
import re
import time
from datetime import datetime
import os

# 目标电视台列表（含央视、地方卫视、凤凰卫视、香港台）
TV_CHANNELS = {
    "央视": ["CCTV-1", "CCTV-2", "CCTV-3", "CCTV-4", "CCTV-5", "CCTV-6", "CCTV-7", "CCTV-8", "CCTV-9", "CCTV-10", "CCTV-11", "CCTV-12", "CCTV-13", "CCTV-14", "CCTV-15", "CCTV-16", "CCTV-17", "CCTV-新闻", "CCTV-少儿", "CCTV-财经"],
    "地方卫视": ["北京卫视", "东方卫视", "湖南卫视", "江苏卫视", "浙江卫视", "安徽卫视", "山东卫视", "广东卫视", "深圳卫视", "四川卫视", "湖北卫视", "河南卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "云南卫视", "贵州卫视", "福建东南卫视", "天津卫视", "重庆卫视"],
    "凤凰卫视": ["凤凰卫视资讯台", "凤凰卫视中文台"],
    "香港台": ["香港TVB翡翠台", "香港ViuTV", "香港无线新闻台", "香港亚洲电视"]
}

# 强化搜索关键词（适配最新网站结构）
SEARCH_KEYWORDS = {
    "CCTV-1": "CCTV1 高清直播源 m3u8",
    "CCTV-2": "CCTV2 财经直播 m3u",
    "北京卫视": "北京卫视 直播源 高清 稳定",
    "东方卫视": "东方卫视 直播 m3u8 最新",
    "湖南卫视": "湖南卫视 直播源 2025",
    "凤凰卫视资讯台": "凤凰卫视资讯台 直播源 可用",
    "凤凰卫视中文台": "凤凰卫视中文台 直播 m3u8",
    "香港TVB翡翠台": "TVB翡翠台 直播源 香港",
    "香港ViuTV": "ViuTV 直播源 高清"
}

# 补充默认关键词（未配置的频道自动使用“频道名+直播源+可用”）
for category, channels in TV_CHANNELS.items():
    for channel in channels:
        if channel not in SEARCH_KEYWORDS:
            SEARCH_KEYWORDS[channel] = f"{channel} 直播源 可用"

def search_live_sources(channel):
    """从tonkiang.us搜索直播源（优化正则匹配）"""
    url = f"https://tonkiang.us/search?q={requests.utils.quote(SEARCH_KEYWORDS[channel])}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = response.apparent_encoding
        # 优化正则：匹配更灵活的直播源链接（含http/https，后缀m3u8/m3u）
        sources = re.findall(r'(https?://[^\s<>"]+\.(m3u8|m3u))', response.text)
        # 去重并提取链接（忽略正则分组）
        unique_sources = list(dict.fromkeys([src[0] for src in sources if "http" in src[0]]))[:8]
        return unique_sources[:8] if len(unique_sources)>=2 else unique_sources + [""]*(2-len(unique_sources))
    except Exception as e:
        print*("[{channel}] 搜索失败：{str(e)}")
        return [""]*2

def test_source_speed(source):
    """测试直播源速度（超时10秒，返回延迟毫秒，失败返回99999）"""
    if not source or "http" not in source:
        return 99999
    try:
        start_time = time.time()
        # 发送HEAD请求测试连通性
        response = requests.head(source, timeout=10, allow_redirects=True)
        delay = (time.time() - start_time) * 1000
        return int(delay) if response.status_code == 200 else 99999
    except:
        return 99999

def generate_files(all_sorted_sources):
    """生成m3u和txt文件（固定文件名，避免Git冲突）"""
    m3u_filename = "tv_live_sources.m3u"
    txt_filename = "tv_live_sources.txt"

    # 写入m3u文件（标准m3u格式）
    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in all_sorted_sources.items():
            f.write(f"#EXTINF:-1,【{category}】\n")
            for channel, sources in channels.items():
                for idx, (source, delay) in enumerate(sources, 1):
                    if delay < 99999:
                        f.write(f"#EXTINF:-1,{channel} (速度{delay}ms 第{idx}源)\n")
                        f.write(f"{source}\n")

    # 写入txt文件（易读格式）
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(f"电视直播源汇总（生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）\n")
        f.write("="*50 + "\n\n")
        for category, channels in all_sorted_sources.items():
            f.write(f"【{category}】\n")
            for channel, sources in channels.items():
                f.write(f"\n{channel}（有效源：{len([s for s, d in sources if d < 99999])}个）\n")
                for idx, (source, delay) in enumerate(sources, 1):
                    status = "✅ 有效" if delay < 99999 else "❌ 无效"
                    f.write(f"  第{idx}源：{source} | 延迟：{delay}ms | {status}\n")
            f.write("-"*30 + "\n")

    print(f"文件生成成功：{m3u_filename}、{txt_filename}")
    return m3u_filename, txt_filename

def main():
    print("开始采集电视直播源...")
    all_sources = {}

    # 遍历所有频道采集源
    for category, channels in TV_CHANNELS.items():
        all_sources[category] = {}
        for channel in channels:
            print(f"正在采集：{category} - {channel}")
            sources = search_live_sources(channel)
            # 测试每个源的速度
            sources_with_speed = [(src, test_source_speed(src)) for src in sources]
            # 按速度排序（快到慢），过滤无效源后保留2-8个
            sorted_sources = sorted([(s, d) for s, d in sources_with_speed if d < 99999], key=lambda x: x[1])
            # 确保最少2个（不足则补充无效占位）
            while len(sorted_sources) < 2:
                sorted_sources.append(("", 99999))
            all_sources[category][channel] = sorted_sources[:8]

    # 生成文件
    generate_files(all_sources)

if __name__ == "__main__":
    main()
