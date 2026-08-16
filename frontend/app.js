/**
 * DeTrace Web Application Logic (Step 9).
 */

document.addEventListener("DOMContentLoaded", () => {
  const questionInput = document.getElementById("questionInput");
  const askBtn = document.getElementById("askBtn");
  const healthBadge = document.getElementById("healthBadge");
  const healthText = document.getElementById("healthText");

  const loadingSection = document.getElementById("loadingSection");
  const errorSection = document.getElementById("errorSection");
  const errorMessage = document.getElementById("errorMessage");
  const resultSection = document.getElementById("resultSection");
  const emptySection = document.getElementById("emptySection");

  const displayQuestion = document.getElementById("displayQuestion");
  const answerBody = document.getElementById("answerBody");
  const groundingBadge = document.getElementById("groundingBadge");
  const evidenceCount = document.getElementById("evidenceCount");
  const evidenceGrid = document.getElementById("evidenceGrid");

  // Check HydraDB Health on Startup
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.status === "ok" && data.hydradb === "ok") {
        healthBadge.className = "status-badge status-ok";
        healthText.textContent = "HydraDB Graph Connected";
      } else {
        healthBadge.className = "status-badge status-err";
        healthText.textContent = `HydraDB ${data.hydradb || "Degraded"}`;
      }
    } catch (err) {
      healthBadge.className = "status-badge status-err";
      healthText.textContent = "HydraDB Offline";
    }
  }

  checkHealth();

  // Quick Prompt Chips
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const query = chip.getAttribute("data-query");
      if (query) {
        questionInput.value = query;
        handleAsk();
      }
    });
  });

  // Enter / Ctrl+Enter key listener
  questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  });

  askBtn.addEventListener("click", handleAsk);

  async function handleAsk() {
    const question = questionInput.value.trim();
    if (!question) {
      questionInput.focus();
      return;
    }

    // UI State: Loading
    setLoading(true);
    hideError();

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, retrieval_limit: 10 }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || `Server returned HTTP ${response.status}`);
      }

      renderResult(data);
    } catch (err) {
      showError(err.message || "Failed to communicate with Graph RAG service.");
    } finally {
      setLoading(false);
    }
  }

  function renderResult(data) {
    emptySection.classList.add("hidden");
    resultSection.classList.remove("hidden");

    displayQuestion.textContent = data.question;

    // Format answer text with interactive [E#] citation pills
    const rawAnswer = data.answer || "No response generated.";
    const formattedAnswer = rawAnswer.replace(/\[E(\d+)\]/g, (match, p1) => {
      return `<button class="citation-pill" data-target="evidence-E${p1}">[E${p1}]</button>`;
    });

    answerBody.innerHTML = formattedAnswer;

    // Grounding Status Badge
    groundingBadge.className = "grounding-badge";
    const isInsufficient = rawAnswer.toLowerCase().includes("insufficient");

    if (data.grounded && !isInsufficient) {
      groundingBadge.classList.add("badge-grounded");
      groundingBadge.textContent = "Grounded";
    } else if (isInsufficient) {
      groundingBadge.classList.add("badge-insufficient");
      groundingBadge.textContent = "Insufficient Evidence";
    } else {
      groundingBadge.classList.add("badge-ungrounded");
      groundingBadge.textContent = "Not Grounded";
    }

    // Render Evidence Items
    const items = data.evidence || [];
    evidenceCount.textContent = `${items.length} item${items.length === 1 ? "" : "s"}`;
    evidenceGrid.innerHTML = "";

    if (items.length === 0) {
      evidenceGrid.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No graph evidence items retrieved for this query.</p>`;
      return;
    }

    items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "evidence-card";
      card.id = `evidence-${item.id}`;

      const relBadge = item.relationship
        ? `<span class="mini-badge badge-rel">${item.relationship}</span>`
        : "";
      const typeBadge = item.statement_type
        ? `<span class="mini-badge badge-${item.statement_type.toLowerCase()}">${item.statement_type}</span>`
        : "";

      const entityHtml = item.entity_name
        ? `<div class="evidence-entity">Entity: ${escapeHtml(item.entity_name)}</div>`
        : "";
      const statementHtml = item.statement
        ? `<div class="evidence-statement">${escapeHtml(item.statement)}</div>`
        : "";

      card.innerHTML = `
        <div class="evidence-card-header">
          <span class="evidence-id-tag">[${item.id}]</span>
          <div class="tag-group">
            ${relBadge}
            ${typeBadge}
          </div>
        </div>
        ${entityHtml}
        ${statementHtml}
        <div class="evidence-provenance">
          <span><strong>Message ID:</strong> ${item.message_id}</span>
          <span><strong>Document:</strong> ${escapeHtml(item.document_id)}</span>
        </div>
      `;

      evidenceGrid.appendChild(card);
    });

    // Add interactive click scroll to citation pills
    document.querySelectorAll(".citation-pill").forEach((pill) => {
      pill.addEventListener("click", (e) => {
        e.preventDefault();
        const targetId = pill.getAttribute("data-target");
        const targetCard = document.getElementById(targetId);
        if (targetCard) {
          document.querySelectorAll(".evidence-card").forEach((c) => c.classList.remove("highlighted"));
          targetCard.classList.add("highlighted");
          targetCard.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      });
    });
  }

  function setLoading(isLoading) {
    if (isLoading) {
      askBtn.disabled = true;
      loadingSection.classList.remove("hidden");
      resultSection.classList.add("hidden");
    } else {
      askBtn.disabled = false;
      loadingSection.classList.add("hidden");
    }
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorSection.classList.remove("hidden");
    resultSection.classList.add("hidden");
  }

  function hideError() {
    errorSection.classList.add("hidden");
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
