# Script para rodar o nó DIRETAMENTE no Windows (sem WSL)
# Isso elimina a necessidade de port forwarding

param(
    [int]$NodeId = 1
)

Write-Host "Iniciando Nó $NodeId DIRETAMENTE no Windows..." -ForegroundColor Yellow
Write-Host "Isso elimina problemas de port forwarding WSL" -ForegroundColor Gray
Write-Host ""

# Verificar se Python está disponível no Windows
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    Write-Host "[ERRO] Python não encontrado no Windows" -ForegroundColor Red
    Write-Host "Instale Python para Windows ou use WSL" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Python encontrado: $pythonCmd" -ForegroundColor Green

# Verificar dependências
Write-Host "Verificando dependências..." -ForegroundColor Yellow
& $pythonCmd -m pip install mysql-connector-python -q

# Rodar o nó
Write-Host ""
Write-Host "Iniciando Nó $NodeId na porta 500$NodeId..." -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Gray
Write-Host ""

& $pythonCmd node.py $NodeId config.json
