# 生产更新流程

后端由 systemd 的 `blog-backend.service` 守护。以下示例使用 `/www/wwwroot/<domain>` 和服务用户 `www`；执行前核对实际 `WorkingDirectory`、服务用户、虚拟环境及 `.env` 中的数据库和存储路径。每步成功后再继续，迁移失败时保持服务停止。

## 停止写入并备份

进入维护期，暂停外部写请求，停止全部后端 worker、定时任务和其他数据库写入进程。记录当前代码提交，保留可回退的前端构建；不要覆盖运行数据或使用初始化脚本重新导入。

```bash
cd /www/wwwroot/<domain>
sudo systemctl stop blog-backend.service
cd blog-backend
backup_dir="/var/backups/nebula/$(date +%Y%m%d-%H%M%S)"
sudo install -d -o www -g www -m 700 "$backup_dir"
sudo -u www sqlite3 blog.db ".backup '$backup_dir/blog.db'"
sudo -u www cp .env "$backup_dir/.env"
sudo -u www tar -czf "$backup_dir/data-content-uploads.tar.gz" data content uploads
```

`blog.db` 和三个目录仅为默认路径，必须按实际 `DATABASE_URL`、`DATA_DIR`、`CONTENT_DIR`、`UPLOAD_DIR` 备份；前端 `.env.production` 等部署配置也要保留。备份目录放在网站根目录之外并限制读取权限。

SQLite 的 `.backup` 会生成包含已提交 WAL 数据的一致性快照。也可在停掉所有数据库进程、确认 checkpoint 成功且连接全部关闭后复制数据库。不要在 WAL 活跃时只 `cp blog.db`，否则可能丢失已提交内容；不要把不同时间的数据库、`-wal`、`-shm` 混合恢复。

## 更新依赖和前端

在当前已验证的部署分支更新代码，不要用 `reset --hard` 或 `clean` 清理运行数据：

```bash
cd /www/wwwroot/<domain>
sudo -u www git pull --ff-only
cd blog-backend
sudo -u www .venv/bin/python -m pip install -r requirements.txt
cd ../blog-frontend
sudo -u www pnpm install --frozen-lockfile
sudo -u www pnpm build
```

将 `dist/` 同步到实际 Nginx 网站根目录；若 Nginx 直接指向该目录，无需另行复制。保留服务器已有的环境配置、数据库、`data/`、`content/` 和 `uploads/`，媒体目录和 URL 路径保持原样。

### 修正说说/评论历史时间

说说数据保存在 `DATA_DIR/moments.json`，不是 SQLite。发布时间记录混有 UTC 与北京时间且没有时区标记；脚本以现有毫秒 `id` 为权威，将说说和评论的 `date` 改为对应的 UTC ISO 时间，不改 ID、正文、图片、点赞、评论关系或顺序。前台与后台再固定显示为北京时间。不要直接对全部记录统一加减 8 小时。

进入维护期并停止全部后端 worker；使用前文创建的受限备份目录（此处以 `$backup_dir` 表示），按实际 `DATA_DIR` 备份 JSON。更新代码后在 `blog-backend/` 使用服务用户和服务实际 Python 预览：

```bash
sudo systemctl stop blog-backend.service
cd /www/wwwroot/<domain>/blog-backend
sudo -u www cp -a data/moments.json "$backup_dir/moments.json.before-timezone-fix"
sudo -u www .venv/bin/python -m scripts.migrate_moment_timestamps
```

预览会报告待改日期数及无效 ID 数，不写文件。确认记录数与备份一致、无效 ID 为 0 后再执行：

```bash
sudo -u www .venv/bin/python -m scripts.migrate_moment_timestamps --apply
```

脚本会在同目录生成带 UTC 时间后缀的 `.bak-...` 原始备份，再以临时文件 + 原子替换写入，并对并发迁移使用 `moments.json.lock`。核对输出备份路径和 API 前三条时间，再按本节“启动和验收”恢复服务。若预览计数不符合预期，或看到无效 ID，先不要 `--apply`；保留原文件并查明记录来源。

