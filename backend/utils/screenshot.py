# backend/utils/screenshot.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os

def capture_screenshot(url, save_path="screenshot.png"):
    """
    捕获网页截图，优先使用本地 Chrome。
    自动补全 URL 并处理异常。
    """
    # 自动补全 URL
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    # 尝试本地 Chrome 可执行路径
    possible_paths = [
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    ]
    chrome_path = None
    for path in possible_paths:
        if os.path.exists(path):
            chrome_path = path
            break

    try:
        with sync_playwright() as p:
            # 优先本地 Chrome
            if chrome_path:
                browser = p.chromium.launch(executable_path=chrome_path, headless=True)
            else:
                # 回退到 Playwright 自带 Chromium
                browser = p.chromium.launch(headless=True)

            page = browser.new_page()
            try:
                page.goto(url, timeout=15000)  # 15 秒超时
                page.screenshot(path=save_path, full_page=True)
            except PlaywrightTimeoutError:
                print(f"[WARN] 网页访问超时：{url}")
                page.screenshot(path=save_path, full_page=True)  # 截取已加载部分
            finally:
                browser.close()
        return save_path
    except Exception as e:
        print(f"[ERROR] 截图失败: {e}")
        return None