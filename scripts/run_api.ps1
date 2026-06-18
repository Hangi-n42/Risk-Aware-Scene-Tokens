param(
    [string]$HostAddress = $(if ($env:RAST_API_HOST) { $env:RAST_API_HOST } else { "127.0.0.1" }),
    [int]$Port = $(if ($env:RAST_API_PORT) { [int]$env:RAST_API_PORT } else { 8000 })
)

$ErrorActionPreference = "Stop"

Write-Host "Starting RAST API on http://$HostAddress`:$Port"
python -m uvicorn apps.api.main:app --host $HostAddress --port $Port
