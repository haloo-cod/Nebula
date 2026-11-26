#!/usr/bin/env bash
# Ubuntu 24.04 博客开发工具链：只安装系统依赖与运行时，项目通过 Git 单独管理。
set -Eeuo pipefail

NODE_VERSION=''
PNPM_VERSION=11.13.0
APT_LOCK_TIMEOUT=600
RUNTIME_ROOT=/opt/nebula-runtime
BIN_DIR=/usr/local/bin
WORK_DIR=''
MODE=install

# 打印安装进度。
log() { printf '\n[环境] %s\n' "$*"; }

# 输出错误并退出，不打印可能含凭据的命令上下文。
die() { printf '[错误] %s\n' "$*" >&2; exit 1; }

# 显示用法；Node 固定 LTS 主版本，pnpm 与当前开发工具链一致。
usage() {
  cat <<'EOF'
用法：sudo bash setup-ubuntu-env.sh [选项]

适用：Ubuntu 24.04，x86_64 / ARM64。
安装：Python 3.12、venv、pip、Node.js 24 LTS 最新补丁、pnpm 11.13.0、Git、SQLite 和编译依赖。

  --check                 只检查工具链，不安装软件，无需 root
  --dry-run               打印安装计划，不安装软件，无需 root
  --node-version X.Y.Z    指定 Node.js 版本（默认 24 LTS 最新补丁）
  --pnpm-version X.Y.Z    指定 pnpm 版本（默认 11.13.0）
  -h, --help              显示帮助

Node.js 从 nodejs.org 下载并校验 SHA256；全局命令位于 /usr/local/bin。
项目代码、Python 虚拟环境、项目依赖与业务数据由仓库部署步骤管理。
EOF
}

