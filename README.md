# 企业健康度智能诊断平台

> Enterprise Health Diagnosis Platform

## 项目简介

企业健康度智能诊断平台是一个智能化的企业诊断自动化系统，旨在帮助企业快速完成健康度评估和诊断报告生成。

### 核心功能

- 📊 **企业数据管理**：管理 4,492 家 A 股上市公司数据
- 💰 **财务数据导入**：自动化批量导入企业财务数据（覆盖率 91.9%）
- 🏢 **企业详情展示**：展示企业基本信息、注册信息、联系方式、经营信息
- ✏️ **企业数据编辑**：支持所有字段的编辑、暂存、保存
- 🔐 **权限控制**：管理员和普通用户的权限分离
- 🤖 **AI 智能分析**：支持多种大模型提供商，自动生成企业健康度诊断报告

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3.11 + FastAPI |
| 前端 | React 18 + TypeScript + Vite |
| UI 库 | Ant Design 5.x |
| 数据库 | PostgreSQL 15 |
| 缓存 | Redis 7 |
| 图表 | ECharts 5.x |
| 部署 | Docker Compose |

## 项目结构

```
ENT_Health_Report-kimi2.5/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic Schemas
│   │   ├── services/          # 业务逻辑
│   │   └── scripts/           # 脚本
│   └── tests/                 # 测试
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # 可复用组件
│   │   ├── pages/             # 页面组件
│   │   ├── hooks/             # 自定义 Hooks
│   │   ├── lib/               # 工具函数
│   │   └── types/             # TypeScript 类型
│   └── package.json
│
├── docker-compose.yml          # Docker 编排
└── .sisyphus/                 # 开发文档
    ├── plans/                 # 开发计划
    └── 开发日志_2026-0318.md  # 开发日志
```

## 快速开始

### 环境要求

- Docker Desktop
- Node.js 18+ (本地开发)
- Python 3.11+ (本地开发)

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 访问地址

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3005 |
| 后端 API 文档 | http://localhost:8005/docs |
| 健康检查 | http://localhost:8005/health |

### 默认账号

- 管理员：`admin@example.com` / `admin123`

## 开发指南

### 后端开发

```bash
# 进入后端容器
docker-compose exec backend-kimi bash

# 运行开发服务器
uvicorn app.main:app --reload

# 运行测试
pytest

# 代码格式化
black app/
ruff check app/
```

### 前端开发

```bash
# 进入前端容器
docker-compose exec frontend-kimi sh

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 代码检查
npm run lint
```

### 数据库操作

```bash
# 进入 PostgreSQL
docker-compose exec postgres-kimi psql -U health_user -d health_db_kimi

# 查看企业数量
SELECT COUNT(*) FROM enterprises;

# 查看财务数据统计
SELECT 
    COUNT(*) as total,
    COUNT(legal_representative) as with_info
FROM enterprises;
```

## API 端点

### 认证

```
POST /api/auth/login     - 用户登录
POST /api/auth/logout    - 用户登出
GET  /api/auth/me        - 获取当前用户
```

### 企业管理

```
GET    /api/enterprises              - 企业列表
GET    /api/enterprises/{id}         - 企业详情
GET    /api/enterprises/{id}/detail  - 企业完整信息
POST   /api/enterprises              - 创建企业
PUT    /api/enterprises/{id}         - 更新企业
DELETE /api/enterprises/{id}         - 删除企业（仅管理员）
```

### 财务数据

```
GET /api/financials/enterprises/summary    - 企业财务概要
GET /api/financials/enterprises/{id}       - 企业财务详情
GET /api/financials/stats                  - 全局统计
GET /api/financials/enterprises/{id}/status - 数据状态
POST /api/financials/enterprises/{id}/refresh - 更新财务数据
GET /api/financials/batch-refresh/status   - 批量更新状态
POST /api/financials/batch-refresh/start   - 启动批量更新
POST /api/financials/batch-refresh/stop    - 停止批量更新
POST /api/financials/export                - 批量导出Excel
```

### AI 配置管理（管理员）

```
GET    /api/ai-configs              - AI 配置列表
GET    /api/ai-configs/{id}         - 配置详情
POST   /api/ai-configs              - 创建配置（需管理员权限）
PUT    /api/ai-configs/{id}         - 更新配置（需管理员权限）
DELETE /api/ai-configs/{id}         - 删除配置（需管理员权限）
POST   /api/ai-configs/{id}/activate - 激活配置
```

### 报告生成

```
POST   /api/reports/generate                    - 启动报告生成
GET    /api/reports/{task_id}/status            - 查询任务状态
GET    /api/reports/{task_id}/download          - 下载报告
GET    /api/reports                             - 报告列表
GET    /api/reports/{report_id}                 - 报告详情
DELETE /api/reports/{task_id}                   - 取消/删除任务
GET    /api/reports/enterprises/{id}/summary    - 企业报告摘要
```

