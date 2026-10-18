# Ubuntu 24.04 服务器环境与仓库更新

适用于 Ubuntu 24.04、x86_64 或 ARM64、2GB 内存的服务器。代码从 GitHub 拉取，生产数据手动上传。

## 1. 安装环境

将仓库中的 `scripts/setup-ubuntu-env.sh` 上传到新服务器，例如 `/root/setup-ubuntu-env.sh`，执行：

```bash
bash /root/setup-ubuntu-env.sh
```

普通用户执行时在命令前加 `sudo`。首次运行需要访问 Ubuntu 软件源、nodejs.org 和 registry.npmjs.org。

新机的 `unattended-upgrades` 可能正在自动更新系统。安装软件遇到 dpkg 锁时，脚本会等待最多 10 分钟；
若等待超时，先让系统更新完成，再重新运行脚本。不要删除锁文件或强行终止更新进程。

脚本安装：

- 系统 Python 3.12、venv、pip；Python 项目依赖装在项目自己的 `.venv` 中。
- Node.js **24 LTS 的最新补丁版本**，从官方发布清单解析版本，下载二进制包并检查 SHA256。
- pnpm **11.13.0**，与本项目当前开发工具链一致，兼容仓库的锁文件和 `allowBuilds` 配置。
- Git、SQLite、curl、rsync，以及常用原生依赖的编译工具和系统库。

Node.js 位于 `/opt/nebula-runtime/`，全局命令位于 `/usr/local/bin/`，适用于后续 SSH 会话。
同版本重复运行会复用已安装的 Node.js 和 pnpm；存在冲突的普通命令文件或不完整目录时会报错，交由部署者检查。

预览和检查：

```bash
bash /root/setup-ubuntu-env.sh --dry-run
```

```bash
bash /root/setup-ubuntu-env.sh --check
```

再次运行默认安装会跟进 Node.js 24 LTS 的新补丁，pnpm 保持固定版本。
需要复现某个环境时可指定完整版本；下面的版本号仅为格式示例，实际应选择经过验证且含所需安全补丁的版本：

```bash
bash /root/setup-ubuntu-env.sh --node-version 24.18.0 --pnpm-version 11.13.0
```

脚本只负责工具链。网站的 Nginx、systemd 配置按备份和实际目录另行恢复，参见 [部署指南](deployment.md)。

## 2. 从 GitHub 拉取代码

沿用原服务器目录，减少数据库中绝对路径和旧部署配置的改动。以下命令以 root 用户为例：

```bash
mkdir -p /www/wwwroot/starlitn.top
```

```bash
git clone --branch dev --single-branch https://github.com/haloo-cod/Nebula.git /www/wwwroot/starlitn.top/repo
```

仓库已存在时直接使用现有检出，先确认 `git status` 和当前分支，再执行 `git pull --ff-only origin dev`。
不要用 `git reset --hard` 或 `git clean -fdx` 更新生产站点，避免丢失本地改动或被忽略的运行数据。

## 3. 恢复备份并安装项目依赖

恢复到 `repo/blog-backend/`：

- 真实生产 `.env`、`blog.db` 及停止旧服务后仍存在的数据库事务文件。
- `uploads/`、`content/`、`data/` 整个目录。

前端实际使用的 `.env.production` 等环境配置恢复到 `repo/blog-frontend/`。同域部署的 `VITE_API_BASE_URL` 留空。
R2 继续使用原桶及媒体域名时，保留原 `.env` 中的凭据和配置。

Python 虚拟环境需要在新机重建。恢复备份时只复制上述数据，不复制旧 `.venv`、`node_modules` 或缓存目录。

```bash
cd /www/wwwroot/starlitn.top/repo/blog-backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

前端在服务器安装依赖并构建：

```bash
cd /www/wwwroot/starlitn.top/repo/blog-frontend
pnpm install --frozen-lockfile
pnpm build
```

首次上线使用的生产数据来自备份；不要运行 `scripts.init_* --force` 覆盖已有内容。

恢复 Nginx 和 `blog-backend.service` 后，核对站点目录、`WorkingDirectory`、虚拟环境路径、服务用户和文件权限。
旧宝塔的 `www` 用户及其 Nginx `include` 路径在纯 Ubuntu 上可能不存在，需要调整；SQLite 所在目录也要允许后端服务用户写入。
小服务器先使用一个 Uvicorn worker（`--workers 1`）。确认 `nginx -t` 通过，再启动服务和验证图片、视频、图书及后台读写。

## 4. 后续更新

每次更新前备份运行数据并确认 `git status` 没有需要保留的代码改动。下面各步成功后再继续下一步；更新失败时查看报错后处理，避免反复重启。

停止后端后拉取同一分支：

```bash
systemctl stop blog-backend.service
cd /www/wwwroot/starlitn.top/repo
git pull --ff-only origin dev
```

更新后端依赖：

```bash
cd /www/wwwroot/starlitn.top/repo/blog-backend
.venv/bin/python -m pip install -r requirements.txt
```

更新前端依赖并构建：

```bash
cd /www/wwwroot/starlitn.top/repo/blog-frontend
pnpm install --frozen-lockfile
pnpm build
```

如果 Nginx 直接指向 `blog-frontend/dist`，新构建即为发布内容；若网站根目录是其他目录，将构建结果同步到该目录。
运行依赖安装和构建的用户需要有对应目录写权限；服务仍使用配置中的非 root 用户运行。

启动并等待数据库就绪：

```bash
systemctl start blog-backend.service
```

```bash
curl --fail --retry 15 --retry-connrefused --retry-delay 2 --max-time 5 --retry-max-time 90 http://127.0.0.1:8000/health
```

正常返回 `{"status":"ok","database":"ok"}` 后，再验证页面及媒体。启动失败时查看：

```bash
journalctl -u blog-backend.service -n 100 --no-pager
```

## 脚本验证

安装脚本的隔离测试使用 Bash 与 Python 标准库，模拟网络和软件包命令，不安装系统软件：

```bash
python3 -m unittest discover -s scripts/tests -v
```

版本与安装方式参考 [Node.js 官方发布清单](https://nodejs.org/dist/index.json)、[pnpm 安装说明](https://pnpm.io/installation) 和 [Ubuntu APT 文档](https://ubuntu.com/server/docs/how-to/software/package-management/)。
