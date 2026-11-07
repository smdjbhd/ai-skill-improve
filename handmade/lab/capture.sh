#!/usr/bin/env bash
# 采集真实终端输出，供 homework1.md 的「问题与解决」章节引用。
#
# 用法（在你的 Ubuntu / openEuler 上执行）：
#   bash handmade/lab/capture.sh install-openssl "bash ~/openssl-3.3.2-setup.sh"
#   bash handmade/lab/capture.sh gmssl-verify  "gmssl version -a"
#
# 输出同时打到屏幕和 lab/logs/<名字>-<时间>.log，
# 这样报告里贴的报错、版本号、耗时都是真实记录，不是编的。
set -u

name="${1:?用法: capture.sh <日志名> <要执行的命令>}"
cmd="${2:?用法: capture.sh <日志名> <要执行的命令>}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
dir="$root/handmade/lab/logs"
mkdir -p "$dir"
log="$dir/${name}-$(date +%Y%m%d-%H%M%S).log"

{
  echo "=== capture: $name"
  echo "=== host   : $(uname -a)"
  echo "=== distro : $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME")"
  echo "=== start  : $(date -Is)"
  echo "=== cmd    : $cmd"
  echo "---"
} | tee "$log"

# 用 script(1) 保留颜色与 stderr 交织，真实还原终端
script -q -e -c "$cmd" /dev/null 2>&1 | tee -a "$log"
status=${PIPESTATUS[0]}

{
  echo "---"
  echo "=== end    : $(date -Is)"
  echo "=== status : $status"
} | tee -a "$log"

echo
echo "已记录到: $log"
exit "$status"