"""W1 minimal app: patent publication number -> plain-language explanation."""
import os

import streamlit as st
from dotenv import load_dotenv

from patent_core import (
    fetch_patent, generate_explanation, normalize_patent_id, to_markdown,
)

load_dotenv()
st.set_page_config(page_title="AI 专利解读助手 · W1", page_icon="📄", layout="centered")
st.title("📄 AI 专利解读助手")
st.caption("W1 热身 · 输入专利号 → 自动读取原文 → AI 用中文解释")

st.info("本工具只解读已有专利，**不判断**新颖性、是否值得申请或是否侵权。")
with st.sidebar:
    st.header("DeepSeek 模型设置")
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=os.getenv("DEEPSEEK_API_KEY", ""),
        help="也可以把 DEEPSEEK_API_KEY 写入本地 .env 文件。",
    )
    model = st.text_input("模型名称", value=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"))
    st.caption("本地演示无需单独开发后端。模型调用通常会产生 API 费用。")

patent_input = st.text_input(
    "专利公开号 / Google Patents 链接",
    value="US7654321B2",
    help="例：US7654321B2、CN112345678A，或对应 Google Patents 链接。",
)

if st.button("开始分析", type="primary"):
    try:
        patent_id = normalize_patent_id(patent_input)
        with st.spinner("正在获取并检查专利文本..."):
            record = fetch_patent(patent_id)
        st.session_state["record"] = record
        st.session_state["explanation"] = ""
        if api_key:
            with st.spinner("正在生成 AI 解读..."):
                st.session_state["explanation"] = generate_explanation(record, api_key, model)
        else:
            st.warning("已成功提取专利信息。填写侧栏 DeepSeek API Key 后，重新点击“开始分析”生成中文解读。")
    except Exception as error:
        st.error(f"分析失败：{error}")
        st.session_state.pop("record", None)
        st.session_state.pop("explanation", None)

record = st.session_state.get("record")
if record:
    st.divider()
    st.subheader(record.title)
    st.caption(f"公开/公告号：{record.patent_id}")
    st.link_button("查看 Google Patents 原文", record.source_url)
    explanation = st.session_state.get("explanation", "")
    if explanation:
        st.markdown(explanation)
    with st.expander("核对原始摘要与权利要求", expanded=not bool(explanation)):
        st.markdown("**摘要**")
        st.write(record.abstract)
        st.markdown("**第一项权利要求**")
        st.write(record.first_claim or "无法自动提取。请查看原文；不能据此推断权利要求内容。")
    if explanation:
        st.download_button(
            "下载 Markdown 解读报告",
            data=to_markdown(record, explanation),
            file_name=f"{record.patent_id}_explanation.md",
            mime="text/markdown",
        )
