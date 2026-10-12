document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("questionInput");
  const messages = document.getElementById("chatMessages");
  const sendButton = document.getElementById("sendBtn");
  const newChatButton = document.getElementById("newChatBtn");
  const typing = document.getElementById("typingIndicator");
  const modelButtons = document.querySelectorAll(".model-btn");
  const initialMarkup = messages.innerHTML;
  let busy = false;

  function scrollLatest() {
    messages.lastElementChild?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function addMessage(text, role, title = "") {
    const article = document.createElement("article");
    article.className = `message ${role}-message`;
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = role === "user" ? "You" : "✦";
    const content = document.createElement("div");
    content.className = "message-content";
    if (title) {
      const heading = document.createElement("h3");
      heading.textContent = title;
      content.appendChild(heading);
    }
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    content.appendChild(paragraph);
    article.append(avatar, content);
    messages.appendChild(article);
    scrollLatest();
  }

  function setBusy(value) {
    busy = value;
    sendButton.disabled = value;
    input.disabled = value;
    typing.hidden = !value;
  }

  async function sendQuestion(rawQuestion) {
    const question = rawQuestion.trim();
    if (!question || busy) return;

    addMessage(question, "user");
    input.value = "";
    input.style.height = "auto";
    document.getElementById("suggestions")?.remove();
    setBusy(true);

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || "The chatbot could not answer.");
      }
      if (typeof data.answer !== "string") {
        throw new Error("The server returned an invalid answer.");
      }

      addMessage(data.answer, "assistant", "Tata Car Guide — Answer");

      if (Array.isArray(data.sources) && data.sources.length) {
        const lastContent = messages.lastElementChild.querySelector(".message-content");
        const heading = document.createElement("h3");
        heading.textContent = "Sources";
        heading.style.marginTop = "14px";
        const list = document.createElement("ul");
        list.className = "source-list";
        data.sources.forEach(source => {
          const item = document.createElement("li");
          if (typeof source === "string") item.textContent = source;
          else item.textContent = source.source || source.page_content || JSON.stringify(source);
          list.appendChild(item);
        });
        lastContent.append(heading, list);
      }
    } catch (error) {
      console.error(error);
      addMessage(error.message || "Could not connect to the server. Please try again.", "assistant", "Connection error");
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    sendQuestion(input.value);
  });

  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
  });

  input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  modelButtons.forEach(button => {
    button.addEventListener("click", () => {
      modelButtons.forEach(item => {
        const active = item === button;
        item.classList.toggle("active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      const model = button.dataset.model;
      input.placeholder = `Ask a question about Tata ${model}...`;
      sendQuestion(`Give me an overview of the Tata ${model}: price range, variants, colours, engine or battery and range, safety rating and key features. If a detail is not present in the provided documents, say so.`);
    });
  });

  document.querySelectorAll(".suggestion-btn").forEach(button => {
    button.addEventListener("click", () => sendQuestion(button.dataset.question));
  });

  newChatButton.addEventListener("click", () => {
    if (busy) return;
    messages.innerHTML = initialMarkup;
    document.querySelectorAll(".model-btn").forEach(button => {
      button.classList.remove("active");
      button.setAttribute("aria-pressed", "false");
    });
    input.value = "";
    input.placeholder = "Ask about a Tata car, variant or feature...";
    input.style.height = "auto";
    bindSuggestions();
    input.focus();
  });

  function bindSuggestions() {
    messages.querySelectorAll(".suggestion-btn").forEach(button => {
      button.addEventListener("click", () => sendQuestion(button.dataset.question));
    });
  }
});
