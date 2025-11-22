#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版 main.py
- 更宽泛地从页面提取 m3u8/m3u 链接（包括 script、data-src、iframe 等）
- 使用 requests.Session 复用连接并统一 headers
- test_source_speed 使用 HEAD 优先，失败时使用流式 GET 读取少量字节确认可用性
- 对 master m3u8 做简单解析，展开变体链接
- 限速与重试，返回更可靠的测速结果
- 生成 tv_live_sources.m3u 和 tv_live_sources.txt 两个输出文件
注意：不要在未经授权的情况下分发受版权保护的流。运行前 pip install requests beautifulsoup4
"""

import re
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# 目标电视台列表（示例，保留原样或按需修改）
TV_CHANNELS = {
    "央视": ["CCTV-1", "CCTV-2", "CCTV-3", "CCTV-4", "CCTV-5"],
    "地方卫视": ["北京卫视", "东方卫视", "湖南卫视", "江苏卫视", "浙江卫视"],
    "凤凰卫视": ["凤凰卫视资讯台", "凤凰卫视中文台"],
    "香港台": ["香港TVB翡翠台", "香港ViuTV"]
}

# 强化搜索关键词（可按需补充）
SEARCH_KEYWORDS = {
    "CCTV-1": "CCTV1 高清直播源",
    "CCTV-2": "CCTV2 财经直播",
    "北京卫视": "北京卫视 直播源",
    "东方卫视": "东方卫视 直播",
    "湖南卫视": "湖南卫视 直播源",
    "凤凰卫视资讯台": "凤凰卫视资讯台 直播源",
    "凤凰卫视中文台": "凤凰卫视中文台 直播源",
    "香港TVB翡翠台": "TVB翡翠台 直播源",
    "香港ViuTV": "ViuTV 直播源"
}

# 填充默认关键词
for cat, chans in TV_CHANNELS.items():
    for ch in chans:
        if ch not in SEARCH_KEYWORDS:
            SEARCH_KEYWORDS[ch] = f"{ch} 直播源"

# 全局 session 复用
_session = None


def get_session():
    global _session
    if _session is None:
        s = requests.Session()
        s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        _session = s
    return _session


# 配置项
SEARCH_BASE = "https://tonkiang.us/search?q="
MAX_CANDIDATES = 20
MAX_SOURCES_PER_CHANNEL = 8
MIN_SOURCES_REQUIRED = 2
RATE_LIMIT_SLEEP = 0.6  # 每次请求间隔秒
HEAD_TIMEOUT = 6
GET_TIMEOUT = 12
SPEED_TIMEOUT = 10


def _extract_urls_from_soup(soup):
    candidates = []
    # 常见属性
    for tag in soup.find_all(True):
        for attr in ("href", "src", "data-src", "data-href", "data-url"):
            if tag.has_attr(attr):
                candidates.append(tag[attr])
        # 内嵌 script 文本可能包含链接
        if tag.name == "script" and tag.string:
            candidates.append(tag.string)
    return candidates


def _regex_find_urls(text):
    # 捕获 http(s)://... .m3u8 或 .m3u，允许带 query
    regex = re.compile(r'https?://[^\s\'"<>]+?\.(?:m3u8|m3u)(?:\?[^\s\'"<>]*)?', re.IGNORECASE)
    return regex.findall(text or "")


def normalize_and_filter_urls(urls, base=None):
    clean = []
    for u in urls:
        if not isinstance(u, str):
            continue
        u = u.strip()
        if not u:
            continue
        # 跳过 javascript: 等非 http
        if u.startswith("javascript:") or u.startswith("data:"):
            continue
        # 完成相对链接
        if base and not u.startswith("http"):
            try:
                u = urljoin(base, u)
            except Exception:
                continue
        # 只保留 m3u/m3u8 链接或含有 m3u8 的 URL
        if ".m3u8" not in u.lower() and ".m3u" not in u.lower():
            continue
        # 简单去掉空白与重复
        if len(u) < 12:
            continue
        if u not in clean:
            clean.append(u)
    return clean


def search_live_sources(channel):
    """
    在 tonkiang.us 搜索并提取可能的 m3u8/m3u 链接，返回候选列表。
    若没找到返回两个空占位。
    """
    sess = get_session()
    q = requests.utils.quote(SEARCH_KEYWORDS.get(channel, channel))
    url = SEARCH_BASE + q
    try:
        r = sess.get(url, timeout=GET_TIMEOUT)
        r.encoding = r.apparent_encoding
        text = r.text or ""
        # 解析 HTML 提取属性链接和脚本内链接
        soup = BeautifulSoup(text, "html.parser")
        raw_candidates = _extract_urls_from_soup(soup)
        # 正则再查一次页面文本
        raw_candidates.extend(_regex_find_urls(text))
        # 处理可能的重定向页面或嵌套页面：查找 iframe/src 指向其他页面
        iframes = soup.find_all("iframe")
        for iframe in iframes:
            if iframe.has_attr("src"):
                try:
                    ir = sess.get(urljoin(url, iframe["src"]), timeout=GET_TIMEOUT)
                    ir.encoding = ir.apparent_encoding
                    raw_candidates.extend(_regex_find_urls(ir.text))
                except Exception:
                    pass
        # 归一化与去重
        candidates = normalize_and_filter_urls(raw_candidates, base=url)
        # 若没有直链，可以尝试更宽泛的正则（包含参数形式）
        if not candidates:
            broader = re.findall(r'https?://[^\s\'"<>]+\?[^\s\'"<>]*m3u8[^\s\'"<>]*', text or "", re.IGNORECASE)
            candidates.extend(broader)
            candidates = normalize_and_filter_urls(candidates, base=url)
        # 限制数量
        if not candidates:
            return [""] * MIN_SOURCES_REQUIRED
        return candidates[:MAX_CANDIDATES]
    except Exception as e:
        print(f"[{channel}] 搜索失败：{e}")
        return [""] * MIN_SOURCES_REQUIRED


def _is_master_m3u8(text):
    # master playlist 含有 EXT-X-STREAM-INF 通常表示包含变体
    return "#EXT-X-STREAM-INF" in (text or "")


def expand_m3u8_variants(source):
    """
    如果 source 是 master m3u8，解析并返回 variant m3u8 的绝对 URL 列表（可能为空）。
    如果不是 master，返回空列表。
    """
    sess = get_session()
    try:
        r = sess.get(source, timeout=GET_TIMEOUT)
        if r.status_code != 200:
            return []
        text = r.text or ""
        if not _is_master_m3u8(text):
            return []
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#EXT-X-SESSION-KEY")]
        variants = []
        for i, ln in enumerate(lines):
            if ln.upper().startswith("#EXT-X-STREAM-INF"):
                # 下一个非注释行应该是 URL（可能相对）
                # 如果当前行包含 URI=... 则也处理
                m = re.search(r'URI="([^"]+)"', ln)
                if m:
                    uri = m.group(1)
                else:
                    # 下行可能是 URI
                    next_uri = ""
                    # 找 next non-comment line after i
                    for j in range(i + 1, min(i + 4, len(lines))):
                        if not lines[j].startswith("#"):
                            next_uri = lines[j]
                            break
                    uri = next_uri
                if uri:
                    full = uri if uri.lower().startswith("http") else urljoin(source, uri)
                    if full not in variants:
                        variants.append(full)
        return variants
    except Exception:
        return []


def test_source_speed(source):
    """
    测试直播源速度（先尝试 HEAD，若不可用则使用 GET 流式读取 1KB），
    返回延迟毫秒；失败返回 99999。
    """
    if not source or not source.startswith("http"):
        return 99999
    sess = get_session()
    try:
        start = time.time()
        # HEAD 先行
        try:
            h = sess.head(source, timeout=HEAD_TIMEOUT, allow_redirects=True)
            if h.status_code == 200:
                delay = int((time.time() - start) * 1000)
                return delay
            # 如果 HEAD 返回 405 或其他非 200，后面会尝试 GET
        except requests.exceptions.RequestException:
            # 忽略，尝试 GET
            pass
        # GET 流式读取少量内容
        start = time.time()
        g = sess.get(source, timeout=SPEED_TIMEOUT, stream=True, allow_redirects=True)
        # 考虑 200 和 206 为有效
        if g.status_code in (200, 206):
            try:
                chunk = next(g.iter_content(chunk_size=1024), b"")
            except Exception:
                chunk = b""
            delay = int((time.time() - start) * 1000)
            if chunk:
                return delay
        return 99999
    except Exception:
        return 99999


def generate_files(all_sorted_sources):
    """生成 m3u 和 txt 文件"""
    m3u_filename = "tv_live_sources.m3u"
    txt_filename = "tv_live_sources.txt"

    with open(m3u_filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for category, channels in all_sorted_sources.items():
            f.write(f"#EXTINF:-1,【{category}】\n")
            for channel, sources in channels.items():
                for idx, (source, delay) in enumerate(sources, 1):
                    if source and delay < 99999:
                        f.write(f"#EXTINF:-1,{channel} (速度{delay}ms 第{idx}源)\n")
                        f.write(f"{source}\n")

    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(f"电视直播源汇总（生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）\n")
        f.write("=" * 50 + "\n\n")
        for category, channels in all_sorted_sources.items():
            f.write(f"【{category}】\n")
            for channel, sources in channels.items():
                valid_count = len([s for s, d in sources if d < 99999])
                f.write(f"\n{channel}（有效源：{valid_count}个）\n")
                for idx, (source, delay) in enumerate(sources, 1):
                    status = "✅ 有效" if delay < 99999 else "❌ 无效"
                    f.write(f"  第{idx}源：{source or '（空）'} | 延迟：{delay}ms | {status}\n")
            f.write("-" * 30 + "\n")

    print(f"文件生成成功：{m3u_filename}、{txt_filename}")
    return m3u_filename, txt_filename


def main():
    print("开始采集电视直播源...")
    sess = get_session()
    all_sources = {}

    for category, channels in TV_CHANNELS.items():
        all_sources[category] = {}
        for channel in channels:
            print(f"正在采集：{category} - {channel}")
            candidates = search_live_sources(channel)
            # 进一步展开 master playlists（把变体加入候选）
            expanded = []
            for c in candidates:
                if not c:
                    continue
                variants = expand_m3u8_variants(c)
                if variants:
                    expanded.extend(variants)
                expanded.append(c)
                # 限制候选数量以防爆炸
                if len(expanded) >= MAX_CANDIDATES:
                    break
            if expanded:
                candidates = expanded[:MAX_CANDIDATES]
            # 测速（并发可以改用线程池，但要小心限流）
            sources_with_speed = []
            for src in candidates:
                delay = test_source_speed(src)
                print(f"  测试：{src} -> {delay}ms")
                sources_with_speed.append((src, delay))
                time.sleep(RATE_LIMIT_SLEEP)
            # 保留有效源并排序
            valid_sorted = sorted([(s, d) for s, d in sources_with_speed if d < 99999], key=lambda x: x[1])
            # 补足最少数量
            while len(valid_sorted) < MIN_SOURCES_REQUIRED:
                valid_sorted.append(("", 99999))
            all_sources[category][channel] = valid_sorted[:MAX_SOURCES_PER_CHANNEL]
            # 若没有有效源，则选最小延迟（即使是 99999）前两个作为占位显示
            if all(d >= 99999 for _, d in all_sources[category][channel]):
                # 选择原候选中最优的两个作为展示（按延迟）
                fallback = sorted(sources_with_speed, key=lambda x: x[1])[:MIN_SOURCES_REQUIRED]
                all_sources[category][channel] = fallback + [("", 99999)] * max(0, MIN_SOURCES_REQUIRED - len(fallback))
            # 轻微间隔避免快速请求
            time.sleep(RATE_LIMIT_SLEEP)

    generate_files(all_sources)
    print("采集完成。")


if __name__ == "__main__":
    main()