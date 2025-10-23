# Script para construir la imagen Docker del Agente Claude
# Nombre: alberth121484/anthropic-py:01.000.01

Write-Host "🚀 Construyendo imagen Docker del Agente Claude..." -ForegroundColor Green
Write-Host "Nombre de la imagen: alberth121484/anthropic-py:01.000.01" -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker esté instalado
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker encontrado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está instalado. Por favor instala Docker primero." -ForegroundColor Red
    exit 1
}

# Verificar que el Dockerfile exista
if (-not (Test-Path "Dockerfile")) {
    Write-Host "❌ No se encontró el archivo Dockerfile en el directorio actual." -ForegroundColor Red
    exit 1
}

# Construir la imagen
Write-Host "📦 Construyendo imagen..." -ForegroundColor Yellow
$buildResult = docker build -t alberth121484/anthropic-py:01.000.01 .

# Verificar si la construcción fue exitosa
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Imagen construida exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Detalles de la imagen:" -ForegroundColor Cyan
    docker images alberth121484/anthropic-py:01.000.01
    Write-Host ""
    Write-Host "🎯 Para subir la imagen a Docker Hub:" -ForegroundColor Yellow
    Write-Host "docker push alberth121484/anthropic-py:01.000.01" -ForegroundColor White
    Write-Host ""
    Write-Host "🔧 Para ejecutar localmente:" -ForegroundColor Yellow
    Write-Host "docker run -d --name claude-agent --env-file .env alberth121484/anthropic-py:01.000.01" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Error al construir la imagen." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🎉 Proceso completado!" -ForegroundColor Green