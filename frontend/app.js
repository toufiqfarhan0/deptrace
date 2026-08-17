/**
 * DeTrace Web Application Logic (Step 9 / Step 11).
 * Supports Graph RAG question answering and deterministic multi-hop Dependency Tracing.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements: Navigation Tabs
  const tabAsk = document.getElementById("tabAsk");
  const tabTrace = document.getElementById("tabTrace");
  const viewAsk = document.getElementById("viewAsk");
  const viewTrace = document.getElementById("viewTrace");

  // Elements: Health Badge
  const healthBadge = document.getElementById("healthBadge");
  const healthText = document.getElementById("healthText");

  // Elements: View 1 (Ask)
  const questionInput = document.getElementById("questionInput");
  const askBtn = document.getElementById("askBtn");
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

  // Elements: View 2 (Trace)
  const traceEntityInput = document.getElementById("traceEntityInput");
  const traceDepthSelect = document.getElementById("traceDepthSelect");
  const traceBtn = document.getElementById("traceBtn");
  const traceLoadingSection = document.getElementById("traceLoadingSection");
  const traceErrorSection = document.getElementById("traceErrorSection");
  const traceErrorMessage = document.getElementById("traceErrorMessage");
  const traceResultSection = document.getElementById("traceResultSection");
  const traceEmptySection = document.getElementById("traceEmptySection");

  const traceRootHeading = document.getElementById("traceRootHeading");
  const metricLinkedCount = document.getElementById("metricLinkedCount");
  const metricStmtCount = document.getElementById("metricStmtCount");
  const metricDepth = document.getElementById("metricDepth");
  const metricMsgCount = document.getElementById("metricMsgCount");
  const linkedComponentsChips = document.getElementById("linkedComponentsChips");
  const stmtBreakdownChips = document.getElementById("stmtBreakdownChips");
  const hopsCount = document.getElementById("hopsCount");
  const hopsGrid = document.getElementById("hopsGrid");
  const timelineCount = document.getElementById("timelineCount");
  const timelineList = document.getElementById("timelineList");

  // -------------------------------------------------------------------
  // Tab Switching
  // -------------------------------------------------------------------
  tabAsk.addEventListener("click", () => {
    tabAsk.classList.add("active");
    tabTrace.classList.remove("active");
    viewAsk.classList.remove("hidden");
    viewTrace.classList.add("hidden");
  });

  tabTrace.addEventListener("click", () => {
    tabTrace.classList.add("active");
    tabAsk.classList.remove("active");
    viewTrace.classList.remove("hidden");
    viewAsk.classList.add("hidden");
  });

  // -------------------------------------------------------------------
  // Check HydraDB Health & Entity List on Startup
  // -------------------------------------------------------------------
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

  // -------------------------------------------------------------------
  // VIEW 1: ASK GRAPH RAG
  // -------------------------------------------------------------------
  document.querySelectorAll(".chip:not(.trace-chip)").forEach((chip) => {
    chip.addEventListener("click", () => {
      const query = chip.getAttribute("data-query");
      if (query) {
        questionInput.value = query;
        handleAsk();
      }
    });
  });

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

    setAskLoading(true);
    hideAskError();

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

      renderAskResult(data);
    } catch (err) {
      showAskError(err.message || "Failed to communicate with Graph RAG service.");
    } finally {
      setAskLoading(false);
    }
  }

  function renderAskResult(data) {
    emptySection.classList.add("hidden");
    resultSection.classList.remove("hidden");

    displayQuestion.textContent = data.question;

    // Format answer text with interactive [E#] citation pills (supports single and grouped [E1, E2])
    const rawAnswer = data.answer || "No response generated.";
    const formattedAnswer = rawAnswer.replace(/\[(.*?)\]/g, (match, inner) => {
      const eMatches = inner.match(/\bE\d+\b/gi);
      if (!eMatches) return match;
      return eMatches
        .map((tag) => {
          const norm = tag.toUpperCase();
          return `<button class="citation-pill" data-target="evidence-${norm}">[${norm}]</button>`;
        })
        .join(" ");
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

  function setAskLoading(isLoading) {
    if (isLoading) {
      askBtn.disabled = true;
      loadingSection.classList.remove("hidden");
      resultSection.classList.add("hidden");
    } else {
      askBtn.disabled = false;
      loadingSection.classList.add("hidden");
    }
  }

  function showAskError(msg) {
    errorMessage.textContent = msg;
    errorSection.classList.remove("hidden");
    resultSection.classList.add("hidden");
  }

  function hideAskError() {
    errorSection.classList.add("hidden");
  }

  // -------------------------------------------------------------------
  // VIEW 2: DEPENDENCY TRACER
  // -------------------------------------------------------------------
  document.querySelectorAll(".trace-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const entity = chip.getAttribute("data-entity");
      if (entity) {
        traceEntityInput.value = entity;
        handleTrace();
      }
    });
  });

  traceEntityInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleTrace();
    }
  });

  traceBtn.addEventListener("click", handleTrace);

  async function handleTrace() {
    const entity = traceEntityInput.value.trim();
    if (!entity) {
      traceEntityInput.focus();
      return;
    }

    const max_depth = parseInt(traceDepthSelect.value, 10) || 2;

    setTraceLoading(true);
    hideTraceError();

    try {
      const response = await fetch("/api/trace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ entity, max_depth, limit: 25 }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || `Server returned HTTP ${response.status}`);
      }

      if (!data.found) {
        showTraceError(data.error || `Entity '${entity}' not found in knowledge graph.`);
        return;
      }

      renderTraceResult(data);
    } catch (err) {
      showTraceError(err.message || "Failed to execute dependency trace.");
    } finally {
      setTraceLoading(false);
    }
  }

  function renderTraceResult(data) {
    traceEmptySection.classList.add("hidden");
    traceResultSection.classList.remove("hidden");

    const summary = data.impact_summary || {};
    traceRootHeading.textContent = `Root Entity: ${data.root_entity}`;

    metricLinkedCount.textContent = summary.total_linked_entities || 0;
    metricStmtCount.textContent = summary.total_statements || 0;
    metricDepth.textContent = summary.traversal_depth || 0;
    metricMsgCount.textContent = (summary.affected_messages || []).length;

    // Render linked component badges
    linkedComponentsChips.innerHTML = "";
    const components = summary.affected_components || [];
    if (components.length === 0) {
      linkedComponentsChips.innerHTML = `<span style="color: var(--text-muted); font-size: 0.85rem;">No secondary linked components</span>`;
    } else {
      components.forEach((comp) => {
        const chip = document.createElement("span");
        chip.className = "mini-badge badge-action";
        chip.style.cursor = "pointer";
        chip.textContent = comp;
        chip.addEventListener("click", () => {
          traceEntityInput.value = comp;
          handleTrace();
        });
        linkedComponentsChips.appendChild(chip);
      });
    }

    // Render statement breakdown badges
    stmtBreakdownChips.innerHTML = "";
    const breakdown = summary.statements_by_type || {};
    Object.entries(breakdown).forEach(([type, count]) => {
      const badge = document.createElement("span");
      badge.className = `mini-badge badge-${type.toLowerCase()}`;
      badge.textContent = `${count} ${type}${count === 1 ? "" : "s"}`;
      stmtBreakdownChips.appendChild(badge);
    });

    // Render Dependency Hops
    const hops = data.dependency_hops || [];
    hopsCount.textContent = `${hops.length} hop${hops.length === 1 ? "" : "s"}`;
    hopsGrid.innerHTML = "";

    if (hops.length === 0) {
      hopsGrid.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No multi-hop links discovered.</p>`;
    } else {
      hops.forEach((hop) => {
        const card = document.createElement("div");
        card.className = "hop-card";

        const stmtsHtml = (hop.statements || [])
          .map((s) => `<div>${escapeHtml(s)}</div>`)
          .join("");

        card.innerHTML = `
          <div class="hop-card-header">
            <span class="mini-badge badge-rel">Hop Distance: ${hop.hop_distance}</span>
            <span class="mini-badge badge-action">${hop.relationship}</span>
          </div>
          <div class="hop-route">
            <span>${escapeHtml(hop.source_entity)}</span>
            <span class="hop-arrow">&rarr;</span>
            <span style="color: #38bdf8;">${escapeHtml(hop.target_entity)}</span>
          </div>
          <div class="hop-statements">
            ${stmtsHtml}
          </div>
          <div class="evidence-provenance">
            <span><strong>Via Message:</strong> ${hop.via_message_id}</span>
            <span><strong>Document:</strong> ${escapeHtml(hop.document_id)}</span>
          </div>
        `;
        hopsGrid.appendChild(card);
      });
    }

    // Render Statement Timeline
    const timeline = data.timeline || [];
    timelineCount.textContent = `${timeline.length} event${timeline.length === 1 ? "" : "s"}`;
    timelineList.innerHTML = "";

    if (timeline.length === 0) {
      timelineList.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;">No statements recorded on this dependency path.</p>`;
    } else {
      timeline.forEach((item) => {
        const itemEl = document.createElement("div");
        itemEl.className = "timeline-item";

        itemEl.innerHTML = `
          <div class="timeline-index-badge">#${item.order_index}</div>
          <div class="timeline-body">
            <div class="timeline-meta">
              <span class="mini-badge badge-${item.statement_type.toLowerCase()}">${item.statement_type}</span>
              <span class="mini-badge badge-rel">${item.relationship}: ${escapeHtml(item.associated_entity)}</span>
            </div>
            <div class="timeline-statement-text">${escapeHtml(item.statement)}</div>
            <div class="evidence-provenance">
              <span><strong>Message ID:</strong> ${item.message_id}</span>
              <span><strong>Document:</strong> ${escapeHtml(item.document_id)}</span>
            </div>
          </div>
        `;
        timelineList.appendChild(itemEl);
      });
    }
  }

  function setTraceLoading(isLoading) {
    if (isLoading) {
      traceBtn.disabled = true;
      traceLoadingSection.classList.remove("hidden");
      traceResultSection.classList.add("hidden");
    } else {
      traceBtn.disabled = false;
      traceLoadingSection.classList.add("hidden");
    }
  }

  function showTraceError(msg) {
    traceErrorMessage.textContent = msg;
    traceErrorSection.classList.remove("hidden");
    traceResultSection.classList.add("hidden");
  }

  function hideTraceError() {
    traceErrorSection.classList.add("hidden");
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
