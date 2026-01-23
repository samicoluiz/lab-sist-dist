# Script para configurar port forwarding do WSL2 para rede externa
# Execute como Administrador

Write-Host "Configurando port forwarding para WSL2..." -ForegroundColor Green

# Obtém o IP do WSL2
$wslIP = (wsl hostname -I).Trim().Split()[0]
Write-Host "IP do WSL2: $wslIP" -ForegroundColor Cyan

# Obtém o IP da interface de rede local (assumindo que é o segundo IPv4)
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or ($_.IPAddress -like "172.*" -and $_.IPAddress -notlike "172.20.*") } | Select-Object -First 1).IPAddress
Write-Host "IP do Windows na rede local: $windowsIP" -ForegroundColor Cyan

# Portas dos bancos de dados MySQL
$mysqlPorts = @(3307, 3308, 3309)

# Portas dos nós do middleware (se necessário)
$nodePorts = @(5000, 5001, 5002)

Write-Host "`nConfigurando port forwarding para MySQL..." -ForegroundColor Yellow

foreach ($port in $mysqlPorts) {
    Write-Host "Configurando porta $port..." -ForegroundColor Gray
    
    # Remove regra existente se houver
    try {
        netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
    } catch {}
    
    # Adiciona nova regra de port forwarding
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP
    
    # Configura firewall para permitir a porta
    $ruleName = "WSL2 MySQL Port $port"
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow | Out-Null
    
    Write-Host "  ✓ Porta $port configurada" -ForegroundColor Green
}

Write-Host "`nConfigurando port forwarding para nós do middleware..." -ForegroundColor Yellow

foreach ($port in $nodePorts) {
    Write-Host "Configurando porta $port..." -ForegroundColor Gray
    
    # Remove regra existente se houver
    try {
        netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
    } catch {}
    
    # Adiciona nova regra de port forwarding
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP
    
    # Configura firewall para permitir a porta
    $ruleName = "WSL2 Node Port $port"
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow | Out-Null
    
    Write-Host "  ✓ Porta $port configurada" -ForegroundColor Green
}

Write-Host "`nPort forwarding configurado com sucesso!" -ForegroundColor Green
Write-Host "`nRegras de port forwarding ativas:" -ForegroundColor Cyan
netsh interface portproxy show all

Write-Host "`n===========================================================" -ForegroundColor Magenta
Write-Host "Outras máquinas podem acessar os bancos MySQL usando:" -ForegroundColor Yellow
Write-Host "  IP: $windowsIP" -ForegroundColor Cyan
Write-Host "  Portas MySQL: 3307 (db2), 3308 (db3), 3309 (db1)" -ForegroundColor Cyan
Write-Host "  Portas Middleware: 5000 (node0), 5001 (node1), 5002 (node2)" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Magenta

Write-Host "`nPara remover as configurações, execute: .\remover_portas_wsl.ps1" -ForegroundColor Gray
