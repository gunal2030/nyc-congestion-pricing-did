$ProgressPreference = 'SilentlyContinue'
New-Item -ItemType Directory -Force -Path "data\raw" | Out-Null

$months = "2023-07","2023-08","2023-09","2023-10","2023-11","2023-12"
foreach ($m in $months) {
  $name = "fhvhv_tripdata_$m.parquet"
  $out = Join-Path "data\raw" $name
  if (-not (Test-Path $out)) {
    Write-Host "Downloading $name ..."
    Invoke-WebRequest "https://d37ci6vzurychx.cloudfront.net/trip-data/$name" -OutFile "$out.part"
    Rename-Item "$out.part" $name
  }
}
Write-Host "Done"
