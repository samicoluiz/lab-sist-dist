# Script para configurar port forwarding e firewall para as portas dos nós
# Execute como Administrador

Write-Host "Configurando port forwarding para as portas dos nós..." -ForegroundColor Cyan

# Port forwarding das portas dos nós (5000-5002)
netsh interface portproxy add v4tov4 listenport=5000 listenaddress=0.0.0.0 connectport=5000 connectaddress=10.255.255.254
netsh interface portproxy add v4tov4 listenport=5001 listenaddress=0.0.0.0 connectport=5001 connectaddress=10.255.255.254
netsh interface portproxy add v4tov4 listenport=5002 listenaddress=0.0.0.0 connectport=5002 connectaddress=10.255.255.254

Write-Host "Configurando regras de firewall..." -ForegroundColor Cyan

# Regras de firewall para as portas dos nós
New-NetFirewallRule -DisplayName "Nó 0 - Porta 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Nó 1 - Porta 5001" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Nó 2 - Porta 5002" -Direction Inbound -LocalPort 5002 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue

Write-Host "`nVerificando port forwarding configurado:" -ForegroundColor Green
netsh interface portproxy show all

Write-Host "`nConfiguração concluída!" -ForegroundColor Green
Write-Host "Agora as portas 5000-5002 estão acessíveis externamente via 192.168.15.6" -ForegroundColor Yellow
