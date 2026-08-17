FROM python:3.9-slim
WORKDIR /workspace

COPY requirements.txt .


RUN pip install --no-cache-dir streamlit requests

COPY frontend/ ./frontend

# Expose Streamlit's default port (Render overrides this, but good for local)
EXPOSE 8501

# Start Streamlit application binding to dynamic port environment variable
CMD ["sh", "-c", "streamlit run frontend/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]