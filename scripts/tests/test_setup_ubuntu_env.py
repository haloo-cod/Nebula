"""隔离验证环境脚本：用本地安装包替身覆盖下载，不运行 apt 或全局安装。"""

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import threading
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "setup-ubuntu-env.sh"
DIRECTORY = "node-v24.18.0-linux-x64"


class SetupEnvironmentTests(unittest.TestCase):
    """覆盖不安装模式、重复安装、校验失败及现有命令保护。"""

    def run_script(self, body, *arguments):
        """在独立 Bash 进程中加载脚本，参数经 argv 传递。"""
        return subprocess.run(
            ["bash", "-c", 'source "$1"; shift\n' + body, "nebula-test", str(SCRIPT), *map(str, arguments)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def make_fixture(self, root):
        """创建可实际解压和执行的 Node.js 安装包替身及 SHA256 清单。"""
        archive = root / f"{DIRECTORY}.tar.xz"
        with tarfile.open(archive, "w:xz") as package:
            for command, version in (("node", "v24.18.0"), ("npm", "11.0.0"), ("npx", "11.0.0")):
                content = f"#!/bin/sh\nprintf '%s\\n' '{version}'\n".encode()
                info = tarfile.TarInfo(f"{DIRECTORY}/bin/{command}")
                info.mode = 0o755
                info.size = len(content)
                package.addfile(info, io.BytesIO(content))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (root / "SHASUMS256.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")

    def installation_body(self):
        """将运行时和命令路径隔离到临时目录，curl 仅复制本地测试夹具。"""
        return r'''
FIXTURE="$1"
NODE_VERSION=24.18.0
RUNTIME_ROOT="$FIXTURE/runtime"
BIN_DIR="$FIXTURE/bin"
trap cleanup EXIT
curl() {
  local output='' url=''
  while (($#)); do
    case "$1" in
      --output) output=$2; shift 2 ;;
      https:*) url=$1; shift ;;
      *) shift ;;
    esac
  done
  case "$url" in
    */SHASUMS256.txt) cp -- "$FIXTURE/SHASUMS256.txt" "$output" ;;
    */node-v24.18.0-linux-x64.tar.xz) cp -- "$FIXTURE/node-v24.18.0-linux-x64.tar.xz" "$output" ;;
    *) return 98 ;;
  esac
}
'''

    def test_dry_run_has_no_package_or_network_calls(self):
        result = self.run_script(r'''
apt-get() { return 91; }
curl() { return 92; }
npm() { return 93; }
main --dry-run
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("24 LTS 最新补丁", result.stdout)
        self.assertIn("11.13.0", result.stdout)

    def test_invalid_version_is_rejected_before_installation(self):
        result = self.run_script('main --node-version "$1"', "24.18.0/../../bad")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("X.Y.Z", result.stderr)

    @unittest.skipUnless(os.name == "posix" and shutil.which("apt-get"), "需要 Linux apt-get 验证实际锁行为")
    def test_system_install_waits_for_dpkg_lock_then_continues(self):
        """真实 apt 只操作临时状态目录，等待另一个进程持有的锁释放；不安装任何软件。"""
        import fcntl

        with tempfile.TemporaryDirectory(prefix="nebula-apt-lock-test-") as temporary:
            root = Path(temporary)
            for folder in ("state/lists/partial", "cache/archives/partial", "sources", "logs"):
                (root / folder).mkdir(parents=True)
            (root / "state/status").write_text("", encoding="utf-8")
            with (root / "state/lock-frontend").open("w") as lock:
                fcntl.lockf(lock, fcntl.LOCK_EX)
                release = threading.Timer(1.1, lambda: fcntl.lockf(lock, fcntl.LOCK_UN))
                release.start()
                try:
                    result = self.run_script(r'''
SANDBOX="$1"
apt-get() {
  if [[ "$1" == update ]]; then return 0; fi
  local options=()
  while (($#)); do
    if [[ "$1" == -o ]]; then options+=("$1" "$2"); shift 2; else shift; fi
  done
  # 不传软件包，所有状态和日志均在临时目录中；保留安装函数给出的原生等待参数。
  /usr/bin/apt-get "${options[@]}" \
    -o "Dir::State=$SANDBOX/state" \
    -o "Dir::State::status=$SANDBOX/state/status" \
    -o "Dir::State::lists=$SANDBOX/state/lists" \
    -o "Dir::Cache=$SANDBOX/cache" \
    -o 'Dir::Cache::pkgcache=' -o 'Dir::Cache::srcpkgcache=' \
    -o 'Dir::Etc::sourcelist=/dev/null' -o "Dir::Etc::sourceparts=$SANDBOX/sources" \
    -o "Dir::Log=$SANDBOX/logs" \
    install --assume-no
}
install_system_packages
''', root)
                finally:
                    release.join()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Waiting for cache lock", result.stdout + result.stderr)

    def test_default_selects_latest_24_lts_from_unsorted_manifest(self):
        with tempfile.TemporaryDirectory(prefix="nebula-env-test-") as temporary:
            root = Path(temporary)
            (root / "index.json").write_text(json.dumps([
                {"version": "v26.0.0", "lts": "Newer"},
                {"version": "v24.18.0", "lts": "Krypton"},
                {"version": "v24.21.0", "lts": False},
                {"version": "v24.20.0", "lts": "Krypton"},
            ]), encoding="utf-8")
            result = self.run_script(r'''
FIXTURE="$1"
trap cleanup EXIT
curl() { cp -- "$FIXTURE/index.json" "${@: -1}"; }
resolve_node_version
printf 'selected=%s\n' "$NODE_VERSION"
''', root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("selected=24.20.0", result.stdout)

    def test_manifest_without_24_lts_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="nebula-env-test-") as temporary:
            root = Path(temporary)
            (root / "index.json").write_text('[{"version":"v26.0.0","lts":false}]', encoding="utf-8")
            result = self.run_script(r'''
FIXTURE="$1"
trap cleanup EXIT
curl() { cp -- "$FIXTURE/index.json" "${@: -1}"; }
resolve_node_version
''', root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("没有 Node.js 24 LTS", result.stderr)

    def test_verified_install_and_repeat_without_redownload(self):
        with tempfile.TemporaryDirectory(prefix="nebula-env-test-") as temporary:
            root = Path(temporary)
            self.make_fixture(root)
            result = self.run_script(self.installation_body() + r'''
install_node x64
curl() { return 94; }
install_node x64
"$BIN_DIR/node" --version
''', root)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("复用 Node.js", result.stdout)
            for command in ("node", "npm", "npx"):
                self.assertTrue((root / "bin" / command).is_symlink())
                self.assertTrue((root / "bin" / command).exists())

    def test_checksum_failure_preserves_previous_runtime_link(self):
        with tempfile.TemporaryDirectory(prefix="nebula-env-test-") as temporary:
            root = Path(temporary)
            self.make_fixture(root)
            (root / "SHASUMS256.txt").write_text(f"{'0' * 64}  {DIRECTORY}.tar.xz\n", encoding="utf-8")
            (root / "bin").mkdir()
            old_node = root / "old-node"
            old_node.write_text("old runtime", encoding="utf-8")
            (root / "bin" / "node").symlink_to(old_node)
            result = self.run_script(self.installation_body() + "install_node x64\n", root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA256 校验失败", result.stderr)
            self.assertEqual((root / "bin" / "node").resolve(), old_node)
            self.assertFalse((root / "runtime" / DIRECTORY).exists())

    def test_existing_regular_command_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix="nebula-env-test-") as temporary:
            root = Path(temporary)
            self.make_fixture(root)
            (root / "bin").mkdir()
            existing = root / "bin" / "node"
            existing.write_text("managed elsewhere", encoding="utf-8")
            result = self.run_script(self.installation_body() + "install_node x64\n", root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("已有普通文件", result.stderr)
            self.assertEqual(existing.read_text(), "managed elsewhere")

    def test_check_rejects_old_node_in_active_path(self):
        result = self.run_script(r'''
python3() { return 0; }
node() { printf 'v20.0.0\n'; }
npm() { return 0; }
pnpm() { printf '11.13.0\n'; }
git() { return 0; }
sqlite3() { return 0; }
main --check
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("当前 PATH 中的 Node.js", result.stderr)


if __name__ == "__main__":
    unittest.main()
