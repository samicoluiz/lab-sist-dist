# Script para corrigir port forwarding das portas MySQL
# Execute como Administrador

Write-Host "Corrigindo port forwarding das portas MySQL..." -ForegroundColor Yellow

# Obter o IP correto do WSL (mesmo da porta 5002 que funciona)
$wslIP = "10.255.255.254"
Write-Host "IP do WSL: $wslIP" -ForegroundColor Cyan

# Portas MySQL que precisam ser corrigidas
$mysqlPorts = @(3307, 3308, 3309)

# Portas dos nós do middleware
$nodePorts = @(5000, 5001)

Write-Host "`nRemovendo regras antigas das portas MySQL..." -ForegroundColor Gray
foreach ($port in $mysqlPorts) {
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0
    Write-Host "  Regra antiga da porta $port removida" -ForegroundColor Gray
}

Write-Host "`nCriando novas regras com o IP correto..." -ForegroundColor Green
foreach ($port in $mysqlPorts) {
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP
    Write-Host "  ✓ Porta $port -> $wslIP configurada" -ForegroundColor Green
}

Write-Host "`nConfigurando portas dos nós do middleware..." -ForegroundColor Yellow
foreach ($port in $nodePorts) {
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>$null
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=0.0.0.0 connectport=$port connectaddress=$wslIP
    Write-Host "  ✓ Porta $port -> $wslIP configurada" -ForegroundColor Green
}

Write-Host "`n===========================================================" -ForegroundColor Magenta
Write-Host "Regras de port forwarding atualizadas:" -ForegroundColor Cyan
netsh interface portproxy show all | Select-String "3307|3308|3309|5000|5001|5002"
Write-Host "===========================================================" -ForegroundColor Magenta

Write-Host "`nTestar conexoes com: .\testar_conexao.ps1" -ForegroundColor Yellow
