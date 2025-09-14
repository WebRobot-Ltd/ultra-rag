# UltraRAG Production Docker Image
FROM nvidia/cuda:12.2.2-base-ubuntu22.04

# Metadata
LABEL maintainer="WebRobot Ltd"
LABEL description="UltraRAG v2.0 - Advanced RAG Framework with MCP Support"
LABEL version="2.0"

# Environment variables
ENV PATH="/opt/miniconda/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bzip2 \
        ca-certificates \
        curl \
        git \
        wget \
        netcat \
        build-essential \
        && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ultrarag && useradd -r -g ultrarag ultrarag

# Setup work directory
WORKDIR /ultrarag

# Setup Miniconda
WORKDIR /opt
ADD https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh /opt/miniconda.sh

# Copy project files
WORKDIR /ultrarag
COPY . .

# Install Miniconda
RUN chmod +x /opt/miniconda.sh && \
    /opt/miniconda.sh -b -p /opt/miniconda && \
    rm -f /opt/miniconda.sh

# Configure conda and create environment
RUN conda --version && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

RUN conda env create -f environment.yml

# Activate environment and install dependencies
ENV PATH="/opt/miniconda/envs/ultrarag/bin:$PATH"
RUN python -m ensurepip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir -r auth/requirements.txt

# Create directories for config and data
RUN mkdir -p /app/config /app/data /app/logs && \
    chown -R ultrarag:ultrarag /app /ultrarag

# Copy production configuration and health check
COPY --chown=ultrarag:ultrarag examples/rag.yaml /app/config/production.yaml
COPY --chown=ultrarag:ultrarag health_check.py /app/health_check.py
RUN chmod +x /app/health_check.py

# Switch to non-root user
USER ultrarag

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/health_check.py || exit 1

# Default command with production config
CMD ["ultrarag", "run", "/app/config/production.yaml"]