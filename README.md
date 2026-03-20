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
| Phase 3 | 指标计算引擎 | ⏳ 待开发 |
| Phase 4 | AI 报告生成 | ⏳ 待开发 |
| Phase 5 | 历史数据与优化 | ⏳ 待开发 |

## 最近更新

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