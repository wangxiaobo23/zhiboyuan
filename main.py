import requests
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
import random

# 目标电视台列表
TV_CHANNELS = {
    "央视": ["CCTV-1", "CCTV-2", "CCTV-3", "CCTV-4", "CCTV-5", "CCTV-6", "CCTV-7", "CCTV-8", "CCTV-9", "CCTV-10", "CCTV-11", "CCTV-12", "CCTV-13", "CCTV-14", "CCTV-15", "CCTV-16", "CCTV-17", "CCTV-新闻", "CCTV-少儿", "CCTV-财经"],
    "地方卫视": ["北京卫视", "东方卫视", "湖南卫视", "江苏卫视", "浙江卫视", "安徽卫视", "山东卫视", "广东卫视", "深圳卫视", "四川卫视", "湖北卫视", "河南卫视", "辽宁卫视", "黑龙江卫视", "吉林卫视", "云南卫视", "贵州卫视", "福建东南卫视", "天津卫视", "重庆卫视"],
    "凤凰卫视": ["凤凰卫视资讯台", "凤凰卫视中文台"],
    "香港台": ["香港TVB翡翠台", "香港ViuTV", "香港无线新闻台", "香港亚洲电视"]
}

# 手动验证有效的搜索关键词（与手动搜索完全一致）
SEARCH_KEYWORDS = {
    "CCTV-1": ["CCTV1 直播源"],
    "CCTV-2": ["CCTV2 直播源"],
    "北京卫视": ["北京卫视 直播源"],
    "东方卫视": ["东方卫视 直播源"],
    "湖南卫视": ["湖南卫视 直播源"],
    "凤凰卫视资讯台": ["凤凰卫视资讯台 直播源"],
    "凤凰卫视中文台": ["凤凰卫视中文台 直播源"],
    "香港TVB翡翠台": ["TVB翡翠台 直播源"],
    "香港ViuTV": ["ViuTV 直播源"]
}

# 补充默认关键词（与手动搜索逻辑一致）
for category, channels in TV_CHANNELS.items():
    for channel in channels:
        if channel not in SEARCH_KEYWORDS:
            SEARCH_KEYWORDS[channel] = [f"{channel} 直播源"]

# 随机User-Agent池（模拟手动浏览器访问）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
]

def search_live_sources(channel):
    """完全模拟手动搜索逻辑：单关键词+精准提取"""
    sources = []
    keyword = SEARCH_KEYWORDS[channel][0]  # 用与手动搜索一致的关键词
    url = f"https://tonkiang.us/search?q={requests.utils.quote(keyword)}"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://tonkiang.us/",
        "Cache-Control": "no-cache"
    }
    
    try:
        # 模拟手动访问延迟
        time.sleep(2)
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 关键优化：提取所有包含直播源的文本块，再匹配链接（手动搜索结果的常见位置）
        all_text = soup.get_text(separator="\n", strip=True)
        # 精准匹配m3u8/m3u链接（包含可能的参数，如?token=xxx）
        link_pattern = r'(https?://[^\s<>"\'`]+?\.(m3u8|m3u)(\?[^\s<>"\'`]*)?)'
        matched_links = re.findall(link_pattern, all_text, re.IGNORECASE)
        
        # 提取并去重
        for link in matched_links:
            full_link = link[0].strip()
            if full_link not in sources and "http" in full_link:
                sources.append(full_link)
        
        # 额外提取a标签中的链接（手动搜索结果的另一种常见位置）
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if re.match(link_pattern, href, re.IGNORECASE) and href not in sources:
                sources.append(href)
    
    except Exception as e:
        print(f"[{channel}] 搜索失败：{str(e)}")
    
    # 去重并限制数量（2-8个）
    unique_sources = list(dict.fromkeys(sources))[:8]
    return unique_sources[:8] if len(unique_sources)>=2 else unique_sources + [""]*(2-len(unique_sources))

def test_source_speed(source):
    """完全模拟手动播放验证逻辑"""
    if not source or "http" not in source:
        return 99999
    try:
        start_time = time.time()
        # 模拟播放器的请求方式：带User-Agent，允许重定向，读取部分内容
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(
            source, 
            headers=headers,
            timeout=20, 
            allow_redirects=True, 
            stream=True
        )
        # 读取前200字节验证是否能正常连接（手动播放的核心验证逻辑）
        next(response.iter_content(chunk_size=200))
        delay = (time.time() - start_time) * 1000
        response.close()
        # 支持更多有效状态码（部分直播源返回206 Partial Content）
        return int(delay) if response.status_code in [200, 206, 302] else 99999
    except Exception as e:
        print(f"[{source}] 测速失败：{str(e)}")
        return 99999

def generate_files(all_sorted_sources):
    """生成m3u和txt文件"""
    m3u_filename = "tv_live_sources.m3u"
    txt_filename = "tv_live_sources.txt"

    # 写入m3u文件（播放器可直接识别）
    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in all_sorted_sources.items():
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
                valid_count = len([s for s, d in sources if d < 99999])
                f.write(f"\n{channel}（有效源：{valid_count}个）\n")
                for idx, (source, delay) in enumerate(sources, 1):
                    status = "✅ 有效" if delay < 99999 else "❌ 无效"
                    f.write(f"  第{idx}源：{source} | 延迟：{delay}ms | {status}\n")
            f.write("-"*30 + "\n")

    print(f"文件生成成功：{m3u_filename}、{txt_filename}")
    return m3u_filename, txt_filename

def main():
    print("开始采集电视直播源（模拟手动搜索逻辑）...")
    all_sources = {}

    for category, channels in TV_CHANNELS.items():
        all_sources[category] = {}
        for channel in channels:
            print(f"正在采集：{category} - {channel}")
            sources = search_live_sources(channel)
            sources_with_speed = [(src, test_source_speed(src)) for src in sources]
            # 按速度排序（快到慢）
            sorted_sources = sorted([(s, d) for s, d in sources_with_speed if d < 99999], key=lambda x: x[1])
            # 确保最少2个源
            while len(sorted_sources) < 2:
                sorted_sources.append(("", 99999))
            all_sources[category][channel] = sorted_sources[:8]

    generate_files(all_sources)

if __name__ == "__main__":
    main()
