param(
  [string]$SaltsNetRoot,
  [string]$Preset,
  [string]$TargetTriplet = $env:QIGAO_TARGET_TRIPLET
)

$ErrorActionPreference = 'Stop'

if (-not $SaltsNetRoot) {
  if (-not $env:GITHUB_WORKSPACE -or -not $env:QIGAO_SDK_RID) {
    throw 'Specify -SaltsNetRoot or set GITHUB_WORKSPACE and QIGAO_SDK_RID'
  }
  $SaltsNetRoot = Join-Path $env:GITHUB_WORKSPACE "stage/sdk/$env:QIGAO_SDK_RID"
}
$prefix = (Resolve-Path -LiteralPath $SaltsNetRoot).Path.Replace('\', '/')
$config = Join-Path $prefix 'lib/cmake/SaltsNet/SaltsNetConfig.cmake'
if (-not (Test-Path -LiteralPath $config -PathType Leaf)) {
  throw "Missing installed SaltsNet config: $config"
}
$env:SALTSNET_ROOT = $prefix
$sourceDir = Join-Path $PSScriptRoot '../../tests/installed_sdk'
$runtimeRoots = @($prefix)
foreach ($name in @('SALTS_BASE_ROOT', 'CMETA_ROOT', 'SALTS_CNET_ROOT', 'SALTS_UTILS_ROOT')) {
  $sdkRoot = [Environment]::GetEnvironmentVariable($name)
  if ([string]::IsNullOrWhiteSpace($sdkRoot)) { throw "Installed SDK verification requires $name" }
  $runtimeRoots += $sdkRoot
}
if ($env:VCPKG_INSTALLED_DIR -and $TargetTriplet) {
  $runtimeRoots += Join-Path $env:VCPKG_INSTALLED_DIR $TargetTriplet
}
$separator = [string][IO.Path]::PathSeparator
$runtimeDirs = $runtimeRoots | ForEach-Object { Join-Path $_ 'bin'; Join-Path $_ 'lib' }
$runtimePrefix = ($runtimeDirs | Where-Object { Test-Path -LiteralPath $_ -PathType Container }) -join $separator
$env:PATH = "$runtimePrefix$separator$env:PATH"
if (-not $IsWindows) {
  $env:LD_LIBRARY_PATH = "$runtimePrefix$separator$env:LD_LIBRARY_PATH"
  $env:DYLD_LIBRARY_PATH = "$runtimePrefix$separator$env:DYLD_LIBRARY_PATH"
}
if (-not $Preset) {
  $Preset = if ($IsWindows) { 'win-release-user' } elseif ($IsMacOS) { 'macos-release-user' } else { 'linux-release-user' }
}
Push-Location $sourceDir
try {
  & cmake --preset $preset
  if ($LASTEXITCODE -ne 0) { throw "Installed SDK C11/C++17 configure failed" }
  & cmake --build --preset $preset --parallel 2
  if ($LASTEXITCODE -ne 0) { throw "Installed SDK C11/C++17 build failed" }
  & ctest --preset $preset
  if ($LASTEXITCODE -ne 0) { throw "Installed SDK C11/C++17 runtime failed" }
} finally {
  Pop-Location
}
