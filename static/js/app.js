/**
 * EcoLogix AI - Frontend Client Controller
 * Manages real-time multi-agent execution visualizer, telemetry simulation,
 * cryptographic ledger verification, and BigQuery analytics.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  let batchesData = [];
  let selectedBatchId = null;

  // DOM Elements
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const batchesContainer = document.getElementById("batches-container");
  const simBatchSelect = document.getElementById("sim-batch-select");
  const pipelineBatchSelect = document.getElementById("pipeline-batch-select");
  const plansContainer = document.getElementById("plans-container");
  const auditTableBody = document.getElementById("audit-table-body");
  const engineStatusPill = document.getElementById("engine-status-text");

  // ESG Ribbon Elements
  const valMeals = document.getElementById("val-meals");
  const valCo2e = document.getElementById("val-co2e");
  const valKg = document.getElementById("val-kg");
  const valUsd = document.getElementById("val-usd");
  const valWater = document.getElementById("val-water");

  // ==========================================
  // TAB NAVIGATION
  // ==========================================
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");

      if (targetId === "tab-audit") loadAuditLedger();
      if (targetId === "tab-dispatch") loadPlans();
      if (targetId === "tab-bigquery") loadBigQueryData();
    });
  });

  // ==========================================
  // INITIALIZATION & API STATUS
  // ==========================================
  async function checkEngineStatus() {
    try {
      const res = await fetch("/api/config/status");
      const data = await res.json();
      engineStatusPill.textContent = data.engine_mode;
      const modalMode = document.getElementById("modal-current-mode");
      if (modalMode) modalMode.textContent = data.engine_mode;
    } catch (e) {
      engineStatusPill.textContent = "Engine Offline";
    }
  }

  async function loadESGMetrics() {
    try {
      const res = await fetch("/api/analytics/esg");
      const data = await res.json();
      valMeals.textContent = Number(data.total_meals_provided).toLocaleString();
      valCo2e.textContent = `${data.total_co2e_abated_kg.toLocaleString()} kg`;
      valKg.textContent = `${data.total_salvaged_kg.toLocaleString()} kg`;
      valUsd.textContent = `$${data.total_economic_value_saved_usd.toLocaleString()}`;
      valWater.textContent = `${data.total_water_saved_m3.toLocaleString()} m³`;
    } catch (e) {
      console.error("Failed to load ESG metrics", e);
    }
  }

  async function loadBatches() {
    try {
      const res = await fetch("/api/batches");
      batchesData = await res.json();
      renderBatchesGrid();
      populateBatchDropdowns();
      if (!selectedBatchId && batchesData.length > 0) {
        selectBatch(batchesData[0].batch_id);
      }
    } catch (e) {
      console.error("Failed to load batches", e);
    }
  }

  function populateBatchDropdowns() {
    simBatchSelect.innerHTML = "";
    pipelineBatchSelect.innerHTML = "";
    batchesData.forEach(b => {
      const opt1 = document.createElement("option");
      opt1.value = b.batch_id;
      opt1.textContent = `${b.batch_id} - ${b.product_name}`;
      simBatchSelect.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = b.batch_id;
      opt2.textContent = `${b.batch_id} - ${b.product_name}`;
      pipelineBatchSelect.appendChild(opt2);
    });
    if (selectedBatchId) {
      simBatchSelect.value = selectedBatchId;
      pipelineBatchSelect.value = selectedBatchId;
    }
  }

  function renderBatchesGrid() {
    batchesContainer.innerHTML = "";
    batchesData.forEach(batch => {
      const isSelected = batch.batch_id === selectedBatchId;
      const card = document.createElement("div");
      card.className = `batch-card ${isSelected ? "selected" : ""}`;
      card.dataset.id = batch.batch_id;

      // Status Badge
      let badgeClass = "badge-optimal";
      if (batch.safety_status.includes("WARNING") || batch.safety_status.includes("MONITOR")) {
        badgeClass = "badge-warning";
      } else if (batch.safety_status.includes("HAZARDOUS") || batch.safety_status.includes("CONDEMNED") || batch.safety_status.includes("HIGH_RISK")) {
        badgeClass = "badge-danger";
      }

      // Spoilage percentage for progress bar
      const spoilagePct = Math.min(100, Math.round(batch.kinetic_spoilage_index * 100));
      const fillClass = spoilagePct > 80 ? "fill-red" : spoilagePct > 45 ? "fill-amber" : "fill-green";

      const latestTemp = batch.telemetry_history.length > 0 
        ? batch.telemetry_history[batch.telemetry_history.length - 1].temperature_c.toFixed(1)
        : "--";

      card.innerHTML = `
        <div class="batch-card-header">
          <div class="batch-title-group">
            <h3>${batch.product_name}</h3>
            <div class="batch-meta-sub">
              <span>ID: ${batch.batch_id}</span>
              <span>•</span>
              <span>${batch.category}</span>
              <span>•</span>
              <span>${batch.current_location_name}</span>
            </div>
          </div>
          <span class="status-badge ${badgeClass}">${batch.safety_status}</span>
        </div>

        <div class="batch-metrics-row">
          <div class="metric-item">
            <span class="val">${latestTemp}°C</span>
            <span class="lbl">Current Temp</span>
          </div>
          <div class="metric-item">
            <span class="val">${batch.effective_rsl_hours.toFixed(1)}h</span>
            <span class="lbl">Dynamic Shelf Life</span>
          </div>
          <div class="metric-item">
            <span class="val">${batch.danger_zone_minutes.toFixed(0)}m</span>
            <span class="lbl">Danger Zone</span>
          </div>
          <div class="metric-item">
            <span class="val">${batch.current_qty_kg} kg</span>
            <span class="lbl">Quantity</span>
          </div>
        </div>

        <div class="progress-group">
          <div class="progress-header">
            <span>Biochemical Spoilage Index (Q-10 Kinetics)</span>
            <span>${spoilagePct}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill ${fillClass}" style="width: ${spoilagePct}%;"></div>
          </div>
        </div>
      `;

      card.addEventListener("click", () => {
        selectBatch(batch.batch_id);
      });

      batchesContainer.appendChild(card);
    });
  }

  function selectBatch(batchId) {
    selectedBatchId = batchId;
    simBatchSelect.value = batchId;
    pipelineBatchSelect.value = batchId;

    document.querySelectorAll(".batch-card").forEach(c => {
      c.classList.toggle("selected", c.dataset.id === batchId);
    });

    const batch = batchesData.find(b => b.batch_id === batchId);
    if (batch) renderTelemetryTrace(batch);
  }

  function renderTelemetryTrace(batch) {
    const container = document.getElementById("telemetry-chart-placeholder");
    if (!batch.telemetry_history || batch.telemetry_history.length === 0) {
      container.innerHTML = "No sensor history logged.";
      return;
    }

    const readings = [...batch.telemetry_history].reverse().slice(0, 8);
    let html = `<strong>Batch: ${batch.batch_id} (${batch.product_name})</strong><br>`;
    html += `Safe Threshold: ${batch.min_safe_temp_c}°C to ${batch.max_safe_temp_c}°C<br><br>`;
    html += `Recent Sensor Feed:<br>`;

    readings.forEach((r, idx) => {
      const dangerMark = (r.temperature_c >= 4.4 && r.temperature_c <= 60.0) ? " ⚠️ [DANGER ZONE]" : "";
      html += `[${idx + 1}] Temp: ${r.temperature_c.toFixed(1)}°C | Hum: ${r.humidity_pct.toFixed(0)}%${dangerMark}<br>`;
    });

    container.innerHTML = html;
  }

  // ==========================================
  // TELEMETRY SIMULATOR ACTIONS
  // ==========================================
  async function simulateTelemetry(tempDelta, durationMin) {
    if (!selectedBatchId) return;
    try {
      const res = await fetch(`/api/batches/${selectedBatchId}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ temp_delta_c: tempDelta, duration_min: durationMin })
      });
      const updated = await res.json();
      await loadBatches();
      selectBatch(updated.batch_id);
    } catch (e) {
      console.error("Simulation error", e);
    }
  }

  document.getElementById("btn-sim-mild-spike").addEventListener("click", () => {
    simulateTelemetry(3.5, 30.0);
  });

  document.getElementById("btn-sim-severe-failure").addEventListener("click", () => {
    simulateTelemetry(12.0, 180.0);
  });

  document.getElementById("btn-sim-restore-cooling").addEventListener("click", () => {
    simulateTelemetry(-6.0, 30.0);
  });

  simBatchSelect.addEventListener("change", (e) => {
    selectBatch(e.target.value);
  });

  pipelineBatchSelect.addEventListener("change", (e) => {
    selectBatch(e.target.value);
  });

  // ==========================================
  // MULTI-AGENT PIPELINE RUNNER
  // ==========================================
  const triggerBtn = document.getElementById("btn-trigger-pipeline");
  const fullJsonBlock = document.getElementById("pipeline-full-json");
  const latencyTag = document.getElementById("pipeline-total-latency");

  triggerBtn.addEventListener("click", async () => {
    const batchId = pipelineBatchSelect.value || selectedBatchId;
    if (!batchId) return;
    await executeAgenticPipeline(batchId);
  });

  document.getElementById("btn-run-all-triage").addEventListener("click", async () => {
    try {
      engineStatusPill.textContent = "Autonomous Fleet Triage Running...";
      const res = await fetch("/api/pipeline/run-all", { method: "POST" });
      const data = await res.json();
      await loadBatches();
      await loadPlans();
      await loadESGMetrics();
      await checkEngineStatus();
      alert(`Autonomous Fleet Triage Complete! Triaged ${data.total_triaged} batches.`);
    } catch (e) {
      console.error("Fleet triage failed", e);
    }
  });

  async function executeAgenticPipeline(batchId) {
    resetPipelineVisualizer();
    triggerBtn.disabled = true;
    triggerBtn.textContent = "Pipeline Running...";

    // Stage 1 visual active
    setStageState(1, "running", "Computing Arrhenius decay...");
    
    try {
      const res = await fetch(`/api/pipeline/run/${batchId}`, { method: "POST" });
      const trace = await res.json();

      // Animate stages step-by-step
      await sleep(250);
      const s1 = trace.stages.find(s => s.stage_name === "SENSING_AND_KINETICS");
      setStageState(1, "success", `KSI: ${s1.output.kinetic_spoilage_index} | RSL: ${s1.output.effective_rsl_hours}h`);

      setStageState(2, "running", "Querying Gemini reasoning engine...");
      await sleep(350);
      const s2 = trace.stages.find(s => s.stage_name === "COGNITIVE_TRIAGE");
      setStageState(2, "success", `${s2.output.triage_verdict} (Conf: ${s2.output.confidence_score * 100}%)`);

      setStageState(3, "running", "Optimizing geospatial matching...");
      await sleep(250);
      const s3 = trace.stages.find(s => s.stage_name === "LOGISTICS_ALLOCATION");
      setStageState(3, "success", `Matched: ${s3.output.matched_hub} (${s3.output.distance_km} km)`);

      setStageState(4, "running", "Verifying HACCP safety boundaries...");
      await sleep(200);
      const s4 = trace.stages.find(s => s.stage_name === "HACCP_SAFETY_GATE");
      setStageState(4, s4.output.haccp_compliant ? "success" : "running", s4.output.haccp_compliant ? "HACCP Certified" : "Safety Override Active");

      setStageState(5, "running", "Generating SHA-256 token...");
      await sleep(200);
      const finalPlan = trace.final_plan;
      setStageState(5, "success", `Token: ${finalPlan ? finalPlan.verification_hash : "N/A"}`);

      latencyTag.textContent = `Total Latency: ${trace.total_latency_ms} ms`;
      fullJsonBlock.textContent = JSON.stringify(trace, null, 2);

      await loadBatches();
      await loadPlans();
      await loadESGMetrics();
    } catch (e) {
      console.error("Pipeline failure", e);
      fullJsonBlock.textContent = `Error executing pipeline: ${e.message}`;
    } finally {
      triggerBtn.disabled = false;
      triggerBtn.textContent = "⚡ Execute Agentic Pipeline";
    }
  }

  function setStageState(stageNum, stateClass, text) {
    const card = document.getElementById(`card-stage-${stageNum}`);
    const status = document.getElementById(`status-stage-${stageNum}`);
    const output = document.getElementById(`output-stage-${stageNum}`);

    card.classList.remove("stage-active", "stage-done");
    status.classList.remove("running", "success");

    if (stateClass === "running") {
      card.classList.add("stage-active");
      status.classList.add("running");
      status.textContent = "Active";
      output.textContent = text;
    } else if (stateClass === "success") {
      card.classList.add("stage-done");
      status.classList.add("success");
      status.textContent = "Completed";
      output.textContent = text;
    }
  }

  function resetPipelineVisualizer() {
    for (let i = 1; i <= 5; i++) {
      const card = document.getElementById(`card-stage-${i}`);
      const status = document.getElementById(`status-stage-${i}`);
      const output = document.getElementById(`output-stage-${i}`);
      card.classList.remove("stage-active", "stage-done");
      status.classList.remove("running", "success");
      status.textContent = "Idle";
      output.textContent = "Awaiting trigger";
    }
    latencyTag.textContent = "Latency: -- ms";
    fullJsonBlock.textContent = "// Executing multi-agent pipeline...";
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ==========================================
  // DISPATCH PLANS & HITL GATEWAY
  // ==========================================
  async function loadPlans() {
    try {
      const res = await fetch("/api/plans");
      const plans = await res.json();
      renderPlans(plans);
    } catch (e) {
      console.error("Failed to load plans", e);
    }
  }

  function renderPlans(plans) {
    plansContainer.innerHTML = "";
    if (plans.length === 0) {
      plansContainer.innerHTML = `
        <div class="sidebar-card text-muted">
          No allocation plans generated yet. Run the Multi-Agent Pipeline to generate intelligent dispatch routes.
        </div>
      `;
      return;
    }

    plans.forEach(plan => {
      const card = document.createElement("div");
      const isHitlPending = plan.hitl_required && !plan.hitl_approved;
      card.className = `plan-card ${isHitlPending ? "hitl-alert" : ""}`;

      let hitlHtml = "";
      if (isHitlPending) {
        hitlHtml = `
          <div style="display: flex; gap: 10px;">
            <button class="btn btn-primary btn-sm btn-approve-plan" data-id="${plan.plan_id}">
              ✍️ Sign & Authorize Dispatch (Food Safety Officer)
            </button>
            <button class="btn btn-danger btn-sm btn-reject-plan" data-id="${plan.plan_id}">
              ⛔ Divert to Biogas
            </button>
          </div>
        `;
      } else if (plan.hitl_approved) {
        hitlHtml = `<span style="color: #34d399; font-weight: 600; font-size: 13px;">✓ Authorized by ${plan.hitl_approved_by}</span>`;
      } else {
        hitlHtml = `<span style="color: #34d399; font-weight: 600; font-size: 13px;">✓ Autonomous Fast-Track Dispatch</span>`;
      }

      card.innerHTML = `
        <div class="plan-header">
          <div>
            <h3>${plan.batch_product} (${plan.quantity_kg} kg)</h3>
            <div class="batch-meta-sub">
              <span>Plan ID: ${plan.plan_id}</span>
              <span>•</span>
              <span>Destination: <strong>${plan.recipient_name}</strong> (${plan.recipient_type})</span>
            </div>
          </div>
          <span class="status-badge ${plan.haccp_compliant ? 'badge-optimal' : 'badge-danger'}">
            ${plan.recommended_action}
          </span>
        </div>

        <div class="plan-grid-details">
          <div class="metric-item">
            <span class="val">${plan.distance_km} km</span>
            <span class="lbl">Transit Distance</span>
          </div>
          <div class="metric-item">
            <span class="val">${plan.estimated_transit_time_min} mins</span>
            <span class="lbl">Estimated Arrival</span>
          </div>
          <div class="metric-item">
            <span class="val">${plan.meals_provided} meals</span>
            <span class="lbl">Food Bank Impact</span>
          </div>
          <div class="metric-item">
            <span class="val">${plan.co2e_abated_kg} kg</span>
            <span class="lbl">CO₂e Abated</span>
          </div>
        </div>

        <div class="plan-reasoning">
          <strong>Cognitive Rationale:</strong> ${plan.ai_reasoning}
        </div>

        <div class="plan-actions-footer">
          <div class="token-pill">HACCP Token: ${plan.verification_hash}</div>
          <div>${hitlHtml}</div>
        </div>
      `;

      plansContainer.appendChild(card);
    });

    // Attach HITL event handlers
    document.querySelectorAll(".btn-approve-plan").forEach(b => {
      b.addEventListener("click", async (e) => {
        const planId = e.target.getAttribute("data-id");
        await approvePlan(planId);
      });
    });

    document.querySelectorAll(".btn-reject-plan").forEach(b => {
      b.addEventListener("click", async (e) => {
        const planId = e.target.getAttribute("data-id");
        await rejectPlan(planId);
      });
    });
  }

  async function approvePlan(planId) {
    try {
      const res = await fetch(`/api/plans/${planId}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approver_name: "Dr. Jane Reynolds, Food Safety Officer" })
      });
      const data = await res.json();
      alert(data.status);
      await loadPlans();
      await loadESGMetrics();
    } catch (e) {
      console.error("Approval error", e);
    }
  }

  async function rejectPlan(planId) {
    try {
      const res = await fetch(`/api/plans/${planId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Manual sensory check failed; diverged to anaerobic biogas." })
      });
      const data = await res.json();
      alert(data.status);
      await loadPlans();
      await loadESGMetrics();
    } catch (e) {
      console.error("Rejection error", e);
    }
  }

  // ==========================================
  // TAMPER-EVIDENT HACCP AUDIT LEDGER
  // ==========================================
  async function loadAuditLedger() {
    try {
      const res = await fetch("/api/audit-ledger");
      const ledger = await res.json();
      renderAuditTable(ledger);
    } catch (e) {
      console.error("Failed to load audit ledger", e);
    }
  }

  function renderAuditTable(ledger) {
    auditTableBody.innerHTML = "";
    if (ledger.length === 0) {
      auditTableBody.innerHTML = `<tr><td colspan="7" class="text-muted" style="text-align: center;">No audit blocks recorded yet.</td></tr>`;
      return;
    }

    [...ledger].reverse().forEach(entry => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><strong>${entry.log_id}</strong></td>
        <td>${entry.timestamp.replace("T", " ").substring(0, 19)}</td>
        <td>${entry.actor_id} <span class="text-dim">(${entry.actor_role})</span></td>
        <td><span class="status-badge badge-optimal">${entry.action_type}</span></td>
        <td>${entry.batch_id || "--"}</td>
        <td class="hash-cell">${entry.previous_hash.substring(0, 12)}...</td>
        <td class="hash-cell">${entry.current_hash.substring(0, 12)}...</td>
      `;
      auditTableBody.appendChild(row);
    });
  }

  document.getElementById("btn-verify-blockchain").addEventListener("click", async () => {
    try {
      const res = await fetch("/api/audit-ledger/verify");
      const data = await res.json();
      const banner = document.getElementById("blockchain-verification-banner");
      const txt = document.getElementById("chain-status-text");
      const tip = document.getElementById("chain-hash-tip");

      if (data.integrity_intact) {
        banner.style.background = "rgba(16, 185, 129, 0.15)";
        banner.style.borderColor = "#10b981";
        txt.innerHTML = `✅ Cryptographic Chain Verified: 100% Tamper-Evident across all ${data.total_blocks} blocks`;
        tip.textContent = `Tip Hash: ${data.latest_hash}`;
      } else {
        banner.style.background = "rgba(239, 68, 68, 0.2)";
        banner.style.borderColor = "#ef4444";
        txt.innerHTML = `❌ Integrity Violation: ${data.error}`;
      }
    } catch (e) {
      console.error("Ledger verification error", e);
    }
  });

  // ==========================================
  // GOOGLE BIGQUERY TAB
  // ==========================================
  async function loadBigQueryData() {
    try {
      const res = await fetch("/api/bigquery/export");
      const data = await res.json();
      document.getElementById("bq-streaming-json").textContent = JSON.stringify(data.streaming_rows, null, 2);
      document.getElementById("bq-ddl-view").textContent = `${data.bigquery_ddl}\n\n${data.analytical_sql}`;
    } catch (e) {
      console.error("BigQuery export failed", e);
    }
  }

  document.getElementById("btn-refresh-bq").addEventListener("click", loadBigQueryData);

  // ==========================================
  // CONFIGURATION MODAL & GEMINI SETTINGS
  // ==========================================
  const configModal = document.getElementById("config-modal");
  document.getElementById("btn-config-modal").addEventListener("click", () => {
    configModal.classList.add("open");
  });
  document.getElementById("btn-close-modal").addEventListener("click", () => {
    configModal.classList.remove("open");
  });
  document.getElementById("btn-dismiss-modal").addEventListener("click", () => {
    configModal.classList.remove("open");
  });

  document.getElementById("btn-save-key").addEventListener("click", async () => {
    const key = document.getElementById("input-gemini-key").value;
    if (!key) {
      alert("Please enter a valid key or dismiss to use the offline cognitive fallback.");
      return;
    }
    try {
      const res = await fetch("/api/config/gemini-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: key })
      });
      const data = await res.json();
      alert(data.status);
      configModal.classList.remove("open");
      await checkEngineStatus();
    } catch (e) {
      alert("Error setting key");
    }
  });

  // Reset Scenarios
  document.getElementById("btn-reset-data").addEventListener("click", async () => {
    if (confirm("Reset all scenario batches, plans, and ledger to seed state?")) {
      await fetch("/api/batches/reset", { method: "POST" });
      await loadBatches();
      await loadPlans();
      await loadAuditLedger();
      await loadESGMetrics();
      alert("Scenario reset complete.");
    }
  });

  // Boot Sequence
  checkEngineStatus();
  loadBatches();
  loadPlans();
  loadESGMetrics();
});
