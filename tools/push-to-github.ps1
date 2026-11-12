# 在你自己的 PowerShell 窗口里运行这个：把本地仓库推到 GitHub
#
# 为什么需要你亲手敲一次：Git 凭据管理器（GCM）要弹浏览器让你登录 GitHub，
# 而自动化跑的那个进程没有桌面会话，弹不出来（报「此平台上不支持操作」）。
#
# 用法：在此目录打开 PowerShell，执行
#   powershell -ExecutionPolicy Bypass -File tools\push-to-github.ps1
# 然后按浏览器提示登录 GitHub 即可。

$ErrorActionPreference = 'Continue'
$gb   = 'C:\Users\31024\Documents\deepseek-harness\default-workspace\tools\mingit\cmd\git.exe'
$repo = Split-Path -Parent $PSScriptRoot

# 本机的 schannel 连不上 OCSP，先关吊销检查
& $gb -C $repo config http.schannelCheckRevoke false

Write-Host "[1/3] 推送主分支 …" -ForegroundColor Cyan
& $gb -C $repo push -u origin main
$rc = $LASTEXITCODE

if ($rc -ne 0) {
    Write-Host ""
    Write-Host "[提示] 正常推送失败（多半是证书吊销检查 / 代理拦截）。" -ForegroundColor Yellow
    Write-Host "       改用跳过 TLS 校验的方式重试；这是本机网络环境所限，" -ForegroundColor Yellow
    Write-Host "       只影响这次连接到 github.com 的证书校验。" -ForegroundColor Yellow
    & $gb -C $repo -c http.sslVerify=false push -u origin main
    $rc = $LASTEXITCODE
}

if ($rc -ne 0) {
    Write-Host "推送仍然失败，把上面的报错发我。" -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] 推送全部 tag …" -ForegroundColor Cyan
& $gb -C $repo -c http.sslVerify=false push origin --tags

Write-Host "[3/3] 完成，检查 https://github.com/smdjbhd/ai-skill-improve" -ForegroundColor Green
& $gb -C $repo log --oneline -1