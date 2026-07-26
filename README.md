# ⚽ FM2024 战术顾问 (AI Tactical Advisor)

一个基于 AI 的 Football Manager 2024 战术顾问应用。通过对话与 AI 助理教练交流，获得基于真实球员数据的战术建议。

## 功能

- 💬 **对话式交互** — 像和真人教练聊天一样讨论战术
- 📊 **阵容诊断** — 自动分析球队优劣势和隐藏问题
- 🎯 **战术设计** — 基于阵容数据和偏好生成完整战术方案
- 🔄 **轮换方案** — 考虑阵容深度的多套轮换建议
- 🛡️ **对手分析** — 赛前针对性分析和调整建议
- 💾 **数据持久化** — 一次导入，反复使用，所有战术自动保存

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Anthropic API Key（[获取地址](https://console.anthropic.com/)）

### 一键启动

```bash
# Windows
双击 run.bat

# Mac/Linux
python run.py
```

### 手动启动

#### 1. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

#### 2. 启动后端

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 3. 启动前端

```bash
cd frontend && npm run dev
```

#### 4. 打开浏览器

访问 http://localhost:5173

## 使用指南

### 1. 设置 API Key

首次启动会自动弹出设置窗口，填入你的 Anthropic API Key。如果使用 API 中转服务，可以修改 API Base URL。

### 2. 导入阵容数据

1. 打开 FMRTE
2. 选择你的俱乐部 → 全选球员 (Ctrl+A)
3. 右键 → 导出为 CSV
4. 拖拽 CSV 文件到应用中的上传区域

> 支持中英文 FMRTE 导出的 CSV 格式

### 3. 开始对话

导入成功后就可以开始和 AI 教练对话了。试试这些：

```
"帮我分析一下阵容"
"设计一套高压逼抢的战术"
"我的阵容适合打什么风格？"
"下轮对手是利物浦，怎么打？"
"我有3000万预算，应该买什么位置的球员？"
```

### 4. 查看结果

- 左侧边栏可随时查看**阵容详情**
- **战术历史**面板可回顾之前生成的战术

## 技术栈

- **后端**: Python / FastAPI / SQLite / Anthropic Claude API
- **前端**: React / TypeScript / Vite
- **战术引擎**: DWRS 评分算法 / FM-Arena 经验系数 / 角色适配系统

## 项目结构

```
fm-tactical-advisor/
├── backend/
│   ├── agent/          # AI Agent 核心（系统提示词、上下文构建、工具注册）
│   ├── tools/          # 战术工具集（评分、诊断、阵型、指令）
│   ├── importers/      # FMRTE CSV 解析器
│   ├── api/            # REST API 路由
│   └── data/           # 静态知识库（角色、阵型、系数、风格）
├── frontend/
│   └── src/
│       ├── components/ # React UI 组件
│       └── api/        # API 调用封装
├── run.bat             # 一键启动
└── requirements.txt
```

## 扩展计划

- [ ] 转会建议：根据阵容缺口和预算推荐引援
- [ ] 训练建议：基于战术体系的训练重点
- [ ] 球员发展：追踪年轻球员的属性增长
- [ ] 比赛复盘：导入比赛统计进行分析
- [ ] 多人存档：支持管理多个球队存档

## 许可

MIT License
