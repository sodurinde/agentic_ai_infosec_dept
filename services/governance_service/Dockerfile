# Stage 1: Build dependencies
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Final minimal runtime image
FROM python:3.11-slim as runner

WORKDIR /app

# Copy installed libraries from builder stage
COPY --from=builder /root/.local /root/.local
COPY requirements.txt .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

# Create directory for local logs (Proxmox fallback)
RUN mkdir -p /var/log/bank_infosec && chmod 777 /var/log/bank_infosec

# Copy application layers
COPY shared/ /app/shared/
COPY services/governance_service/ /app/services/governance_service/

EXPOSE 8000

# Run as non-root user for security baselines
USER 1000:1000

CMD ["uvicorn", "services.governance_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
