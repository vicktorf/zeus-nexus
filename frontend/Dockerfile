FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY pages_llm_setup.py .
COPY pages_agent_config.py .
COPY pages_system_settings.py .

# Create non-root user for OpenShift
RUN useradd -u 1001 -r -g 0 -d /app -s /sbin/nologin \
    -c "Streamlit user" streamlit && \
    chown -R 1001:0 /app && \
    chmod -R g=u /app

USER 1001

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
