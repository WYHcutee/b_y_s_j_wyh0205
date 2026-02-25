# backend/feature_extractor/url_features.py

import re
from urllib.parse import urlparse, urlunparse
import requests
import idna
import time

def extract_url_features(url):
    """
    提取 URL 本身的结构特征
    """
    parsed = urlparse(url)
    features = {
        "url_length": len(url),
        "has_ip": bool(re.search(r'\d+\.\d+\.\d+\.\d+', url)),
        "has_at_symbol": "@" in url,
        "subdomain_count": parsed.netloc.count('.'),
        "uses_https": parsed.scheme == "https"
    }
    return features

def fetch_url_content_safe(url, retries=3, delay=2):
    """
    安全抓取网页内容，自动处理中文域名（Punycode），遇到失败不会崩溃
    """
    try:
        parsed = urlparse(url)
        if not parsed.hostname:
            print(f"[WARN] URL {url} 无法解析主机名，跳过")
            return None

        # 将中文域名转换为 Punycode
        punycode_host = idna.encode(parsed.hostname).decode('ascii')
        new_url = urlunparse((
            parsed.scheme or "https",
            punycode_host + (':' + str(parsed.port) if parsed.port else ''),
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

        for attempt in range(1, retries + 1):
            try:
                response = requests.get(new_url, timeout=5)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"[WARN] 第 {attempt} 次请求失败: {e}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    print(f"[WARN] URL {url} 请求失败，跳过该 URL")
                    return None
    except idna.IDNAError as e:
        print(f"[WARN] 域名无法编码为 Punycode: {e}, 跳过该 URL")
        return None
    except Exception as e:
        print(f"[WARN] 请求失败: {e}, 跳过该 URL")
        return None