# 1. 기반 이미지 설정 (CUDA 개발 환경이 포함된 NVIDIA 공식 이미지 사용)
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# 2. 환경 변수 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul

# 3. 빌드에 필요한 시스템 의존성 설치
# [수정] CURL과 CUDA Driver 의존성을 모두 한 번에 설치합니다.
RUN apt-get update && \
    apt-get install -y git cmake build-essential libcurl4-openssl-dev cuda-drivers && \
    rm -rf /var/lib/apt/lists/*

# 4. llama.cpp 소스 코드 클론
# /opt 디렉토리는 외부 소프트웨어를 설치하는 표준 위치입니다.
RUN git clone https://github.com/ggerganov/llama.cpp.git /opt/llama.cpp

# 5. 작업 디렉토리를 클론된 소스 코드로 변경
WORKDIR /opt/llama.cpp

# 6. 빌드 디렉토리 생성 및 CMake 실행 (CUDA 지원 활성화)
# 최신 버전에 맞춰 GGML_CUDA=on 사용
RUN mkdir build && \
    cd build && \
    cmake .. -DGGML_CUDA=on

# 7. 소스 코드 컴파일
# cmake --build 명령어를 사용하여 컴파일을 진행합니다.
# 이 단계는 시간이 다소 소요될 수 있습니다.
RUN cd build && \
    cmake --build . --config Release -j $(nproc)

# 8. 모델 파일을 저장할 디렉토리 생성
WORKDIR /
RUN mkdir /models

# 9. 서버가 사용할 포트 노출
EXPOSE 8001

# 10. 컨테이너의 기본 실행 명령(Entrypoint) 설정
# docker-compose.yml의 command는 이 Entrypoint에 대한 인자로 전달됩니다.
ENTRYPOINT ["/opt/llama.cpp/build/bin/llama-server"]