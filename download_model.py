"""
下载嵌入模型到本地，一劳永逸
运行此脚本后，RAG知识库将使用本地模型，无需每次联网下载
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LOCAL_MODEL_PATH = os.path.join(MODELS_DIR, "all-MiniLM-L6-v2")

def download_model():
    print("=" * 60)
    print("RAG嵌入模型下载工具")
    print("=" * 60)
    print(f"\n模型名称: {MODEL_NAME}")
    print(f"本地路径: {LOCAL_MODEL_PATH}")
    print(f"模型大小: 约 90MB")
    
    if os.path.exists(LOCAL_MODEL_PATH):
        print(f"\n本地模型已存在: {LOCAL_MODEL_PATH}")
        print("如需重新下载，请先删除该目录")
        return True
    
    print("\n[1/3] 创建模型目录...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    print(f"  ✓ 模型目录: {MODELS_DIR}")
    
    print("\n[2/3] 下载模型文件...")
    print("  提示: 首次下载需要几分钟，请耐心等待...")
    print("  如果下载缓慢，请确保网络能访问 HuggingFace")
    print("  或设置代理: set HTTP_PROXY=http://your-proxy:port")
    
    try:
        from huggingface_hub import snapshot_download
        
        print(f"\n  正在从 HuggingFace 下载 {MODEL_NAME}...")
        local_path = snapshot_download(
            repo_id=MODEL_NAME,
            local_dir=LOCAL_MODEL_PATH,
            local_dir_use_symlinks=False
        )
        print(f"  ✓ 模型已下载到: {local_path}")
        
    except Exception as e:
        print(f"  ✗ 下载失败: {e}")
        print("\n备选方案: 使用国内镜像")
        print("  请在命令行运行:")
        print(f"  $env:HF_ENDPOINT='https://hf-mirror.com'")
        print(f"  python {os.path.basename(__file__)}")
        return False
    
    print("\n[3/3] 验证模型...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(LOCAL_MODEL_PATH)
        test_embedding = model.encode("测试")
        print(f"  ✓ 模型验证成功，嵌入维度: {len(test_embedding)}")
    except Exception as e:
        print(f"  ✗ 模型验证失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 模型下载完成！")
    print("=" * 60)
    print("\n现在RAG知识库将使用本地模型，无需联网下载")
    print("重启服务即可生效")
    
    return True

if __name__ == "__main__":
    download_model()
