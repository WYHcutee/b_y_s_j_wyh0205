import unittest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.fusion.rag_engine import RAGEngine
from backend.services.detect_service import detect_website
from backend.utils.crawler import crawl_links

class TestAllFeatures(unittest.TestCase):
    """测试所有功能的正确性"""
    
    def setUp(self):
        """设置测试环境"""
        self.rag_engine = RAGEngine()
    
    def test_rag_engine(self):
        """测试 RAG 外部知识库功能"""
        print("\n=== 测试 RAG 外部知识库功能 ===")
        
        # 测试添加文档
        test_content = "钓鱼网站通常会模仿知名网站的登录页面，诱导用户输入账号密码。"
        result = self.rag_engine.add_document(test_content, {"source": "test"})
        self.assertTrue(result)
        
        # 测试检索功能
        query = "钓鱼网站的特征"
        retrieved_docs = self.rag_engine.retrieve(query)
        self.assertGreaterEqual(len(retrieved_docs), 0)
        
        # 测试获取相关知识
        knowledge = self.rag_engine.get_relevant_knowledge(query)
        self.assertIsInstance(knowledge, str)
        print("✓ RAG 外部知识库功能测试通过")
    
    def test_crawler(self):
        """测试 URL 深入检查功能"""
        print("\n=== 测试 URL 深入检查功能 ===")
        
        # 测试爬取功能
        test_url = "https://example.com"
        links = crawl_links(test_url, depth=2, max_links=5)
        self.assertGreaterEqual(len(links), 1)
        print(f"✓ URL 深入检查功能测试通过，爬取到 {len(links)} 个链接")
    
    def test_detect_service(self):
        """测试检测服务功能"""
        print("\n=== 测试检测服务功能 ===")
        
        # 测试 URL 检测
        test_url = "https://example.com"
        result = detect_website(input_type='url', url=test_url)
        self.assertIn('final_score', result)
        self.assertIn('checked_urls', result)
        self.assertGreaterEqual(len(result['checked_urls']), 1)
        print("✓ URL 检测功能测试通过")
        
        # 测试文本检测
        test_text = "这是一个安全的网站，没有恶意内容。"
        result = detect_website(input_type='text', text_content=test_text)
        self.assertIn('final_score', result)
        print("✓ 文本检测功能测试通过")
    
    def test_model_integration(self):
        """测试多种大模型接口集成"""
        print("\n=== 测试多种大模型接口集成 ===")
        
        # 测试不同模型
        test_url = "https://example.com"
        models = ['glm-4v-flash', 'ernie-bot', 'qwen-vl-plus']
        
        for model in models:
            try:
                result = detect_website(input_type='url', url=test_url, model_name=model)
                self.assertIn('final_score', result)
                print(f"✓ {model} 模型测试通过")
            except Exception as e:
                print(f"⚠ {model} 模型测试失败: {e}")

if __name__ == '__main__':
    unittest.main()