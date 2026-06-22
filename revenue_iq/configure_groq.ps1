$ErrorActionPreference = "Stop"

$secureKey = Read-Host "Digite sua GROQ_API_KEY" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)

try {
    $plainKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    if ([string]::IsNullOrWhiteSpace($plainKey)) {
        throw "A chave não pode ser vazia."
    }

    $lines = @(
        "GROQ_API_KEY=$plainKey"
        "GROQ_MODEL=llama-3.3-70b-versatile"
        "ALLOWED_ORIGINS=http://127.0.0.1:8765,https://alexrodrigues0711.github.io"
        "RATE_LIMIT_PER_10_MIN=30"
    )
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot ".env"), $lines, $utf8WithoutBom)

    Write-Host "Chave configurada localmente em revenue_iq/.env."
} finally {
    if ($pointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
    $plainKey = $null
}
