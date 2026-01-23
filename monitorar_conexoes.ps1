# Execute como Administrador
# Monitora conexões na porta 5001 em tempo real

Write-Host "Monitorando porta 5001..." -ForegroundColor Yellow
Write-Host "Peça para a outra máquina tentar conectar AGORA" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Gray
Write-Host ""

$i = 0
while ($true) {
    $connections = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
    
    if ($connections) {
        Clear-Host
        Write-Host "[$i] CONEXÕES DETECTADAS NA PORTA 5001:" -ForegroundColor Green
        $connections | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State, OwningProcess | Format-Table -AutoSize
    } else {
        Write-Host "[$i] Nenhuma conexão na porta 5001" -ForegroundColor Gray
    }
    
    Start-Sleep -Seconds 1
    $i++
}
