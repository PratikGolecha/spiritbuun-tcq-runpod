FROM nvidia/cuda:12.4.0-devel-ubuntu22.04 AS builder

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    python3 \
    python3-pip \
    ccache \
    libssl-dev \
    libgomp1 \
    libcurl4-openssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN cmake --version && nvcc --version

RUN git clone --depth 1 \
    https://github.com/spiritbuun/llama-cpp-turboquant-cuda.git /tmp/llama.cpp

WORKDIR /tmp/llama.cpp

RUN --mount=type=cache,target=/ccache \
    export CCACHE_DIR=/ccache && \
    cmake -B build \
        -DGGML_CUDA=ON \
        -DGGML_CUDA_FA=ON \
        -DGGML_CUDA_FA_ALL_QUANTS=ON \
        -DCMAKE_CUDA_ARCHITECTURES="100" \
        -DLLAMA_BUILD_SERVER=ON \
        -DLLAMA_BUILD_TESTS=OFF \
        -DCMAKE_BUILD_TYPE=Release \
        -DGGML_CCACHE=ON && \
    cmake --build build --config Release -j$(nproc)

FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

WORKDIR /

RUN apt-get update && apt-get install -y \
    libgomp1 \
    libstdc++6 \
    libgcc1 \
    libssl3 \
    libcurl4 \
    ca-certificates \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /tmp/llama.cpp/build/bin/llama-server /app/
COPY --from=builder /tmp/llama.cpp/build/lib/ /app/

RUN echo "/app" > /etc/ld.so.conf.d/app.conf && \
    ldconfig && \
    chmod +x /app/llama-server && \
    (chmod +x /app/llama-cli 2>/dev/null || true)

RUN ldd /app/llama-server | grep "not found" && echo "ERROR: Missing dependencies!" && exit 1 || echo "✓ TCQ dependencies verified"

ENV LD_LIBRARY_PATH=/app:/usr/local/cuda/lib64:$LD_LIBRARY_PATH
ENV PYTHONUNBUFFERED=1

RUN apt-get update --yes --quiet && DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
    software-properties-common \
    build-essential \
    && add-apt-repository --yes ppa:deadsnakes/ppa && apt update --yes --quiet \
    && DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    python3.11-venv \
    && ln -s /usr/bin/python3.11 /usr/bin/python && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    pip install --no-cache-dir runpod && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY runpod_handler.py /app/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["python3.11", "/app/runpod_handler.py"]
