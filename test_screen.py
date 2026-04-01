import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing screenshot function...")

try:
    from backend.feature_extractor.image_features import extract_image_features
    result = extract_image_features('https://www.baidu.com')
    length = len(result.get('image_base64', ''))
    print(f"Screenshot length: {length}")
    if length > 100:
        print("SUCCESS: Screenshot works!")
    else:
        print("FAILED: Screenshot is empty")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

input("Press Enter to exit...")
