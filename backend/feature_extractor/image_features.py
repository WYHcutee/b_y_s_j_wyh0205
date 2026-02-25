import base64
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)


def extract_image_features(url):
    """
    使用 Selenium + 本地 Chrome 截取网页全屏截图，返回 base64 编码的图片
    """
    image_base64 = ""
    driver = None
    try:
        # 配置 Chrome 无头模式
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式（不显示浏览器窗口）
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        driver_path = r"F:\1111AAA毕业设计\基于多模态大模型的恶意网站检测系统\drivers\chromedriver.exe"
        service = Service(executable_path=driver_path)

        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)  # 增加到30秒
        driver.implicitly_wait(10)  # 隐式等待10秒，定位元素时也等待

        screenshot_bytes = driver.get_screenshot_as_png()
        image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        logger.info(f"Selenium 截图成功，base64 长度: {len(image_base64)}")

    except Exception as e:
        logger.error(f"Selenium 截图失败: {e}")
        image_base64 = ""  # 失败时返回空字符串，上层会走 mock 数据
    finally:
        if driver:
            driver.quit()

    return {"image_base64": image_base64}