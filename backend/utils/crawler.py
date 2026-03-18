import requests
from bs4 import BeautifulSoup

def get_page_text(url):
    try:
        response = requests.get(url, timeout=5)
        # 自动检测编码，避免乱码
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        # 去掉 script 和 style 标签
        for tag in soup(["script", "style"]):
            tag.extract()
        # 获取文本，使用分隔符和去除首尾空白
        text = soup.get_text(separator=' ', strip=True)
        return text[:3000]  # 防止太长
    except Exception as e:
        return ""