## AI 智能分析

### 支持的 AI 提供商

平台支持以下 8 种大模型提供商：

| 提供商 | 标识符 | 默认 API 地址 | 说明 |
|--------|--------|---------------|------|
| OpenAI | `openai` | https://api.openai.com/v1 | GPT-4、GPT-3.5 等 |
| DeepSeek | `deepseek` | https://api.deepseek.com/v1 | DeepSeek Chat、Coder 等 |
| 通义千问 | `qwen` | https://dashscope.aliyuncs.com/compatible-mode/v1 | 阿里云 Qwen 系列 |
| Kimi | `kimi` | https://api.moonshot.cn/v1 | Moonshot AI |
| MiniMax | `minimax` | https://api.minimax.chat/v1 | MiniMax 模型 |
| Gemini | `gemini` | Google AI API | Google Gemini 系列 |
| 智谱 GLM | `glm` | https://open.bigmodel.cn/api/paas/v4 | ChatGLM 系列 |
| OpenAI 兼容 | `openai-compatible` | 自定义 | 任何兼容 OpenAI API 的服务 |

### 配置 AI 提供商

1. 管理员登录系统
2. 进入「系统设置」→「AI 配置」
3. 添加新配置：
   - 配置名称：如 "DeepSeek-生产"
   - 选择提供商：deepseek
   - 输入 API Key
   - 选择模型：如 deepseek-chat
   - 设置默认配置
4. 点击「激活」启用配置

### 生成企业健康报告

```bash
# 通过 API 生成报告
curl -X POST http://localhost:8005/api/reports/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "enterprise_id": 1,
    "report_type": "full_diagnosis",
    "report_years": "2021-2023",
    "include_peer_comparison": true,
    "peer_count": 5
  }'

# 查询报告生成状态
curl http://localhost:8005/api/reports/{task_id}/status \
  -H "Authorization: Bearer <token>"
```

### 报告类型

| 类型 | 标识符 | 说明 |
|------|--------|------|
| 完整诊断报告 | `full_diagnosis` | 包含财务分析、风险评估、健康度评分 |
| 快速诊断报告 | `quick_diagnosis` | 核心指标分析，适合快速了解企业状况 |
| 财务分析报告 | `financial_analysis` | 专注财务指标分析 |
| 风险评估报告 | `risk_assessment` | 侧重风险识别与评估 |

## 数据统计

### 企业数据

| 指标 | 数值 |
|------|------|
| 总企业数 | 4,492 |
| 有详细信息 | 4,309 (95.9%) |

### 财务数据

| 指标 | 数值 |
|------|------|
| 有财务数据企业 | 4,126 (91.9%) |
| 资产负债表记录 | 16,511 |
| 利润表记录 | 16,496 |
| 现金流量表记录 | 16,504 |
| **总记录数** | **49,511** |

## 开发阶段

| 阶段 | 描述 | 状态 |
|------|------|------|
| Phase 0 | 基础设施搭建 | ✅ 已完成 |
| Phase 1 | 核心框架开发 | ✅ 已完成 |
| Phase 2 | 企业数据管理 | ✅ 已完成 |
| Phase 3 | 指标计算引擎 | ✅ 已完成 |
| Phase 4 | AI 报告生成 | ✅ 已完成 |
| Phase 5 | 历史数据与优化 | ⏳ 待开发 |

## 最近更新

### v3.0 (2026-03-20)

- 🤖 **AI 智能分析**：集成 8 种大模型提供商，支持企业健康度诊断报告自动生成
- 🔧 AI 配置管理：支持多配置、配置切换、审计日志
- 📊 报告生成 API：异步任务、进度追踪、报告下载
- 🔐 API Key 加密存储，敏感信息安全保护

### v2.3 (2026-03-20)

- ✨ 一键批量更新：后台更新所有企业财务数据，实时进度显示
- 📊 批量导出 Excel：多选企业、选择年份、导出三大报表
- 🛠️ 新增批量更新状态 API、停止更新 API、导出 API

### v2.2 (2026-03-20)

- ✨ 企业编辑功能：支持所有字段编辑、暂存、保存
- 🔐 删除权限控制：仅管理员可删除企业
- 📝 更新 README.md

### v2.1 (2026-03-19)

- ✨ 企业详细信息获取（覆盖率 95.9%）
- 🏢 企业详情页面开发

### v2.0 (2026-03-19)

- ✨ 财务数据批量导入（覆盖率 91.9%）
- 📊 财务数据查询界面
- 🔧 解决 Sina API 对沪市不可用问题

## 相关文档

- [开发计划（分层迭代版）](.sisyphus/plans/开发计划%20-%20分层迭代版.md)
- [开发日志](.sisyphus/开发日志_2026-0318.md)
- [AGENTS.md](AGENTS.md) - 开发命令参考

## License

MIT