# Script para atualizar port forwarding do WSL2
# EXECUTE COMO ADMINISTRADOR (botão direito -> Executar como Administrador)

Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host "CONFIGURANDO PORT FORWARDING WSL2 -> WINDOWS" -ForegroundColor Yellow
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host ""

# Obtém o IP do WSL2 dinamicamente
$wslIP = (wsl hostname -I).Trim().Split()[0]
Write-Host "[1/4] IP do WSL2 detectado: $wslIP" -ForegroundColor Cyan

# Obtém o IP do Windows na rede local
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*" -or 
    ($_.IPAddress -like "172.*" -and $_.IPAddress -notlike "172.20.*") 
} | Select-Object -First 1).IPAddress
Write-Host "[2/4] IP do Windows na rede: $windowsIP" -ForegroundColor Cyan
Write-Host ""

# Portas a serem configuradas
$ports = @(3307, 3308, 3309, 5000, 5001, 5002)

Write-Host "[3/4] Configurando port forwarding..." -ForegroundColor Yellow

foreach ($port in $ports) {
    # Remove regra existente
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null | Out-Null
    
    # Adiciona nova regra
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP | Out-Null
    
    # Configura firewall
    $ruleName = "WSL2 Port $port"
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -LocalPort $port -Protocol TCP -Action Allow -ErrorAction SilentlyContinue | Out-Null
    
    Write-Host "  [OK] Porta $port - Windows -> WSL" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/4] Verificando configuração..." -ForegroundColor Yellow
netsh interface portproxy show all

Write-Host ""
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host "[OK] PORT FORWARDING CONFIGURADO COM SUCESSO!" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "Outras maquinas podem conectar usando:" -ForegroundColor Yellow
Write-Host "  IP do Windows: $windowsIP" -ForegroundColor Cyan
Write-Host ""
Write-Host "  MySQL Databases:" -ForegroundColor White
Write-Host "    - db2: ${windowsIP}:3307" -ForegroundColor Cyan
Write-Host "    - db3: ${windowsIP}:3308" -ForegroundColor Cyan
Write-Host "    - db1: ${windowsIP}:3309" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Middleware Nodes:" -ForegroundColor White
Write-Host "    - Node 0: ${windowsIP}:5000" -ForegroundColor Cyan
Write-Host "    - Node 1: ${windowsIP}:5001" -ForegroundColor Cyan
Write-Host "    - Node 2: ${windowsIP}:5002" -ForegroundColor Cyan
Write-Host ""
Write-Host "===========================================================" -ForegroundColor Magenta
Write-Host ""
