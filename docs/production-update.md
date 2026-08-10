# 生产更新流程

当前服务器使用 systemd 服务 `blog-backend.service` 守护后端 Uvicorn（两个 worker）。

## 更新后端

```bash
cd /www/wwwroot/<domain>
sudo systemctl stop blog-backend.service
sudo -u www git pull --ff-only origin main

cd blog-backend
sudo -u www .venv/bin/python -m compileall app
sudo systemctl start blog-backend.service
sudo systemctl status blog-backend.service --no-pager
sudo journalctl -u blog-backend.service -n 100 --no-pager
curl http://127.0.0.1:8000/health
```

不要覆盖服务器已有的 `.env`、`blog.db` 和 `uploads/`。更新前备份：

```bash
cd /www/wwwroot/<domain>/blog-backend
sudo cp .env ".env.backup.$(date +%Y%m%d-%H%M%S)"
sudo cp blog.db "blog.db.backup.$(date +%Y%m%d-%H%M%S)" 2>/dev/null || true
sudo tar -czf "uploads.backup.$(date +%Y%m%d-%H%M%S).tar.gz" uploads
```

应用启动时会自动执行兼容数据库迁移并创建 `uploads/backgrounds/`。生产环境不要使用
`python main.py`（开发入口会启用 reload），由 systemd 调用无 reload 的 Uvicorn。

## 前端发布

```bash
cd blog-frontend
pnpm install
pnpm type-check
pnpm build
```

将 `dist/` 内容同步到 Nginx 网站根目录，然后检查并重载 Nginx：

```bash
sudo nginx -t
sudo systemctl reload nginx
```
