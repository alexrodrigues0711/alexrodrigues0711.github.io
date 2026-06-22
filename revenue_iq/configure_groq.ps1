$ErrorActionPreference = "Stop"

$secureKey = Read-Host "Digite sua GROQ_API_KEY" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    if ([string]::IsNullOrWhiteSpace($plainKey)) {
        throw "A chave não pode ser vazia."
    }

    @(
        "GROQ_API_KEY=$plainKey"
        "GROQ_MODEL=llama-3.3-70b-versatile"
        "ALLOWED_ORIGINS=http://127.0.0.1:8765,https://alexrodrigues0711.github.io"
        "RATE_LIMIT_PER_10_MIN=30"
    ) | Set-Content -LiteralPath (Join-Path $PSScriptRoot ".env") -Encoding utf8

    Write-Host "Chave configurada localmente em revenue_iq/.env."
} finally {
    if ($pointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
    $plainKey = $null
}
