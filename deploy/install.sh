#!/usr/bin/env bash

set -Eeuo pipefail
umask 077

REPO_RAW="https://raw.githubusercontent.com/zhy0504/PubChat_smart_literature_search"
SUDO_CMD=()
DOCKER_CMD=(docker)
PACKAGE_MANAGER=""

die() {
  echo "错误：$*" >&2
  exit 1
}

ask() {
  local prompt="$1"
  local default_value="$2"
  local result_name="$3"
  local value
  read -r -p "${prompt} [${default_value}]: " value
  printf -v "$result_name" '%s' "${value:-$default_value}"
}

confirm() {
  local prompt="$1"
  local answer

  read -r -p "${prompt} [Y/n]: " answer
  case "${answer:-y}" in
    y|Y|yes|YES|Yes) return 0 ;;
    *) return 1 ;;
  esac
}

ensure_sudo() {
  if (( EUID == 0 )); then
    SUDO_CMD=()
    return 0
  fi

  command -v sudo >/dev/null 2>&1 || die "当前用户不是 root，且未找到 sudo。请使用 root 或安装 sudo 后重试。"
  SUDO_CMD=(sudo)
}

detect_package_manager() {
  [[ -n "$PACKAGE_MANAGER" ]] && return 0
  [[ "$(uname -s)" == "Linux" ]] || die "自动安装 Docker 仅支持 Linux 服务器。"

  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
  fi

  case "${ID:-}" in
    ubuntu|debian|linuxmint|pop|raspbian)
      PACKAGE_MANAGER="apt-get"
      ;;
    fedora|rhel|centos|rocky|almalinux|amzn)
      if command -v dnf >/dev/null 2>&1; then
        PACKAGE_MANAGER="dnf"
      elif command -v yum >/dev/null 2>&1; then
        PACKAGE_MANAGER="yum"
      fi
      ;;
  esac

  if [[ -z "$PACKAGE_MANAGER" ]]; then
    if command -v apt-get >/dev/null 2>&1; then
      PACKAGE_MANAGER="apt-get"
    elif command -v dnf >/dev/null 2>&1; then
      PACKAGE_MANAGER="dnf"
    elif command -v yum >/dev/null 2>&1; then
      PACKAGE_MANAGER="yum"
    fi
  fi

  [[ -n "$PACKAGE_MANAGER" ]] || die "未识别的 Linux 发行版，无法自动安装 Docker。请先手动安装 Docker Engine 和 Docker Compose 插件。"
}

install_packages() {
  ensure_sudo
  detect_package_manager

  case "$PACKAGE_MANAGER" in
    apt-get)
      "${SUDO_CMD[@]}" apt-get update
      "${SUDO_CMD[@]}" apt-get install -y "$@"
      ;;
    dnf|yum)
      "${SUDO_CMD[@]}" "$PACKAGE_MANAGER" install -y "$@"
      ;;
    *)
      die "不支持的系统包管理器：${PACKAGE_MANAGER}"
      ;;
  esac
}

ensure_curl() {
  command -v curl >/dev/null 2>&1 && return 0

  echo "未找到 curl，正在安装 curl..."
  install_packages ca-certificates curl
  command -v curl >/dev/null 2>&1 || die "curl 安装失败。"
}

docker_cmd() {
  "${DOCKER_CMD[@]}" "$@"
}

set_docker_command() {
  DOCKER_CMD=(docker)
  command -v docker >/dev/null 2>&1 || return 1

  if docker info >/dev/null 2>&1; then
    return 0
  fi

  if command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
    DOCKER_CMD=(sudo docker)
    return 0
  fi

  return 1
}

compose_ready() {
  docker_cmd compose version --short >/dev/null 2>&1 || \
    docker_cmd compose version >/dev/null 2>&1
}

start_docker_service() {
  if command -v systemctl >/dev/null 2>&1; then
    "${SUDO_CMD[@]}" systemctl enable --now docker >/dev/null 2>&1 || \
      "${SUDO_CMD[@]}" systemctl start docker >/dev/null 2>&1 || true
  elif command -v service >/dev/null 2>&1; then
    "${SUDO_CMD[@]}" service docker start >/dev/null 2>&1 || true
  fi
}

