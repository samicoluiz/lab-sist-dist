# SOLUÇÃO DEFINITIVA: Criar regras de firewall explícitas
# EXECUTE COMO ADMINISTRADOR

Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host "CONFIGURANDO FIREWALL PARA PERMITIR ACESSO EXTERNO" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host ""

$portas = @(3307, 3308, 3309, 5000, 5001, 5002)

foreach ($porta in $portas) {
    $ruleName = "Allow WSL Port $porta"
    
    Write-Host "Porta $porta..." -ForegroundColor Gray
    
    # Remove regras antigas
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    
    # Cria regra INBOUND (entrada) para TCP
    New-NetFirewallRule `
        -DisplayName $ruleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $porta `
        -Action Allow `
        -Profile Any `
        -Enabled True | Out-Null
    
    Write-Host "  [OK] Regra criada: $ruleName" -ForegroundColor Green
}

Write-Host ""
Write-Host "Verificando regras criadas..." -ForegroundColor Yellow
Get-NetFirewallRule -DisplayName "Allow WSL Port*" | 
    Select-Object DisplayName, Enabled, Direction, Action | 
    Format-Table -AutoSize

Write-Host ""
Write-Host "Verificando se as portas estão LISTENING..." -ForegroundColor Yellow
Get-NetTCPConnection -State Listen | 
    Where-Object { $_.LocalPort -in @(3307,3308,3309,5000,5001,5002) } | 
    Select-Object LocalAddress, LocalPort, State | 
    Format-Table -AutoSize

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host "[OK] FIREWALL CONFIGURADO!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Magenta
Write-Host ""
Write-Host "AGORA TESTE NOVAMENTE DA OUTRA MÁQUINA:" -ForegroundColor Cyan
Write-Host "  python3 test_simples.py" -ForegroundColor White
Write-Host ""
