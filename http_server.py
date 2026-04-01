import http.server
import json
import socketserver
import sys
import traceback
import os
import requests
import re
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import urllib.parse

load_dotenv()

PORT = 5555

SUPPORTED_MODELS = {
    'glm-4v-flash': {'name': '智谱 GLM-4V-Flash', 'api': 'zhipu'},
    'glm-4v': {'name': '智谱 GLM-4V', 'api': 'zhipu'},
    'ernie-bot': {'name': '百度千帆', 'api': 'ernie'},
    'qwen-vl-plus': {'name': '阿里 通义千问', 'api': 'qwen'},
    'hunyuan-lite': {'name': '腾讯混元', 'api': 'hunyuan'},
    'step-1v': {'name': '阶跃星辰', 'api': 'step'},
    'deepseek-vl': {'name': 'DeepSeek', 'api': 'deepseek'},
}

print("=" * 50)
print("HTTP 服务器启动")
print(f"端口: {PORT}")
print(f"支持模型: {list(SUPPORTED_MODELS.keys())}")
print("=" * 50)

def get_rag_knowledge(query):
    """
    获取RAG知识库相关内容
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from backend.fusion.rag_engine import get_relevant_knowledge
        knowledge = get_relevant_knowledge(query)
        if knowledge:
            print(f"[RAG] 检索到相关知识: {len(knowledge)} 字符")
            return knowledge
    except Exception as e:
        print(f"[RAG] 检索失败: {e}")
    return ""

def call_model_api(prompt, image_base64, model_name='glm-4v-flash'):
    """
    根据模型名称调用对应的API
    """
    api_key = os.environ.get("ZHIPU_API_KEY")
    
    if model_name.startswith('glm'):
        return call_zhipu_api(prompt, image_base64, model_name, api_key)
    elif model_name == 'ernie-bot':
        return call_ernie_api(prompt, image_base64)
    elif model_name == 'qwen-vl-plus':
        return call_qwen_api(prompt, image_base64)
    elif model_name.startswith('hunyuan'):
        return call_hunyuan_api(prompt, image_base64, model_name)
    elif model_name == 'step-1v':
        return call_step_api(prompt, image_base64)
    elif model_name == 'deepseek-vl':
        return call_deepseek_api(prompt, image_base64)
    else:
        print(f"[API] 未知模型 {model_name}，使用默认智谱")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', api_key)

def call_zhipu_api(prompt, image_base64, model_name, api_key):
    """调用智谱API"""
    content = [{"type": "text", "text": prompt}]
    if image_base64:
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    return requests.post(
        "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=60
    )

def call_ernie_api(prompt, image_base64):
    """调用百度千帆 API (OpenAI兼容模式)"""
    api_key = os.environ.get("ERNIE_API_KEY")
    if not api_key:
        print("[API] 百度千帆API密钥未配置，使用智谱代替")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    
    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    available_models = ["ernie-4.5-8k-preview", "ernie-3.5-8k", "ernie-speed-8k", "ernie-lite-8k"]
    
    for model in available_models:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024
        }
        
        print(f"[API] 调用百度千帆 (模型: {model})")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"[API] 百度千帆调用成功 (模型: {model})")
                return result
            else:
                print(f"[API] 模型 {model} 不可用: {response.status_code}")
                continue
        except Exception as e:
            print(f"[API] 模型 {model} 调用异常: {e}")
            continue
    
    print("[API] 百度千帆所有模型不可用，使用智谱代替")
    return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))

def call_qwen_api(prompt, image_base64):
    """调用通义千问 API"""
    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        print("[API] 通义千问API密钥未配置，使用智谱代替")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    print("[API] 调用通义千问")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("[API] 通义千问调用成功")
            return result
        else:
            print(f"[API] 通义千问调用失败: {response.status_code}")
            return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    except Exception as e:
        print(f"[API] 通义千问调用异常: {e}")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))

def call_hunyuan_api(prompt, image_base64, model_name='hunyuan-lite'):
    """
    调用腾讯混元API（免费版）
    
    官方文档：https://cloud.tencent.com/document/product/1729/111007
    
    使用说明：
    1. 访问 https://console.cloud.tencent.com/hunyuan 获取API密钥
    2. 在 .env 文件中添加：HUNYUAN_API_KEY=你的密钥
    
    错误排查：
    - 401错误：API密钥无效或未配置
    - 429错误：请求频率超限，请稍后重试
    - 500错误：服务器内部错误，请稍后重试
    - 连接失败：检查网络连接
    """
    api_key = os.environ.get("HUNYUAN_API_KEY")
    if not api_key:
        print("[API] 腾讯混元API密钥未配置，使用智谱代替")
        print("[API] 请在.env文件中添加：HUNYUAN_API_KEY=你的密钥")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    
    url = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "hunyuan-lite",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    print(f"[API] 调用腾讯混元 (hunyuan-lite)")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"[API] 混元响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[API] 腾讯混元调用成功")
            return result
        elif response.status_code == 401:
            print("[API] 腾讯混元认证失败，请检查API密钥")
            return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
        elif response.status_code == 429:
            print("[API] 腾讯混元请求频率超限")
            return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
        else:
            print(f"[API] 腾讯混元调用失败: {response.status_code}")
            return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    except requests.exceptions.Timeout:
        print("[API] 腾讯混元请求超时")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    except requests.exceptions.ConnectionError:
        print("[API] 腾讯混元连接失败")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    except Exception as e:
        print(f"[API] 腾讯混元调用异常: {e}")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))

def call_step_api(prompt, image_base64):
    """调用阶跃星辰 API"""
    api_key = os.environ.get("STEP_API_KEY")
    if not api_key:
        print("[API] 阶跃星辰API密钥未配置，使用智谱代替")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    
    url = "https://api.stepfun.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "step-1-8k",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    print("[API] 调用阶跃星辰")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("[API] 阶跃星辰调用成功")
            return result
        else:
            print(f"[API] 阶跃星辰调用失败: {response.status_code}")
            return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    except Exception as e:
        print(f"[API] 阶跃星辰调用异常: {e}")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))

def call_deepseek_api(prompt, image_base64):
    """调用 DeepSeek API"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("[API] DeepSeek API密钥未配置，使用智谱代替")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }
    
    print("[API] 调用 DeepSeek")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("[API] DeepSeek 调用成功")
            return result
        else:
            print(f"[API] DeepSeek 调用失败: {response.status_code}")
            return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))
    except Exception as e:
        print(f"[API] DeepSeek 调用异常: {e}")
        return call_zhipu_api(prompt, image_base64, 'glm-4v-flash', os.environ.get("ZHIPU_API_KEY"))

