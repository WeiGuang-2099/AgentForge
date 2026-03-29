# AgentForge

<div align="center">

**🚀 开箱即用的多Agent协作框架**

*Clone → 配置API → 一键启动 → 立即使用*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

[English](./README_EN.md) | 简体中文

</div>

---

## 📖 目录

- [项目概述](#-项目概述)
- [核心特性](#-核心特性)
- [技术架构](#-技术架构)
- [快速开始](#-快速开始)
- [安装部署](#-安装部署)
- [API配置](#-api配置)
- [预置Agent模板](#-预置agent模板)
- [使用场景](#-使用场景)
- [自定义Agent](#-自定义agent)
- [项目结构](#-项目结构)
- [开发路线](#-开发路线)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 项目概述

**AgentForge** 是一个开箱即用的多Agent协作框架，专为希望快速部署AI Agent应用的开发者和团队设计。

### 设计理念

```
┌─────────────────────────────────────────────────────────────┐
│                    传统Agent框架                             │
│  繁琐配置 → 编写代码 → 调试 → 部署 → 维护                    │
│                    ⏱️ 数小时 ~ 数天                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    AgentForge                                │
│  Clone → 填API → 启动 → 使用                                 │
│                    ⏱️ 5分钟                                  │
└─────────────────────────────────────────────────────────────┘
```

### 核心价值主张

| 特性 | 描述 |
|------|------|
| 🎁 **开箱即用** | 预置6+实用Agent模板，无需编写代码即可使用 |
| 🔧 **简单配置** | 仅需配置API Key，支持OpenAI、Claude、本地模型 |
| 🤝 **多Agent协作** | 支持单Agent和多Agent团队协作模式 |
| 🌐 **Web界面** | 现代化Web UI，支持实时对话和工作流可视化 |
| 🔌 **工具生态** | 内置搜索、代码执行、文件处理等工具 |
| 📦 **一键部署** | Docker支持，3秒启动完整服务 |

---

## ✨ 核心特性

### 1. 多种Agent模式

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│    单Agent模式    │    │   多Agent协作     │    │   工作流模式      │
│                  │    │                  │    │                  │
│  ┌────────────┐  │    │  ┌───┐ ┌───┐    │    │  ┌───┐→┌───┐→┌───┐│
│  │   Agent    │  │    │  │ A │ │ B │    │    │  │ 1 │ │ 2 │ │ 3 ││
│  │            │  │    │  └─┬─┘ └─┬─┘    │    │  └───┘ └───┘ └───┘│
│  └────────────┘  │    │    └──┬──┘      │    │                  │
│                  │    │       ↓         │    │   条件分支/循环   │
│  一对一对话      │    │    ┌─────┐      │    │                  │
│                  │    │    │ 结果 │      │    │                  │
└──────────────────┘    │    └─────┘      │    └──────────────────┘
                        └──────────────────┘
```

### 2. 内置工具集

| 工具类别 | 工具名称 | 功能描述 |
|----------|----------|----------|
| 🔍 搜索 | `web_search` | 网络搜索（支持Google/Bing/DuckDuckGo） |
| 📄 网页 | `scrape_web` | 网页内容抓取和提取 |
| 💻 代码 | `python_repl` | Python代码安全执行 |
| 📁 文件 | `read_file` / `write_file` | 文件读写操作 |
| 🧮 计算 | `calculator` | 数学计算和公式求解 |
| 🌐 翻译 | `translator` | 多语言翻译 |
| 📊 数据 | `data_analyzer` | CSV/Excel数据分析 |

### 3. 记忆系统

```
短期记忆 (Session)          长期记忆 (Persistent)
┌─────────────────┐         ┌─────────────────┐
│ 当前对话上下文   │         │ 向量数据库存储   │
│ 自动管理        │   →     │ 跨会话记忆      │
│ 窗口滑动裁剪    │         │ 语义检索        │
└─────────────────┘         └─────────────────┘
```

### 4. 多模型支持

通过 LiteLLM 统一接口，支持：

| 提供商 | 模型示例 | 配置方式 |
|--------|----------|----------|
| OpenAI | GPT-4, GPT-3.5 | `OPENAI_API_KEY` |
| Anthropic | Claude 3系列 | `ANTHROPIC_API_KEY` |
| Google | Gemini Pro | `GOOGLE_API_KEY` |
| 本地模型 | Ollama, LM Studio | `OPENAI_API_BASE` |

---

## 🏗️ 技术架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户层                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     Web UI (Next.js)                          │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │  │
│  │  │ 对话界面 │ │ 工作流   │ │ 监控面板 │ │ 设置页面 │            │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ WebSocket / REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          服务层                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   FastAPI Backend                             │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │  │
│  │  │ Agent Router │ │ Chat Router  │ │ Tool Router │            │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          核心引擎层                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │ Agent Engine │ │ Memory Mgr  │ │ Tool Runner │ │ LLM Client  │  │
│  │             │ │             │ │             │ │             │  │
│  │ - 角色管理   │ │ - 短期记忆  │ │ - 工具注册  │ │ - LiteLLM   │  │
│  │ - 消息路由   │ │ - 长期记忆  │ │ - 执行沙箱  │ │ - 流式响应  │  │
│  │ - 状态管理   │ │ - 向量检索  │ │ - 结果解析  │ │ - 重试机制  │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          存储层                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                   │
│  │ PostgreSQL  │ │  ChromaDB   │ │   Redis     │                   │
│  │             │ │             │ │             │                   │
│  │ - 会话数据  │ │ - 向量存储  │ │ - 缓存      │                   │
│  │ - 用户配置  │ │ - 嵌入向量  │ │ - 队列      │                   │
│  │ - 日志记录  │ │ - 记忆检索  │ │ - 状态      │                   │
│  └─────────────┘ └─────────────┘ └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 技术栈详情

```
前端技术栈
├── 框架: Next.js 14 (App Router)
├── 语言: TypeScript
├── 样式: TailwindCSS + shadcn/ui
├── 状态: Zustand
├── 通信: WebSocket (实时) + Axios (REST)
└── 可视化: React Flow (工作流)

后端技术栈
├── 框架: FastAPI
├── 语言: Python 3.10+
├── 异步: asyncio + uvicorn
├── 验证: Pydantic v2
├── LLM: LiteLLM (统一接口)
├── 向量库: ChromaDB
└── ORM: SQLAlchemy 2.0

基础设施
├── 容器: Docker + Docker Compose
├── 数据库: PostgreSQL 15
├── 缓存: Redis 7
└── 反向代理: Nginx (可选)
```

---

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose（推荐）
- 或 Python 3.10+ / Node.js 18+（本地开发）

### 30秒快速启动

```bash
# 1. Clone项目
git clone https://github.com/WeiGuang-2099/AgentForge.git
cd agentforge

# 2. 配置API Key
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 3. 一键启动
docker-compose up -d

# 4. 访问Web界面
# 打开浏览器访问 http://localhost:3000
```

### 启动成功标志

```
✅ [agentforge-web]     Running on http://localhost:3000
✅ [agentforge-api]     Running on http://localhost:8000
✅ [agentforge-db]      PostgreSQL ready
✅ [agentforge-redis]   Redis ready
```

---

## 📦 安装部署

### 方式一：Docker部署（推荐）

```bash
# 完整服务启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：本地开发部署

```bash
# 后端设置
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# 前端设置（新终端）
cd frontend
npm install
npm run dev
```

### 环境变量完整配置

```env
# ===========================================
# AgentForge 配置文件
# ===========================================

# ----- LLM 提供商配置（至少配置一个）-----
# OpenAI (推荐)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Claude (可选)
# ANTHROPIC_API_KEY=your-anthropic-api-key
# ANTHROPIC_MODEL=claude-3-opus-20240229

# Google Gemini (可选)
# GOOGLE_API_KEY=your-google-api-key

# 本地模型 - Ollama/LM Studio (可选)
# OPENAI_API_BASE=http://localhost:11434/v1
# OPENAI_API_KEY=ollama

# ----- 应用配置 -----
APP_ENV=development
APP_SECRET_KEY=your-secret-key-change-in-production
APP_DEBUG=true

# ----- 数据库配置 -----
DATABASE_URL=postgresql://agentforge:password@localhost:5432/agentforge
REDIS_URL=redis://localhost:6379/0

# ----- 向量数据库配置 -----
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=text-embedding-3-small

# ----- 工具配置（可选）-----
# 搜索工具
SERPER_API_KEY=your-serper-api-key
BING_API_KEY=your-bing-api-key

# ----- 功能开关 -----
ENABLE_CODE_EXECUTION=true
ENABLE_WEB_SEARCH=true
ENABLE_FILE_OPS=true

# ----- 语言和地区 -----
DEFAULT_LANGUAGE=zh-CN
TIMEZONE=Asia/Shanghai
```

---

## 🔑 API配置

### 支持的LLM提供商

#### 1. OpenAI（推荐）

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview
```

获取方式：
1. 访问 https://platform.openai.com/api-keys
2. 创建新的API Key
3. 复制到 `.env` 文件

#### 2. Anthropic Claude

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
ANTHROPIC_MODEL=claude-3-opus-20240229
```

#### 3. 本地模型（Ollama）

```bash
# 安装Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 拉取模型
ollama pull llama2
ollama pull mistral

# 启动服务
ollama serve
```

```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama2
```

### 模型选择建议

| 使用场景 | 推荐模型 | 原因 |
|----------|----------|------|
| 日常对话 | GPT-3.5-Turbo | 速度快、成本低 |
| 复杂推理 | GPT-4-Turbo | 能力最强 |
| 长文本处理 | Claude 3 Opus | 200K上下文 |
| 本地/隐私 | Llama2/Mistral | 数据不离本地 |
| 成本敏感 | GPT-3.5 / Gemini Pro | 免费额度 |

---

## 🤖 预置Agent模板

### 模板概览

```
presets/
├── assistant.yaml      # 通用助手
├── coder.yaml          # 代码专家
├── researcher.yaml     # 网络研究员
├── translator.yaml     # 翻译专家
├── writer.yaml         # 内容创作者
├── analyst.yaml        # 数据分析师
└── team/
    ├── dev_team.yaml   # 开发团队（多Agent）
    └── research_team.yaml  # 研究团队（多Agent）
```

---

### 1. 🎯 通用助手 (Assistant)

**适用场景：** 日常问答、信息查询、创意头脑风暴

```yaml
name: assistant
display_name: 通用助手
description: 友好的AI助手，擅长回答各类问题
model: gpt-4-turbo-preview
system_prompt: |
  你是一个友好、专业的AI助手。
  - 回答准确、简洁
  - 适当使用emoji增加亲和力
  - 不确定时坦诚说明
tools: []
```

---

### 2. 💻 代码专家 (Coder)

**适用场景：** 代码编写、Debug、代码审查、技术问答

```yaml
name: coder
display_name: 代码专家
description: 精通多种编程语言的代码助手
model: gpt-4-turbo-preview
system_prompt: |
  你是一位经验丰富的软件工程师。
  
  技能：
  - 精通 Python, JavaScript, TypeScript, Go, Rust, Java
  - 熟悉主流框架和最佳实践
  - 擅长代码优化和问题诊断
  
  工作原则：
  - 提供可运行的完整代码
  - 解释关键实现思路
  - 指出潜在问题和改进建议
  - 遵循代码规范和最佳实践
tools:
  - python_repl
  - read_file
  - write_file
```

---

### 3. 🔍 网络研究员 (Researcher)

**适用场景：** 信息搜集、文献调研、市场分析

```yaml
name: researcher
display_name: 网络研究员
description: 擅长网络搜索和信息整理的研究助手
model: gpt-4-turbo-preview
system_prompt: |
  你是一位专业的研究员。
  
  工作流程：
  1. 理解研究问题
  2. 搜索相关信息
  3. 验证信息可靠性
  4. 整理结构化报告
  
  输出要求：
  - 信息来源明确
  - 观点客观中立
  - 结构清晰有条理
tools:
  - web_search
  - scrape_web
```

---

### 4. 🌐 翻译专家 (Translator)

**适用场景：** 文档翻译、多语言沟通、润色校对

```yaml
name: translator
display_name: 翻译专家
description: 专业多语言翻译，支持50+语言
model: gpt-4-turbo-preview
system_prompt: |
  你是一位专业翻译专家。
  
  能力：
  - 支持50+语言互译
  - 保留原文风格和语气
  - 专业术语准确翻译
  - 提供多种翻译版本
  
  翻译原则：
  - 信达雅
  - 本地化表达
  - 保持格式一致
tools: []
```

---

### 5. ✍️ 内容创作者 (Writer)

**适用场景：** 文章撰写、营销文案、邮件起草

```yaml
name: writer
display_name: 内容创作者
description: 专业的内容创作助手
model: gpt-4-turbo-preview
system_prompt: |
  你是一位专业的内容创作者。
  
  擅长领域：
  - 技术博客和教程
  - 营销文案和Slogan
  - 商业邮件和报告
  - 社交媒体内容
  
  写作原则：
  - 目标受众明确
  - 结构清晰
  - 语言生动
  - SEO友好（如需要）
tools:
  - read_file
  - write_file
```

---

### 6. 📊 数据分析师 (Analyst)

**适用场景：** 数据分析、报表生成、可视化

```yaml
name: analyst
display_name: 数据分析师
description: 数据分析和可视化专家
model: gpt-4-turbo-preview
system_prompt: |
  你是一位数据分析专家。
  
  能力：
  - 数据清洗和预处理
  - 统计分析
  - 数据可视化
  - 趋势预测
  
  工作方式：
  1. 理解分析目标
  2. 检查数据质量
  3. 选择合适方法
  4. 输出洞察和建议
tools:
  - python_repl
  - read_file
  - write_file
  - data_analyzer
```

---

### 7. 👥 开发团队 (Dev Team) - 多Agent协作

**适用场景：** 完整的软件开发任务

```yaml
name: dev_team
display_name: 开发团队
description: 多Agent协作完成开发任务
mode: team
agents:
  - role: architect
    name: 架构师
    responsibility: 系统设计和架构决策
    
  - role: developer
    name: 开发者
    responsibility: 代码实现
    
  - role: reviewer
    name: 审查者
    responsibility: 代码审查和质量把控
    
workflow:
  - agent: architect
    task: "分析需求，设计技术方案"
    
  - agent: developer
    task: "根据架构师的方案实现代码"
    depends_on: [architect]
    
  - agent: reviewer
    task: "审查代码，提出改进建议"
    depends_on: [developer]
```

---

## 💡 使用场景

### 场景一：日常开发辅助

```
用户：帮我写一个Python函数，解析CSV文件并计算平均值

Coder Agent：
1. 理解需求
2. 生成代码
3. 执行测试
4. 返回结果和代码
```

### 场景二：技术调研

```
用户：调研一下2024年最流行的前端框架

Researcher Agent：
1. 搜索最新信息
2. 整理对比数据
3. 生成调研报告
```

### 场景三：多语言翻译

```
用户：将这份技术文档翻译成英文

Translator Agent：
1. 读取文档
2. 分段翻译
3. 保持格式
4. 输出译文
```

### 场景四：数据分析

```
用户：分析这份销售数据，找出趋势

Analyst Agent：
1. 读取CSV
2. 数据清洗
3. 统计分析
4. 生成图表
5. 输出洞察
```

---

## 🛠️ 自定义Agent

### 创建自定义Agent

在 `presets/` 目录下创建新的YAML文件：

```yaml
# presets/my_agent.yaml

name: my_custom_agent
display_name: 我的自定义Agent
description: 这是一个自定义Agent示例
model: gpt-4-turbo-preview

system_prompt: |
  你是一个[具体角色描述]。
  
  技能：
  - 技能1
  - 技能2
  
  工作原则：
  - 原则1
  - 原则2

tools:
  - web_search
  - python_repl

# 可选：记忆配置
memory:
  type: conversation  # conversation / vector
  max_tokens: 4000

# 可选：参数配置
parameters:
  temperature: 0.7
  max_tokens: 2000
```

### Agent配置说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | Agent唯一标识 |
| `display_name` | string | ✅ | 显示名称 |
| `description` | string | ✅ | 功能描述 |
| `model` | string | ✅ | 使用的模型 |
| `system_prompt` | string | ✅ | 系统提示词 |
| `tools` | array | ❌ | 启用的工具列表 |
| `memory` | object | ❌ | 记忆配置 |
| `parameters` | object | ❌ | 模型参数 |

---

## 📁 项目结构

```
agentforge/
├── .env.example              # 环境变量模板
├── .env                      # 实际环境变量（不提交）
├── docker-compose.yml        # Docker编排配置
├── Dockerfile.api            # API服务镜像
├── Dockerfile.web            # Web服务镜像
├── requirements.txt          # Python依赖
├── README.md                 # 项目文档
│
├── presets/                  # Agent预设模板
│   ├── assistant.yaml
│   ├── coder.yaml
│   ├── researcher.yaml
│   ├── translator.yaml
│   ├── writer.yaml
│   ├── analyst.yaml
│   └── team/
│       ├── dev_team.yaml
│       └── research_team.yaml
│
├── backend/                  # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI入口
│   │   ├── config.py        # 配置管理
│   │   ├── routers/         # API路由
│   │   │   ├── agent.py
│   │   │   ├── chat.py
│   │   │   └── tool.py
│   │   ├── core/            # 核心引擎
│   │   │   ├── agent.py
│   │   │   ├── memory.py
│   │   │   ├── llm.py
│   │   │   └── workflow.py
│   │   ├── tools/           # 工具实现
│   │   │   ├── base.py
│   │   │   ├── search.py
│   │   │   ├── code.py
│   │   │   └── file.py
│   │   ├── models/          # 数据模型
│   │   └── utils/           # 工具函数
│   ├── tests/
│   └── pyproject.toml
│
├── frontend/                 # 前端服务
│   ├── src/
│   │   ├── app/             # Next.js App Router
│   │   ├── components/      # React组件
│   │   │   ├── chat/
│   │   │   ├── workflow/
│   │   │   └── common/
│   │   ├── stores/          # 状态管理
│   │   ├── lib/             # 工具库
│   │   └── types/           # TypeScript类型
│   ├── public/
│   ├── package.json
│   └── next.config.js
│
├── data/                     # 数据目录
│   ├── chroma/              # 向量数据库
│   └── uploads/             # 上传文件
│
└── scripts/                  # 脚本
    ├── start.sh             # Linux/Mac启动
    ├── start.bat            # Windows启动
    └── init_db.py           # 数据库初始化
```

---

## 🗓️ 开发路线

### Phase 1: 核心基础 (v0.1.0)

- [x] 项目结构搭建
- [x] 核心Agent引擎
- [x] LLM集成（LiteLLM）
- [x] 基础CLI工具
- [x] 3个预置Agent

### Phase 2: Web界面 (v0.2.0)

- [x] Next.js前端框架
- [x] 实时对话界面
- [x] Agent选择器
- [x] 流式响应显示

### Phase 3: 工具生态 (v0.3.0)

- [x] 工具注册系统
- [x] 代码执行沙箱
- [x] 网络搜索工具
- [x] 文件操作工具

### Phase 4: 多Agent协作 (v0.4.0)

- [x] 多Agent通信协议
- [x] 工作流引擎
- [x] 团队协作模板
- [x] 可视化编排器

### Phase 5: 企业级功能 (v0.5.0)

- [x] 用户认证系统
- [x] API Key管理
- [x] 使用量统计
- [x] 审计日志

### Phase 6: 生态扩展 (v1.0.0)

- [x] 插件系统
- [x] 模板市场
- [x] 云端部署方案
- [ ] 移动端适配

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 贡献方式

- 🐛 提交Bug报告
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码PR
- 🌟 给项目点Star

### 开发指南

```bash
# 1. Fork并Clone
git clone https://github.com/WeiGuang-2099/AgentForge.git

# 2. 创建分支
git checkout -b feature/your-feature

# 3. 安装开发依赖
make install-dev

# 4. 运行测试
make test

# 5. 提交代码
git commit -m "feat: add your feature"
git push origin feature/your-feature

# 6. 创建Pull Request
```

### 代码规范

- Python: 遵循 PEP 8，使用 Black 格式化
- TypeScript: 使用 ESLint + Prettier
- 提交信息: 遵循 Conventional Commits

---

## 📄 许可证

本项目基于 [MIT License](./LICENSE) 开源。

---

## 🙏 致谢

感谢以下开源项目的启发：

- [LangChain](https://github.com/langchain-ai/langchain) - LLM应用框架
- [AutoGen](https://github.com/microsoft/autogen) - 多Agent框架
- [CrewAI](https://github.com/joaomdmoura/crewAI) - Agent协作框架
- [ChatGPT-Next-Web](https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web) - Web界面参考

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！**

Made with ❤️ by AgentForge Team

</div>
