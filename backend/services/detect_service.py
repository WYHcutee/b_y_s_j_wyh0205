from backend.feature_extractor.url_features import extract_url_features
from backend.feature_extractor.text_features import extract_text_features
from backend.feature_extractor.image_features import extract_image_features
from backend.fusion.prompt_builder import build_multimodal_prompt
from backend.fusion.model_inference import call_multimodal_model
from backend.fusion.result_parser import parse_model_output
from backend.fusion.fusion_engine import weighted_fusion
from backend.risk.risk_classifier import classify_risk
from backend.utils.crawler import crawl_links
from backend.fusion.rag_engine import get_knowledge_status
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

def detect_website(input_type='url', url=None, text_content=None, image_base64=None, model_name='glm-4v-flash'):
    """
    统一检测入口，支持URL、文本、图片三种输入
    优化：并行处理截图、文本提取、图片提取
    """
    start_time = time.time()
    try:
        checked_urls = []
        
        if input_type == 'url':
            logger.info(f"开始检测 URL: {url}")
            
            url_features = extract_url_features(url)
            logger.info("URL 特征提取完成")
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                text_future = executor.submit(extract_text_features, url)
                image_future = executor.submit(extract_image_features, url)
                
                text_data = text_future.result()
                logger.info(f"文本特征提取完成 ({time.time()-start_time:.1f}秒)")
                
                image_data = image_future.result()
                img_b64 = image_data.get("image_base64")
                page_images = image_data.get("page_images", [])
                logger.info(f"图像特征提取完成，截图长度: {len(img_b64) if img_b64 else 0}，网页图片: {len(page_images)}张 ({time.time()-start_time:.1f}秒)")
            
            prompt = build_multimodal_prompt(url_features, text_data["text_content"], mode='url', page_images=page_images)
            
            checked_urls = crawl_links(url, depth=1, max_links=3)
            logger.info(f"爬取链接完成，共 {len(checked_urls)} 个 ({time.time()-start_time:.1f}秒)")
            
        elif input_type == 'text':
            logger.info("开始检测文本内容")
            url_features = {"raw_url": "", "domain": "", "path": "", "params": ""}
            
            if image_base64:
                prompt = build_multimodal_prompt(url_features, text_content, mode='text_with_image')
                logger.info("使用文本+图片模式")
            else:
                prompt = build_multimodal_prompt(url_features, text_content, mode='text')
                logger.info("使用纯文本模式")
            img_b64 = image_base64
            page_images = None
            
        elif input_type == 'image':
            logger.info("开始检测图片")
            url_features = {"raw_url": "", "domain": "", "path": "", "params": ""}
            prompt = build_multimodal_prompt(url_features, "", mode='image')
            img_b64 = image_base64
            page_images = None
        else:
            raise ValueError(f"未知输入类型: {input_type}")

        logger.info("正在调用大模型分析...")
        response = call_multimodal_model(prompt, img_b64, model_name=model_name, extra_images=page_images)
        model_text = response["choices"][0]["message"]["content"]
        logger.info(f"大模型返回内容: {model_text[:500]}... ({time.time()-start_time:.1f}秒)")

        url_score, text_score, image_score, reason = parse_model_output(model_text)
        logger.info(f"解析结果 - URL分数: {url_score}, 文本分数: {text_score}, 图片分数: {image_score}")
        logger.info(f"分析详情: {reason[:200]}...")

        if input_type == 'text':
            url_score = 0
            if img_b64:
                reason = "[文本+图片模式]\n" + reason
            else:
                image_score = 0
                reason = "[文本模式]\n" + reason
        elif input_type == 'image':
            url_score = 0
            text_score = 0
            reason = "[图片模式]" + reason

        if input_type == 'url':
            final_score = weighted_fusion(url_score, text_score, image_score)
        elif input_type == 'text':
            final_score = text_score
        elif input_type == 'image':
            final_score = image_score

        risk_level = classify_risk(final_score)
        total_time = time.time() - start_time
        logger.info(f"检测完成，风险等级: {risk_level}，总耗时: {total_time:.1f}秒")

        query_text = f"{url_features.get('raw_url', '')} {text_data.get('text_content', '')[:200] if input_type == 'url' else text_content[:200] if text_content else ''}"
        knowledge_info = get_knowledge_status(query_text)
        logger.info(f"知识库状态: {knowledge_info['status']}, 模式: {knowledge_info['mode']}")

        result = {
            "url_analysis": {"score": url_score},
            "text_analysis": {"score": text_score},
            "image_analysis": {"score": image_score},
            "final_score": final_score,
            "risk_level": risk_level,
            "reason": reason,
            "checked_urls": checked_urls,
            "rag_knowledge": knowledge_info.get("content", ""),
            "rag_status": knowledge_info.get("status", "unknown"),
            "rag_mode": knowledge_info.get("mode", "none"),
            "rag_sources": knowledge_info.get("sources", []),
            "detection_time": f"{total_time:.1f}秒"
        }
        
        if input_type == 'url':
            result["page_text"] = text_data.get("text_content", "")[:2000]
            img_b64 = image_data.get("image_base64", "")
            logger.info(f"网页截图base64长度: {len(img_b64) if img_b64 else 0}")
            result["page_image"] = f"data:image/png;base64,{img_b64}" if img_b64 else ""
            result["page_images"] = [
                {"url": img["url"], "base64": f"data:image/jpeg;base64,{img['base64']}"}
                for img in image_data.get("page_images", [])
            ]
        
        return result

    except Exception as e:
        logger.error(f"检测失败: {e}")
        return {
            "url_analysis": {"score": 0.0},
            "text_analysis": {"score": 0.0},
            "image_analysis": {"score": 0.0},
            "final_score": 0.0,
            "risk_level": "未知",
            "reason": f"检测过程发生错误: {str(e)}",
            "checked_urls": [],
            "rag_knowledge": ""
        }