import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_page_text(url):
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.extract()
        text = soup.get_text(separator=' ', strip=True)
        return text[:3000]
    except Exception as e:
        return ""

def crawl_links(url, depth=1, max_links=10):
    """
    深入爬取页面链接
    depth: 爬取深度，默认为1层
    max_links: 每层最大链接数
    """
    visited = set()
    result = []
    
    def crawl(current_url, current_depth):
        if current_depth > depth or current_url in visited or len(result) >= max_links:
            return
        
        try:
            visited.add(current_url)
            response = requests.get(current_url, timeout=8, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, "html.parser")
            
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href')
                absolute_url = urljoin(current_url, href)
                
                parsed_url = urlparse(absolute_url)
                parsed_current = urlparse(current_url)
                
                if (parsed_url.scheme in ['http', 'https'] and 
                    parsed_url.netloc == parsed_current.netloc and 
                    absolute_url not in visited):
                    links.append(absolute_url)
            
            result.append(current_url)
            
            for link in links[:max_links - len(result)]:
                crawl(link, current_depth + 1)
        
        except Exception as e:
            pass
    
    try:
        crawl(url, 0)
    except Exception as e:
        pass
    
    return result