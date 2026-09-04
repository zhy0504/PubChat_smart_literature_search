# PubChat：可溯源的多语言生物医学文献智能检索

[中文](README.md) | [English](README.en.md)

PubChat 是一个以 **PubMed** 为数据基础的生物医学文献检索与筛选工具。用户只需输入自然语言研究问题，系统即可完成问题拆解、检索式生成、多轮检索、文献去重、语义预筛选、大模型复核和相关性分层。

与直接让大语言模型“生成参考文献”不同，PubChat 只对 PubMed 检出的真实记录进行筛选与排序，让结果能够回到原始数据库核验，从源头降低虚构引用风险。

> PubChat 适合辅助文献检索与初筛，但不能替代研究人员的专业判断，也不能替代规范的系统综述流程。

## 主要功能

- **自然语言检索**：直接输入临床或科研问题，无需从零编写复杂检索式。
- **动态多轮检索**：自动拆解研究问题、生成并迭代 PubMed 检索式，提高文献覆盖度。
- **五级相关性分层**：根据研究问题建立相关性标准，对候选文献进行分层整理。
- **语义预筛选与三轮复核**：结合语义模型和大语言模型进行多阶段筛选，减少人工阅读负担。
- **三种检索模式**：可根据任务需要，在“尽可能找全”和“聚焦高度相关文献”之间进行选择。
  - `Broad`：优先提高召回率，适合探索性检索和系统综述前期。
  - `Standard`：兼顾召回率与精确率，适合多数日常科研任务。
  - `Core`：聚焦高度相关文献，适合快速把握核心证据。
- **八种输出语言**：支持中文、英文、西班牙文、法文、葡萄牙文、意大利文、德文和俄文。
- **本地 Docker 部署**：通过浏览器使用，便于个人电脑或机构内部环境部署。

![PubChat 系统架构与研究设计](docs/pubchat-system-architecture.png)

*PubChat 系统架构与研究设计：从自然语言问题生成五级相关性标准，再通过动态检索式生成、PubMed 多轮检索、文献去重、语义预筛选和三轮大模型复核完成文献分层（来源：原论文 Fig. 5）。*

## 为什么使用 PubChat

### 1. 文献真实、结果可核验

所有候选文献均来自 PubMed，而非由模型凭空生成。使用者可以依据 PMID 等信息返回数据库核查来源。

### 2. 检索策略可调节

Broad、Standard 和 Core 三种模式分别对应不同的召回率与精确率取向，可适配系统综述、课题调研、临床问题检索和研究方向探索等场景。

### 3. 降低重复劳动

PubChat 将检索式设计、反复检索、去重、初筛和相关性判断串联为一个流程，帮助研究者把更多时间用于全文阅读、证据评价和科研决策。

### 4. 面向真实科研流程验证

相关研究以 20 项 Cochrane 系统综述中的 585 篇 PubMed 收录文献作为金标准，并与多款主流 AI 文献检索工具进行比较。在该基准测试中：

- PubChat-Broad 的召回率为 `0.734`，nDCG 为 `0.441`，均为参评工具中的最高值。
- PubChat-Core 取得最高的 F1 和 F2 综合评分。
- PubChat 检出的文献均可通过 PubMed 核验，测试中未出现虚构引用。

![PubChat 与主流 AI 文献检索工具的性能比较](docs/pubchat-benchmark-performance.jpg)

*PubChat 与多款主流 AI 文献检索工具的召回率和精确率比较（来源：原论文 Fig. 2C-D）。*

研究还纳入来自 18 个国家和地区的 279 名生物医学研究人员。PubChat 在可靠性、创新性、效率、用户体验和总体满意度等维度的评分均超过 80 分。

![PubChat 用户评价结果](docs/pubchat-user-assessment.png)

*用户评价核心结果：左侧为各评价维度的评分分布，右侧为 PubChat 与专业工具、通用大语言模型及传统人工检索的主观比较（来源：原论文 Fig. 4D-E）。*

> 上述结果来自论文设定的基准与用户研究，不代表所有主题、网络环境或模型配置下均能得到相同表现。

## 适用场景

- 系统综述或 Meta 分析的前期检索与文献初筛
- 临床问题、指南证据和研究进展的快速检索
- 课题设计、开题报告及基金申请前的文献调研
- 新研究方向的证据脉络梳理与研究空白探索
- 多语言科研团队的文献检索与结果整理

## 使用边界

- 当前以 PubMed 为核心数据源，不能完整覆盖灰色文献、会议论文及其他专业数据库。
- 自动分层结果仍需研究人员结合全文、纳排标准和专业背景进行复核。
- 涉及诊疗决策时，应结合临床指南、原始研究和专业人员判断，不应仅依赖自动检索结果。
- 大模型调用会使用所选服务商的 API，请勿提交患者隐私或其他敏感信息，并遵循所在机构的数据管理要求。

## 环境准备

