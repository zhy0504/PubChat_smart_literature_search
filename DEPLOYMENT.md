# PubChat Docker 自动构建与部署

这个 fork 已加入 GitHub Actions：向 `main` 推送代码时，会构建并推送两个 GHCR 镜像：

- `ghcr.io/zhy0504/pubchat-web`
- `ghcr.io/zhy0504/pubchat-search-server`

随后 Actions 通过 SSH 到服务器执行生产 Compose 更新。数据库、Redis、检索服务和 worker 都在同一个私有 Docker 网络中，部署使用提交 SHA 标签，而不是漂移的 `latest`。

## 服务器准备

在服务器安装 Docker Engine 和 Compose v2，创建部署目录，例如 `/opt/pubchat`，并将 `deploy/.env.example` 复制为 `/opt/pubchat/.env` 后填写真实值。至少需要修改 `POSTGRES_PASSWORD`，并补充实际使用的模型服务密钥。

将 `db/postgres/init.sql` 放到 `/opt/pubchat/../db/postgres/init.sql` 对应的位置，或把仓库根目录同步到服务器后在仓库根目录执行 Compose。最简单的目录布局是：

```text
/opt/pubchat/
  .env
  docker-compose.prod.yml
  init.sql
```

Actions 会自动把 `docker-compose.prod.yml` 和 `db/postgres/init.sql` 上传到这个目录。

## GitHub Secrets

在 fork 的 `Settings -> Secrets and variables -> Actions` 中设置：

- `DEPLOY_HOST`：服务器域名或 IP
- `DEPLOY_PORT`：SSH 端口，可填 `22`
- `DEPLOY_USER`：部署用户
- `DEPLOY_PATH`：服务器部署目录，例如 `/opt/pubchat`
- `DEPLOY_SSH_KEY`：部署用户私钥
- `DEPLOY_KNOWN_HOSTS`：服务器的 SSH 主机指纹
- `GHCR_USERNAME`、`GHCR_TOKEN`：当 GHCR 镜像为私有时填写；令牌只需 `read:packages`

再在 `Settings -> Secrets and variables -> Actions -> Variables` 中新增 `DEPLOY_ENABLED=true`。未设置这个变量时，推送仍会自动构建并推送镜像，但不会尝试连接服务器。

首次运行前，确保服务器目录中已经有 `.env`。之后每次合并到 `main`，Actions 会构建镜像、推送 GHCR，并在服务器执行：

```bash
IMAGE_TAG=sha-<commit> docker compose --env-file .env -f docker-compose.prod.yml pull
IMAGE_TAG=sha-<commit> docker compose --env-file .env -f docker-compose.prod.yml up -d --remove-orphans
```

## 当前仓库边界

上游仓库没有提交前端源码和 Celery worker 源码。前端镜像因此直接使用已提交的 `frontend/dist`，构建时把 API 地址改为同源 `/api/search`；worker 继续使用 `wuyuxuan1037/pubchat-celery-worker:latest`，Actions 不会假装编译不存在的 worker 源码。要实现完整源码构建，需要先从上游取得这两部分源码，再补充对应 Dockerfile 和 workflow job。

公开部署前还应配置 HTTPS、访问控制和日志/备份策略；当前 API 路由没有真正启用用户鉴权，不能直接当作多用户公网服务使用。
