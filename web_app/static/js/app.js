const AppState = {
    socket: null,
    sessionId: null,
    isConnected: false,
    isStreaming: false,
    settings: {
        streamOutput: true,
        autoScroll: true,
        autoSave: true,
    },
    chatHistory: [],
};

const DOM = {};

function initApp() {
    AppState.sessionId = generateSessionId();
    cacheDOMElements();
    bindEvents();
    loadSettings();
    initSocket();
    checkSystemStatus();
    loadChatHistory();
}

function generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

function cacheDOMElements() {
    DOM.loadingOverlay = document.getElementById("loading-overlay");
    DOM.loadingStatus = document.getElementById("loading-status");
    DOM.chatHistory = document.getElementById("chat-history");
    DOM.welcomeMessage = document.getElementById("welcome-message");
    DOM.userInput = document.getElementById("user-input");
    DOM.sendButton = document.getElementById("send-message");
    DOM.clearChat = document.getElementById("clear-chat");
    DOM.charCount = document.getElementById("char-count");
    DOM.toastContainer = document.getElementById("toast-container");
}

function bindEvents() {
    DOM.sendButton?.addEventListener("click", sendMessage);
    DOM.clearChat?.addEventListener("click", clearChat);

    DOM.userInput?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    DOM.userInput?.addEventListener("input", () => {
        const length = DOM.userInput.value.length;
        DOM.charCount.textContent = `${length}/2000`;
        if (length >= 1900) {
            DOM.charCount.style.color = "var(--danger)";
        } else if (length >= 1500) {
            DOM.charCount.style.color = "var(--warning)";
        } else {
            DOM.charCount.style.color = "var(--text-muted)";
        }
    });
}

function initSocket() {
    updateLoadingStatus("正在连接对话服务");
    AppState.socket = io();

    AppState.socket.on("connect", () => {
        AppState.isConnected = true;
        updateLoadingStatus("连接成功，正在准备模型");
    });

    AppState.socket.on("disconnect", () => {
        AppState.isConnected = false;
        showToast("与服务端的连接已断开", "warning");
    });

    AppState.socket.on("stream_start", () => {
        AppState.isStreaming = true;
        setWelcomeMessageVisibility(false);
        startStreamingMessage();
    });

    AppState.socket.on("stream_chunk", (data) => {
        appendStreamingChunk(data.chunk || "");
    });

    AppState.socket.on("stream_end", (data) => {
        AppState.isStreaming = false;
        finishStreamingMessage(data.full_response || "");
    });

    AppState.socket.on("error", (data) => {
        AppState.isStreaming = false;
        showToast(data.message || "对话请求失败", "error");
    });
}

function sendMessage() {
    const message = DOM.userInput.value.trim();
    if (!message) {
        showToast("请输入问题内容", "warning");
        return;
    }
    if (!AppState.isConnected) {
        showToast("服务尚未连接完成，请稍后重试", "warning");
        return;
    }
    if (AppState.isStreaming) {
        showToast("请等待当前回答完成", "warning");
        return;
    }

    setWelcomeMessageVisibility(false);
    addMessageToChat("user", message);
    DOM.userInput.value = "";
    DOM.charCount.textContent = "0/2000";
    DOM.charCount.style.color = "var(--text-muted)";

    if (AppState.settings.streamOutput) {
        AppState.socket.emit("chat_message", {
            message,
            session_id: AppState.sessionId,
            settings: AppState.settings,
        });
        return;
    }

    sendNonStreamMessage(message);
}

async function sendNonStreamMessage(message) {
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                session_id: AppState.sessionId,
            }),
        });
        const data = await response.json();
        if (!data.success) {
            showToast(data.error || "请求失败", "error");
            return;
        }
        addMessageToChat("assistant", data.response || "");
    } catch (error) {
        showToast(`请求失败：${error.message}`, "error");
    }
}

function setWelcomeMessageVisibility(visible) {
    if (DOM.welcomeMessage) {
        DOM.welcomeMessage.style.display = visible ? "block" : "none";
    }
}

function formatMessageContent(content) {
    return String(content)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
}

function addMessageToChat(role, content, timestamp = null) {
    renderMessage(role, content, timestamp);

    AppState.chatHistory.push({
        role,
        content,
        timestamp: timestamp || new Date().toISOString(),
    });

    if (AppState.settings.autoSave) {
        saveChatHistory();
    }
    if (AppState.settings.autoScroll) {
        scrollToBottom();
    }
}

