"""
测试截图采集脚本
用于采集真实网站截图作为测试样本
"""
import os
import base64
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "test_data", "screenshots")

NORMAL_SITES = [
    {"url": "https://www.baidu.com", "name": "baidu", "description": "百度搜索"},
    {"url": "https://www.taobao.com", "name": "taobao", "description": "淘宝电商"},
    {"url": "https://www.jd.com", "name": "jd", "description": "京东电商"},
    {"url": "https://www.bilibili.com", "name": "bilibili", "description": "B站视频"},
    {"url": "https://www.zhihu.com", "name": "zhihu", "description": "知乎问答"},
    {"url": "https://www.github.com", "name": "github", "description": "GitHub"},
    {"url": "https://www.csdn.net", "name": "csdn", "description": "CSDN技术社区"},
    {"url": "https://www.sina.com.cn", "name": "sina", "description": "新浪门户"},
]

PHISHING_DEMO_SITES = [
    {"url": "https://www.phishtank.com", "name": "phishtank", "description": "PhishTank钓鱼网站数据库"},
]

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1280,800")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def capture_screenshot(driver, url, save_path):
    try:
        print(f"正在访问: {url}")
        driver.get(url)
        time.sleep(3)
        
        driver.save_screenshot(save_path)
        print(f"截图已保存: {save_path}")
        
        with open(save_path, "rb") as f:
            image_data = f.read()
        
        base64_data = base64.b64encode(image_data).decode("utf-8")
        
        return {
            "success": True,
            "base64": base64_data,
            "size": len(image_data)
        }
    except Exception as e:
        print(f"截图失败: {e}")
        return {"success": False, "error": str(e)}

def main():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(SCREENSHOTS_DIR, "normal"), exist_ok=True)
    os.makedirs(os.path.join(SCREENSHOTS_DIR, "malicious"), exist_ok=True)
    
    print("=" * 50)
    print("测试截图采集工具")
    print("=" * 50)
    
    driver = None
    try:
        print("\n初始化浏览器...")
        driver = init_driver()
        
        results = {"normal": [], "malicious": []}
        
        print("\n[1/2] 采集正常网站截图...")
        for site in NORMAL_SITES:
            save_path = os.path.join(SCREENSHOTS_DIR, "normal", f"{site['name']}.png")
            result = capture_screenshot(driver, site["url"], save_path)
            
            if result["success"]:
                results["normal"].append({
                    "id": f"img_normal_{site['name']}",
                    "name": site["name"],
                    "url": site["url"],
                    "description": site["description"],
                    "expected": "safe",
                    "screenshot_path": save_path,
                    "base64_length": len(result["base64"])
                })
            
            time.sleep(1)
        
        print("\n[2/2] 采集钓鱼网站数据库截图...")
        for site in PHISHING_DEMO_SITES:
            save_path = os.path.join(SCREENSHOTS_DIR, "malicious", f"{site['name']}.png")
            result = capture_screenshot(driver, site["url"], save_path)
            
            if result["success"]:
                results["malicious"].append({
                    "id": f"img_malicious_{site['name']}",
                    "name": site["name"],
                    "url": site["url"],
                    "description": site["description"],
                    "expected": "malicious",
                    "screenshot_path": save_path,
                    "base64_length": len(result["base64"])
                })
        
        print("\n" + "=" * 50)
        print("采集完成！")
        print(f"正常网站截图: {len(results['normal'])} 个")
        print(f"恶意网站截图: {len(results['malicious'])} 个")
        print(f"保存位置: {SCREENSHOTS_DIR}")
        print("=" * 50)
        
        import json
        results_file = os.path.join(SCREENSHOTS_DIR, "screenshot_info.json")
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n截图信息已保存到: {results_file}")
        
    except Exception as e:
        print(f"\n错误: {e}")
    finally:
        if driver:
            driver.quit()
            print("\n浏览器已关闭")

if __name__ == "__main__":
    main()
