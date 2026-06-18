# Tumia toleo thabiti la Python
FROM python:3.11.9-slim

# Weka folder ya kazi
WORKDIR /app

# Nakili requirements na usakinisha
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Nakili msimbo wote
COPY . .

# Weka njia ya database
ENV DATABASE_URL=sqlite:///./db/sales.db

# Fungua port
EXPOSE 10000

# Anza server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]