import re

def parse_model_output(text):

    url_score_match = re.search(r"URL_Score:\s*(\d+)", text)
    text_score_match = re.search(r"Text_Score:\s*(\d+)", text)
    image_score_match = re.search(r"Image_Score:\s*(\d+)", text)

    url_score = int(url_score_match.group(1)) if url_score_match else 50
    text_score = int(text_score_match.group(1)) if text_score_match else 50
    image_score = int(image_score_match.group(1)) if image_score_match else 50

    return url_score, text_score, image_score