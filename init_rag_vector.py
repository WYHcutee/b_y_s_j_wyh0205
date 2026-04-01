"""
初始化RAG知识库向量存储
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def init_vector_store():
    print("=" * 50)
    print("RAG知识库向量存储初始化")
    print("=" * 50)

    knowledge_base_path = os.path.join(PROJECT_ROOT, "knowledge_base")
    documents_path = os.path.join(knowledge_base_path, "documents")
    index_path = os.path.join(knowledge_base_path, "faiss_index")

    # 转换为 Path 对象，便于处理
    index_path = Path(index_path).resolve()

    print(f"\n知识库路径: {knowledge_base_path}")
    print(f"文档路径: {documents_path}")
    print(f"索引路径: {index_path}")

    if not os.path.exists(documents_path):
        os.makedirs(documents_path)
        print(f"\n创建文档目录: {documents_path}")

    print("\n[1/4] 检查依赖...")
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        print("  ✓ 所有依赖已安装")
    except ImportError as e:
        print(f"  ✗ 依赖缺失: {e}")
        print("\n请运行以下命令安装依赖:")
        print("  pip install langchain-community langchain-huggingface faiss-cpu sentence-transformers")
        return False

    print("\n[2/4] 加载嵌入模型...")

    local_model_path = os.path.join(PROJECT_ROOT, "models", "all-MiniLM-L6-v2")

    if os.path.exists(local_model_path):
        print(f"  使用本地模型: {local_model_path}")
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name=local_model_path,
                model_kwargs={'local_files_only': True}
            )
            print("  ✓ 本地嵌入模型加载成功")
        except Exception as e:
            print(f"  ✗ 本地模型加载失败: {e}")
            return False
    else:
        print("  (首次加载需要从HuggingFace下载模型，请耐心等待...)")
        print("  提示: 运行 python download_model.py 可提前下载模型到本地")
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'local_files_only': False}
            )
            print("  ✓ 嵌入模型加载成功")
        except Exception as e:
            print(f"  ✗ 嵌入模型加载失败: {e}")
            print("\n可能的解决方案:")
            print("  1. 检查网络连接，确保能访问 HuggingFace")
            print("  2. 设置代理: set HTTP_PROXY=http://your-proxy:port")
            print("  3. 使用国内镜像: set HF_ENDPOINT=https://hf-mirror.com")
            print("  4. 运行 python download_model.py 提前下载模型")
            return False

    print("\n[3/4] 加载知识文档...")
    import glob
    documents = []
    txt_files = glob.glob(os.path.join(documents_path, "*.txt"))

    if not txt_files:
        print("  ! 文档目录为空，创建示例文档...")
        sample_content = """网络安全基础知识

1. 钓鱼网站特征
- 域名仿冒：使用与正规网站相似的域名
- 缺少HTTPS：正规网站通常使用HTTPS加密
- 界面仿冒：模仿知名网站的登录界面

2. 恶意网站识别
- 检查域名是否正确
- 查看是否有HTTPS安全证书
- 不点击来源不明的链接
"""
        sample_file = os.path.join(documents_path, "sample_knowledge.txt")
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        txt_files = [sample_file]
        print(f"  创建示例文档: sample_knowledge.txt")

    for file_path in txt_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if content.strip():
                documents.append(content)
                print(f"  ✓ 加载: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  ✗ 加载失败 {os.path.basename(file_path)}: {e}")

    if not documents:
        documents = ["网络安全知识库初始化"]
        print("  ! 没有有效文档，使用默认内容")

    print(f"\n  共加载 {len(documents)} 个文档")

    print("\n[4/4] 创建向量索引...")
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        all_texts = []
        for doc in documents:
            chunks = text_splitter.split_text(doc)
            all_texts.extend(chunks)

        print(f"  文档分割为 {len(all_texts)} 个文本块")

        # 检查索引文件是否存在（而不是仅检查文件夹）
        index_file = index_path / "index.faiss"
        if index_file.exists():
            try:
                vector_store = FAISS.load_local(
                    str(index_path),
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                print("  已加载现有索引，正在添加新文档...")
                vector_store.add_texts(all_texts)
            except Exception as e:
                print(f"  加载现有索引失败，将重新创建: {e}")
                vector_store = FAISS.from_texts(all_texts, embeddings)
        else:
            print("  未找到现有索引文件，正在创建新索引...")
            vector_store = FAISS.from_texts(all_texts, embeddings)

        # 确保索引目录存在，并检查权限
        try:
            index_path.mkdir(parents=True, exist_ok=True)
            print(f"  索引目录已确保存在: {index_path}")
        except Exception as e:
            print(f"  ✗ 无法创建索引目录: {e}")
            return False

        # 保存前再次检查目录可写性
        if not index_path.exists():
            print(f"  ✗ 索引目录不存在，请检查路径和权限")
            return False

        # 尝试写入测试文件检查权限
        test_file = index_path / "test_write.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print("  目录可写权限正常")
        except Exception as e:
            print(f"  ✗ 目录没有写入权限: {e}")
            return False

        # 保存索引
        vector_store.save_local(str(index_path))
        print(f"  ✓ 向量索引已保存到: {index_path}")

    except Exception as e:
        print(f"  ✗ 创建向量索引失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 50)
    print("✓ RAG知识库初始化完成！")
    print("=" * 50)
    return True


if __name__ == "__main__":
    init_vector_store()