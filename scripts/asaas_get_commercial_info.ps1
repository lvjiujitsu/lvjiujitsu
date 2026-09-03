if ([string]::IsNullOrWhiteSpace($env:ASAAS_API_KEY)) {
    Write-Error "Defina `$env:ASAAS_API_KEY antes de rodar este script."
    exit 1
}

$headers = @{
    "access_token" = $env:ASAAS_API_KEY
    "Content-Type" = "application/json"
}

$response = Invoke-RestMethod `
    -Uri "https://api-sandbox.asaas.com/v3/myAccount/commercialInfo/" `
    -Method GET `
    -Headers $headers `
    -TimeoutSec 30 `
    -ErrorAction Stop

$response | ConvertTo-Json -Depth 10
