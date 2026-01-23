Write-Host "=== Diagnóstico de Conectividade WSL/Docker ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. IP da rede local do Windows:" -ForegroundColor Yellow
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' -or $_.IPAddress -like '10.*' } | Select-Object -First 1).IPAddress
Write-Host "   $windowsIP" -ForegroundColor Green

Write-Host "`n2. IP do WSL:" -ForegroundColor Yellow
$wslIP = (wsl bash -c "ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v 127.0.0.1 | grep -v 172")
Write-Host "   $wslIP" -ForegroundColor Green

Write-Host "`n3. IPs dos containers Docker:" -ForegroundColor Yellow
wsl docker ps --format '{{.Names}}' | ForEach-Object {
    $containerIP = wsl docker inspect $_ --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
    Write-Host "   ${_}: $containerIP" -ForegroundColor Green
}

Write-Host "`n4. Portas em escuta no WSL:" -ForegroundColor Yellow
wsl bash -c "netstat -tlnp 2>/dev/null | grep -E ':(3307|3308|3309|5000|5001|5002)' | awk '{print \$4}'"

Write-Host "`n5. Regras de Port Forwarding do Windows:" -ForegroundColor Yellow
netsh interface portproxy show all | Select-String "3307|3308|3309|5000|5001|5002"

Write-Host "`n6. Portas em escuta no Windows:" -ForegroundColor Yellow
netstat -ano | Select-String ":(3307|3308|3309|5000|5001|5002)" | Select-String "LISTENING"

Write-Host "`n7. Testando MySQL dentro do WSL:" -ForegroundColor Yellow
wsl bash -c "nc -zv 127.0.0.1 3309 2>&1 | head -1"

Write-Host "`n8. Status do serviço IP Helper:" -ForegroundColor Yellow
Get-Service iphlpsvc | Format-Table Status, Name, DisplayName -AutoSize

Write-Host "`n=== RESUMO ===" -ForegroundColor Magenta
Write-Host "Para outras máquinas acessarem, use:" -ForegroundColor White
Write-Host "  IP: $windowsIP" -ForegroundColor Cyan
Write-Host "  Portas: 3307, 3308, 3309 (MySQL), 5000, 5001, 5002 (Nodes)" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANTE: Se o port forwarding não funcionar, pode ser:" -ForegroundColor Yellow
Write-Host "  1. Firewall do Windows bloqueando" -ForegroundColor Gray
Write-Host "  2. VPN interferindo no roteamento" -ForegroundColor Gray
Write-Host "  3. Serviço IP Helper não iniciado (precisa admin)" -ForegroundColor Gray
Write-Host "  4. WSL2 usando modo 'mirrored' - verifique .wslconfig" -ForegroundColor Gray
