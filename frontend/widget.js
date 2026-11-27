/**
 * Sathya Assist - Plug-and-Play Embeddable Chat Widget
 * Owner: Vikram (Full-Stack Integration & API Engineer)
 * Usage: Include widget.css + widget.js in any HTML page, optionally set window.SATHYA_API_BASE
 */
(function () {
  const API_BASE = window.SATHYA_API_BASE || "";

  const launcher = document.createElement("button");
  launcher.id = "sa-widget-launcher";
  launcher.innerHTML = "<span>Sathya Assist</span>";

  const panel = document.createElement("div");
  panel.id = "sa-widget-panel";
  panel.innerHTML = `
    <div class="sa-header">
      <div>
        <div class="sa-header-title">Sathya Assist</div>
        <div class="sa-header-sub">Sathyabama Official Campus AI • Microsoft Club</div>
      </div>
      <button class="sa-close-btn" id="sa-close" aria-label="Close chat">&times;</button>
    </div>
    <div class="sa-messages" id="sa-messages">
      <div class="sa-msg bot">Hi! Ask me about Sathyabama attendance rules, exams, hostel curfew, bus timings, or placement policies. Every answer cites official university sources.</div>
    </div>
    <div class="sa-quick-chips">
      <button class="sa-chip" data-q="What is the minimum attendance required for semester exams?">Attendance Rule</button>
      <button class="sa-chip" data-q="What is the hostel curfew time?">Hostel Curfew</button>
      <button class="sa-chip" data-q="What are the college bus timings?">Bus Timings</button>
      <button class="sa-chip" data-q="What is the Dream company CTC difference rule?">Placements</button>
    </div>
    <form class="sa-input-row" id="sa-form">
      <input id="sa-input" type="text" placeholder="Ask a campus question..." autocomplete="off" required />
      <button id="sa-send" type="submit">Send</button>
    </form>
  `;

  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  const messagesEl = panel.querySelector("#sa-messages");
  const formEl = panel.querySelector("#sa-form");
  const inputEl = panel.querySelector("#sa-input");
  const sendBtn = panel.querySelector("#sa-send");

  launcher.addEventListener("click", () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) inputEl.focus();
  });

  panel.querySelector("#sa-close").addEventListener("click", () => {
    panel.classList.remove("open");
  });

  panel.querySelectorAll(".sa-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      inputEl.value = chip.getAttribute("data-q");
      formEl.dispatchEvent(new Event("submit"));
    });
  });

  function appendMessage(text, sender, citations = [], queryText = "") {
    const msg = document.createElement("div");
    msg.className = `sa-msg ${sender}`;
    msg.textContent = text;

    if (sender === "bot" && citations.length > 0) {
      const citeBox = document.createElement("div");
      citeBox.className = "sa-citations";
      citations.forEach((c) => {
        const isUrl = c.reference && c.reference.startsWith("http");
        const pill = document.createElement(isUrl ? "a" : "span");
        pill.className = "sa-cite-pill";
        pill.textContent = c.document_id;
        if (isUrl) {
          pill.href = c.reference;
          pill.target = "_blank";
          pill.rel = "noopener noreferrer";
        }
        citeBox.appendChild(pill);
      });
      msg.appendChild(citeBox);
    }

    if (sender === "bot" && queryText) {
      const fbRow = document.createElement("div");
      fbRow.className = "sa-feedback-row";
      fbRow.innerHTML = `<span>Helpful?</span>`;
      const upBtn = document.createElement("button");
      upBtn.className = "sa-fb-btn";
      upBtn.textContent = "Yes";
      const downBtn = document.createElement("button");
      downBtn.className = "sa-fb-btn";
      downBtn.textContent = "No";

      const sendFb = async (rating) => {
        try {
          await fetch(`${API_BASE}/api/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: queryText, answer: text, rating }),
          });
          fbRow.textContent = "Feedback recorded. Thank you!";
        } catch (_) {}
      };
      upBtn.addEventListener("click", () => sendFb(5));
      downBtn.addEventListener("click", () => sendFb(1));
      fbRow.appendChild(upBtn);
      fbRow.appendChild(downBtn);
      msg.appendChild(fbRow);
    }

    messagesEl.appendChild(msg);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return msg;
  }

  formEl.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = inputEl.value.trim();
    if (!query) return;

    appendMessage(query, "user");
    inputEl.value = "";
    sendBtn.disabled = true;

    const thinking = appendMessage("Searching official documents...", "bot");
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      thinking.remove();
      appendMessage(data.answer, "bot", data.citations || [], query);
    } catch (err) {
      thinking.textContent = `Unable to reach Sathya Assist API (${err.message}).`;
    } finally {
      sendBtn.disabled = false;
      inputEl.focus();
    }
  });
})();
