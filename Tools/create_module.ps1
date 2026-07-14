param(
    [Parameter(Mandatory = $true)]
    [string]$ModuleName
)

$basePath = Join-Path "Source" $ModuleName

Write-Host ""
Write-Host "Creating module: $ModuleName" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $basePath | Out-Null

$files = @(
    "__init__.py",
    "$($ModuleName.ToLower()).py",
    "models.py",
    "test_$($ModuleName.ToLower()).py"
)

foreach ($file in $files)
{
    $path = Join-Path $basePath $file

    if (!(Test-Path $path))
    {
        New-Item -ItemType File -Path $path | Out-Null
        Write-Host "[OK] $path"
    }
    else
    {
        Write-Host "[EXISTS] $path"
    }
}

Write-Host ""
Write-Host "Module created successfully." -ForegroundColor Green
