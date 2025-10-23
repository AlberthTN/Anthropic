#!/bin/bash

# Script para construir la imagen Docker del Agente Claude
# Nombre: alberth121484/anthropic-py:01.000.01

echo "🚀 Construyendo imagen Docker del Agente Claude..."
echo "Nombre de la imagen: alberth121484/anthropic-py:01.000.01"
echo ""

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

# Verificar que el Dockerfile exista
if [ ! -f "Dockerfile" ]; then
    echo "❌ No se encontró el archivo Dockerfile en el directorio actual."
    exit 1
fi

# Construir la imagen
echo "📦 Construyendo imagen..."
docker build -t alberth121484/anthropic-py:01.000.01 .

# Verificar si la construcción fue exitosa
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Imagen construida exitosamente!"
    echo ""
    echo "📋 Detalles de la imagen:"
    docker images alberth121484/anthropic-py:01.000.01
    echo ""
    echo "🎯 Para subir la imagen a Docker Hub:"
    echo "docker push alberth121484/anthropic-py:01.000.01"
    echo ""
    echo "🔧 Para ejecutar localmente:"
    echo "docker run -d --name claude-agent --env-file .env alberth121484/anthropic-py:01.000.01"
else
    echo ""
    echo "❌ Error al construir la imagen."
    exit 1
fi