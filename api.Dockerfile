# 1. 기반 이미지 설정 (Python 3.10 경량 이미지 사용)
FROM python:3.10-slim

# 2. 환경 변수 설정 (타임존, 언어 설정 등)
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul
ENV LANG=C.UTF-8
ENV PYTHONUNBUFFERED=1

# 3. 시스템 의존성 설치 및 pip 업그레이드
# - tzdata: 타임존 설정을 위해 필요
# - --no-install-recommends: 불필요한 패키지 설치 방지
# - rm -rf /var/lib/apt/lists/*: 이미지 경량화를 위해 apt 캐시 삭제
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    pip install --no-cache-dir --upgrade pip && \
    rm -rf /var/lib/apt/lists/*

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. Python 의존성 설치 (소스 코드 복사 전 실행하여 레이어 캐싱 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. 소스 코드 복사
COPY api ./api
COPY core ./core
COPY data ./data
COPY models ./models
COPY services ./services
COPY main.py .

# 7. API 서버 포트 노출 (컨테이너 내부 포트)
EXPOSE 38001

# 8. 컨테이너 시작 시 API 서버 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "38001"]