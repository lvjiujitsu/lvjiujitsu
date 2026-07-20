# Leitura (GET) dos dados comerciais atuais da conta Asaas sandbox.
# Nao altera nada. Roda com a ASAAS_API_KEY do seu .env (nunca hardcoded).
#
# Uso:
#   1. Abrir PowerShell na raiz do projeto.
#   2. Carregar a variavel a partir do .env (ou colar o valor manualmente na sessao):
#        $line = Get-Content .env | Where-Object { $_ -like 'ASAAS_API_KEY=*' }
#        $env:ASAAS_API_KEY = $line.Substring(15)
#   3. Rodar: .\scripts\asaas_get_commercial_info.ps1
#   4. Copiar a saida JSON e compartilhar para montarmos o POST (Passo 2)
#      preservando todos os campos e so trocando "site".

if (-not $env:ASAAS_API_KEY) {
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
    -Headers $headers

$response | ConvertTo-Json -Depth 10
