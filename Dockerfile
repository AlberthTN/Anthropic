# Usar imagen base de Python 3.11 slim para producción
FROM python:3.11-slim

# Establecer variables de entorno para producción
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios y establecer permisos
RUN mkdir -p logs evals/results && \
    chown -R appuser:appuser /app && \
    chmod +x main.py

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8080

# Comando por defecto
CMD ["python", "main.py"]

# Health check optimizado
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1