import re
from urllib.parse import urlparse

def analyze_url(url):
    score = 0
    hit_rules = []

    parsed = urlparse(url)
    domain = parsed.netloc
    length = len(url)

    if length > 75:
        score += 15
        hit_rules.append("URL长度过长")

    if not url.startswith("https"):
        score += 15
        hit_rules.append("未使用HTTPS协议")

    suspicious_keywords = ["login", "verify", "bank", "update", "account"]
    for keyword in suspicious_keywords:
        if keyword in url.lower():
            score += 20
            hit_rules.append(f"包含可疑关键词 {keyword}")
            break

    score = min(score, 100)

    return {
        "url_score": score,
        "hit_rules": hit_rules,
        "feature_detail": {
            "length": length,
            "domain": domain
        }
    }