# 限定版本参数，避免把标签或路径当成版本使用。
validate_versions() {
  [[ "$PNPM_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die 'pnpm 版本必须为 X.Y.Z。'
  [[ -n "$NODE_VERSION" ]] || return 0
  [[ "$NODE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die 'Node.js 版本必须为 X.Y.Z。'
  local major=${NODE_VERSION%%.*} minor=${NODE_VERSION#*.}
  minor=${minor%%.*}
  (( 10#$major > 22 || (10#$major == 22 && 10#$minor >= 12) )) ||
    die '本项目请选择 Node.js 22.12 或更新版本，推荐 24 LTS。'
}

# 从官方发布清单中选择最新的 24 LTS 补丁，避免安装旧补丁或自动跨主版本。
resolve_node_version() {
  [[ -z "$NODE_VERSION" ]] || return 0
  [[ -n "$WORK_DIR" ]] || WORK_DIR=$(mktemp -d /tmp/nebula-env.XXXXXXXX)
  curl --fail --show-error --location --retry 3 --connect-timeout 20 --max-time 120 \
    https://nodejs.org/dist/index.json --output "$WORK_DIR/index.json"
  NODE_VERSION=$(python3 - "$WORK_DIR/index.json" <<'PY'
import json
from pathlib import Path
import re
import sys

records = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
versions = [item["version"][1:] for item in records
            if item.get("lts") and re.fullmatch(r"v24\.\d+\.\d+", item.get("version", ""))]
if not versions:
    raise SystemExit("官方发布清单中没有 Node.js 24 LTS。")
print(max(versions, key=lambda version: tuple(map(int, version.split(".")))))
PY
  )
  validate_versions
  log "选择 Node.js $NODE_VERSION (24 LTS)"
}

# 将内核架构映射到 Node.js 官方二进制包名称。
node_architecture() {
  case "$(uname -m)" in
    x86_64) printf 'x64\n' ;;
    aarch64|arm64) printf 'arm64\n' ;;
    *) die '仅支持 x86_64 和 ARM64。' ;;
  esac
}

# 真正安装前确认系统和权限，防止在开发电脑或其他发行版上误执行。
require_supported_host() {
  [[ "$(uname -s)" == Linux ]] || die '安装仅支持 Ubuntu 24.04。'
  [[ "$EUID" -eq 0 ]] || die '请使用 sudo bash 运行安装；检查可用 --check。'
  [[ -r /etc/os-release ]] || die '无法读取 /etc/os-release。'
  local ID='' VERSION_ID=''
  # /etc/os-release 是操作系统提供的标准配置，不读取项目的 .env。
  # shellcheck disable=SC1091
  . /etc/os-release
  [[ "$ID" == ubuntu && "$VERSION_ID" == 24.04 ]] ||
    die "此脚本面向 Ubuntu 24.04，当前为 ${ID:-未知} ${VERSION_ID:-未知}。"
}

# 只清理本次安装自己创建的临时目录。
cleanup() {
  if [[ "$WORK_DIR" == /tmp/nebula-env.* && -d "$WORK_DIR" && ! -L "$WORK_DIR" ]]; then
    rm -rf -- "$WORK_DIR"
  fi
}

# 安装 Python 系统包及 Python/Node 原生依赖常用的编译工具。
install_system_packages() {
  log '安装 Python、Git 和系统依赖'
  apt-get update
  log '若自动更新占用 dpkg 安装锁，将等待最多 10 分钟。'
  DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout="$APT_LOCK_TIMEOUT" install -y --no-install-recommends \
    ca-certificates curl git xz-utils sqlite3 rsync \
    python3 python3-venv python3-pip python3-dev \
    build-essential pkg-config libffi-dev libssl-dev libjpeg-dev zlib1g-dev
  python3 -c 'import sys; assert sys.version_info >= (3, 11), "需要 Python 3.11 或更新版本"'
}

# 校验官方清单中的唯一 SHA256，校验失败时保留已安装的运行时。
verify_archive() {
  local archive=$1 checksum_file=$2 expected
  expected=$(awk -v name="${archive##*/}" '$2 == name { print $1 }' "$checksum_file")
  [[ "$expected" =~ ^[a-fA-F0-9]{64}$ ]] || die '官方校验文件缺少唯一、有效的 SHA256。'
  printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status || die 'Node.js 安装包 SHA256 校验失败。'
}

# 下载固定版本的官方 Node.js；同一版本重复运行会直接复用。
install_node() {
  local arch=$1 directory archive target node_url
  directory="node-v${NODE_VERSION}-linux-${arch}"
  archive="${directory}.tar.xz"
  target="$RUNTIME_ROOT/$directory"
  node_url="https://nodejs.org/dist/v${NODE_VERSION}"
  [[ ! -L "$target" ]] || die "运行时目录不应是符号链接：$target"

  if [[ -x "$target/bin/node" && "$("$target/bin/node" --version)" == "v$NODE_VERSION" ]]; then
    log "复用 Node.js $NODE_VERSION"
  else
    [[ ! -e "$target" ]] || die "运行时目录已存在但不完整，请先检查或改名：$target"
    log "下载并校验 Node.js $NODE_VERSION ($arch)"
    [[ -n "$WORK_DIR" ]] || WORK_DIR=$(mktemp -d /tmp/nebula-env.XXXXXXXX)
    curl --fail --show-error --location --retry 3 --connect-timeout 20 --max-time 600 \
      "$node_url/$archive" --output "$WORK_DIR/$archive"
    curl --fail --show-error --location --retry 3 --connect-timeout 20 --max-time 120 \
      "$node_url/SHASUMS256.txt" --output "$WORK_DIR/SHASUMS256.txt"
    verify_archive "$WORK_DIR/$archive" "$WORK_DIR/SHASUMS256.txt"
    tar --extract --xz --no-same-owner --file "$WORK_DIR/$archive" --directory "$WORK_DIR"
    [[ -x "$WORK_DIR/$directory/bin/node" ]] || die '安装包中未找到 node。'
    [[ "$("$WORK_DIR/$directory/bin/node" --version)" == "v$NODE_VERSION" ]] || die '安装包版本与请求版本不一致。'
    install -d -m 0755 "$RUNTIME_ROOT"
    mv -- "$WORK_DIR/$directory" "$target"
  fi

  install -d -m 0755 "$BIN_DIR"
  local command
  for command in node npm npx; do
    [[ ! -d "$BIN_DIR/$command" ]] || die "命令位置被目录占用：$BIN_DIR/$command"
    if [[ -e "$BIN_DIR/$command" && ! -L "$BIN_DIR/$command" ]]; then
      die "命令位置已有普通文件，请先检查或改名：$BIN_DIR/$command"
    fi
  done
  for command in node npm npx; do
    ln -sfn -- "$target/bin/$command" "$BIN_DIR/$command"
  done
  hash -r
}

# 通过官方 npm 注册表安装与项目一致的 pnpm 版本，所有 SSH 用户均可使用。
install_pnpm() {
  log "安装 pnpm $PNPM_VERSION"
  if [[ -x "$BIN_DIR/pnpm" && "$("$BIN_DIR/pnpm" --version)" == "$PNPM_VERSION" ]]; then
    log "复用 pnpm $PNPM_VERSION"
    return
  fi
  npm install --global --prefix /usr/local --registry https://registry.npmjs.org "pnpm@$PNPM_VERSION"
  hash -r
}

# 核对运行时、venv 和 SQLite 可用性，检查模式不会写入项目数据。
check_environment() {
  local command active_node
  for command in python3 node npm pnpm git sqlite3; do
    command -v "$command" >/dev/null || die "未安装或 PATH 中找不到：$command"
  done
  python3 -c 'import sqlite3, ssl, sys, venv; assert sys.version_info >= (3, 11); print("Python:", sys.version.split()[0], "SQLite 模块:", sqlite3.sqlite_version)'
  active_node=$(node --version)
  if [[ -n "$NODE_VERSION" ]]; then
    [[ "$active_node" == "v$NODE_VERSION" ]] || die "当前 PATH 中的 Node.js 不是 v$NODE_VERSION，请检查旧的 nvm/命令路径。"
  else
    [[ "$active_node" == v24.* ]] || die '当前 PATH 中的 Node.js 不是 24 LTS，请检查旧的 nvm/命令路径。'
  fi
  [[ "$(pnpm --version)" == "$PNPM_VERSION" ]] || die "当前 PATH 中的 pnpm 不是 $PNPM_VERSION。"
  node --version
  npm --version
  pnpm --version
  git --version
  sqlite3 --version
}

# 主入口：安装环境后仍由部署者拉取仓库、恢复数据和管理服务。
main() {
  while (($#)); do
    case "$1" in
      --check) MODE=check; shift ;;
      --dry-run) MODE=dry-run; shift ;;
      --node-version|--pnpm-version)
        (($# >= 2)) || die "$1 缺少版本号。"
        if [[ "$1" == --node-version ]]; then NODE_VERSION=$2; else PNPM_VERSION=$2; fi
        shift 2 ;;
      -h|--help) usage; return ;;
      *) die "未知参数：$1。使用 --help 查看帮助。" ;;
    esac
  done
  validate_versions
  if [[ "$MODE" == dry-run ]]; then
    printf '安装计划：Ubuntu 24.04；Python 3.12 + venv/pip；Node.js %s (%s)；pnpm %s；Git/SQLite/编译依赖。\n' \
      "${NODE_VERSION:-24 LTS 最新补丁}" "$(node_architecture)" "$PNPM_VERSION"
    printf 'Node.js 目录：%s；全局命令目录：%s。\n' "$RUNTIME_ROOT" "$BIN_DIR"
    return
  fi
  if [[ "$MODE" == check ]]; then check_environment; return; fi
  require_supported_host
  local arch
  arch=$(node_architecture)
  export PATH="$BIN_DIR:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"
  umask 022
  trap cleanup EXIT
  trap 'printf "[错误] 安装在第 %s 行失败，请处理后重新运行。\n" "$LINENO" >&2' ERR
  install_system_packages
  resolve_node_version
  install_node "$arch"
  install_pnpm
  log '校验安装结果'
  check_environment
  log '环境已准备好。下一步：git clone 仓库、恢复生产数据、安装项目依赖。详见 docs/server-environment.md。'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
