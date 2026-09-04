(function () {
  "use strict";

  var STORAGE_KEY = "pubchat.custom-llm-config";
  var DEFAULT_CONFIG = {
    enabled: false,
    baseUrl: "https://api.openai.com/v1",
    model: "gpt-4o-mini"
  };
  var config = loadConfig();
  var panelId = "pubchat-custom-llm-config";
  var errorId = "pubchat-custom-llm-error";

  function loadConfig() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      var saved = raw ? JSON.parse(raw) : {};
      return Object.assign({}, DEFAULT_CONFIG, saved);
    } catch (_error) {
      return Object.assign({}, DEFAULT_CONFIG);
    }
  }

  function saveConfig() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify({
        enabled: Boolean(config.enabled),
        baseUrl: String(config.baseUrl || ""),
        model: String(config.model || "")
      }));
    } catch (_error) {
      // Ignore storage restrictions; the current page can still use the fields.
    }
  }

  function setError(message) {
    var error = document.getElementById(errorId);
    if (!error) return;
    error.textContent = message || "";
    error.hidden = !message;
  }

  function updateFieldState(panel) {
    var enabled = panel.querySelector("[data-custom-enabled]").checked;
    panel.querySelectorAll("[data-custom-field]").forEach(function (field) {
      field.disabled = !enabled;
    });
  }

  function createPanel(section) {
    if (document.getElementById(panelId)) return;

    if (!document.getElementById("pubchat-custom-llm-style")) {
      var style = document.createElement("style");
      style.id = "pubchat-custom-llm-style";
      style.textContent = [
        ".pubchat-custom-llm-panel { margin-top: 1rem; }",
        ".pubchat-custom-toggle { display: flex; align-items: center; gap: .5rem; cursor: pointer; }",
        ".pubchat-custom-toggle input { width: 1rem; height: 1rem; accent-color: var(--primary-color, #20558A); }",
        ".pubchat-custom-llm-error { color: #b42318; margin: .5rem 0 0; }",
        ".pubchat-custom-llm-panel input:disabled { opacity: .55; cursor: not-allowed; }"
      ].join("");
      document.head.appendChild(style);
    }

    var panel = document.createElement("div");
    panel.id = panelId;
    panel.className = "form-section section-box pubchat-custom-llm-panel";
    panel.innerHTML = [
      '<div class="section-header">',
      '  <h3>自定义 OpenAI 兼容接口 / Custom endpoint</h3>',
      '</div>',
      '<div class="grid-form">',
      '  <div class="form-group full-width">',
      '    <label class="pubchat-custom-toggle">',
      '      <input type="checkbox" data-custom-enabled>',
      '      <span>使用自定义地址和模型</span>',
      '    </label>',
      '  </div>',
      '  <div class="form-group full-width">',
      '    <label for="pubchat-custom-base-url">接口地址 / Base URL</label>',
      '    <input id="pubchat-custom-base-url" class="form-input" data-custom-field data-custom-base-url type="url" autocomplete="off" placeholder="https://api.openai.com/v1">',
      '  </div>',
      '  <div class="form-group full-width">',
      '    <label for="pubchat-custom-model">模型名称 / Model</label>',
      '    <input id="pubchat-custom-model" class="form-input" data-custom-field data-custom-model type="text" autocomplete="off" placeholder="gpt-4o-mini">',
      '  </div>',
      '</div>',
      '<p class="api-help-text">支持 OpenAI、DeepSeek、通义千问、SiliconFlow、OpenRouter、Ollama 等 OpenAI 兼容接口。配置只在提交任务时发送，API Key 仍填写上方输入框。</p>',
      '<p id="' + errorId + '" class="pubchat-custom-llm-error" hidden></p>'
    ].join("");

    section.insertAdjacentElement("afterend", panel);

    var enabled = panel.querySelector("[data-custom-enabled]");
    var baseUrl = panel.querySelector("[data-custom-base-url]");
    var model = panel.querySelector("[data-custom-model]");
    enabled.checked = Boolean(config.enabled);
    baseUrl.value = config.baseUrl || DEFAULT_CONFIG.baseUrl;
    model.value = config.model || DEFAULT_CONFIG.model;

    function onChange() {
      config.enabled = enabled.checked;
      config.baseUrl = baseUrl.value.trim();
      config.model = model.value.trim();
      saveConfig();
      setError("");
      updateFieldState(panel);
    }

    enabled.addEventListener("change", onChange);
    baseUrl.addEventListener("input", onChange);
    model.addEventListener("input", onChange);
    updateFieldState(panel);
  }

  function ensurePanel() {
    var section = document.querySelector(".ai-api-config-section");
    if (section && !document.getElementById(panelId)) createPanel(section);
  }

  function getRequestUrl(input) {
    if (typeof input === "string") return input;
    if (input && input.url) return input.url;
    return "";
  }

  function isCreateTaskRequest(input, init) {
    var method = (init && init.method) || (input && input.method) || "GET";
    if (String(method).toUpperCase() !== "POST") return false;
    try {
      var url = new URL(getRequestUrl(input), window.location.href);
      return url.pathname === "/api/search/task";
    } catch (_error) {
      return false;
    }
  }

  function validateConfig() {
    var baseUrl = String(config.baseUrl || "").trim();
    var model = String(config.model || "").trim();
    if (!model) return "请填写模型名称 / Please enter a model name";
    try {
      if (!/^https?:\/\//i.test(baseUrl)) throw new Error("absolute URL required");
      var parsed = new URL(baseUrl, window.location.href);
      if (!["http:", "https:"].includes(parsed.protocol) || !parsed.hostname) {
        throw new Error("invalid URL");
      }
      if (parsed.username || parsed.password || parsed.search || parsed.hash) {
        throw new Error("unsafe URL");
      }
    } catch (_error) {
      return "接口地址必须是完整的 http(s) 地址 / Base URL must be a full http(s) URL";
    }
    return null;
  }

  var originalFetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    if (!config.enabled || !isCreateTaskRequest(input, init)) {
      return originalFetch(input, init);
    }

    var validationError = validateConfig();
    if (validationError) {
      ensurePanel();
      setError(validationError);
      return Promise.reject(new Error(validationError));
    }

    var requestInit = Object.assign({}, init || {});
    var body = requestInit.body;
    if (typeof body !== "string") return originalFetch(input, init);

    try {
      var payload = JSON.parse(body);
      payload.llm_config = Object.assign({}, payload.llm_config || {}, {
        provider: "openai-compatible",
        base_url: String(config.baseUrl).trim().replace(/\/+$/, ""),
        model: String(config.model).trim()
      });
      requestInit.body = JSON.stringify(payload);
      var headers = new Headers(requestInit.headers || {});
      headers.set("Content-Type", "application/json");
      requestInit.headers = headers;
      return originalFetch(input, requestInit);
    } catch (_error) {
      return originalFetch(input, init);
    }
  };

  function start() {
    ensurePanel();
    var observer = new MutationObserver(ensurePanel);
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start, { once: true });
  } else {
    start();
  }
})();
