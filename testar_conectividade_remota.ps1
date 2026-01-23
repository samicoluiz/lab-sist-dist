# Script para testar conectividade com os nós e bancos de dados
# Pode ser executado de outra máquina na rede

param(
    [Parameter(Mandatory=$true)]
    [string]$TargetIP
)

Write-Host "Testando conectividade com $TargetIP..." -ForegroundColor Cyan

# Testar portas MySQL
Write-Host "`n=== Testando Bancos MySQL ===" -ForegroundColor Yellow
@(3307, 3308, 3309) | ForEach-Object {
    $port = $_
    $result = Test-NetConnection -ComputerName $TargetIP -Port $port -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        Write-Host "✓ MySQL porta $port : ACESSÍVEL" -ForegroundColor Green
    } else {
        Write-Host "✗ MySQL porta $port : FALHOU" -ForegroundColor Red
    }
}

# Testar portas dos Nós
Write-Host "`n=== Testando Nós ===" -ForegroundColor Yellow
@(5000, 5001, 5002) | ForEach-Object {
    $port = $_
    $result = Test-NetConnection -ComputerName $TargetIP -Port $port -WarningAction SilentlyContinue
    if ($result.TcpTestSucceeded) {
        Write-Host "✓ Nó porta $port : ACESSÍVEL" -ForegroundColor Green
    } else {
        Write-Host "✗ Nó porta $port : FALHOU" -ForegroundColor Red
    }
}

Write-Host "`n=== Teste concluído ===" -ForegroundColor Cyan
