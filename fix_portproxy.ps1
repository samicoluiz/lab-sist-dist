# SOLUÇÃO: Reconfigura port forwarding com IP específico
# EXECUTE COMO ADMINISTRADOR

$wslIP = (wsl hostname -I).Trim().Split()[0]
$windowsIP = "192.168.15.6"

Write-Host "Reconfigurando port forwarding..." -ForegroundColor Yellow
Write-Host "  WSL IP: $wslIP" -ForegroundColor Cyan
Write-Host "  Windows IP: $windowsIP" -ForegroundColor Cyan
Write-Host ""

$ports = @(5000, 5001, 5002, 3307, 3308, 3309)

foreach ($port in $ports) {
    Write-Host "Configurando porta $port..." -ForegroundColor Gray
    
    # Remove todas as regras antigas desta porta
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null | Out-Null
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=$windowsIP 2>$null | Out-Null
    
    # Adiciona regra com 0.0.0.0 (escuta em todas as interfaces)
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP | Out-Null
    
    # Adiciona regra específica com IP do Windows também
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=$windowsIP connectport=$port connectaddress=$wslIP | Out-Null
    
    Write-Host "  [OK] Porta $port" -ForegroundColor Green
}

Write-Host ""
Write-Host "Regras configuradas:" -ForegroundColor Yellow
netsh interface portproxy show all

Write-Host ""
Write-Host "Reiniciando serviço IP Helper..." -ForegroundColor Yellow
Restart-Service iphlpsvc -Force

Write-Host ""
Write-Host "[OK] Concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "Agora teste novamente de outra máquina:" -ForegroundColor Cyan
Write-Host "  python3 test_remote_access.py" -ForegroundColor White
