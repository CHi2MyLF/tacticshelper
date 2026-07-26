# ⚽ FM2024 战术顾问 (AI Tactical Advisor)

基于 AI 的 Football Manager 2024 战术顾问。导入球队数据，与 AI 教练对话，获得量身定制的战术方案。

## 功能

- 💬 **对话式交互** — 像和真人教练聊天一样讨论战术，AI 记住上下文和偏好
- 📊 **阵容诊断** — 自动分析球队优劣势、隐藏问题、阵容深度
- 🎯 **战术生成** — DWRS 评分算法 + FM-Arena 经验系数 → 阵型推荐 → 角色分配 → 球队/个人指令
- 🔄 **轮换方案** — 每位置提供替代人选和轮换建议
- 🛡️ **对手分析** — 录入对手信息，生成针对性调整方案
- 📚 **RAG 知识库** — 14 篇中文 FM 攻略（战术、训练、转会、定位球、比赛管理）
- 🔍 **语义球员搜索** — "找一个像哈维的中场"
- 💾 **数据持久化** — 一次导入，反复使用，战术自动保存

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- LLM API Key（DeepSeek / Anthropic / OpenAI 任选其一）

### 一键启动

```bash
# Windows
双击 run.bat

# Mac/Linux
python run.py
```

### 手动启动

```bash
# 1. 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. 启动后端
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 3. 启动前端
cd frontend && npm run dev

# 4. 打开 http://localhost:5173
```

## 使用指南

### 1. 设置 API

首次启动弹出设置窗口。支持三种 LLM：

| 预设 | 默认模型 |
|------|---------|
| DeepSeek | `deepseek-chat` |
| Anthropic | `claude-sonnet-4-20250514` |
| OpenAI | `gpt-4o` |

支持自定义 API 中转地址和模型名。

### 2. 导入阵容数据（任选一种）

| 方式 | 来源 | 操作 |
|------|------|------|
| 📊 JSON | FMRTE 导出 | 直接上传 |
| 🌐 HTML | FM24 游戏内 | Squad → Ctrl+A → Ctrl+P → Web Page → 上传 |
| 📄 CSV | FMRTE 导出 | 上传 |
| 📋 粘贴 | FMRTE / FM24 | Ctrl+A → Ctrl+C → 粘贴 |
| 🧪 示例 | 内置巴萨数据 | 一键加载 |

> **推荐**：FM24 游戏中 Squad 页自定义视图（加全属性列）→ Ctrl+A → Ctrl+P → Web Page → 上传 .html

### 3. 开始对话

```
"帮我分析一下阵容"
"设计一套高压逼抢的 433 战术"
"我的阵容适合打什么风格？"
"下轮对手是利物浦，怎么打？"
"我有 3000 万预算，应该买什么位置的球员？"
```

### 4. 查看结果

- 左侧边栏查看**阵容详情**和**战术历史**

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python / FastAPI / SQLite / ChromaDB |
| 前端 | React / TypeScript / Vite |
| AI | DeepSeek / Anthropic / OpenAI 多 Provider |
| 评分引擎 | DWRS 算法 + FM-Arena 位置系数 + 190+ 角色定义 |
| RAG | ChromaDB 向量存储 + 嵌入检索 |

## 项目结构

```
fm-tactical-advisor/
├── backend/
│   ├── agent/          # AI Agent（系统提示词、上下文、工具注册）
│   ├── tools/          # 战术工具（评分、诊断、阵型、指令、深度、对手）
│   ├── importers/      # 数据导入（FMRTE JSON/CSV、FM24 HTML、剪贴板）
│   ├── rag/            # RAG 模块（嵌入、向量存储、知识检索、球员索引）
│   ├── api/            # REST API
│   └── data/           # 静态知识库（角色、阵型、系数、风格）
├── data/knowledge/     # RAG 知识文档（14 篇 FM 攻略）
├── frontend/
│   └── src/
│       ├── components/ # 对话/面板/共享 UI 组件
│       └── api/        # API 调用封装
├── run.bat             # 一键启动
└── requirements.txt
```

## 扩展计划

- [ ] 转会建议：阵容缺口 + 预算 → 推荐引援
- [ ] 训练建议：战术体系 → 训练重点
- [ ] 球员发展：追踪属性增长
- [ ] 比赛复盘：导入比赛统计
- [ ] 多人存档：管理多个球队

## 更新日志

### v1.0 (2026-07-26)

- 💬 多 Provider AI 对话：DeepSeek / Anthropic / OpenAI
- 📊 阵容诊断 + DWRS 球员评分 + 阵型推荐 + 角色分配 + 球队指令生成
- 📚 RAG 知识库：14 篇中文 FM 攻略（战术、训练、转会、定位球、比赛管理）
- 🔍 语义球员搜索
- 📥 数据导入：FMRTE JSON/CSV、FM24 HTML 导出、剪贴板粘贴、示例数据
- 🎨 FM 风格暗绿主题 UI
- 🗄️ SQLite 持久化：一次导入反复使用，战术历史自动保存

## 许可

MIT License
