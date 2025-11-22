import requests
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

# 多组搜索关键词（提高匹配概率）
SEARCH_KEYWORDS = {
    "CCTV-1": ["CCTV1 直播源", "央视一套 直播 m3u8", "CCTV1 HD 直播链接"],
    "CCTV-2": ["CCTV2 财经 直播源", "央视二套 直播 m3u", "CCTV2 直播链接"],
    "北京卫视": ["北京卫视 直播源", "BTV 直播 m3u8", "北京卫视 高清直播"],
    "东方卫视": ["东方卫视 直播源", "Dragon TV 直播 m3u", "东方卫视 直播链接"],
    "湖南卫视": ["湖南卫视 直播源", "Hunan TV 直播 m3u8", "芒果台 直播链接"],
    "凤凰卫视资讯台": ["凤凰资讯台 直播源", "Phoenix Info News 直播 m3u", "凤凰资讯台 直播链接"],
    "凤凰卫视中文台": ["凤凰中文台 直播源", "Phoenix Chinese 直播 m3u8", "凤凰中文台 直播链接"],
    "香港TVB翡翠台": ["TVB翡翠台 直播源", "Jade TV 直播 m3u", "翡翠台 香港直播"],
    "香港ViuTV": ["ViuTV 直播源", "Viu TV 直播 m3u8", "香港ViuTV 直播链接"]
}

# 补充默认关键词（每组3个）
for category, channels in TV_CHANNELS.items():
    for channel in channels:
        if channel not in SEARCH_KEYWORDS:
            SEARCH_KEYWORDS[channel] = [
                f"{channel} 直播源",
                f"{channel} 直播 m3u8",
                f"{channel} 高清直播链接"
            ]

# 随机User-Agent池（绕过反爬）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/128.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
]

def search_live_sources(channel):
    """多关键词+多User-Agent采集，绕过反爬"""
    sources = []
    # 遍历该频道的所有搜索关键词
    for keyword in SEARCH_KEYWORDS[channel]:
        url = f"https://tonkiang.us/search?q={requests.utils.quote(keyword)}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://tonkiang.us/",
            "Cache-Control": "no-cache"
        }
        try:
            # 随机延迟（避免高频请求被封）
            time.sleep(random.uniform(1, 3))
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 多维度提取链接（a标签、script标签、div标签）
            # 1. 提取a标签href
            for link in soup.find_all("a", href=True):
                href = link["href"].strip()
                if href.endswith((".m3u8", ".m3u")) and "http" in href and href not in sources:
                    sources.append(href)
            # 2. 提取script标签中的链接
            for script in soup.find_all("script"):
                script_text = script.text
                if ".m3u8" in script_text or ".m3u" in script_text:
                    links = re.findall(r'(https?://[^\s<>"]+\.(m3u8|m3u))', script_text)
                    for link in links:
                        if link[0] not in sources:
                            sources.append(link[0])
            # 3. 提取div标签中的链接
            for div in soup.find_all("div", string=re.compile(r'https?://')):
                div_text = div.text
                links = re.findall(r'(https?://[^\s<>"]+\.(m3u8|m3u))', div_text)
                for link in links:
                    if link[0] not in sources:
                        sources.append(link[0])
        except Exception as e:
            print(f"[{channel}] 关键词[{keyword}]搜索失败：{str(e)}")
            continue
        # 收集到8个源就停止（达到上限）
        if len(sources) >= 8:
            break
    # 去重并限制数量（2-8个）
    unique_sources = list(dict.fromkeys(sources))[:8]
    return unique_sources[:8] if len(unique_sources)>=2 else unique_sources + [""]*(2-len(unique_sources))

def test_source_speed(source):
    """优化测速逻辑（允许重定向，延长超时）"""
    if not source or "http" not in source:
        return 99999
    try:
        start_time = time.time()
        # 改用GET请求（部分源不支持HEAD），增加超时到15秒
        response = requests.get(source, timeout=15, allow_redirects=True, stream=True)
        # 只读取前100字节验证连通性
        response.iter_content(chunk_size=100).__next__()
        delay = (time.time() - start_time) * 1000
        response.close()
        return int(delay) if response.status_code in [200, 206] else 99999
    except:
        return 99999

def generate_files(all_sorted_sources):
    """生成m3u和txt文件"""
    m3u_filename = "tv_live_sources.m3u"
    txt_filename = "tv_live_sources.txt"

    # 写入m3u文件
    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in all_sorted_sources.items():
            for channel, sources in channels.items():
                for idx, (source, delay) in enumerate(sources, 1):
                    if delay < 99999:
                        f.write(f"#EXTINF:-1,{channel} (速度{delay}ms 第{idx}源)\n")
                        f.write(f"{source}\n")

    # 写入txt文件
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
    print("开始采集电视直播源...")
    all_sources = {}

    for category, channels in TV_CHANNELS.items():
        all_sources[category] = {}
        for channel in channels:
            print(f"正在采集：{category} - {channel}")
            sources = search_live_sources(channel)
            sources_with_speed = [(src, test_source_speed(src)) for src in sources]
            # 按速度排序（快到慢）
            sorted_sources = sorted([(s, d) for s, d in sources_with_speed if d < 99999], key=lambda x: x[1])
            # 确保最少2个
            while len(sorted_sources) < 2:
                sorted_sources.append(("", 99999))
            all_sources[category][channel] = sorted_sources[:8]

    generate_files(all_sources)

if __name__ == "__main__":
    main()
