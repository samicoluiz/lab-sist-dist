# Testa se portas alternativas (8080, 8081) funcionam
# EXECUTE COMO ADMINISTRADOR

$wslIP = (wsl hostname -I).Trim().Split()[0]
$portasAlt = @(8080, 8081, 8082)

Write-Host "Configurando port forwarding para portas alternativas..." -ForegroundColor Yellow
Write-Host "WSL IP: $wslIP" -ForegroundColor Cyan
Write-Host ""

foreach ($port in $portasAlt) {
    Write-Host "Porta $port..." -ForegroundColor Gray
    
    # Remove antigas
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null | Out-Null
    
    # Mapeia porta Windows -> WSL (ajusta mapeamento)
    $wslPort = 5000 + ($port - 8080)  # 8080->5000, 8081->5001, 8082->5002
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$wslPort connectaddress=$wslIP | Out-Null
    
    Write-Host "  [OK] Windows:$port -> WSL:$wslPort" -ForegroundColor Green
}

Write-Host ""
Write-Host "Port forwarding configurado:" -ForegroundColor Yellow
netsh interface portproxy show all | Select-String "8080|8081|8082"

Write-Host ""
Write-Host "Agora teste da outra máquina:" -ForegroundColor Cyan
Write-Host '  Test-NetConnection -ComputerName 192.168.15.6 -Port 8081' -ForegroundColor White
