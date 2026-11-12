# 在你自己的 PowerShell 窗口里运行 this：把本地仓库推到 GitHub
#
# 为什么需要你自己敲一次：Git 的凭据管理器要弹浏览器让你登录 GitHub，
# 而自动化的那个进程里没有桌面会话，弹不出来（报 "此平台上不支持操作"）。
#
# 用法：右键 → “使用 PowerShell 运行”，或在此目录打开 PowerShell 后：
#   powershell -ExecutionPolicy Bypass -File tools\push-to-github.ps1

$ErrorActionPreference = 'Stop'
$gb  = 'C:\Users\31024\Documents\deepseek-harness\default-workspace\tools\mingit\cmd\git.exe'
$repo = Split-Path -Parent $PSScriptRoot          # 仓库根目录

# 1) 关掉吊销检查（本机 schannel 连不上 OCSP，否则报 CRYPT_E_NO_REVOCATION_CHECK）
& $gb -C $repo config http.schannelCheckRevoke false

# 2) 推主分支，再推 tag
& $gb -C $repo push -u origin main
& $gb -C $repo push origin --tags

Write-Host ""
Write-Host "完成。检查 https://github.com/smdjbhd/ai-skill-improve" -ForegroundColor Green
& $gb -C $repo log --oneline -1