# PubChat 一键部署

当前镜像适用于 Linux `amd64`，GHCR 镜像为公开包，不需要登录。脚本会自动检测并安装 Docker Engine 和 Docker Compose 插件（`docker compose` 命令）。

执行下面一条命令：

```bash
curl -fsSL https://raw.githubusercontent.com/zhy0504/PubChat_smart_literature_search/main/deploy/install.sh -o /tmp/pubchat-install.sh && bash /tmp/pubchat-install.sh
```

按提示输入部署目录、镜像标签、Web 端口、访问范围和 PostgreSQL 密码。默认是内网模式，只绑定自动检测到的私有 IP；未检测到内网 IP 时仅允许本机访问。选择公网模式前必须输入 `YES` 确认。

脚本会自动下载配置、拉取 GitHub 镜像、初始化数据库、启动服务并检查健康状态。完成后按脚本显示的地址访问：

```text
http://绑定地址:设置的端口
```

公网模式只负责监听所有网卡，不包含 HTTPS 或登录认证；公网使用时请自行配置反向代理、域名证书、登录认证和防火墙。升级时再次执行上面的命令即可；不要执行 `docker compose down -v`。
