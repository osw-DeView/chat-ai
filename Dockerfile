FROM python:3.12-slim

WORKDIR /app

# 비루트 사용자 생성
RUN addgroup --system fastapi && adduser --system --group fastapi

# Healthcheck를 위해 curl 설치 (비루트 전환 전 설치)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 권한 변경 후 비루트 사용자로 전환
RUN chown -R fastapi:fastapi /app
USER fastapi

# 포트 노출
EXPOSE 8000

# 환경변수 설정 (필요한 환경변수는 컨테이너 실행 시 주입)
ENV PYTHONUNBUFFERED=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8000/ || exit 1

# 애플리케이션 실행
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
