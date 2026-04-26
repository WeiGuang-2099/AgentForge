# AgentForge

<div align="center">

**Ready-to-use Multi-Agent Collaboration Framework**

*Clone -> Configure API -> One-click Start -> Use Immediately*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

English | [简体中文](./README.md)

</div>

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Features](#core-features)
- [Technical Architecture](#technical-architecture)
- [Quick Start](#quick-start)
- [Installation and Deployment](#installation-and-deployment)
- [API Configuration](#api-configuration)
- [Preset Agent Templates](#preset-agent-templates)
- [Use Cases](#use-cases)
- [Custom Agent](#custom-agent)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing Guide](#contributing-guide)
- [License](#license)

---

## Project Overview

**AgentForge** is a ready-to-use multi-agent collaboration framework designed for developers and teams who want to quickly deploy AI Agent applications.

### Design Philosophy

```
+-------------------------------------------------------------+
|                  Traditional Agent Framework                  |
|  Tedious Config -> Write Code -> Debug -> Deploy -> Maintain  |
|                    Hours to Days                              |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      AgentForge                               |
|  Clone -> Fill API -> Start -> Use                            |
|                    5 Minutes                                  |
+-------------------------------------------------------------+
```

### Core Value Proposition

| Feature | Description |
|---------|-------------|
| **Ready to Use** | 6+ preset Agent templates, no coding required |
| **Simple Config** | Only API Key needed, supports OpenAI, Claude, local models |
| **Multi-Agent Collaboration** | Supports single Agent and multi-Agent team collaboration modes |
| **Web Interface** | Modern Web UI with real-time chat and workflow visualization |
| **Tool Ecosystem** | Built-in search, code execution, file processing and more |
| **Memory System** | Short-term sliding window + ChromaDB long-term vector memory, cross-session recall |
| **Security Hardened** | Rate limiting, CORS whitelist, API key format validation, route authentication |
| **One-click Deploy** | Docker multi-stage builds, health checks, production-grade Gunicorn deployment |

---

## Core Features

### 1. Multiple Agent Modes

```
+------------------+    +------------------+    +------------------+
|  Single Agent    |    | Multi-Agent Collab|    |  Workflow Mode   |
|                  |    |                  |    |                  |
|  +------------+  |    |  +---+ +---+    |    |  +---+>+---+>+---+|
|  |   Agent    |  |    |  | A | | B |    |    |  | 1 | | 2 | | 3 ||
|  |            |  |    |  +-+-+ +-+-+    |    |  +---+ +---+ +---+|
|  +------------+  |    |    +--+--+      |    |                  |
|                  |    |       |         |    |  Conditional     |
|  One-on-one Chat |    |    +-----+      |    |  Branching/Loop  |
|                  |    |    |Result|      |    |                  |
+------------------+    |    +-----+      |    +------------------+
                        +------------------+
```

### 2. Built-in Toolset

| Category | Tool | Description |
|----------|------|-------------|
| Search | `web_search` | Web search (supports Google/Bing/DuckDuckGo) |
| Web | `scrape_web` | Web content scraping and extraction |
| Code | `python_repl` | Safe Python code execution |
| File | `read_file` / `write_file` | File read/write operations |
| Calculator | `calculator` | Math calculations and formula solving |
| Translation | `translator` | Multi-language translation |
| Data | `data_analyzer` | CSV/Excel data analysis |

### 3. Memory System

```
Short-term Memory (ShortTermMemory)     Long-term Memory (LongTermMemory)
+---------------------------+           +---------------------------+
| Current chat context      |           | ChromaDB vector storage   |
| Configurable sliding window|    ->   | Cross-session memory      |
| Auto-trim old messages    |           | Semantic similarity search|
| Query and clear support   |           | Auto embedding generation |
+---------------------------+           +---------------------------+
                  |                                |
                  v                                v
         +-----------------------------------------------+
         |        MemoryManager (Unified Facade)          |
         |  - add() / search() / get_context()            |
         |  - Toggle via ENABLE_MEMORY setting            |
         |  - Configurable window size and top_k          |
         +-----------------------------------------------+
```

### 4. Security and Production Readiness

| Feature | Description |
|---------|-------------|
| Rate Limiting | SlowAPI per-IP throttling, 30 req/min on tool execution by default |
| CORS Whitelist | Configurable origins, no wildcard `*` in production |
| API Key Validation | Provider-specific format validation (OpenAI/Anthropic/Google etc.) |
| Route Authentication | Unified auth on Usage/Plugin/Marketplace routes |
| Feature Flags | `ENABLE_CODE_EXECUTION`, `ENABLE_WEB_SEARCH`, `ENABLE_FILE_OPS` toggles |
| Production Deploy | Gunicorn + Uvicorn Worker multi-process, multi-stage Docker builds |
| Health Checks | Docker Compose service-level health checks, K8s ready |

### 5. Multi-Model Support

Unified interface through LiteLLM, supporting:

| Provider | Model Examples | Configuration |
|----------|----------------|---------------|
| OpenAI | GPT-4, GPT-3.5 | `OPENAI_API_KEY` |
| Anthropic | Claude 3 series | `ANTHROPIC_API_KEY` |
| Google | Gemini Pro | `GOOGLE_API_KEY` |
| Local Models | Ollama, LM Studio | `OPENAI_API_BASE` |

---

## Technical Architecture

### Overall Architecture Diagram

```
+---------------------------------------------------------------------+
|                          User Layer                                   |
|  +--------------------------------------------------------------+  |
|  |                     Web UI (Next.js)                          |  |
|  |  +---------+ +---------+ +---------+ +---------+            |  |
|  |  | Chat UI | |Workflow | | Monitor | | Settings|            |  |
|  |  +---------+ +---------+ +---------+ +---------+            |  |
|  +--------------------------------------------------------------+  |
+---------------------------------------------------------------------+
                                  |
                                  | WebSocket / REST API
                                  v
+---------------------------------------------------------------------+
|                        Service Layer                                  |
|  +--------------------------------------------------------------+  |
|  |                   FastAPI Backend                             |  |
|  |  +-------------+ +-------------+ +-------------+            |  |
|  |  | Agent Router| | Chat Router | | Tool Router |            |  |
|  |  +-------------+ +-------------+ +-------------+            |  |
|  +--------------------------------------------------------------+  |
+---------------------------------------------------------------------+
                                  |
                                  v
+---------------------------------------------------------------------+
|                      Core Engine Layer                                |
|  +-------------+ +-------------+ +-------------+ +-------------+  |
|  | Agent Engine| | Memory Mgr  | | Tool Runner | | LLM Client  |  |
|  |             | |             | |             | |             |  |
|  | -Role Mgmt  | | -Short-term | | -Tool Reg   | | -LiteLLM    |  |
|  | -Msg Routing| | -Long-term  | | -Exec Sandbox| | -Streaming  |  |
|  | -State Mgmt | | -Vec Search | | -Result Parse| | -Retry      |  |
|  +-------------+ +-------------+ +-------------+ +-------------+  |
+---------------------------------------------------------------------+
                                  |
                                  v
+---------------------------------------------------------------------+
|                        Storage Layer                                  |
|  +-------------+ +-------------+ +-------------+                   |
|  | PostgreSQL  | |  ChromaDB   | |   Redis     |                   |
|  |             | |             | |             |                   |
|  | -Sessions   | | -Vec Store  | | -Cache      |                   |
|  | -User Config| | -Embeddings | | -Queue      |                   |
|  | -Logging    | | -Mem Search | | -State      |                   |
|  +-------------+ +-------------+ +-------------+                   |
+---------------------------------------------------------------------+
```

### Tech Stack Details

```
Frontend Stack
|-- Framework: Next.js 14 (App Router)
|-- Language: TypeScript
|-- Styling: TailwindCSS + shadcn/ui
|-- State: Zustand
|-- Communication: WebSocket (real-time) + Axios (REST)
+-- Visualization: React Flow (workflow)

Backend Stack
|-- Framework: FastAPI
|-- Language: Python 3.10+
|-- Async: asyncio + uvicorn
|-- Production: Gunicorn + Uvicorn Workers
|-- Validation: Pydantic v2
|-- LLM: LiteLLM (unified interface)
|-- Vector DB: ChromaDB
|-- ORM: SQLAlchemy 2.0
|-- Rate Limiting: SlowAPI
+-- Testing: pytest + httpx

Infrastructure
|-- Containers: Docker + Docker Compose
|-- Database: PostgreSQL 15
|-- Cache: Redis 7
+-- Reverse Proxy: Nginx (optional)
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- Or Python 3.10+ / Node.js 18+ (local development)

### 30-Second Quick Launch

```bash
# 1. Clone the project
git clone https://github.com/WeiGuang-2099/AgentForge.git
cd agentforge

# 2. Configure API Key
cp .env.example .env
# Edit the .env file and fill in your API Key

# 3. One-click start
docker-compose up -d

# 4. Access the Web interface
# Open your browser and visit http://localhost:3000
```

### Startup Success Indicators

```
[agentforge-web]     Running on http://localhost:3000
[agentforge-api]     Running on http://localhost:8000
[agentforge-db]      PostgreSQL ready
[agentforge-redis]   Redis ready
```

---

## Installation and Deployment

### Option 1: Docker Deployment (Recommended)

```bash
# Start complete services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Option 2: Local Development Setup

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

### Complete Environment Variable Configuration

```env
# ===========================================
# AgentForge Configuration File
# ===========================================

# ----- LLM Provider Configuration (at least one required) -----
# OpenAI (recommended)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Claude (optional)
# ANTHROPIC_API_KEY=your-anthropic-api-key
# ANTHROPIC_MODEL=claude-3-opus-20240229

# Google Gemini (optional)
# GOOGLE_API_KEY=your-google-api-key

# Local Models - Ollama/LM Studio (optional)
# OPENAI_API_BASE=http://localhost:11434/v1
# OPENAI_API_KEY=ollama

# ----- Application Configuration -----
APP_ENV=development
APP_SECRET_KEY=your-secret-key-change-in-production
APP_DEBUG=true

# ----- Database Configuration -----
DATABASE_URL=postgresql://agentforge:password@localhost:5432/agentforge
REDIS_URL=redis://localhost:6379/0

# ----- Vector Database Configuration -----
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=text-embedding-3-small

# ----- Tool Configuration (optional) -----
# Search tools
SERPER_API_KEY=your-serper-api-key
BING_API_KEY=your-bing-api-key

# ----- Security Configuration -----
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
RATE_LIMIT_PER_MINUTE=30

# ----- Feature Toggles -----
ENABLE_CODE_EXECUTION=true
ENABLE_WEB_SEARCH=true
ENABLE_FILE_OPS=true

# ----- Memory System Configuration -----
ENABLE_MEMORY=true
MEMORY_SHORT_TERM_WINDOW=20
MEMORY_LONG_TERM_TOP_K=5

# ----- Language and Region -----
DEFAULT_LANGUAGE=zh-CN
TIMEZONE=Asia/Shanghai
```

---

## API Configuration

### Supported LLM Providers

#### 1. OpenAI (Recommended)

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview
```

How to obtain:
1. Visit https://platform.openai.com/api-keys
2. Create a new API Key
3. Copy to `.env` file

#### 2. Anthropic Claude

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
ANTHROPIC_MODEL=claude-3-opus-20240229
```

#### 3. Local Models (Ollama)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama2
ollama pull mistral

# Start service
ollama serve
```

```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama2
```

### Model Selection Guide

| Use Case | Recommended Model | Reason |
|----------|-------------------|--------|
| Daily Chat | GPT-3.5-Turbo | Fast, low cost |
| Complex Reasoning | GPT-4-Turbo | Most capable |
| Long Text Processing | Claude 3 Opus | 200K context |
| Local/Privacy | Llama2/Mistral | Data stays local |
| Cost Sensitive | GPT-3.5 / Gemini Pro | Free tier available |

---

## Preset Agent Templates

### Template Overview

```
presets/
|-- assistant.yaml      # General Assistant
|-- coder.yaml          # Code Expert
|-- researcher.yaml     # Web Researcher
|-- translator.yaml     # Translation Expert
|-- writer.yaml         # Content Creator
|-- analyst.yaml        # Data Analyst
+-- team/
    |-- dev_team.yaml   # Dev Team (Multi-Agent)
    +-- research_team.yaml  # Research Team (Multi-Agent)
```

---

### 1. General Assistant

**Use cases:** Daily Q&A, information lookup, creative brainstorming

```yaml
name: assistant
display_name: General Assistant
description: Friendly AI assistant, skilled at answering all kinds of questions
model: gpt-4-turbo-preview
system_prompt: |
  You are a friendly and professional AI assistant.
  - Answer accurately and concisely
  - Use emoji appropriately for approachability
  - Be honest when uncertain
tools: []
```

---

### 2. Code Expert

**Use cases:** Code writing, debugging, code review, technical Q&A

```yaml
name: coder
display_name: Code Expert
description: Code assistant proficient in multiple programming languages
model: gpt-4-turbo-preview
system_prompt: |
  You are an experienced software engineer.

  Skills:
  - Proficient in Python, JavaScript, TypeScript, Go, Rust, Java
  - Familiar with mainstream frameworks and best practices
  - Skilled at code optimization and problem diagnosis

  Work Principles:
  - Provide runnable, complete code
  - Explain key implementation ideas
  - Point out potential issues and improvement suggestions
  - Follow coding standards and best practices
tools:
  - python_repl
  - read_file
  - write_file
```

---

### 3. Web Researcher

**Use cases:** Information gathering, literature research, market analysis

```yaml
name: researcher
display_name: Web Researcher
description: Research assistant skilled at web search and information synthesis
model: gpt-4-turbo-preview
system_prompt: |
  You are a professional researcher.

  Workflow:
  1. Understand the research question
  2. Search for relevant information
  3. Verify information reliability
  4. Compile a structured report

  Output Requirements:
  - Clear information sources
  - Objective and neutral viewpoints
  - Well-organized structure
tools:
  - web_search
  - scrape_web
```

---

### 4. Translation Expert

**Use cases:** Document translation, multi-language communication, proofreading

```yaml
name: translator
display_name: Translation Expert
description: Professional multi-language translator, supporting 50+ languages
model: gpt-4-turbo-preview
system_prompt: |
  You are a professional translation expert.

  Capabilities:
  - Support 50+ language translation
  - Preserve original style and tone
  - Accurate technical term translation
  - Provide multiple translation versions

  Translation Principles:
  - Faithful, expressive, elegant
  - Localized expression
  - Maintain consistent formatting
tools: []
```

---

### 5. Content Creator

**Use cases:** Article writing, marketing copy, email drafting

```yaml
name: writer
display_name: Content Creator
description: Professional content creation assistant
model: gpt-4-turbo-preview
system_prompt: |
  You are a professional content creator.

  Areas of Expertise:
  - Technical blogs and tutorials
  - Marketing copy and slogans
  - Business emails and reports
  - Social media content

  Writing Principles:
  - Clear target audience
  - Well-organized structure
  - Engaging language
  - SEO-friendly (when needed)
tools:
  - read_file
  - write_file
```

---

### 6. Data Analyst

**Use cases:** Data analysis, report generation, visualization

```yaml
name: analyst
display_name: Data Analyst
description: Data analysis and visualization expert
model: gpt-4-turbo-preview
system_prompt: |
  You are a data analysis expert.

  Capabilities:
  - Data cleaning and preprocessing
  - Statistical analysis
  - Data visualization
  - Trend forecasting

  Work Approach:
  1. Understand analysis objectives
  2. Check data quality
  3. Select appropriate methods
  4. Output insights and recommendations
tools:
  - python_repl
  - read_file
  - write_file
  - data_analyzer
```

---

### 7. Dev Team - Multi-Agent Collaboration

**Use cases:** Complete software development tasks

```yaml
name: dev_team
display_name: Dev Team
description: Multi-Agent collaboration for development tasks
mode: team
agents:
  - role: architect
    name: Architect
    responsibility: System design and architecture decisions

  - role: developer
    name: Developer
    responsibility: Code implementation

  - role: reviewer
    name: Reviewer
    responsibility: Code review and quality control

workflow:
  - agent: architect
    task: "Analyze requirements, design technical solution"

  - agent: developer
    task: "Implement code based on architect's solution"
    depends_on: [architect]

  - agent: reviewer
    task: "Review code, suggest improvements"
    depends_on: [developer]
```

---

## Use Cases

### Scenario 1: Daily Development Assistance

```
User: Write a Python function to parse a CSV file and calculate averages

Coder Agent:
1. Understand requirements
2. Generate code
3. Execute tests
4. Return results and code
```

### Scenario 2: Technical Research

```
User: Research the most popular frontend frameworks in 2024

Researcher Agent:
1. Search for latest information
2. Compile comparison data
3. Generate research report
```

### Scenario 3: Multi-language Translation

```
User: Translate this technical document into English

Translator Agent:
1. Read document
2. Translate paragraph by paragraph
3. Preserve formatting
4. Output translation
```

### Scenario 4: Data Analysis

```
User: Analyze this sales data and identify trends

Analyst Agent:
1. Read CSV
2. Data cleaning
3. Statistical analysis
4. Generate charts
5. Output insights
```

---

## Custom Agent

### Creating a Custom Agent

Create a new YAML file in the `presets/` directory:

```yaml
# presets/my_agent.yaml

name: my_custom_agent
display_name: My Custom Agent
description: This is a custom Agent example
model: gpt-4-turbo-preview

system_prompt: |
  You are a [specific role description].

  Skills:
  - Skill 1
  - Skill 2

  Work Principles:
  - Principle 1
  - Principle 2

tools:
  - web_search
  - python_repl

# Optional: Memory configuration
memory:
  type: conversation  # conversation / vector
  max_tokens: 4000

# Optional: Parameter configuration
parameters:
  temperature: 0.7
  max_tokens: 2000
```

### Agent Configuration Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique Agent identifier |
| `display_name` | string | Yes | Display name |
| `description` | string | Yes | Feature description |
| `model` | string | Yes | Model to use |
| `system_prompt` | string | Yes | System prompt |
| `tools` | array | No | List of enabled tools |
| `memory` | object | No | Memory configuration |
| `parameters` | object | No | Model parameters |

---

## Project Structure

```
agentforge/
|-- .env.example              # Environment variable template
|-- .env                      # Actual environment variables (not committed)
|-- docker-compose.yml        # Docker orchestration config
|-- Dockerfile.api            # API service image
|-- Dockerfile.web            # Web service image
|-- requirements.txt          # Python dependencies
|-- README.md                 # Project documentation
|
|-- presets/                  # Agent preset templates
|   |-- assistant.yaml
|   |-- coder.yaml
|   |-- researcher.yaml
|   |-- translator.yaml
|   |-- writer.yaml
|   |-- analyst.yaml
|   +-- team/
|       |-- dev_team.yaml
|       +-- research_team.yaml
|
|-- backend/                  # Backend service
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py          # FastAPI entry point
|   |   |-- config.py        # Configuration management
|   |   |-- routers/         # API routes
|   |   |   |-- agent.py
|   |   |   |-- chat.py
|   |   |   +-- tool.py
|   |   |-- core/            # Core engine
|   |   |   |-- agent.py
|   |   |   |-- memory.py
|   |   |   |-- llm.py
|   |   |   +-- workflow.py
|   |   |-- tools/           # Tool implementations
|   |   |   |-- base.py
|   |   |   |-- search.py
|   |   |   |-- code.py
|   |   |   +-- file.py
|   |   |-- models/          # Data models
|   |   +-- utils/           # Utility functions
|   |-- tests/
|   +-- pyproject.toml
|
|-- frontend/                 # Frontend service
|   |-- src/
|   |   |-- app/             # Next.js App Router
|   |   |-- components/      # React components
|   |   |   |-- chat/
|   |   |   |-- workflow/
|   |   |   +-- common/
|   |   |-- stores/          # State management
|   |   |-- lib/             # Utility libraries
|   |   +-- types/           # TypeScript types
|   |-- public/
|   |-- package.json
|   +-- next.config.js
|
|-- data/                     # Data directory
|   |-- chroma/              # Vector database
|   +-- uploads/             # Uploaded files
|
+-- scripts/                  # Scripts
    |-- start.sh             # Linux/Mac startup
    |-- start.bat            # Windows startup
    +-- init_db.py           # Database initialization
```

---

## Roadmap

### Phase 1: Core Foundation (v0.1.0)

- [x] Project structure setup
- [x] Core Agent engine
- [x] LLM integration (LiteLLM)
- [x] Basic CLI tools
- [x] 3 preset Agents

### Phase 2: Web Interface (v0.2.0)

- [x] Next.js frontend framework
- [x] Real-time chat interface
- [x] Agent selector
- [x] Streaming response display

### Phase 3: Tool Ecosystem (v0.3.0)

- [x] Tool registration system
- [x] Code execution sandbox
- [x] Web search tool
- [x] File operation tools

### Phase 4: Multi-Agent Collaboration (v0.4.0)

- [x] Multi-Agent communication protocol
- [x] Workflow engine
- [x] Team collaboration templates
- [x] Visual orchestrator

### Phase 5: Enterprise Features (v0.5.0)

- [x] User authentication system
- [x] API Key management
- [x] Usage statistics
- [x] Audit logging

### Phase 6: Ecosystem Expansion (v1.0.0)

- [x] Plugin system
- [x] Template marketplace
- [x] Cloud deployment solution
- [ ] Mobile adaptation

### Phase 1 (Improvement Plan): Data Persistence

- [x] Alembic database migration (7 tables)
- [x] Conversation and message persistence
- [x] Usage statistics recording after LLM calls
- [x] Audit log recording for auth, API key, and agent endpoints
- [x] Database initialization on app startup
- [x] Transaction management fix (routers control their own commits)
- [x] Unit and integration tests for persistence layer
- [x] Frontend API client for conversation CRUD operations

### Phase 2 (Improvement Plan): Security and Production Hardening

- [x] SlowAPI rate limiting integration
- [x] CORS whitelist replacing wildcard
- [x] Provider-level API key format validation
- [x] Authentication on Usage/Plugin/Marketplace routes
- [x] Feature flags (code execution, web search, file ops)
- [x] Full memory system (short-term sliding window + ChromaDB long-term vectors)
- [x] Docker multi-stage builds + Gunicorn production deployment
- [x] Docker Compose service health checks
- [x] K8s Secret security hardening
- [x] Frontend auth token interceptors + persistent chat sessions
- [x] 6 core module test suites + shared fixtures
- [x] DB index migration optimization

---

## Contributing Guide

We welcome all forms of contributions!

### How to Contribute

- Submit bug reports
- Suggest new features
- Improve documentation
- Submit code pull requests
- Star the project

### Development Guide

```bash
# 1. Fork and Clone
git clone https://github.com/WeiGuang-2099/AgentForge.git

# 2. Create a branch
git checkout -b feature/your-feature

# 3. Install development dependencies
make install-dev

# 4. Run tests
make test

# 5. Commit code
git commit -m "feat: add your feature"
git push origin feature/your-feature

# 6. Create a Pull Request
```

### Code Standards

- Python: Follow PEP 8, use Black for formatting
- TypeScript: Use ESLint + Prettier
- Commit messages: Follow Conventional Commits

---

## License

This project is licensed under the [MIT License](./LICENSE).

---

## Acknowledgments

Inspired by the following open-source projects:

- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [AutoGen](https://github.com/microsoft/autogen) - Multi-Agent framework
- [CrewAI](https://github.com/joaomdmoura/crewAI) - Agent collaboration framework
- [ChatGPT-Next-Web](https://github.com/ChatGPTNextWeb/ChatGPT-Next-Web) - Web interface reference

---

<div align="center">

**If this project helps you, please give it a Star!**

Made by AgentForge Team

</div>
