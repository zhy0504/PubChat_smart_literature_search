# PubChat 一键部署

当前镜像适用于 Linux `amd64`，GHCR 镜像为公开包，不需要登录。脚本会优先检测 Docker Compose v2（`docker compose`），不可用时尝试使用兼容模式 `docker-compose`。

执行下面一条命令：

```bash
curl -fsSL https://raw.githubusercontent.com/zhy0504/PubChat_smart_literature_search/main/deploy/install.sh -o /tmp/pubchat-install.sh && bash /tmp/pubchat-install.sh
```

按提示输入部署目录、镜像标签、Web 端口、访问范围和 PostgreSQL 密码。默认是内网模式，只绑定自动检测到的私有 IP；未检测到内网 IP 时仅允许本机访问。选择公网模式前必须输入 `YES` 确认。

脚本会自动下载配置、拉取 GitHub 镜像、初始化数据库、启动服务并检查健康状态。完成后按脚本显示的地址访问：

```text
http://绑定地址:设置的端口
```

首次检索时，在“API 接口配置”中填写 AI API Key；需要使用自定义服务时勾选“使用自定义地址和模型”，填写 OpenAI 兼容接口地址和模型名称，例如：

```text
DeepSeek:    https://api.deepseek.com/v1            deepseek-chat
OpenRouter:  https://openrouter.ai/api/v1           google/gemini-3.1-flash-lite-preview
Ollama:      http://host.docker.internal:11434/v1   你的本地模型名
```

同时填写 NCBI PubMed API Key。

公网模式只负责监听所有网卡，不包含 HTTPS 或登录认证；公网使用时请自行配置反向代理、域名证书、登录认证和防火墙。升级时再次执行上面的命令即可；不要执行 `docker compose down -v`。
