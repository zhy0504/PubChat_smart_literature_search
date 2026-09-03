# PubChat Smart Literature Search Project User Guide

## 🇬🇧 English Version

### 1. Prerequisites
1. A stable international network access environment is recommended throughout installation and use, so that GitHub, Docker Hub, and related model services remain accessible. Otherwise, Docker image pulling or service requests may fail.

2. Please ensure **Docker**  https://www.docker.com   is installed and running on your local machine (start Docker Desktop for Win / macOS then continue following steps).

3. Before first use, register an account at [OpenRouter](https://openrouter.ai/). Registration and payment setup should be completed in a stable overseas network environment. If payment is required, use a valid U.S. billing address that matches your payment method.

### 2. Quick Start Steps
1.  **Mac/Linux User**
    Open ‘Terminal’, copy the command below and press ’Enter‘：
```bash
curl -L -o PubChat.zip https://github.com/PubChatOfficial/PubChat_smart_literature_search/archive/refs/heads/main.zip && unzip -q PubChat.zip && cd PubChat_smart_literature_search-main && if ! docker image inspect python:3.11-slim >/dev/null 2>&1; then docker pull python:3.11-slim; fi && if docker image inspect wuyuxuan1037/pubchat-celery-worker:latest >/dev/null 2>&1; then docker image rm -f wuyuxuan1037/pubchat-celery-worker:latest; fi && docker compose up -d --build && rm ../PubChat.zip

```

2.  **Windows User**
    Press the ’Win‘ key, search for ’PowerShell‘, open it, then copy the command below and press ’Enter‘. Please do not install the software on the system drive, as installation is prone to failure due to permission issues.：
```bash
Invoke-WebRequest -Uri "https://github.com/PubChatOfficial/PubChat_smart_literature_search/archive/refs/heads/main.zip" -OutFile "PubChat.zip"; Expand-Archive -Path "PubChat.zip" -DestinationPath "." -Force; Set-Location "PubChat_smart_literature_search-main"; docker image inspect python:3.11-slim *> $null; if ($LASTEXITCODE -ne 0) { docker pull python:3.11-slim }; docker image inspect wuyuxuan1037/pubchat-celery-worker:latest *> $null; if ($LASTEXITCODE -eq 0) { docker image rm -f wuyuxuan1037/pubchat-celery-worker:latest }; docker compose up -d --build; Remove-Item "..\PubChat.zip" -Force
 ```
    

### 3. Access the Application
Once the services are ready, open your browser and visit:   
    http://localhost:8000

### 4. Stop the Services
1. To stop or restart the service, please go to **Containers** in the left sidebar of **Docker Desktop**, locate the container named `pubchat_smart_literature_search-main`, and click its restart or stop button.

2. To uninstall the project, run this command in the project root directory. Containers will shut down automatically:
```bash
docker compose down
```


---


# PubChat 智能文献检索项目使用指南


## 🇨🇳 中文版

### 一、环境准备
1. 安装及使用过程中，请确保具备稳定的国际网络访问环境，以便正常访问 GitHub、Docker Hub 及相关模型服务；网络条件不满足时，可能出现镜像拉取或服务调用失败。

2. 请确保本地已安装 **Docker**  https://www.docker.com  ， 并且 Docker 服务处于**正常运行状态**（Win / macOS 用户启动 Docker Desktop 再进行后续操作）。

3. 首次使用前，请前往 [OpenRouter](https://openrouter.ai/) 注册账号。注册及付款设置建议在稳定的海外网络环境中完成；如需付款，请填写与支付方式一致的有效美国账单地址。

### 二、快速启动步骤
1.  **Mac/Linux用户**
    打开**“终端 (Terminal)”，复制粘贴这一整行**代码并回车：
```bash
curl -L -o PubChat.zip https://github.com/PubChatOfficial/PubChat_smart_literature_search/archive/refs/heads/main.zip && unzip -q PubChat.zip && cd PubChat_smart_literature_search-main && if ! docker image inspect python:3.11-slim >/dev/null 2>&1; then docker pull python:3.11-slim; fi && if docker image inspect wuyuxuan1037/pubchat-celery-worker:latest >/dev/null 2>&1; then docker image rm -f wuyuxuan1037/pubchat-celery-worker:latest; fi && docker compose up -d --build && rm ../PubChat.zip
```

2.  **Win用户**
    按 Win键，搜索 PowerShell并打开，然后复制粘贴这一整行代码并回车。请勿在系统盘符下进行安装，容易因为权限问题而安装失败：
```bash
Invoke-WebRequest -Uri "https://github.com/PubChatOfficial/PubChat_smart_literature_search/archive/refs/heads/main.zip" -OutFile "PubChat.zip"; Expand-Archive -Path "PubChat.zip" -DestinationPath "." -Force; Set-Location "PubChat_smart_literature_search-main"; docker image inspect python:3.11-slim *> $null; if ($LASTEXITCODE -ne 0) { docker pull python:3.11-slim }; docker image inspect wuyuxuan1037/pubchat-celery-worker:latest *> $null; if ($LASTEXITCODE -eq 0) { docker image rm -f wuyuxuan1037/pubchat-celery-worker:latest }; docker compose up -d --build; Remove-Item "..\PubChat.zip" -Force

```

### 三、访问应用
服务启动成功后，打开浏览器，访问以下地址：
    http://localhost:8000

### 四、停止服务
1. 如需停止或者重启服务，请点击在**Docker Desktop**左侧边栏的**Container**里的容器列表，找到`pubchat_smart_literature_search-main`的重启/关闭按钮。

2. 如需关闭项目，在项目根目录执行，容器会自动关闭退出：
```bash
docker compose down
```

## 联系

欢迎关注微信公众号，获取项目更新与使用交流：

<img src="docs/yixue-ai-ganhuo-wechat-qrcode.jpg" alt="医学AI干货微信公众号二维码" width="50%">
