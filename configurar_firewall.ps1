# Script para garantir que o Firewall permite conexões nas portas do sistema
# EXECUTE COMO ADMINISTRADOR

Write-Host "Configurando regras de firewall para permitir acesso externo..." -ForegroundColor Yellow
Write-Host ""

$ports = @(3307, 3308, 3309, 5000, 5001, 5002)

foreach ($port in $ports) {
    $ruleName = "WSL2 Port $port"
    
    Write-Host "Configurando porta $port..." -ForegroundColor Gray
    
    # Remove regras antigas
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    
    # Cria regra para TODOS os perfis (Domain, Private, Public)
    New-NetFirewallRule -DisplayName $ruleName `
        -Direction Inbound `
        -LocalPort $port `
        -Protocol TCP `
        -Action Allow `
        -Profile Domain,Private,Public `
        -Enabled True | Out-Null
    
    Write-Host "  [OK] Porta $port configurada (Domain, Private, Public)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Verificando regras criadas..." -ForegroundColor Yellow
Get-NetFirewallRule -DisplayName "WSL2 Port*" | Select-Object DisplayName, Enabled, Profile, Direction, Action | Format-Table -AutoSize

Write-Host ""
Write-Host "[OK] Firewall configurado!" -ForegroundColor Green
Write-Host ""
Write-Host "Agora teste de outra máquina com: python3 test_remote_access.py" -ForegroundColor Cyan
