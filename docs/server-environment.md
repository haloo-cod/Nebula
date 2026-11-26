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

- 真实生产 `.env` 和 SQLite 一致性备份（默认恢复为 `blog.db`）。使用 SQLite `.backup`，或停掉全部数据库进程并确认 checkpoint 完成后备份；不能使用在线仅复制 `blog.db` 的文件，也不能混用不同备份的 WAL/SHM。
- `uploads/`、`content/`、`data/` 整个目录。

源站备份时先停止写入，完整步骤见[生产更新流程](production-update.md)。恢复时沿用原用户 ID、媒体路径和 `.env` 中的实际数据库／存储目录，不运行初始化脚本重建账户或覆盖内容。

前端实际使用的 `.env.production` 等环境配置恢复到 `repo/blog-frontend/`。同域部署的 `VITE_API_BASE_URL` 留空。
R2 继续使用原桶及媒体域名时，保留原 `.env` 中的凭据和配置。

Python 虚拟环境需要在新机重建。恢复备份时只复制上述数据，不复制旧 `.venv`、`node_modules` 或缓存目录。

```bash
cd /www/wwwroot/starlitn.top/repo/blog-backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

核对 systemd 的服务用户和 Python 路径。以下以 `www` 为例，必须使用服务实际运行的 `.venv/bin/python` 确认其 SQLite **至少为 3.35**，不能仅检查系统 `sqlite3` 命令的版本：

```bash
sudo -u www .venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version); assert sqlite3.sqlite_version_info >= (3, 35, 0), 'SQLite >= 3.35 required'"
sudo -u www .venv/bin/python -c "import tempfile; from app.config import settings; settings.DATA_DIR.mkdir(parents=True, exist_ok=True); tempfile.TemporaryFile(dir=settings.DATA_DIR).close(); print('DATA_DIR writable')"
```

`DATA_DIR`（默认 `data/`）须允许服务用户创建锁和临时文件、原子替换 `friends.json`。数据库及其所在目录也必须可写；不要通过 root 运行应用来绕过权限问题。

前端在服务器安装依赖并构建：

```bash
cd /www/wwwroot/starlitn.top/repo/blog-frontend
pnpm install --frozen-lockfile
pnpm build
```

首次上线使用的生产数据来自备份；不要运行 `scripts.init_* --force` 覆盖已有内容。启动任何 worker 前，在后端工作目录以服务用户执行：

```bash
cd /www/wwwroot/starlitn.top/repo/blog-backend
sudo -u www .venv/bin/python -m scripts.migrate
```

命令使用当前 `.env`、数据库引擎和生产配置校验，只迁移结构；不会导入 `app.main`、运行启动流程、创建管理员、清理资源或修改 JSON。成功后再启动服务，配置或迁移失败时保持停止。建表与升级通过文件锁和 SQLite `BEGIN IMMEDIATE` 串行处理，支持多 worker 首次启动；仍应先运行 CLI，重复运行安全。

认证迁移会生成内部 `users.auth_id`，新刷新会话保存签发时的 `auth_id`，并一次性记录 `20261023_auth_identity_uuid`、撤销旧刷新会话。旧会话新增的 `auth_id` 保持空值，不用当前整数 ID 对应的用户回填历史身份，已有非空值保留。所有用户需重新登录一次；旧整数／用户名主体 JWT 和旧邮箱验证链接不再接受，需要时重新发送验证邮件。整数用户 ID、资料、关联和媒体路径保留，UUID 与迁移标记不新增到用户资料 API。正常启动仍会从数据库重建正式友链 JSON 副本。

恢复 Nginx 和 `blog-backend.service` 后，核对站点目录、`WorkingDirectory`、虚拟环境路径、服务用户和文件权限。
旧宝塔的 `www` 用户及其 Nginx `include` 路径在纯 Ubuntu 上可能不存在，需要调整；SQLite 所在目录也要允许后端服务用户写入。
小服务器先使用一个 Uvicorn worker（`--workers 1`）。迁移成功并确认 `nginx -t` 通过后再启动服务；保持维护状态验证健康检查、管理员和普通账户登录／刷新、图片、视频、图书及后台读写，并确认匿名和其他账户不能看到申请邮箱等私有数据，完成后才恢复写流量。

## 4. 后续更新

每次更新先进入维护期、暂停写流量，停止全部后端 worker 和其他写库进程。确认 `git status` 没有需要保留的代码改动，记录当前提交和前端构建，再按[生产更新流程](production-update.md)使用 `.backup` 备份数据库，并保存 `.env`、`data/`、`content/`、`uploads/` 及前端部署配置。下面各步成功后再继续下一步；更新失败保持服务停止，避免反复重启。

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

先确认上述 SQLite 版本与目录权限检查仍通过，再从后端工作目录以服务用户迁移；不要在拉起多个 worker 的同时手工改库：

```bash
cd /www/wwwroot/starlitn.top/repo/blog-backend
sudo -u www .venv/bin/python -m scripts.migrate
```

退出码为零后启动并等待数据库就绪：

```bash
systemctl start blog-backend.service
```

```bash
curl --fail --retry 15 --retry-connrefused --retry-delay 2 --max-time 5 --retry-max-time 90 http://127.0.0.1:8000/health
```

正常返回 `{"status":"ok","database":"ok"}` 后，按上述登录、刷新、媒体和私有申请检查验收，再恢复写流量。本次 UUID 迁移仅使用户首次重新登录，重跑迁移不会更换 UUID 或撤销新会话。启动失败时查看：

```bash
journalctl -u blog-backend.service -n 100 --no-pager
```

失败时的回滚只在写流量恢复前进行：停掉全部数据库进程，将代码、前端构建和匹配的数据库／`.env`／数据目录一并恢复，隔离失败版本的 WAL/SHM，保留原 ID 和路径。恢复写入后不要直接覆盖旧备份，应先停写并保存当前完整数据，再处理新增数据的保留和恢复。

## 双域名的 GitHub 登录

同一个博客的 `starlitn.top`、`blog.starlitn.top` 可共用同一 GitHub OAuth App。保留一个固定回调域名，并确保 GitHub 应用中登记的回调 URL 与后端配置一致：

```dotenv
GITHUB_CALLBACK_URL=https://starlitn.top/api/v1/auth/github/callback
FRONTEND_URL=https://starlitn.top
COOKIE_SECURE=true
```

从别名访问 `/api/v1/auth/github` 时，后端先跳转到配置的回调主机，再创建 state 并跳转 GitHub。授权回调在同一主机校验 host-only、HttpOnly Cookie，完成后回到 `FRONTEND_URL`。因此两个域名都能作为登录入口，GitHub 登录流程最终统一在主域完成；不会让两个浏览器源的 localStorage 自动共用。

Nginx 的 `/api/` 代理保留实际 Host，现有示例已包含 `proxy_set_header Host $host;`。主机匹配不依赖源站收到的 HTTP/HTTPS 协议，因此兼容 Cloudflare Flexible 外部 HTTPS、源站 HTTP 的部署，避免协议判断造成跳转循环。登录发起响应禁止缓存。

以前从 `blog` 发起、回到主域的流程会丢失 state Cookie，并返回 `OAuth state 无效`。不要仅将固定回调改为另一个入口域名；应更新包含上述修复的后端代码、重启服务，再从登录按钮重新发起流程。本次修复无需新增数据库迁移或修改现有账户。

GitHub 应用的授权用户数与本地 `users.github_id` 已绑定账号数量不是同一统计。用户可在 GitHub 完成授权，但在本站的 state 校验、资料请求或同邮箱密码账号绑定确认阶段失败/中断；此时不会新增成功绑定的本地 GitHub 账号。授权阶段与本站回调步骤见 [GitHub 官方流程](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)。仅凭人数差异不能判断具体哪个账号失败，需要结合对应回调结果核对。

本地认证回归使用独立测试数据库和模拟 GitHub 响应：

```bash
python -B -m pytest -q tests/test_github_oauth_domains.py tests/test_auth_identity.py
```

## 脚本验证

安装脚本的隔离测试使用 Bash 与 Python 标准库，模拟网络和软件包命令，不安装系统软件：

```bash
python3 -m unittest discover -s scripts/tests -v
```

版本与安装方式参考 [Node.js 官方发布清单](https://nodejs.org/dist/index.json)、[pnpm 安装说明](https://pnpm.io/installation) 和 [Ubuntu APT 文档](https://ubuntu.com/server/docs/how-to/software/package-management/)。
