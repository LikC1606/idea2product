# Kill all processes listening on port 8080
$connections = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
foreach ($conn in $connections) {
    if ($conn.State -eq 'Listen') {
        $procId = $conn.OwningProcess
        Write-Host "Killing process $procId on port 8080"
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2
Write-Host "Port 8080 should be free now. Start with: python -m src.web.app"
