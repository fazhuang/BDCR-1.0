import json
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

# 加载环境变量 (API Key)
load_dotenv()

from ai_core.gansu_rules import GANSU_NEGATIVE_LIST, GENERAL_BIDDING_RULES, HIGH_COMPLAINT_ZONES, E_TRADING_WARNINGS

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
        
        # 2. 升级提示词模板
        prompt_template = PromptTemplate(
            input_variables=["gansu_rules", "general_rules", "high_complaints", "document"],
            template=(
                "你现在是拥有十年以上经验的【甘肃省公共资源交易中心资深评标专家】及【纪检监察审计员】。\n"
                "请严格依照下述的《甘肃省招标投标常见错误与负面清单》：\n{gansu_rules}\n\n"
                "并务必同时开启本系统独有的《甘肃省政府采购高频投诉雷达》进行核心交叉排查：\n{high_complaints}\n\n"
                "以及《招标通用审查基准》：\n{general_rules}\n\n"
                "对以下招标文件全卷内容进行极为严苛的排雷与审查：\n"
                "------------------\n"
                "{document}\n"
                "------------------\n\n"
                "你的任务是深度分析并找出：\n"
                "1. 合规性风险（极高权重）：重点扫除隐性排他（特指量身定制的刁钻技术参数或死尺寸）、违规品牌指定、畸高或带主观黑箱的评分项、中小企业扶持条款缺失、地方奖项加分等引发废标的高频雷区。如果有任何蛛丝马迹，必须严厉重拳指出并要求修改评分表/参数表。\n"
                "2. 逻辑错误：分析履约时间是否太短、违约金是否合理、上下文数据是否前后矛盾等容易被投诉的常规错误。\n"
                "3. 核心信息：提取出预算金额、核心技术与资质限制要求等核心关注点。\n\n"
                "请务必仅返回纯 JSON 格式结果，必须且只能包含 '合规性风险'、'逻辑错误'、'核心信息' 这三个一级列表名称。"
                "列表中的每个对象只包含 '描述' 和 '建议' 两个纯文本字段。若未发现问题，则将对应列表置为空 `[]`。"
            )
        )
        
        # 3. 组合链条
        chain = prompt_template | llm | JsonOutputParser()
        
        # 4. 执行推理 (解除 5000 字符限制，扩大至 80000 字符以覆盖全本核心章节)
        response = chain.invoke({
            "gansu_rules": GANSU_NEGATIVE_LIST,
            "general_rules": GENERAL_BIDDING_RULES,
            "high_complaints": HIGH_COMPLAINT_ZONES,
            "document": document_text[:80000] 
        })
        
        return response
        
    except Exception as e:
        return {
            "status": "error",
            "error_detail": str(e),
            "message": "AI 调用过程中发生错误，请检查 API Key 或网络连接。"
        }

def operation_warning_agent(user_query: str) -> dict:
    """处理甘肃省政府采购电子交易系统实操报错的智能预警客服"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key or "YOUR_DEEPSEEK_API_KEY" in api_key:
        return {"Diagnosis": "API未接通", "Warning": "您的系统还未绑定 AI 核心库", "ActionPlan": "请先前往 .env 配置文件完成 DEEPSEEK_API_KEY 的填写"}
        
    try:
        llm = ChatOpenAI(
            api_key=api_key, base_url="https://api.deepseek.com",
            model="deepseek-chat", temperature=0.3
        )
        prompt_template = PromptTemplate(
            input_variables=["warnings", "query"],
            template=(
                "你现在是【甘肃省公共资源交易政采系统高级排障专家】。\n"
                "用户遇到如下操作问题或报错提示：\"{query}\"\n\n"
                "参考以下绝密的《常见实操排障指南库》：\n{warnings}\n\n"
                "请给出分析。以纯 JSON 返回结果，且必须只包含这三个确切的英文字母键：\n"
                "1. 'Diagnosis': 诊断原因（用专业且直白的话解释到底卡在哪一步了，是什么配置导致了这种现象）。\n"
                "2. 'Warning': 严重后果预警（明确指出如果不马上解决，是否会造成彻底的“实质性废标”或失去竞标资格）。\n"
                "3. 'ActionPlan': 紧急抢救指南（给出分清步骤的处理对策：第1步应该点什么浏览器图标，第2步联系谁等）。"
            )
        )
        chain = prompt_template | llm | JsonOutputParser()
        return chain.invoke({"warnings": E_TRADING_WARNINGS, "query": user_query})
    except Exception as e:
        return {"Diagnosis": "调用大模型通信失败", "Warning": "网络异常", "ActionPlan": f"错误详情: {str(e)}"}
