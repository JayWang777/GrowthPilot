# AI 商品增长运营助手

一款面向**电商运营岗位求职**的 AI 辅助工具 Demo，展示 **AI + 电商运营** 结合能力。

> **求职方向：** AI 电商运营实习 / AI 产品运营实习 / 大模型应用实习

---

## 功能展示

| 功能 | 说明 | 体现能力 |
|------|------|---------|
| 📊 商品智能分析 | 输入商品信息，AI 输出定位、痛点、卖点排序 | 数据驱动的商品分析思维 |
| ✏️ 标题优化 | 原标题 → AI 输出多个优化方案 + 优化原因 | 搜索优化、关键词策略 |
| 📝 营销内容生成 | 选择平台（小红书/淘宝/抖音），AI 生成平台适配内容 | 内容运营、平台差异理解 |
| 📈 运营策略建议 | 输出目标用户 + 内容方向 + 平台组合策略 | 运营全局视角和决策能力 |

### 增强能力

- **RAG 增强**：生成内容前检索运营知识库，注入 Prompt 提升输出质量
- **多模型支持**：.env 一键切换 DeepSeek / Qwen / GPT

---

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 | Python 3.14+ / FastAPI | 异步 API，Pydantic 数据验证 |
| 前端 | 纯 HTML + CSS + JS | 零依赖，单页应用，响应式设计 |
| LLM | OpenAI 兼容 SDK | DeepSeek / Qwen / GPT 切换 |
| RAG | 关键词检索（可扩展 ChromaDB） | 轻量运营知识库 |
| 配置 | pydantic-settings + .env | 密钥和参数管理 |

---

## 快速启动

### 前置要求

- Python 3.10+
- LLM API Key（DeepSeek / Qwen / OpenAI 均可）

### 1. 安装依赖

```bash
cd ai-product-growth-assistant
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key 和模型配置
```

`.env` 示例：

```env
LLM_API_KEY=sk-your_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-flash
```

### 3. 启动服务

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. 打开浏览器

访问 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 项目结构

```
ai-product-growth-assistant/
├── backend/
│   ├── main.py              # FastAPI 入口 + 静态文件托管
│   ├── config.py            # .env 配置
│   ├── api/
│   │   └── routes.py        # API 路由
│   ├── services/
│   │   ├── llm.py           # LLM 调用（OpenAI 兼容）
│   │   ├── prompt.py        # 4 套 Prompt 模板
│   │   └── rag.py           # RAG 检索服务
│   └── schemas/
│       └── models.py        # Pydantic 数据模型
├── frontend/
│   ├── index.html           # 页面结构
│   ├── style.css            # 样式
│   └── app.js               # 交互逻辑
├── knowledge/               # 运营知识库
│   ├── 电商标题优化规则.md
│   ├── 小红书内容结构.md
│   └── 商品卖点提炼方法.md
├── .env.example
├── requirements.txt
└── README.md
```

---

## 使用流程

```
1. 填写商品信息（名称、价格、特点、目标用户）
       ↓
2. 选择功能 Tab
       ↓
3. 点击生成 → AI 处理 → 展示结果
       ↓
4. 切换 Tab 体验不同功能
```

### 示例输入

```
商品：无线降噪耳机
价格：299 元
特点：蓝牙5.3、40小时续航、主动降噪
用户：学生
```

---

## 切换模型

修改 `.env` 中的三行即可切换：

```env
# DeepSeek（默认）
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-flash

# 通义千问
# LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# LLM_MODEL=qwen-plus

# OpenAI
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4o-mini
```

---

## 面试亮点

1. **Prompt Engineering**：角色锚定 + 结构化输出 + RAG注入，Prompt 质量决定结果
2. **RAG + LLM + 业务**：知识库增强生成，符合行业趋势
3. **业务理解**：从商品定位到运营策略，覆盖完整运营链条
4. **工程规范**：Pydantic 校验、异步 API、Pydantic Settings、代码格式化

---

## License

MIT
