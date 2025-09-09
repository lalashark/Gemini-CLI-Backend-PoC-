FROM python:3.12-slim

# 安裝 Node.js & npm（供 gemini CLI）
RUN apt-get update && apt-get install -y curl ca-certificates gnupg && \
    install -d /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && apt-get install -y nodejs && \
    npm install -g @google/gemini-cli && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Python 依賴
WORKDIR /app
COPY app/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 程式碼
COPY app /app

# 預留登入憑證掛載到 /root/.gemini
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