install_compose_plugin() {
  echo "正在安装 Docker Compose 插件..."
  if ! install_packages docker-compose-plugin; then
    return 1
  fi

  hash -r 2>/dev/null || true
  compose_ready
}

install_docker() {
  local installer

  ensure_sudo
  detect_package_manager
  ensure_curl

  installer="$(mktemp)"
  if ! curl --retry 3 --retry-delay 1 -fsSL https://get.docker.com -o "$installer"; then
    rm -f "$installer"
    die "Docker 官方安装脚本下载失败。"
  fi

  echo "正在运行 Docker 官方安装程序..."
  if ! "${SUDO_CMD[@]}" sh "$installer"; then
    rm -f "$installer"
    die "Docker Engine 安装失败。"
  fi
  rm -f "$installer"
  hash -r 2>/dev/null || true

  command -v docker >/dev/null 2>&1 || die "Docker Engine 安装后仍未找到 docker 命令。"
  start_docker_service
  set_docker_command || die "Docker 已安装，但无法连接 Docker 服务。"

  if ! compose_ready; then
    install_compose_plugin || die "Docker Compose 插件安装失败。"
  fi
}

ensure_docker() {
  local missing=()
  local docker_available=0
  local missing_text

  if command -v docker >/dev/null 2>&1 && set_docker_command; then
    docker_available=1
    if compose_ready; then
      return 0
    fi
  elif command -v docker >/dev/null 2>&1; then
    ensure_sudo
    start_docker_service
    if set_docker_command; then
      docker_available=1
      if compose_ready; then
        return 0
      fi
    fi
  fi

  (( docker_available )) || missing+=("Docker Engine")
  if (( docker_available == 0 )) || ! compose_ready; then
    missing+=("Docker Compose 插件")
  fi

  missing_text="$(IFS='、'; printf '%s' "${missing[*]}")"
  echo "未检测到：${missing_text}。"
  confirm "是否现在自动安装/修复 Docker 环境？" || die "请先准备 Docker Engine 和 Docker Compose 插件后重试。"

  if (( docker_available )) && ! compose_ready; then
    if ! install_compose_plugin; then
      echo "系统包中未提供 Compose 插件，正在使用 Docker 官方安装程序修复..."
      install_docker
    fi
  else
    install_docker
  fi

  set_docker_command || die "Docker 安装完成，但当前用户无法访问 Docker。请重新登录后重试。"
  compose_ready || die "Docker Compose 插件安装失败。"
}

read_env_value() {
  local key="$1"
  local file="$2"

  [[ -f "$file" ]] || return 0
  awk -F= -v target="$key" '$1 == target {sub(/^[^=]*=/, ""); print; exit}' "$file"
}

