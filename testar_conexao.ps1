$ports = @(3307, 3308, 3309, 5000, 5001, 5002)
$localhost = '127.0.0.1'

Write-Host 'Testando conectividade com os servicos...' -ForegroundColor Green
Write-Host ''

foreach ($port in $ports) {
    $serviceName = switch ($port) {
        3309 { 'MySQL db1' }
        3307 { 'MySQL db2' }
        3308 { 'MySQL db3' }
        5000 { 'Node 0' }
        5001 { 'Node 1' }
        5002 { 'Node 2' }
    }
    
    Write-Host "Testando $serviceName (porta $port)... " -NoNewline
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect($localhost, $port)
        $connection.Close()
        Write-Host 'OK' -ForegroundColor Green
    } catch {
        Write-Host 'FALHOU' -ForegroundColor Red
    }
}

Write-Host ''
Write-Host 'Para testar de outras maquinas, use o IP da rede: ' -NoNewline
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' -or $_.IPAddress -like '10.*' } | Select-Object -First 1).IPAddress
Write-Host $windowsIP -ForegroundColor Cyan
