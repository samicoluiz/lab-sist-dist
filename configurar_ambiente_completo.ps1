# Script COMPLETO de configuração - Execute como Administrador
# Após executar, REINICIE o Windows para que o port forwarding funcione

Write-Host "=== Configuração Completa do Ambiente Multi-Máquina ===" -ForegroundColor Cyan

# 1. Port Forwarding
Write-Host "`n1. Configurando Port Forwarding..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=3307 listenaddress=0.0.0.0 connectport=3307 connectaddress=10.255.255.254
netsh interface portproxy add v4tov4 listenport=3308 listenaddress=0.0.0.0 connectport=3308 connectaddress=10.255.255.254
netsh interface portproxy add v4tov4 listenport=3309 listenaddress=0.0.0.0 connectport=3309 connectaddress=10.255.255.254
netsh interface portproxy add v4tov4 listenport=5000 listenaddress=0.0.0.0 connectport=5000 connectaddress=10.255.255.254
netsh interface portproxy add v4tov4 listenport=5001 listenaddress=0.0.0.0 connectport=5001 connectaddress=10.255.255.254
netsh interface portproxy add v4tov4 listenport=5002 listenaddress=0.0.0.0 connectport=5002 connectaddress=10.255.255.254

# 2. Firewall
Write-Host "`n2. Configurando Firewall..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "MySQL DB1 - Porta 3307" -Direction Inbound -LocalPort 3307 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "MySQL DB2 - Porta 3308" -Direction Inbound -LocalPort 3308 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "MySQL DB3 - Porta 3309" -Direction Inbound -LocalPort 3309 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Nó 0 - Porta 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Nó 1 - Porta 5001" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue
New-NetFirewallRule -DisplayName "Nó 2 - Porta 5002" -Direction Inbound -LocalPort 5002 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue

Write-Host "`n=== Port Forwarding Configurado ===" -ForegroundColor Green
netsh interface portproxy show all

Write-Host "`n=== IMPORTANTE ===" -ForegroundColor Red
Write-Host "REINICIE o Windows para que o port forwarding funcione corretamente!" -ForegroundColor Yellow
Write-Host "`nApós reiniciar, execute:" -ForegroundColor Cyan
Write-Host "  wsl bash -c 'cd /mnt/c/Users/s988666302/Documents/Projetos/lab-sist-dist && ./iniciar_ambiente.sh'" -ForegroundColor White
