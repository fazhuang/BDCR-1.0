import sys
import os
import io
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from docx import Document
import time

# 将根目录加入路径以方便导入 ai_core 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ai_core.rag_engine import analyze_document_with_ai
except ImportError:
    pass

app = FastAPI(title="AI 招标文件审查 API", version="1.0.0")

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """从不同格式的文件中提取文本"""
    text = ""
    file_extension = filename.split('.')[-1].lower()
    
    try:
        if file_extension == 'pdf':
            reader = PdfReader(io.BytesIO(file_content))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif file_extension in ['docx', 'doc']:
            doc = Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            # 尝试作为纯文本读取
            text = file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")
    
    return text.strip()

@app.post("/api/v1/review_document")
async def review_document(file: UploadFile = File(...)):
    """
    接收前端上传的文档（PDF/Word等），提取文本并调用 AI RAG 引擎进行审查。
    """
    # 1. 读取文件内容
    content = await file.read()
    
    # 2. 真实的文件文本解析
    extracted_text = extract_text_from_file(content, file.filename)
    
    if not extracted_text:
        return {"error": "无法从文件中提取有效文本内容", "status": "failed"}
    
    # 3. 核心审查逻辑：交给基于 LangChain 的 AI 引擎处理
    try:
        from ai_core.rag_engine import analyze_document_with_ai
        review_result = analyze_document_with_ai(extracted_text)
    except Exception as e:
        review_result = {"error": str(e), "status": "failed"}

    # 4. 返回标准化的 JSON 完整审查报告给前端
    return {
        "filename": file.filename,
        "extracted_snippet": extracted_text[:200] + "...",
        "review_report": review_result
    }

# 本地调试运行指令: uvicorn backend.main:app --reload
