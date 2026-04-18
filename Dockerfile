# -------- Base Image --------
FROM python:3.11-slim

# -------- Environment --------
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# -------- Work Directory --------
WORKDIR /app

# -------- Install System Dependencies --------
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# -------- Copy Requirements --------
COPY requirements.txt .

# -------- Install Python Dependencies --------
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# -------- Copy Project --------
COPY . .

# -------- Expose Port --------
EXPOSE 8000

# -------- Run App --------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]