#!/bin/bash
# OpenSSL 3.3.2 安装脚本（修正版）
#
# 基于老师给的 sh/opensslinstall.sh，修了三处：
#   1) 版本：脚本里写死 3.2.1，作业要求 3.3.2 → 改成 3.3.2
#   2) heredoc 结束符：原脚本 "EOF" 后面带了两个空格，bash 认不出来，
#      导致环境变量脚本被吞、整个脚本提前退出（退出码 1，env 文件 0 字节）
#   3) 库路径：x86_64 上 make install 装到 lib64，原脚本却 export lib →
#      即使执行到也会找不到 libssl.so.3
#
# 另外刻意去掉了原脚本的 `sudo cp bin/openssl /usr/bin/`：
# 直接覆盖系统 openssl 会让 apt/系统工具链处在"二进制 3.3.2 + 库 3.0.2"的错配状态。
# 需要全局生效时，用 update-alternatives 或改 ld.so.conf，别直接 cp 二进制。
set -euo pipefail

VER="3.3.2"
CUROPENSSL="openssl-${VER}"
DOWNLOAD_URL="https://github.com/openssl/openssl/releases/download/${CUROPENSSL}/${CUROPENSSL}.tar.gz"

ROCHOME="$HOME"
SRC_DIR="${ROCHOME}/rocopenssl_src"
BUILD_DIR="${ROCHOME}/rocopenssl332"
INSTALL_DIR="${ROCHOME}/rocopenssl332_conf"
TARBALL="${ROCHOME}/${CUROPENSSL}.tar.gz"

mkdir -p "${SRC_DIR}" "${BUILD_DIR}" "${INSTALL_DIR}"

if [ ! -f "${TARBALL}" ]; then
    echo ">>> 下载 OpenSSL ${VER} ..."
    wget -O "${TARBALL}" "${DOWNLOAD_URL}"
fi

if [ ! -d "${SRC_DIR}/${CUROPENSSL}" ]; then
    echo ">>> 解压 ${CUROPENSSL}.tar.gz ..."
    tar -zxf "${TARBALL}" -C "${SRC_DIR}"
fi

cd "${SRC_DIR}/${CUROPENSSL}"

echo ">>> 配置（prefix=${BUILD_DIR}）..."
./config --prefix="${BUILD_DIR}" --openssldir="${INSTALL_DIR}" shared

echo ">>> 编译 ..."
make -j"$(nproc)"

echo ">>> 安装 ..."
make install_sw

# x86_64 上装到 lib64，这里按实际目录选
LIBDIR="${BUILD_DIR}/lib64"
[ -d "${LIBDIR}" ] || LIBDIR="${BUILD_DIR}/lib"

ENV_SCRIPT="${ROCHOME}/openssl_env.sh"
echo ">>> 生成环境变量脚本 ${ENV_SCRIPT} （库目录 ${LIBDIR}）"
cat > "${ENV_SCRIPT}" <<EOF
# OpenSSL ${VER} 环境变量
export PATH="${BUILD_DIR}/bin:\$PATH"
export LD_LIBRARY_PATH="${LIBDIR}:\$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="${LIBDIR}/pkgconfig:\$PKG_CONFIG_PATH"
EOF

echo ">>> 验证（当前 shell 内）"
export PATH="${BUILD_DIR}/bin:$PATH"
export LD_LIBRARY_PATH="${LIBDIR}:${LD_LIBRARY_PATH:-}"
"${BUILD_DIR}/bin/openssl" version -a | head -3

echo ">>> 完成。使用方式：source ${ENV_SCRIPT}"