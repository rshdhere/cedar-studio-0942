(function () {
  "use strict";

  const STORAGE_KEY = "chat_username";

  const welcome = document.getElementById("welcome");
  const chatPanel = document.getElementById("chat-panel");
  const joinForm = document.getElementById("join-form");
  const usernameInput = document.getElementById("username-input");
  const messageForm = document.getElementById("message-form");
  const messageInput = document.getElementById("message-input");
  const messagesEl = document.getElementById("messages");
  const userBadge = document.getElementById("user-badge");
  const displayName = document.getElementById("display-name");
  const changeNameBtn = document.getElementById("change-name");

  let username = localStorage.getItem(STORAGE_KEY) || "";
  let seenIds = new Set();

  function formatTime(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function appendMessage(msg) {
    if (seenIds.has(msg.id)) return;
    seenIds.add(msg.id);

    const li = document.createElement("li");
    li.className = "message" + (msg.username === username ? " message-own" : "");
    li.dataset.id = msg.id;

    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.innerHTML =
      "<span class=\"message-author\">" + escapeHtml(msg.username) + "</span>" +
      "<time class=\"message-time\">" + formatTime(msg.timestamp) + "</time>";

    const body = document.createElement("div");
    body.className = "message-text";
    body.textContent = msg.text;

    li.appendChild(meta);
    li.appendChild(body);
    messagesEl.appendChild(li);
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function showChat() {
    welcome.hidden = true;
    chatPanel.hidden = false;
    userBadge.hidden = false;
    displayName.textContent = username;
    messageInput.focus();
  }

  function showWelcome() {
    welcome.hidden = false;
    chatPanel.hidden = true;
    userBadge.hidden = true;
    usernameInput.value = username;
    usernameInput.focus();
  }

  function join(name) {
    username = name.trim().slice(0, 32);
    if (!username) return;
    localStorage.setItem(STORAGE_KEY, username);
    showChat();
    loadHistory();
    connectSSE();
  }

  async function loadHistory() {
    try {
      const res = await fetch("/api/messages");
      const data = await res.json();
      messagesEl.innerHTML = "";
      seenIds.clear();
      data.forEach(appendMessage);
    } catch (err) {
      console.error("Failed to load messages", err);
    }
  }

  function connectSSE() {
    const source = new EventSource("/api/events");
    source.onmessage = function (event) {
      try {
        const msg = JSON.parse(event.data);
        appendMessage(msg);
      } catch {
        /* ignore */
      }
    };
    source.onerror = function () {
      source.close();
      setTimeout(connectSSE, 2000);
    };
  }

  joinForm.addEventListener("submit", function (e) {
    e.preventDefault();
    join(usernameInput.value);
  });

  messageForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;
    messageInput.value = "";
    try {
      await fetch("/api/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, text }),
      });
    } catch (err) {
      console.error("Failed to send message", err);
      messageInput.value = text;
    }
  });

  changeNameBtn.addEventListener("click", function () {
    showWelcome();
  });

  if (username) {
    join(username);
  } else {
    showWelcome();
  }
})();
