import base64
import logging
import os
import requests
from io import BytesIO
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

def extract_images_from_page(driver, base_url, max_images=2):
    """
    从网页中提取关键图片（logo、banner等）
    """
    images = []
    try:
        img_elements = driver.find_elements("tag name", "img")
        logger.info(f"找到 {len(img_elements)} 张图片")
        
        for img in img_elements[:max_images]:
            try:
                src = img.get_attribute("src")
                if not src:
                    continue
                
                if src.startswith("data:"):
                    continue
                
                absolute_url = urljoin(base_url, src)
                
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": base_url
                    }
                    response = requests.get(absolute_url, headers=headers, timeout=3)
                    if response.status_code == 200 and len(response.content) > 500:
                        img_base64 = base64.b64encode(response.content).decode('utf-8')
                        images.append({
                            "url": absolute_url,
                            "base64": img_base64,
                            "size": len(response.content)
                        })
                        logger.info(f"提取图片成功: {absolute_url[:50]}...")
                        if len(images) >= max_images:
                            break
                except Exception as e:
                    logger.debug(f"下载图片失败: {e}")
                    
            except Exception as e:
                logger.debug(f"处理图片元素失败: {e}")
                continue
                
    except Exception as e:
        logger.error(f"提取网页图片失败: {e}")
    
    return images

def compress_image(image_bytes, max_size=(800, 600)):
    """
    压缩图片尺寸
    """
    try:
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=70)
        return output.getvalue()
    except Exception as e:
        logger.debug(f"图片压缩失败: {e}")
        return image_bytes

def extract_image_features(url):
    """
    使用 Selenium + 本地 Chrome 截取网页全屏截图，并提取关键图片
    优化：减少超时时间，压缩图片
    """
    image_base64 = ""
    page_images = []
    driver = None
    try:
        logger.info(f"开始截图: {url}")
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.common.exceptions import TimeoutException, WebDriverException
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")

        driver_path = r"F:\1111AAA毕业设计\基于多模态大模型的恶意网站检测系统\drivers\chromedriver.exe"
        
        if not os.path.exists(driver_path):
            logger.error(f"ChromeDriver 不存在: {driver_path}")
            return {"image_base64": "", "page_images": []}
        
        logger.info(f"启动Chrome浏览器...")
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(8)
        driver.implicitly_wait(2)

        logger.info(f"正在访问 URL: {url}")
        driver.get(url)
        
        logger.info(f"正在截图...")
        screenshot_bytes = driver.get_screenshot_as_png()
        screenshot_bytes = compress_image(screenshot_bytes)
        image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        logger.info(f"Selenium 截图成功，base64 长度: {len(image_base64)}")
        
        logger.info(f"正在提取网页内图片...")
        page_images = extract_images_from_page(driver, url, max_images=2)
        logger.info(f"提取到 {len(page_images)} 张网页图片")

    except TimeoutException:
        logger.error(f"页面加载超时: {url}")
        image_base64 = ""
    except WebDriverException as e:
        logger.error(f"WebDriver 错误: {e}")
        image_base64 = ""
    except Exception as e:
        logger.error(f"Selenium 截图失败: {type(e).__name__}: {e}")
        image_base64 = ""
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Chrome浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")

    return {"image_base64": image_base64, "page_images": page_images}