set_env_value() {
  local key="$1"
  local value="$2"
  local file="$3"
  local escaped

  escaped="$(printf '%s' "$value" | sed 's/[\\&|]/\\&/g')"
  if grep -qE "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${escaped}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

ensure_docker
ensure_curl

default_dir="${PUBCHAT_DIR:-}"
if [[ -z "$default_dir" ]]; then
  if [[ "$(id -u)" -eq 0 ]]; then
    default_dir="/opt/pubchat"
  else
    default_dir="${HOME}/pubchat"
  fi
fi

default_ref="${PUBCHAT_REF:-main}"

echo "PubChat 一键部署"
echo
ask "部署目录" "$default_dir" target_dir
[[ -n "$target_dir" ]] || die "部署目录不能为空。"

env_file="$target_dir/.env"
existing_tag="$(read_env_value IMAGE_TAG "$env_file")"
existing_port="$(read_env_value WEB_PORT "$env_file")"
default_tag="${IMAGE_TAG:-${existing_tag:-latest}}"
default_port="${WEB_PORT:-${existing_port:-8000}}"
if [[ ! "$default_port" =~ ^[0-9]+$ ]]; then
  default_port="8000"
else
  default_port_number=$((10#$default_port))
  if ((default_port_number < 1 || default_port_number > 65535)); then
    default_port="8000"
  fi
fi

ask "PubChat 镜像标签" "$default_tag" image_tag
ask "Web 端口" "$default_port" web_port

[[ "$web_port" =~ ^[0-9]+$ ]] || die "Web 端口必须是数字。"
web_port_number=$((10#$web_port))
((web_port_number >= 1 && web_port_number <= 65535)) || die "Web 端口必须在 1 到 65535 之间。"
web_port="$web_port_number"

if ! mkdir -p "$target_dir"; then
  die "无法创建部署目录：$target_dir"
fi

compose_file="$target_dir/docker-compose.prod.yml"
init_file="$target_dir/init.sql"
env_example_file="$target_dir/.env.example"

download_file() {
  local remote_path="$1"
  local output_path="$2"
  local temporary_path="${output_path}.tmp.$$"

  if ! curl --retry 3 --retry-delay 1 -fsSL "${REPO_RAW}/${default_ref}/${remote_path}" -o "$temporary_path"; then
    rm -f "$temporary_path"
    die "下载失败：${remote_path}"
  fi
  mv "$temporary_path" "$output_path"
}

echo
echo "正在下载部署文件..."
download_file "deploy/docker-compose.prod.yml" "$compose_file"
download_file "db/postgres/init.sql" "$init_file"
download_file "deploy/.env.example" "$env_example_file"

if [[ ! -f "$env_file" ]]; then
  cp "$env_example_file" "$env_file"
fi

set_env_value "IMAGE_PREFIX" "ghcr.io/zhy0504" "$env_file"
set_env_value "IMAGE_TAG" "$image_tag" "$env_file"
set_env_value "WEB_PORT" "$web_port" "$env_file"
set_env_value "PROJECT_ENV" "production" "$env_file"
if [[ -n "${CELERY_WORKER_IMAGE:-}" ]]; then
  set_env_value "CELERY_WORKER_IMAGE" "$CELERY_WORKER_IMAGE" "$env_file"
fi

current_password="$(read_env_value POSTGRES_PASSWORD "$env_file")"
if [[ -z "$current_password" || "$current_password" == "replace-with-a-long-random-password" ]]; then
  generated_password=""
  if command -v openssl >/dev/null 2>&1; then
    generated_password="$(openssl rand -hex 24)"
  fi

  read -r -s -p "PostgreSQL 密码（直接回车自动生成）: " postgres_password
  echo
  if [[ -z "$postgres_password" ]]; then
    [[ -n "$generated_password" ]] || die "未找到 openssl，请手动输入 PostgreSQL 密码。"
    postgres_password="$generated_password"
    echo "已自动生成 PostgreSQL 密码，并写入 ${env_file}。"
  else
    read -r -s -p "再次输入 PostgreSQL 密码: " password_confirmation
    echo
    [[ "$postgres_password" == "$password_confirmation" ]] || die "两次输入的密码不一致。"
  fi
  set_env_value "POSTGRES_PASSWORD" "$postgres_password" "$env_file"
else
  echo "检测到已有 PostgreSQL 密码，保留现有值。"
fi

chmod 600 "$env_file"

compose() {
  docker_cmd compose --env-file "$env_file" -f "$compose_file" "$@"
}

echo
echo "正在校验 Compose 配置..."
compose config --quiet || die "Compose 配置校验失败，请检查 ${env_file}。"

echo "正在拉取镜像..."
compose pull || die "镜像拉取失败，请检查 GHCR 包可见性、镜像标签和服务器网络。"

echo "正在启动服务..."
compose up -d --remove-orphans || die "服务启动失败，请执行：docker compose --env-file ${env_file} -f ${compose_file} logs"

echo "等待 API 就绪..."
ready=0
for ((attempt = 1; attempt <= 60; attempt++)); do
  if curl -fsS "http://127.0.0.1:${web_port}/api/search/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done

compose ps
if [[ "$ready" -ne 1 ]]; then
  echo
  echo "API 尚未就绪，最近日志："
  compose logs --tail=100 search-server celery-worker || true
  exit 1
fi

echo
echo "部署完成。"
echo "部署目录：${target_dir}"
echo "访问地址：http://服务器IP:${web_port}"
echo "首次检索时，请在页面填写 AI API Key 和 NCBI PubMed API Key。"
