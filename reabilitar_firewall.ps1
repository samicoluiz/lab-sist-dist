# Reabilita o Windows Firewall
# EXECUTE COMO ADMINISTRADOR

Write-Host "Reabilitando Windows Firewall..." -ForegroundColor Yellow

Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

Write-Host ""
Write-Host "Status do Firewall:" -ForegroundColor Cyan
Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table

Write-Host ""
Write-Host "[OK] Firewall reabilitado!" -ForegroundColor Green
