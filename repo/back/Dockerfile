FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema necesarias para psycopg2 y bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python primero (aprovecha la cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Carpeta donde se guardan los documentos subidos (por si no existe)
RUN mkdir -p /app/archivos_documentos

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
