import os
from backend.fusion.model_inference import call_zhipu_api

# 可选：打印环境变量确认
print("ZHIPU_API_KEY:", os.environ.get("ZHIPU_API_KEY"))

result = call_zhipu_api("简单测试，请输出：URL_Score: 10, Text_Score: 20, Image_Score: 30", "", "glm-4v-flash")
print(result)