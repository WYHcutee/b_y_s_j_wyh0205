import requests
from bs4 import BeautifulSoup

def get_page_text(url):

    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        # 去掉script和style
        for tag in soup(["script", "style"]):
            tag.extract()

        text = soup.get_text()
        return text[:3000]  # 防止太长

    except Exception as e:
        return ""