## 先迁移，再启动 worker

使用服务实际运行的 Python 检查 SQLite **至少为 3.35**，并以服务用户确认 `DATA_DIR` 可创建临时文件。该目录还必须允许写入锁文件和原子替换 `friends.json`，否则启动或后续友链同步会失败。

```bash
cd /www/wwwroot/<domain>/blog-backend
sudo -u www .venv/bin/python -c "import sqlite3; print(sqlite3.sqlite_version); assert sqlite3.sqlite_version_info >= (3, 35, 0), 'SQLite >= 3.35 required'"
sudo -u www .venv/bin/python -c "import tempfile; from app.config import settings; settings.DATA_DIR.mkdir(parents=True, exist_ok=True); tempfile.TemporaryFile(dir=settings.DATA_DIR).close(); print('DATA_DIR writable')"
sudo -u www .venv/bin/python -m scripts.migrate
```

命令从后端工作目录读取同一份 `.env` 和 `DATABASE_URL`，执行生产配置校验及数据库结构迁移，成功后输出完成信息；配置或迁移失败时返回非零退出码。它不会启动 Web 应用、创建默认管理员、清理资源或重建 JSON。正常应用启动时会同步 `friends.json`。

本次认证切换为每个账户补齐内部 UUID `users.auth_id`，新刷新会话保存签发时的 `auth_id`，并记录 `schema_migrations` 中的 `20261023_auth_identity_uuid`。旧会话新加的 `auth_id` 保持空值，不按当前整数 ID 的占用者回填历史身份；已有非空值保留，尚未撤销的旧会话一次性撤销。原整数用户 ID、业务关联、用户资料和媒体路径保留。所有用户（含管理员）需重新登录一次；旧整数或用户名主体的访问令牌、旧邮箱验证链接不再接受，需要时重新发送验证邮件。

迁移的建表、升级和版本记录受文件锁及 SQLite `BEGIN IMMEDIATE` 事务保护，首次多个 worker 启动也会串行执行；生产仍应在启动 worker 前先运行此命令。重复运行不会改写已有 UUID，也不会再次撤销迁移后新建的会话。字段细节见[数据库说明](database.md)。

## 启动和验收

```bash
sudo systemctl start blog-backend.service
sudo systemctl status blog-backend.service --no-pager
sudo journalctl -u blog-backend.service -n 100 --no-pager
curl --fail --retry 15 --retry-connrefused --retry-delay 2 --max-time 5 --retry-max-time 90 http://127.0.0.1:8000/health
sudo nginx -t
sudo systemctl reload nginx
```

健康接口应返回 `{"status":"ok","database":"ok"}`。维护期内使用管理员和普通账户重新登录，检查刷新会话、评论、本人友链申请及管理操作；退出后确认匿名访问不能看到申请邮箱或审核信息，其他账户不能读取本人申请。核对图片、视频、图书、内容文件及友链 JSON 同步正常，再恢复写流量。生产使用 systemd 的无 reload Uvicorn，不运行开发入口 `python main.py`。

## 失败和回滚

任一步失败先保持维护状态，检查配置、权限和服务日志；迁移事务失败会回滚，可修复原因后重跑命令。回滚应在恢复写流量之前完成：停止全部相关进程，将代码和前端构建恢复到记录的版本，同时恢复与该版本匹配的数据库、`.env`、`data/`、`content/`、`uploads/`。先隔离失败版本的数据库及 WAL/SHM，避免旧事务文件污染备份；不要仅回退代码或仅覆盖数据库。

一旦恢复了写流量，就不能直接用旧备份覆盖：这会丢失新用户、评论和其他写入。应重新停写并保存当前完整数据，再制定数据保留方案。恢复过程中保留原用户 ID 和媒体路径，避免重建账户或批量改写文件地址。
