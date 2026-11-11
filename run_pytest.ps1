$env:PYTHONPATH = "H:\Almacen\.venv\Lib\site-packages"

# Levantar servidor
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = "H:\Almacen\.venv\Scripts\python.exe"
$startInfo.Arguments = "-m uvicorn app.main:app --host 127.0.0.1 --port 8000"
$startInfo.WorkingDirectory = "H:\Almacen-V1\backend"
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
foreach ($key in $env.Keys) { $startInfo.EnvironmentVariables[$key] = $env[$key] }

$proc = [System.Diagnostics.Process]::Start($startInfo)
Write-Host "Servidor iniciado PID: $($proc.Id)"

# Esperar a que esté listo
$serverReady = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            Write-Host "Servidor listo en intento $($i+1)"
            $serverReady = $true
            break
        }
    } catch {
        Write-Host "Esperando... $($i+1)"
    }
}

if (-not $serverReady) {
    Write-Host "ERROR: Servidor no respondió"
    $proc.Kill()
    exit 1
}

# Ejecutar pytest
Write-Host ""
Write-Host "=== EJECUTANDO pytest ==="
& "H:\Almacen\.venv\Scripts\python.exe" -m pytest H:\Almacen-V1\backend\tests_integration.py -v 2>&1

# Detener servidor
$proc.Kill()
Write-Host ""
Write-Host "Servidor detenido. Pruebas completadas."
