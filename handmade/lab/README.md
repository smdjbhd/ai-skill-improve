# 实验记录（真实输出采集）

> 目的：`homework1.md` 的「学习实践过程遇到的问题与解决方式」必须贴真实报错与真实命令输出。
> 本目录只放原始日志，不放润色后的文本。

## 为什么需要它

第一周要求在 Linux（Ubuntu / openEuler）上把 OpenSSL 装到 3.3.2、GmSSL 装到 3.1.1。
安装过程大概率会遇到问题（系统自带 OpenSSL 抢 PATH、缺 perl、共享库找不到、
`apt` 依赖被破坏……），这些正是报告里最有价值的部分。

但**不能凭记忆写**。手动复述的报错往往和真实输出差几个字，
老师一比对就能看出来。所以用一个包装脚本把终端原样录下来。

## 怎么用

```bash
# 1) 把仓库拷到 Linux 机器（或用共享目录）
cd ~/预习作业-skill迭代

# 2) 跑老师给的安装脚本，同时记录
bash handmade/lab/capture.sh install-openssl "bash ~/tools/setup_openssl_gmssl.sh"

# 3) 单独记录验证命令
bash handmade/lab/capture.sh verify "openssl version -a; gmssl version -a"

# 4) 记录某个具体报错的复现过程
bash handmade/lab/capture.sh path-conflict "which -a openssl; echo \$LD_LIBRARY_PATH"
```

每次执行会在 `handmade/lab/logs/` 生成 `名字-时间戳.log`，里面包含：

- 主机与发行版信息、起止时间、退出码；
- 命令原样输出（`script(1)` 保留 stderr 与颜色）。

## 写报告时

从日志里**原样复制**报错片段到 `homework1.md` 的代码块，并在批注/反思里写清楚：

1. 我一开始以为是 X；
2. 实际原因是 Y（用哪条命令确认的）；
3. 解决方式是 Z，验证命令与结果为 …。

## 注意

- 日志里可能有 `$HOME` 路径、主机名，提交前检查一遍，别泄露无关隐私；
- 如果用的是学校机房或云主机，先把 `logs/` 里的主机名替换成 `<host>`；
- **不要**为了让日志"好看"而重跑或删改——老师看的正是踩坑过程。