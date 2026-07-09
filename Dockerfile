# 多阶段构建：Node 前端 + Python 后端
FROM node:18-alpine AS frontend
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# 保持与原项目相同的目录结构
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目（保持原结构）
COPY backend/ ./backend/
COPY --from=frontend /src/frontend/dist ./frontend/dist
COPY algorithm/ ./algorithm/

# SQLite 可写
RUN mkdir -p /app/backend/instance && chmod 777 /app/backend/instance
RUN mkdir -p /app/algorithm/data/raw

ENV FLASK_ENV=production
EXPOSE 5000
WORKDIR /app/backend
CMD ["python", "-m", "flask", "--app", "run.py", "run", "--host=0.0.0.0", "--port=5000"]
