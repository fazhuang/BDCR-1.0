import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000/api/v1/review_document"

st.set_page_config(page_title="AI 智能招标文件审查系统", layout="wide")

st.title("🤖 智能审查大脑 - 招标文件自动诊断")
st.markdown("通过大语言模型深度理解和 RAG 技术，一键识别标书中的**合规性风险**与**前后逻辑冲突**。")

# --- 侧边栏系统执行架构可视化 ---
with st.sidebar:
    st.header("⚙️ 引擎流转状态")
    st.info("✓ 建立文档上传通道")
    st.info("✓ FastAPI 异步解析调度")
    st.info("✓ RAG 本地知识检索回溯")
    st.info("✓ LLM 大模型长文本推理")

# --- 主体操作区 ---
uploaded_file = st.file_uploader("请上传待审查的招标文件 (支持 PDF / Word / TXT 格式)", type=["pdf", "docx", "txt", "doc"])

if uploaded_file is not None:
    st.success(f"文件加载就绪：{uploaded_file.name}")
    
    if st.button("🚀 开始 AI 智能审查"):
        # UI：使用 st.status 显示实时解析状态
        with st.status(">> 正在启动 AI 审查引擎...", expanded=True) as status:
            st.write(">> 阶段 1：正在上传文件并解析非结构化数据...")
            
            # 将文件封装并通过 POST 请求发送到本地测试的 FastAPI 后端
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            
            st.write(">> 阶段 2：大模型正在进行语义理解与合规推断 (这可能需要一些时间，请耐心等待)...")
            
            try:
                # 发送请求到后端
                response = requests.post(BACKEND_URL, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    status.update(label="审查完毕，成功生成结构化报告。", state="complete", expanded=False)
                    
                    report = data.get("review_report", {})
                    
                    # --- 审查报告结果可视化 ---
                    st.divider()
                    st.subheader(f"📊 【{uploaded_file.name}】自动审查诊断报告", divider="red")
                    
                    # 使用 Tabs 优化分类展示
                    tab1, tab2, tab3 = st.tabs(["🔴 合规风险", "🟡 逻辑异常", "🔵 核心提取信息"])
                    
                    with tab1:
                        # 1. 危险级别 (合规性风险)
                        risks = report.get("合规性风险", [])
                        if risks:
                            st.error(f"AI 识别出 **{len(risks)}** 个合规性风险点（**触及红线，必须整改**）")
                            for idx, risk in enumerate(risks):
                                with st.expander(f"⚠️ 风险 {idx+1}: {risk.get('描述', '未知')}", expanded=True):
                                    st.markdown(f"**⚡ AI 修复建议**：\n{risk.get('建议', '无')}")
                        else:
                            st.success("✅ 未发现明显的合规性风险。")
    
                    with tab2:
                        # 2. 警告级别 (逻辑错误)
                        logics = report.get("逻辑错误", [])
                        if logics:
                            st.warning(f"AI 识别出 **{len(logics)}** 处前后逻辑或数据自相矛盾")
                            for idx, logic in enumerate(logics):
                                with st.expander(f"📌 异常 {idx+1}: {logic.get('描述', '未知')}", expanded=True):
                                    st.markdown(f"**⚡ AI 修复建议**：\n{logic.get('建议', '无')}")
                        else:
                            st.success("✅ 未发现明显的逻辑矛盾。")
                                    
                    with tab3:
                        # 3. 提示级别 (核心信息提取)
                        infos = report.get("核心信息", [])
                        if infos:
                            st.info(f"AI 提取了以下关键项目要素：")
                            for idx, info in enumerate(infos):
                                st.markdown(f"- **{info.get('描述', '未知')}**：{info.get('建议', '')}")
                        else:
                            st.info("暂未提取到具体的要素记录。")
                            
                    # 给开发者提供的原始 JSON Payload 展示
                    st.divider()
                    with st.expander("开发者模式：查看服务端返回的完整 JSON 原始结构"):
                        st.json(report)
                else:
                    status.update(label="审查失败，接口调用异常", state="error", expanded=True)
                    st.error(f"调用后端 API 失败！错误状态码：{response.status_code}")
                    st.write(response.text)
                    
            except requests.exceptions.ConnectionError:
                status.update(label="审查失败，网络连接异常", state="error", expanded=True)
                st.error("🚨 无法连接到后端的审查 API 服务！")
                st.warning("请确保已经在终端运行了后端程序：`uvicorn backend.main:app --reload`")
