$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Cloudflared = Join-Path $Root "tools\bin\cloudflared.exe"
$LogDir = Join-Path $Root "logs"
$TunnelInfo = Join-Path $Root ".public_tunnel.json"
$ServerInfo = Join-Path $Root ".last_server.json"

New-Item -ItemType Directory -Force -Path (Split-Path $Cloudflared) | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path -LiteralPath $Cloudflared)) {
  Write-Host "Downloading cloudflared..."
  Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $Cloudflared -UseBasicParsing
}

function Test-Url($Url) {
  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 8
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
}

if (-not (Test-Url "http://127.0.0.1:8787/")) {
  Write-Host "Starting local Galgame server..."
  $python = (Get-Command python).Source
  Start-Process -FilePath $python -ArgumentList @("tools\serve.py", "--host", "127.0.0.1", "--port", "8787", "--open") -WorkingDirectory $Root -WindowStyle Hidden | Out-Null
  Start-Sleep -Seconds 5
  if (-not (Test-Url "http://127.0.0.1:8787/")) {
    throw "Local server did not start. Run run.bat first, then retry."
  }
}

Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match "127\.0\.0\.1:8787|localhost:8787" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$OutLog = Join-Path $LogDir "cloudflared.out.log"
$ErrLog = Join-Path $LogDir "cloudflared.err.log"
Remove-Item -LiteralPath $OutLog, $ErrLog -Force -ErrorAction SilentlyContinue

Write-Host "Starting Cloudflare Quick Tunnel..."
$proc = Start-Process -FilePath $Cloudflared -ArgumentList @("tunnel", "--url", "http://127.0.0.1:8787", "--protocol", "http2", "--no-autoupdate") -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru

$publicUrl = $null
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 1
  $text = ""
  if (Test-Path -LiteralPath $OutLog) { $text += Get-Content -LiteralPath $OutLog -Raw -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $ErrLog) { $text += "`n" + (Get-Content -LiteralPath $ErrLog -Raw -ErrorAction SilentlyContinue) }
  $match = [regex]::Match($text, "https://[a-zA-Z0-9-]+\.trycloudflare\.com")
  if ($match.Success) {
    $publicUrl = $match.Value
    break
  }
  if ((Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) -eq $null) { break }
}

if (-not $publicUrl) {
  Write-Host "Cloudflare tunnel failed to provide a URL."
  if (Test-Path -LiteralPath $ErrLog) { Get-Content -LiteralPath $ErrLog -Tail 80 }
  exit 1
}

$info = [pscustomobject]@{
  publicUrl = $publicUrl
  tunnelPid = $proc.Id
  localUrl = "http://127.0.0.1:8787/"
  startedAt = (Get-Date).ToString("s")
  stdoutLog = $OutLog
  stderrLog = $ErrLog
}
$info | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $TunnelInfo -Encoding UTF8

Write-Host ""
Write-Host "Public Galgame URL:"
Write-Host $publicUrl
Write-Host ""
Write-Host "Keep this computer awake and keep these processes running."
Write-Host "Tunnel info: $TunnelInfo"
if (Test-Path -LiteralPath $ServerInfo) {
  Write-Host "Local server info: $ServerInfo"
}
