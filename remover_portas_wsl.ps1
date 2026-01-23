# Script para remover port forwarding do WSL2
# Execute como Administrador

Write-Host "Removendo port forwarding do WSL2..." -ForegroundColor Yellow

# Portas dos bancos de dados MySQL
$mysqlPorts = @(3307, 3308, 3309)

# Portas dos nós do middleware
$nodePorts = @(5000, 5001, 5002)

foreach ($port in $mysqlPorts) {
    Write-Host "Removendo porta $port..." -ForegroundColor Gray
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
    Remove-NetFirewallRule -DisplayName "WSL2 MySQL Port $port" -ErrorAction SilentlyContinue
}

foreach ($port in $nodePorts) {
    Write-Host "Removendo porta $port..." -ForegroundColor Gray
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
    Remove-NetFirewallRule -DisplayName "WSL2 Node Port $port" -ErrorAction SilentlyContinue
}

Write-Host "`nPort forwarding removido!" -ForegroundColor Green
Write-Host "`nRegras de port forwarding restantes:" -ForegroundColor Cyan
netsh interface portproxy show all
