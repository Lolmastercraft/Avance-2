param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,

    [string]$ProfileName = "avance2-lab",

    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw "No se encontró el archivo indicado."
}

$values = @{}
foreach ($rawLine in Get-Content -LiteralPath $SourcePath) {
    $line = $rawLine.Trim()
    if (-not $line -or $line.StartsWith("#") -or $line.StartsWith("[")) {
        continue
    }

    if ($line -match "^(?:export\s+)?(?<key>AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_SESSION_TOKEN|aws_access_key_id|aws_secret_access_key|aws_session_token)\s*=\s*(?<value>.+?)\s*$") {
        $key = $Matches["key"].ToLowerInvariant()
        $value = $Matches["value"].Trim().Trim('"').Trim("'")
        $values[$key] = $value
    }
}

$required = @("aws_access_key_id", "aws_secret_access_key", "aws_session_token")
$missing = @($required | Where-Object {
    -not $values.ContainsKey($_) -or [string]::IsNullOrWhiteSpace($values[$_])
})

if ($missing.Count -gt 0) {
    throw "El archivo no contiene los tres campos temporales requeridos por AWS CLI."
}

& aws configure set aws_access_key_id $values["aws_access_key_id"] --profile $ProfileName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "No se pudo guardar el identificador de acceso." }

& aws configure set aws_secret_access_key $values["aws_secret_access_key"] --profile $ProfileName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "No se pudo guardar la clave secreta." }

& aws configure set aws_session_token $values["aws_session_token"] --profile $ProfileName | Out-Null
if ($LASTEXITCODE -ne 0) { throw "No se pudo guardar el token temporal." }

& aws configure set region $Region --profile $ProfileName | Out-Null
& aws configure set output json --profile $ProfileName | Out-Null

$identityRaw = & aws sts get-caller-identity --profile $ProfileName --output json 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "AWS rechazó las credenciales temporales."
}

$identity = ($identityRaw | Out-String) | ConvertFrom-Json
if (-not $identity.Account -or -not $identity.Arn) {
    throw "AWS respondió, pero la identidad no pudo validarse."
}

[pscustomobject]@{
    authenticated = $true
    profile = $ProfileName
    region = $Region
    identity_type = if ($identity.Arn -match ":assumed-role/") { "temporary-lab-role" } else { "aws-identity" }
} | ConvertTo-Json -Compress
