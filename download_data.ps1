# ============================================================
# NYC TLC HVFHV Data Downloader — Congestion Pricing Analysis
# ============================================================
# Coverage : Jan 2024 – Jun 2025  (12 months pre + 6 months post launch)
# Launch   : NYC Congestion Pricing, January 5, 2025
# Source   : https://d37ci6vzurychx.cloudfront.net/trip-data/
# ============================================================

$BASE = "https://d37ci6vzurychx.cloudfront.net"
$OUT  = "$PSScriptRoot\data\raw"

# Ensure output directory exists
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

# ---- Taxi Zone Lookup (once) ----
$lookupDest = "$OUT\taxi_zone_lookup.csv"
if (-not (Test-Path $lookupDest)) {
    Write-Host "Downloading taxi_zone_lookup.csv ..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "$BASE/misc/taxi_zone_lookup.csv" -OutFile $lookupDest
    Write-Host "  -> OK" -ForegroundColor Green
} else {
    Write-Host "taxi_zone_lookup.csv already exists, skipping." -ForegroundColor DarkGray
}

# ---- HVFHV monthly files ----
# Jan 2024 - Jun 2025  (18 files, ~500 MB-1 GB each)
$months = @(
    "2024-01","2024-02","2024-03","2024-04","2024-05","2024-06",
    "2024-07","2024-08","2024-09","2024-10","2024-11","2024-12",
    "2025-01","2025-02","2025-03","2025-04","2025-05","2025-06"
)

$total   = $months.Count
$current = 0

foreach ($ym in $months) {
    $current++
    $fname = "fhvhv_tripdata_$ym.parquet"
    $dest  = "$OUT\$fname"

    if (Test-Path $dest) {
        $sz = (Get-Item $dest).Length / 1MB
        Write-Host "[$current/$total] $fname already exists ($([math]::Round($sz,0)) MB), skipping." -ForegroundColor DarkGray
        continue
    }

    $url = "$BASE/trip-data/$fname"
    Write-Host "[$current/$total] Downloading $fname ..." -ForegroundColor Cyan

    try {
        $start = Get-Date
        Invoke-WebRequest -Uri $url -OutFile $dest -TimeoutSec 600
        $elapsed = ((Get-Date) - $start).TotalSeconds
        $sz = (Get-Item $dest).Length / 1MB
        Write-Host "  -> OK  $([math]::Round($sz,0)) MB in $([math]::Round($elapsed,0))s" -ForegroundColor Green
    } catch {
        Write-Warning "  FAILED: $_"
        # Remove partial file if present
        if (Test-Path $dest) { Remove-Item $dest -Force }
    }
}

Write-Host ""
Write-Host "===== Download complete =====" -ForegroundColor Yellow
Write-Host "Files saved to: $OUT"
Get-ChildItem $OUT | Select-Object Name, @{N="MB";E={[math]::Round($_.Length/1MB,0)}} | Format-Table -AutoSize
