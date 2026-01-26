FROM python:3.11-slim
WORKDIR /app

# 의존성 설치
COPY collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사 (shared 포함)
COPY shared /app/shared
COPY collector /app

CMD ["python", "main.py"]