# syntax=docker/dockerfile:1
#
# Resume Generator — single-image build for Render (mirrors interview-lab).
#
# One uvicorn process serves both the JSON API (ui/backend) and the built
# React SPA (ui/frontend/dist) — SPA mount + spa_fallback in
# ui/backend/main.py. No separate nginx/container needed.
#
# Stage 1  node    — build the React SPA  -> ui/frontend/dist
# Stage 2  python  — FastAPI runtime that serves API + SPA from one process

# ---------- Stage 1: build the React SPA ----------
FROM node:22-alpine AS webui-build
WORKDIR /webui
COPY ui/frontend/package.json ui/frontend/package-lock.json ./
RUN npm ci
COPY ui/frontend/ ./
RUN npm run build

# ---------- Stage 2: FastAPI runtime ----------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install Python deps. rendercv[full] bundles typst + rendercv_fonts (needed
# by the classic sidebar layout). All pinned deps ship manylinux wheels, so
# no build tools or apt packages are required on the slim base.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App source — REPO_ROOT resolves to /app (ui/backend/main.py)
COPY resume.py resume.py
COPY profiles/ profiles/
COPY src/ src/
# Photo referenced by profiles/*.yaml (identity.photo). NOTE: gitignored on
# the repo — commit it or classic-theme renders fail on Render.
COPY assets/ assets/
# WebUI backend (the FastAPI app itself)
COPY ui/backend/ ui/backend/
# Built SPA — served from ui/frontend/dist relative to REPO_ROOT (main.py)
COPY --from=webui-build /webui/dist ui/frontend/dist

# Runtime writes: SQLite history (runs.db) + generated variants/outputs
RUN mkdir -p output variants

# Render injects $PORT (default 10000); 8000 is only the local-docker fallback.
EXPOSE 8000
CMD ["sh", "-c", "python -m uvicorn ui.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]