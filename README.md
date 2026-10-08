# AI 专利解读助手 · W1 热身工具

目标：输入专利公开号，自动提取 Google Patents 页面中的**标题、摘要和第一项权利要求**，可选通过 DeepSeek API 生成中文通俗解释，并导出报告。

**范围：只做“已有专利内容的技术解读”。不是专利新颖性、创造性、FTO 或侵权判断。**

## 运行环境

- Python 3.10 或更新版本
- 能访问 https://patents.google.com 的网络
- 若要自动生成中文解释：有效的 [DeepSeek API Key](https://platform.deepseek.com/) 和可用额度（API 按用量计费）

## Windows 最短启动方法

1. 解压整个文件夹，例如到桌面 `patent_explainer_w1`。
2. 在该文件夹地址栏输入 `cmd` 后回车，打开命令提示符。
3. 输入：

   ```powershell
   py -m pip install -r requirements.txt
   py -m streamlit run app.py
   ```

4. 浏览器通常会自动打开 http://localhost:8501 。
5. 在左侧输入 DeepSeek API Key，输入完整专利公开号，例如 `US7654321B2`，点击“开始分析”。
6. 查看原文、AI 解释，下载 `.md` 文件。

如 `py` 不可用，把上述 `py` 改为 `python`。首次安装依赖需要网络。停止服务：终端中按 Ctrl+C。

## API Key 的安全保存方式（可选）

复制 `.env.example` 为 `.env`，填写 `DEEPSEEK_API_KEY`。默认模型为 `deepseek-flash`，需要时可通过 `DEEPSEEK_MODEL` 或左侧输入框更改。**不要**把 `.env` 上传到 GitHub 或分享给他人。也可以只在本地运行时，在 Streamlit 左侧密码框输入 API Key。

模型调用使用 DeepSeek 的 `https://api.deepseek.com` 地址和 Chat Completions 接口。DeepSeek 兼容 OpenAI 格式，因此依赖列表中的 `openai` 是客户端 SDK，实际请求会发送到 DeepSeek。默认关闭思考模式，以便快速生成简洁解读。[DeepSeek 官方接入文档](https://api-docs.deepseek.com/guides/codex)

## 工具如何运行

`patent_core.py` 负责：

1. `normalize_patent_id`：检查并标准化公开号/链接
2. `fetch_patent`：请求对应 Google Patents HTML 页面
3. `extract_patent`：尝试提取标题、摘要、第一项权利要求
4. `generate_explanation`：给 AI 明确的技术解读规则，要求标明依据
5. `to_markdown`：导出报告及原文

`app.py` 是本地 Streamlit 网页界面。这个本地服务包括 Python 执行逻辑，但不需要独立前后端工程、数据库、部署或多 Agent。

## 局限与注意

- Google Patents 是公开网页；**本演示通过 HTML 读取页面，不依赖 Google 官方稳定的专利 REST API**。网页结构、网络限制、流量限制或地域访问问题都可能导致失败。
- 只抓取**第一项权利要求**，不保证足以理解完整法律保护范围。第一项不一定代表全部独立权利要求。
- 模型的逐条解释可能有误，必须回看原文。发现缺失字段就应标记为“未取得”，不能用模型补造。
- 页面某些字段（例如法律状态）可能过时，本工具不会就此做法律判断。
- 访问公开页面时应遵守网站条款，控制访问频率；如果要升级成稳定产品，应考虑许可数据源、官方数据、缓存与速率限制。
- 请不要将未公开、敏感的发明材料上传到外部模型，除非已经核实组织的数据安全规则。

## W1 交付建议

- 现场演示输入一个已验证可读取的专利号。
- 展示原文与 AI 的文字解读并排核对。
- 记录一处局限，比如某些专利号无法获取权利要求，说明失败时程序如何处理。
- 提交程序压缩包 + 下载的报告 + 简短开题说明。

## W2 如何扩展

W2 再做“输入一个技术想法 → 拆解技术特征 → 检索候选专利 → 逐要素比对”。**没有充分证据时，应输出‘证据不足’，不要武断输出‘可申请’或‘不侵权’。**
