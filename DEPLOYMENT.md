# PubChat 一键部署

当前镜像适用于 Linux `amd64`，GHCR 镜像为公开包，不需要登录。脚本会自动检测 Docker Engine 和 Docker Compose v2；缺少时询问是否安装，支持 Ubuntu/Debian 及 RHEL/CentOS 系列，需要 root 或 sudo 权限。

执行下面一条命令：

```bash
curl -fsSL https://raw.githubusercontent.com/zhy0504/PubChat_smart_literature_search/main/deploy/install.sh -o /tmp/pubchat-install.sh && bash /tmp/pubchat-install.sh
```

按提示输入部署目录、镜像标签、Web 端口和 PostgreSQL 密码。密码直接回车会自动生成；已有部署会保留原来的 `.env` 和数据。

脚本会自动下载配置、拉取 GitHub 镜像、启动服务并检查健康状态。完成后访问：

```text
http://服务器IP:设置的端口
```

升级时再次执行上面的命令，输入新的镜像标签即可。不要执行 `docker compose down -v`，否则会删除数据库和检索结果。
