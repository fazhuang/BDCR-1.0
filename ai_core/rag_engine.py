import json
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

# 加载环境变量 (API Key)
load_dotenv()

# 模拟的检索数据库（未来替换为 Pinecone 等向量数据库查询引擎）
# 在 Stage 3 中，我们依然保留这个 Mock 知识库，但将其作为上下文注入到真实 LLM 中
MOCK_KNOWLEDGE_BASE = {
    "法规": "《中华人民共和国招标投标法》第十八条：招标人不得以不合理的条件限制或者排斥潜在投标人。",
    "规范": "《内部招标文件编制规范》V2.1：所有涉及金额必须准确无歧义，不能前后矛盾；禁止指定特定品牌。"
}

def analyze_document_with_ai(document_text: str) -> dict:
    """
    接收抽取的文档文本，调用 Google Gemini LLM 返回审查结果。
    """
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or "YOUR_DEEPSEEK_API_KEY" in api_key:
        return {
            "status": "warning",
            "message": "未检测到有效的 DEEPSEEK_API_KEY，请在 .env 文件中配置。当前返回 Mock 数据。",
            "合规性风险": [{"描述": "请配置 DeepSeek API KEY 以启用真实 AI 审查", "建议": "访问 https://platform.deepseek.com/ 获取"}]
        }

    # 1. 定义大模型 (DeepSeek-Chat 兼容 OpenAI 接口)
    try:
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model="deepseek-chat",
            temperature=0.1
        )
        
        # 2. 定义提示词模板
        prompt_template = PromptTemplate(
            input_variables=["regulations", "norms", "document"],
            template=(
                "你现在是资深招标代理专家。请根据提供的法律法规：\n{regulations}\n\n"
                "以及公司内部规范：\n{norms}\n\n"
                "严格对照审查以下招标文件内容：\n{document}\n\n"
                "你的任务是找出：\n"
                "1. 合规性风险（如排他性条款、不合理资格要求、违反招标投标法等）；\n"
                "2. 逻辑错误（如前后时间矛盾、金额单位不一致、评分标准不严谨等）；\n"
                "3. 核心信息提取（如项目预算、关键时间节点）。\n\n"
                "请以纯 JSON 格式返回结果，包含 '合规性风险'、'逻辑错误'、'核心信息' 三个列表。"
                "每个列表项包含 '描述' 和 '建议' 两个字段。"
            )
        )
        
        # 3. 组合链条
        chain = prompt_template | llm | JsonOutputParser()
        
        # 4. 执行推理 (由于招标文件可能很长，目前仅截取前 3000 字符，未来可扩展为分段处理)
        response = chain.invoke({
            "regulations": MOCK_KNOWLEDGE_BASE["法规"],
            "norms": MOCK_KNOWLEDGE_BASE["规范"],
            "document": document_text[:3000] 
        })
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "error_detail": str(e),
            "message": "AI 调用过程中发生错误，请检查 API Key 或网络连接。"
        }
