# PubChat Docker 自动构建与手动部署

这个 fork 的 GitHub Actions 只负责构建并推送 Docker 镜像，不连接服务器、不执行远程部署。向 `main` 推送代码，或推送 `v*.*.*` 标签时，会发布两个 GHCR 镜像：

- `ghcr.io/zhy0504/pubchat-web`
- `ghcr.io/zhy0504/pubchat-search-server`

镜像标签包括 `latest`、提交短 SHA（例如 `sha-8196a48`）和版本标签。生产环境建议使用提交 SHA 标签，便于回滚。

## 服务器准备

服务器需要 Docker Engine 和 Compose v2。创建部署目录，例如 `/opt/pubchat`，并准备以下文件：

```text
/opt/pubchat/
  .env
  docker-compose.prod.yml
  init.sql
```

首次准备可以从仓库复制：

```bash
git clone https://github.com/zhy0504/PubChat_smart_literature_search.git /opt/pubchat-src
mkdir -p /opt/pubchat
cp /opt/pubchat-src/deploy/docker-compose.prod.yml /opt/pubchat/docker-compose.prod.yml
cp /opt/pubchat-src/db/postgres/init.sql /opt/pubchat/init.sql
cp /opt/pubchat-src/deploy/.env.example /opt/pubchat/.env
```

编辑 `/opt/pubchat/.env`，至少替换 `POSTGRES_PASSWORD`，并填写实际使用的模型服务配置。不要把真实密钥提交回 GitHub。

## 手动拉取并启动

如果 GHCR 镜像为私有，先在服务器登录一次：

```bash
echo '<GHCR_READ_TOKEN>' | docker login ghcr.io -u '<GITHUB_USERNAME>' --password-stdin
```

然后选择要部署的镜像标签：

```bash
cd /opt/pubchat
export IMAGE_TAG=sha-8196a48
docker compose --env-file .env -f docker-compose.prod.yml pull
docker compose --env-file .env -f docker-compose.prod.yml up -d --remove-orphans
docker compose --env-file .env -f docker-compose.prod.yml ps
```

只想跟随最新构建时，将 `IMAGE_TAG` 改为 `latest`。更新版本时重复执行拉取和启动命令即可；数据库、Redis、文档和日志保存在命名卷中。

## 当前仓库边界

上游仓库没有提交前端源码和 Celery worker 源码。前端镜像因此直接使用已提交的 `frontend/dist`，构建时把 API 地址改为同源 `/api/search`；worker 继续使用 `wuyuxuan1037/pubchat-celery-worker:latest`，Actions 不会假装编译不存在的 worker 源码。要实现完整源码构建，需要先从上游取得这两部分源码，再补充对应 Dockerfile 和 workflow job。

公开部署前还应配置 HTTPS、访问控制和日志/备份策略；当前 API 路由没有真正启用用户鉴权，不能直接当作多用户公网服务使用。