def fetch_webpage_content(url, use_selenium=False):
    """
    获取网页内容，支持多种方式
    use_selenium: 是否使用Selenium（批量检测时建议关闭以提速）
    """
    print(f"[抓取] 开始获取: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }
    
    text_content = ""
    title = ""
    
    try:
        print(f"[抓取] 方式1: requests 直接请求")
        resp = requests.get(
            url, 
            headers=headers, 
            timeout=8,
            allow_redirects=True,
            verify=True
        )
        print(f"[抓取] 响应状态码: {resp.status_code}")
        print(f"[抓取] 响应长度: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 100:
            resp.encoding = resp.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(resp.text, "html.parser")
            
            for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
                tag.extract()
            
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else ""
            
            body = soup.find('body')
            if body:
                text_content = body.get_text(separator=' ', strip=True)
            else:
                text_content = soup.get_text(separator=' ', strip=True)
            
            text_content = ' '.join(text_content.split())[:3000]
            print(f"[抓取] 提取文本长度: {len(text_content)}")
            
            if len(text_content) > 50:
                return text_content, title, "requests"
    
    except requests.exceptions.Timeout:
        print(f"[抓取] 请求超时")
    except requests.exceptions.SSL_ERROR:
        print(f"[抓取] SSL 错误")
    except requests.exceptions.ConnectionError as e:
        print(f"[抓取] 连接错误: {e}")
    except Exception as e:
        print(f"[抓取] requests 错误: {e}")
    
    if len(text_content) < 50 and use_selenium:
        print(f"[抓取] 方式2: 尝试 Selenium")
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument(f"--user-agent={headers['User-Agent']}")
            
            driver_path = r"F:\1111AAA毕业设计\基于多模态大模型的恶意网站检测系统\drivers\chromedriver.exe"
            
            if os.path.exists(driver_path):
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(20)
                
                try:
                    print(f"[抓取] Selenium 访问: {url}")
                    driver.get(url)
                    
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    title = driver.title or ""
                    text_content = driver.find_element(By.TAG_NAME, "body").text
                    text_content = ' '.join(text_content.split())[:3000]
                    
                    print(f"[抓取] Selenium 提取文本长度: {len(text_content)}")
                    
                    if len(text_content) > 50:
                        return text_content, title, "selenium"
                        
                except Exception as e:
                    print(f"[抓取] Selenium 错误: {e}")
                finally:
                    driver.quit()
            else:
                print(f"[抓取] ChromeDriver 不存在: {driver_path}")
        except ImportError:
            print(f"[抓取] Selenium 未安装")
        except Exception as e:
            print(f"[抓取] Selenium 初始化失败: {e}")
    
    if len(text_content) < 50:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc
        path = parsed.path
        
        text_content = f"""
网页内容获取受限，以下是基本信息：
- 域名: {domain}
- 路径: {path}
- 完整URL: {url}

注意：该网站可能有反爬虫机制或需要JavaScript渲染。
请根据URL结构进行初步风险分析。
"""
        print(f"[抓取] 使用备用信息")
    
    return text_content, title, "fallback"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            print(f"\n{'='*50}")
            print(f"[检测] 收到请求: {self.path}")
            
            if self.path == '/batch_detect':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                urls = data.get('urls', [])
                model_name = data.get('model', 'glm-4v-flash')
                
                if isinstance(urls, str):
                    urls = [u.strip() for u in urls.split('\n') if u.strip()]
                
                urls = urls[:10]
                
                print(f"[批量检测] 收到 {len(urls)} 个URL, 模型: {model_name}")
                
                results = []
                for i, url in enumerate(urls):
                    print(f"[批量检测] 处理第 {i+1}/{len(urls)} 个: {url}")
                    try:
                        result = self._detect_single_url(url, model_name)
                        result['url'] = url
                        result['index'] = i + 1
                        results.append(result)
                    except Exception as e:
                        results.append({
                            'url': url,
                            'index': i + 1,
                            'error': str(e),
                            'final_score': 0,
                            'risk_level': 'Error'
                        })
                
                response_data = {
                    'success': True,
                    'total': len(urls),
                    'model': model_name,
                    'results': results
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                print(f"[批量检测] 完成，共处理 {len(results)} 个URL")
                return
            
            if self.path == '/detect':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                print(f"[检测] 数据: {data}")
                
                url = data.get('url', '')
                input_type = data.get('input_type', 'url')
                text_input = data.get('text_content', '')
                image_base64 = data.get('image_base64', '')
                title = data.get('title', '未知')
                model_name = data.get('model', 'glm-4v-flash')
                
                if input_type == 'url' and url:
                    text_content, title, method = fetch_webpage_content(url)
                    print(f"[检测] 获取方式: {method}")
                    print(f"[检测] 标题: {title}")
                    print(f"[检测] 内容长度: {len(text_content)}")
                elif input_type == 'text':
                    text_content = text_input if text_input else "用户未提供文本内容"
                    if not title or title == '未知':
                        title = "当前页面扫描"
                    print(f"[检测] 文本输入模式")
                    print(f"[检测] URL: {url}")
                    print(f"[检测] 标题: {title}")
                    print(f"[检测] 内容长度: {len(text_content)}")
                    print(f"[检测] 图片: {'有' if image_base64 else '无'}")
                else:
                    text_content = "无内容"
                    title = "未知"
                
                rag_knowledge = get_rag_knowledge(url or text_content[:200])
                rag_section = ""
                if rag_knowledge:
                    rag_section = f"""
【RAG知识库参考】
{rag_knowledge[:500]}
"""
                    print(f"[检测] RAG知识库已启用")
                
                prompt = f"""
你是一个中文网络安全专家，请用中文分析以下网站并给出风险评分。

【重要提示】你的所有回复必须使用中文！不要使用英文！

【URL】
{url if url else '当前页面扫描模式'}

【网页标题】
{title}

【网页文本内容】
{text_content}
{rag_section}
请严格按照以下格式输出（分数范围0-100，0表示完全安全，100表示极度危险）：
URL_Score: [数字分数]
Text_Score: [数字分数]
Image_Score: [数字分数]
Reason:
- URL风险分析：[用中文详细分析URL结构、域名是否可疑、是否使用HTTPS等]
- 文本风险分析：[用中文详细分析网页内容是否包含欺诈信息、敏感词等]
- 图像风险分析：[用中文分析网页截图是否存在可疑元素、虚假内容、钓鱼界面等]
- 综合判断：[用中文总结风险等级和建议]

再次提醒：所有分析内容必须使用中文！
"""
                
                print(f"[检测] 使用模型: {model_name}")
                print(f"[检测] Prompt 长度: {len(prompt)}")
                print(f"[检测] 图片数据: {'有(' + str(len(image_base64)) + '字符)' if image_base64 else '无'}")
                
                api_response = call_model_api(prompt, image_base64, model_name)
                
                print(f"[检测] API 响应: {api_response.status_code}")
                
                if api_response.status_code == 200:
                    result = api_response.json()
                    content = result["choices"][0]["message"]["content"]
                    print(f"[检测] 模型返回:\n{content}")
                    
                    url_score_match = re.search(r"URL_Score:\s*(\d+)", content)
                    text_score_match = re.search(r"Text_Score:\s*(\d+)", content)
                    image_score_match = re.search(r"Image_Score:\s*(\d+)", content)
                    reason_match = re.search(r"Reason:\s*([\s\S]*)", content)
                    
                    url_score = int(url_score_match.group(1)) if url_score_match else 50
                    text_score = int(text_score_match.group(1)) if text_score_match else 50
                    image_score = int(image_score_match.group(1)) if image_score_match else 50
                    reason = reason_match.group(1).strip() if reason_match else "模型未提供详细分析理由。"
                    
                    final_score = (url_score + text_score + image_score) / 3
                    
                    risk_level = "Safe"
                    if final_score >= 70:
                        risk_level = "High Risk"
                    elif final_score >= 40:
                        risk_level = "Medium Risk"
                    
                    response_data = {
                        "checked_urls": [url] if url else [],
                        "final_score": round(final_score, 1),
                        "image_analysis": {"score": image_score},
                        "rag_knowledge": rag_knowledge[:500] if rag_knowledge else "",
                        "reason": reason,
                        "risk_level": risk_level,
                        "text_analysis": {"score": text_score},
                        "url_analysis": {"score": url_score},
                        "model": model_name
                    }
                else:
                    response_data = {"error": f"API 调用失败: {api_response.status_code}", "details": api_response.text}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                print(f"[检测] 响应已发送")
                print(f"{'='*50}\n")
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            print(f"[检测] 错误: {e}")
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/models':
            models_list = [
                {"id": k, "name": v["name"], "api": v["api"]} 
                for k, v in SUPPORTED_MODELS.items()
            ]
            response_data = {"models": models_list}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _detect_single_url(self, url, model_name='glm-4v-flash'):
        text_content, title, method = fetch_webpage_content(url, use_selenium=False)
        
        rag_knowledge = get_rag_knowledge(url)
        rag_section = ""
        if rag_knowledge:
            rag_section = f"""
【RAG知识库参考】
{rag_knowledge[:300]}
"""
        
        prompt = f"""
你是一个中文网络安全专家，请用中文分析以下网站并给出风险评分。

【重要提示】你的所有回复必须使用中文！不要使用英文！

【URL】
{url}

【网页标题】
{title}

【网页文本内容】
{text_content[:2000]}
{rag_section}
请严格按照以下格式输出（分数范围0-100，0表示完全安全，100表示极度危险）：
URL_Score: [数字分数]
Text_Score: [数字分数]
Image_Score: [数字分数]
Reason: [用中文简要说明风险判断依据]

再次提醒：所有分析内容必须使用中文！
"""
        
        api_response = call_model_api(prompt, None, model_name)
        
        if api_response.status_code == 200:
            result = api_response.json()
            content = result["choices"][0]["message"]["content"]
            
            url_score_match = re.search(r"URL_Score:\s*(\d+)", content)
            text_score_match = re.search(r"Text_Score:\s*(\d+)", content)
            image_score_match = re.search(r"Image_Score:\s*(\d+)", content)
            reason_match = re.search(r"Reason:\s*([\s\S]*)", content)
            
            url_score = int(url_score_match.group(1)) if url_score_match else 50
            text_score = int(text_score_match.group(1)) if text_score_match else 50
            image_score = int(image_score_match.group(1)) if image_score_match else 50
            reason = reason_match.group(1).strip() if reason_match else "模型未提供详细分析"
            
            final_score = (url_score + text_score + image_score) / 3
            
            if final_score <= 20:
                risk_level = "安全"
            elif final_score <= 40:
                risk_level = "低风险"
            elif final_score <= 60:
                risk_level = "中风险"
            elif final_score <= 80:
                risk_level = "高风险"
            else:
                risk_level = "危险"
            
            return {
                "final_score": round(final_score, 1),
                "risk_level": risk_level,
                "url_analysis": {"score": url_score},
                "text_analysis": {"score": text_score},
                "image_analysis": {"score": image_score},
                "reason": reason[:200],
                "rag_knowledge": rag_knowledge[:300] if rag_knowledge else "",
                "model": model_name
            }
        else:
            return {
                "final_score": 0,
                "risk_level": "错误",
                "error": f"API调用失败: {api_response.status_code}"
            }
    
    def log_message(self, format, *args):
        pass

class ReuseAddrServer(socketserver.TCPServer):
    allow_reuse_address = True

try:
    server = ReuseAddrServer(("", PORT), Handler)
    print(f"服务器正在运行...")
    server.serve_forever()
except Exception as e:
    print(f"服务器错误: {e}")
    traceback.print_exc()