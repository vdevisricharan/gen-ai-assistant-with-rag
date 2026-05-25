const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const statusLabel = document.querySelector("#status");

const sessionId = getOrCreateSessionId();

function getOrCreateSessionId() {
  const existing = localStorage.getItem("sessionId");
  if (existing) {
    return existing;
  }

  const id =
    crypto.randomUUID?.() ??
    `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  localStorage.setItem("sessionId", id);
  return id;
}

function appendMessage(role, text, metaText = "") {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = text;

  if (metaText) {
    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = metaText;
    message.appendChild(meta);
  }

  messages.appendChild(message);
  messages.scrollTop = messages.scrollHeight;
}

function setBusy(isBusy) {
  sendButton.disabled = isBusy;
  input.disabled = isBusy;
  statusLabel.textContent = isBusy ? "Thinking" : "Ready";
  statusLabel.classList.remove("error");
}

function setError(message) {
  statusLabel.textContent = "Error";
  statusLabel.classList.add("error");
  appendMessage("error", message);
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}

input.addEventListener("input", resizeInput);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  input.value = "";
  resizeInput();
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sessionId,
        message,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Request failed");
    }

    appendMessage(
      "assistant",
      payload.reply,
      `${payload.retrievedChunks} chunks | ${payload.tokensUsed} tokens`
    );
  } catch (error) {
    setError(error.message || "Unable to reach the chat API");
  } finally {
    setBusy(false);
    input.focus();
  }
});

appendMessage(
  "assistant",
  "What would you like to know about your account?"
);
