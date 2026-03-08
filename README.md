# HPTraffic Scaffold

Python 单体项目脚手架，包含：
- FastAPI (`/app/api`)
- Celery Worker + Beat (`/app/workers`)
- Redis + Postgres (Docker Compose)
- SQLAlchemy + Alembic (`/app/models`, `/migrations`)
- pytest (`/tests`)

## 快速开始

1. 复制环境变量：
   ```bash
   cp .env.example .env
   ```
2. 启动开发环境：
   ```bash
   make dev
   ```
3. 运行测试：
   ```bash
   make test
   ```
4. 代码检查：
   ```bash
   make lint
   ```

API 健康检查：`GET /healthz`
