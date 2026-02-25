from backend.utils.crawler import get_page_text

def extract_text_features(url):

    text = get_page_text(url)

    return {
        "text_content": text
    }