function renderMessage(role, content, timestamp = null) {
    const wrapper = document.createElement("div");
    wrapper.className = `message message-${role}`;

    const body = document.createElement("div");
    body.className = "message-content";
    body.innerHTML = formatMessageContent(content);

    const time = document.createElement("div");
    time.className = "message-time";
    time.textContent = new Date(timestamp || Date.now()).toLocaleTimeString();

    wrapper.appendChild(body);
    wrapper.appendChild(time);
    DOM.chatHistory.appendChild(wrapper);
}

function startStreamingMessage() {
    const wrapper = document.createElement("div");
    wrapper.className = "message message-assistant";
    wrapper.id = "streaming-message";

    const body = document.createElement("div");
    body.className = "message-content";
    body.innerHTML = '<span class="streaming-cursor"></span>';

    wrapper.appendChild(body);
    DOM.chatHistory.appendChild(wrapper);
    scrollToBottom();
}

function appendStreamingChunk(chunk) {
    const message = document.getElementById("streaming-message");
    if (!message) return;
    const body = message.querySelector(".message-content");
    const cursor = body.querySelector(".streaming-cursor");
    const textNode = document.createTextNode(chunk);
    body.insertBefore(textNode, cursor);
    scrollToBottom();
}

function finishStreamingMessage(fullResponse) {
    const message = document.getElementById("streaming-message");
    if (!message) return;

    message.removeAttribute("id");
    const body = message.querySelector(".message-content");
    body.innerHTML = formatMessageContent(fullResponse);

    const time = document.createElement("div");
    time.className = "message-time";
    time.textContent = new Date().toLocaleTimeString();
    message.appendChild(time);

    AppState.chatHistory.push({
        role: "assistant",
        content: fullResponse,
        timestamp: new Date().toISOString(),
    });

    if (AppState.settings.autoSave) {
        saveChatHistory();
    }
    scrollToBottom();
}

function clearChat() {
    if (AppState.chatHistory.length === 0) {
        showToast("当前没有可清空的内容", "info");
        return;
    }
    if (!window.confirm("确认清空当前对话吗？")) {
        return;
    }

    DOM.chatHistory.innerHTML = "";
    AppState.chatHistory = [];
    setWelcomeMessageVisibility(true);

    fetch("/api/history/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: AppState.sessionId }),
    }).catch(() => {});

    localStorage.removeItem(`chatHistory_${AppState.sessionId}`);
    showToast("对话已清空", "success");
}

function scrollToBottom() {
    DOM.chatHistory.scrollTop = DOM.chatHistory.scrollHeight;
}

function updateLoadingStatus(text) {
    if (DOM.loadingStatus) {
        DOM.loadingStatus.textContent = text;
    }
}

function hideLoading() {
    DOM.loadingOverlay?.classList.add("hidden");
}

async function checkSystemStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();
        if (data.status === "ready") {
            updateLoadingStatus("模型与模块已就绪");
            setTimeout(hideLoading, 500);
            return;
        }
        updateLoadingStatus("系统正在初始化，请稍候");
        setTimeout(hideLoading, 1200);
    } catch (error) {
        updateLoadingStatus("状态检查失败，已进入本地界面");
        setTimeout(hideLoading, 1000);
    }
}

function showToast(message, type = "info", duration = 2600) {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    DOM.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, duration);
}

function saveSettings() {
    localStorage.setItem("appSettings", JSON.stringify(AppState.settings));
}

function loadSettings() {
    const saved = localStorage.getItem("appSettings");
    if (!saved) return;
    try {
        AppState.settings = { ...AppState.settings, ...JSON.parse(saved) };
    } catch (_) {}
}

function saveChatHistory() {
    localStorage.setItem(`chatHistory_${AppState.sessionId}`, JSON.stringify(AppState.chatHistory));
}

function loadChatHistory() {
    const saved = localStorage.getItem(`chatHistory_${AppState.sessionId}`);
    if (!saved) return;
    try {
        AppState.chatHistory = JSON.parse(saved);
        if (!AppState.chatHistory.length) return;
        setWelcomeMessageVisibility(false);
        AppState.chatHistory.forEach((item) => renderMessage(item.role, item.content, item.timestamp));
        scrollToBottom();
    } catch (_) {}
}

document.addEventListener("DOMContentLoaded", initApp);
