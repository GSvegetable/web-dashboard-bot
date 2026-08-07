FROM python:3.10-slim
RUN apt-get update && apt-get install -y libzbar0
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# ✅ 核心修复：把 main.py 改成 app.py
CMD ["python", "app.py"]
