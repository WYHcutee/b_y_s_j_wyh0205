@echo off
cd /d F:\1111AAA毕业设计\克隆\b_y_s_j_wyh0205
python -c "from backend.feature_extractor.image_features import extract_image_features; r = extract_image_features('https://www.baidu.com'); print('Screenshot length:', len(r.get('image_base64', '')))"
pause
