param(
    [string]$BaseUrl = $(if ($env:RAST_API_BASE_URL) { $env:RAST_API_BASE_URL } else { "http://127.0.0.1:8000" })
)

$ErrorActionPreference = "Stop"

function Assert-Value($Condition, $Message) {
    if (-not $Condition) {
        throw $Message
    }
}

Write-Host "Smoke testing RAST API at $BaseUrl"

$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
Assert-Value ($health.status -eq "ok") "Health check failed."

$scenarios = Invoke-RestMethod -Uri "$BaseUrl/api/scenarios" -Method Get
Assert-Value ($scenarios.scenarios.Count -gt 0) "Scenario list is empty."

$policies = Invoke-RestMethod -Uri "$BaseUrl/api/policies" -Method Get
Assert-Value ($policies.policies -contains "rast") "Policy list does not include rast."

$body = @{
    scenario = "clear_path"
    apply_policy = "rast"
    max_steps = 3
    update_mode = "full_recompute"
} | ConvertTo-Json

$result = Invoke-RestMethod -Uri "$BaseUrl/api/run-scenario" -Method Post -ContentType "application/json" -Body $body
Assert-Value ($result.selected_action) "Scenario result has no selected_action."
Assert-Value ($null -ne $result.token_counts) "Scenario result has no token_counts."

Write-Host "RAST API smoke test passed."