1. **国际网络访问环境**

   安装及使用过程中，请确保具备稳定的国际网络访问环境，以便正常访问 GitHub、Docker Hub、PubMed 及相关模型服务。网络条件不满足时，可能出现项目下载、镜像拉取或模型调用失败。

2. **Docker**

   请安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/) 并确保 Docker 服务正常运行。Windows 和 macOS 用户请先启动 Docker Desktop，再继续安装。

3. **OpenRouter 账号及 API Key**

   - 前往 [OpenRouter](https://openrouter.ai/) 注册账号。
   - 注册及付款设置建议在稳定的海外网络环境中完成。
   - 如需付款，账单地址需使用与支付方式一致的有效美国地址。
   - 注册完成后，在 [OpenRouter API Keys](https://openrouter.ai/workspaces/default/keys) 页面创建并复制 API Key；进入 PubChat 后选择 `OpenRouter · Gemini` 并填写该 Key。
   - API Key 属于敏感凭据，请勿公开、截图分享或提交到 Git 仓库。

## 快速安装

### macOS / Linux

打开“终端（Terminal）”，复制并运行下面的完整命令：

```bash
curl -L -o PubChat.zip https://github.com/PubChatOfficial/PubChat_smart_literature_search/archive/refs/heads/main.zip && unzip -q PubChat.zip && cd PubChat_smart_literature_search-main && if ! docker image inspect python:3.11-slim >/dev/null 2>&1; then docker pull python:3.11-slim; fi && if docker image inspect wuyuxuan1037/pubchat-celery-worker:latest >/dev/null 2>&1; then docker image rm -f wuyuxuan1037/pubchat-celery-worker:latest; fi && docker compose up -d --build && rm ../PubChat.zip
```

### Windows

建议不要安装在系统盘目录，以免因权限问题导致安装失败。按 `Win` 键，搜索并打开 PowerShell，然后运行：

```powershell
Invoke-WebRequest -Uri "https://github.com/PubChatOfficial/PubChat_smart_literature_search/archive/refs/heads/main.zip" -OutFile "PubChat.zip"; Expand-Archive -Path "PubChat.zip" -DestinationPath "." -Force; Set-Location "PubChat_smart_literature_search-main"; docker image inspect python:3.11-slim *> $null; if ($LASTEXITCODE -ne 0) { docker pull python:3.11-slim }; docker image inspect wuyuxuan1037/pubchat-celery-worker:latest *> $null; if ($LASTEXITCODE -eq 0) { docker image rm -f wuyuxuan1037/pubchat-celery-worker:latest }; docker compose up -d --build; Remove-Item "..\PubChat.zip" -Force
```

首次安装需要下载 Docker 镜像，耗时取决于网络状况。请等待相关容器启动完成。

## 开始使用

1. 在浏览器中打开 <http://localhost:8000>。
2. 选择模型服务并填写对应的 API Key；使用 OpenRouter 时请选择 `OpenRouter · Gemini`。
3. 输入需要检索的医学或科研问题。
4. 根据任务选择 Broad、Standard 或 Core 模式，并设置输出语言。
5. 提交任务，等待系统完成检索、筛选与分层。
6. 在结果页面核查文献信息，并下载需要的结果文件。

## 服务管理

需要自动构建镜像并手动部署到服务器时，请参阅 [DEPLOYMENT.md](DEPLOYMENT.md)。

### 停止或重新启动

打开 Docker Desktop，在左侧 `Containers` 中找到 PubChat 相关容器，点击停止或重新启动按钮。

也可以在项目根目录执行：

```bash
docker compose stop
```

重新启动：

```bash
docker compose up -d
```

### 关闭并移除容器

在项目根目录执行：

```bash
docker compose down
```

## 常见问题

### Docker 镜像下载失败

请确认 Docker Desktop 已启动，并检查当前网络是否能够稳定访问 GitHub 和 Docker Hub，然后重新执行安装命令。

### 页面无法打开

先在 Docker Desktop 中确认相关容器均处于运行状态，再检查本机 `8000` 端口是否被其他程序占用。

### OpenRouter 模型调用失败

请依次检查 API Key 是否正确、账户余额是否充足、所选模型是否可用，以及当前网络能否访问 OpenRouter。

## 论文与相关项目

- 论文：*Development and benchmark validation of PubChat for PubMed-grounded multilingual biomedical literature retrieval*
- 期刊：*npj Digital Medicine*
- 原文：[https://doi.org/10.1038/s41746-026-03186-0](https://doi.org/10.1038/s41746-026-03186-0)
- 相关项目：[MIDE 微创新发现引擎](https://github.com/PubChatOfficial/MIDE-skill)

## 联系

欢迎关注微信公众号，获取项目更新与使用交流：

<img src="docs/yixue-ai-ganhuo-wechat-qrcode.jpg" alt="医学AI干货微信公众号二维码" width="50%">
