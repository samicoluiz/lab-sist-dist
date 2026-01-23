# Reinicia o servico de port forwarding e recria as regras
# DEVE SER EXECUTADO COMO ADMINISTRADOR

Write-Host "Reiniciando port forwarding..." -ForegroundColor Yellow

# Para o servico
Write-Host "Parando IP Helper Service..." -ForegroundColor Gray
Stop-Service iphlpsvc -Force -ErrorAction SilentlyContinue

# Aguarda 2 segundos
Start-Sleep -Seconds 2

# Inicia o servico
Write-Host "Iniciando IP Helper Service..." -ForegroundColor Gray
Start-Service iphlpsvc

# Aguarda 2 segundos
Start-Sleep -Seconds 2

# IP do WSL
$wslIP = "10.255.255.254"

# Remove e recria as regras
Write-Host ""
Write-Host "Recriando regras de port forwarding..." -ForegroundColor Yellow

$ports = @(3307, 3308, 3309, 5000, 5001)

foreach ($port in $ports) {
    Write-Host "Processando porta $port..." -ForegroundColor Gray
    
    # Remove regra existente
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
    
    # Aguarda um pouco
    Start-Sleep -Milliseconds 200
    
    # Adiciona nova regra
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Porta $port configurada" -ForegroundColor Green
    } else {
        Write-Host "  ERRO na porta $port" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Aguardando 3 segundos para o sistema aplicar as mudancas..." -ForegroundColor Gray
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Regras atuais:" -ForegroundColor Cyan
netsh interface portproxy show all

Write-Host ""
Write-Host "Portas em escuta no Windows:" -ForegroundColor Cyan
Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in @(3307,3308,3309,5000,5001,5002) } | Format-Table LocalAddress, LocalPort, State -AutoSize

Write-Host ""
Write-Host "Concluido! Teste com: .\testar_conexao.ps1" -ForegroundColor Green
