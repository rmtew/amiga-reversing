/* Restoration UI is a client of the same operations as CLI and MCP. */
const restorationView = {project: null, revision: null, selected: null, inspected: null, page: null, query: null, verificationId: null, probeId: null};

async function restorationRequest(project, operation, parameters = {}) {
  return fetchJson(`/api/projects/${encodeURIComponent(project)}/restoration`, {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({operation, ...parameters}),
  });
}

function restorationValue(value) {
  if (value === null || value === undefined) return "unknown";
  if (typeof value !== "object") return String(value);
  return JSON.stringify(value);
}

function restorationFacts(items) {
  if (!Array.isArray(items) || !items.length) return '<p class="restoration-empty">No facts in this scope.</p>';
  return items.map((item, index) => `<details class="restoration-fact"><summary>
    ${Number.isInteger(item.section_index) && Number.isFinite(item.source_offset) ? `<button type="button" data-restore-inspect="${index}">s${item.section_index}:$${item.source_offset.toString(16)}</button>` : ""}
    ${escapeHtml(item.name || item.symbol || item.text || item.interpretation?.question || item.kind || item.action_id || "Evidence")}
    ${item.action_id ? `<button type="button" data-restore-review="${escapeHtml(item.action_id)}">Review this action</button>` : ""}
    ${item.status ? `<span class="project-badge">${escapeHtml(item.status)}${item.status === "accepted" && item.verification_current === false ? " · needs reverification" : ""}</span>` : ""}
    </summary><dl>${Object.entries(item).map(([key, value]) => `<dt>${escapeHtml(key.replaceAll("_", " "))}</dt><dd>${escapeHtml(restorationValue(value))}</dd>`).join("")}</dl></details>`).join("");
}

function restorationMessage(message, error = false) {
  const status = document.getElementById("restoration-status");
  if (status) { status.textContent = message; status.classList.toggle("error", error); }
}

async function restorationRun(operation, parameters = {}) {
  restorationMessage("Working…");
  try {
    const result = await restorationRequest(restorationView.project, operation, parameters);
    restorationView.revision = result.revision || restorationView.revision;
    const revision = document.getElementById("restoration-revision");
    if (revision) revision.textContent = `Revision ${String(restorationView.revision || "pending").slice(0, 12)}`;
    restorationMessage((result.unknowns || []).map(restorationValue).join(" · ") || "Ready");
    return result;
  } catch (error) {
    restorationMessage(`${error.message || error}. Refresh and inspect before retrying a refused change.`, true);
    throw error;
  }
}

async function openRestorationPanel() {
  document.getElementById("restoration-panel")?.remove();
  restorationView.project = state.project;
  restorationView.revision = null;
  restorationView.inspected = null;
  restorationView.verificationId = null;
  restorationView.probeId = null;
  const selected = SelectionModel.current()?.locator;
  restorationView.selected = selected ? {section_index: selected.section_index, source_offset: selected.start_offset, row_kind: selected.row_kind} : null;
  document.getElementById("app").insertAdjacentHTML("beforeend", `<section id="restoration-panel" class="restoration-panel" aria-label="Source restoration">
    <header><strong>Source restoration</strong><span id="restoration-revision"></span><button type="button" id="restoration-close">Close</button></header>
    <p>Select a gap, inspect evidence, preserve an interpretation, rebuild, then review.</p>
    <div id="restoration-status" role="status">Preparing analysis…</div>
    <nav><button type="button" id="restoration-refresh">Refresh state</button><button type="button" id="restoration-selected">Inspect selected source</button><button type="button" id="restoration-history">History</button><button type="button" id="restoration-pointer-exceptions">Pointer exceptions</button></nav>
    <form id="restoration-search"><label>Explore <select name="kind">${["gaps", "symbols", "functions", "references", "fields", "edges", "instructions", "typed_pointers"].map(x => `<option value="${x}">${x === "typed_pointers" ? "pointer exceptions" : x}</option>`).join("")}</select></label><label>Name / symbol / type <input name="query" type="search"></label><button>Search</button></form>
    <div id="restoration-results"></div><button id="restoration-next" type="button" hidden>Next page</button>
    <section id="restoration-inspection"></section>
    <section class="restoration-validation"><h3>Verify and review</h3><button id="restoration-verify" type="button">Regenerate and verify exact bytes</button><div id="restoration-verification"></div>
    <form id="restoration-probe"><label>Runtime question <input name="question" required></label><label>Configured scenario <input name="scenario" placeholder="pandora-gameplay-entry" required></label><button>Run bounded probe</button></form>
    <form id="restoration-review"><label>Action ID <input name="action_id" required></label><label>Decision <select name="decision"><option>defer</option><option>accept</option><option>reject</option></select></label><label>Reason <input name="reason" required></label><button>Record review</button><button type="button" id="restoration-undo">Undo action</button><button type="button" id="restoration-redo">Redo action</button></form>
    </section></section>`);
  const panel = document.getElementById("restoration-panel");
  const safe = fn => async event => { try { await fn(event); } catch (_) { /* status above retains refusal */ } };
  panel.querySelector("#restoration-close").onclick = () => panel.remove();
  panel.querySelector("#restoration-refresh").onclick = safe(async () => {
    const result = await restorationRun("state");
    if (!result.ready) restorationMessage("Analysis is preparing. Refresh state when ready.");
  });
  panel.querySelector("#restoration-selected").onclick = safe(async () => {
    const locator = SelectionModel.current()?.locator;
    if (locator) await restorationInspect({section_index: locator.section_index, source_offset: locator.start_offset, row_kind: locator.row_kind});
    else restorationMessage("Select a source row first.");
  });
  panel.querySelector("#restoration-search").onsubmit = safe(async event => {
    event.preventDefault();
    const form = new FormData(event.target);
    const kind = form.get("kind"), text = String(form.get("query") || "").trim();
    restorationView.query = {kind, limit: 25, ...(kind === "typed_pointers" ? {exceptions_only: true} : {}), ...(text ? {[kind === "typed_pointers" ? "struct_name" : kind === "references" ? "symbol" : "query"]: text} : {})};
    await restorationSearch();
  });
  panel.querySelector("#restoration-next").onclick = safe(() => restorationSearch(restorationView.page.next_cursor));
  panel.querySelector("#restoration-pointer-exceptions").onclick = safe(async () => {
    restorationView.query = {kind: "typed_pointers", exceptions_only: true, limit: 25};
    await restorationSearch();
  });
  panel.querySelector("#restoration-history").onclick = safe(async () => {
    restorationView.query = null;
    const result = await restorationRun("history", {expected_revision: restorationView.revision, limit: 25});
    restorationShowPage(result);
  });
  panel.querySelector("#restoration-verify").onclick = safe(async () => {
    const result = await restorationRun("verify", {expected_revision: restorationView.revision});
    restorationView.verificationId = result.receipt_id;
    panel.querySelector("#restoration-verification").textContent = restorationValue(result);
  });
  panel.querySelector("#restoration-probe").onsubmit = safe(async event => {
    event.preventDefault();
    const result = await restorationRun("probe", {expected_revision: restorationView.revision, ...Object.fromEntries(new FormData(event.target)), verification_id: restorationView.verificationId});
    restorationView.probeId = result.receipt_id;
    panel.querySelector("#restoration-verification").textContent = restorationValue(result);
  });
  panel.querySelector("#restoration-review").onsubmit = safe(async event => {
    event.preventDefault();
    const result = await restorationRun("review", {expected_revision: restorationView.revision, ...Object.fromEntries(new FormData(event.target)), verification_id: restorationView.verificationId, probe_id: restorationView.probeId});
    restorationMessage(`Review recorded: ${restorationValue(result.decision || result.status || "saved")}`);
  });
  for (const redo of [false, true]) panel.querySelector(redo ? "#restoration-redo" : "#restoration-undo").onclick = safe(async () => {
    const action_id = panel.querySelector('[name="action_id"]').value;
    await restorationRun("rollback", {expected_revision: restorationView.revision, action_id, redo});
    await refreshAnalysisAfterManualMetadataAction(state.project, {});
  });
  try {
    const snapshot = await restorationRun("state");
    if (snapshot.ready && restorationView.selected) await restorationInspect(restorationView.selected);
    else if (!snapshot.ready) restorationMessage("Analysis is preparing. Refresh state when ready.");
  } catch (_) { /* message displayed */ }
}

function restorationShowPage(result) {
  restorationView.page = result;
  const items = result.items || [];
  const node = document.getElementById("restoration-results");
  const pointerSummary = result.population_total !== undefined
    ? `<p>${result.population_total} typed pointers: ${result.outcomes?.symbolic || 0} symbolic, ${result.outcomes?.null || 0} null, ${result.outcomes?.unresolved || 0} unresolved, ${result.outcomes?.invalid || 0} invalid. Boundary fragments require inspection.</p>` : "";
  node.innerHTML = `${pointerSummary}<p>${items.length} of ${result.total ?? "unknown"} ${result.exceptions_only ? "exceptions" : "facts"} · ${escapeHtml(restorationValue(result.scope || "current revision"))}</p>${restorationFacts(items)}`;
  document.getElementById("restoration-next").hidden = !result.next_cursor;
  node.querySelectorAll("[data-restore-inspect]").forEach(button => { button.onclick = async () => {
    try { await restorationInspect(items[Number(button.dataset.restoreInspect)]); } catch (_) { /* message displayed */ }
  }; });
}

async function restorationSearch(cursor = null) {
  const result = await restorationRun(restorationView.query ? "query" : "history", {expected_revision: restorationView.revision, ...(restorationView.query || {limit: 25}), ...(cursor ? {cursor} : {})});
  restorationShowPage(result);
}

async function restorationInspect(item) {
  const result = await restorationRun("inspect", {expected_revision: restorationView.revision, section_index: item.section_index, source_offset: item.source_offset, ...(item.row_kind ? {row_kind: item.row_kind} : {})});
  restorationView.inspected = result;
  const catalog = result.commands || {};
  const actions = (catalog.commands || []).filter(action => action.enabled !== false && action.appends_to_manual_action_log);
  const node = document.getElementById("restoration-inspection");
  node.innerHTML = `<h3>Source s${item.section_index}:$${item.source_offset.toString(16)}</h3>
    <button type="button" id="restoration-jump">Show in source</button><button type="button" id="restoration-label">Inspect label at this address</button>
    <h4>Instructions</h4>${restorationFacts(result.instructions?.items || result.instructions || [])}
    <h4>Function relationships</h4><p>Candidate ownership remains explicit; an unresolved transfer is not an absent call.</p>
    <nav>${["callers", "callees", "unresolved_transfers", "ranges"].map(relation => `<button type="button" data-restore-relation="${relation}">${relation.replaceAll("_", " ")}</button>`).join("")}</nav>
    <h4>Relationships and unknowns</h4><pre>${escapeHtml(restorationValue(result.relationships))}</pre>
    <h4>Interpretations</h4>${restorationFacts(result.interpretations?.items || result.interpretations || [])}
    <form id="restoration-interpret"><label>Change <select name="command">${actions.map((action, index) => `<option value="${index}">${escapeHtml(action.label || action.command_id)}</option>`).join("")}</select></label><div id="restoration-parameters"></div>
    <label>Question <input name="question" required></label><label>Evidence and reasoning <textarea name="reason" required></textarea></label>
    <label>Status <select name="status"><option value="hypothesis">Hypothesis</option><option value="analysis_proven">Supported by analysis</option></select></label>
    <label>Evidence source keys (one per line)<textarea name="refs" required>${escapeHtml(result.locator?.row_key || result.row_locator?.row_key || "")}</textarea></label>
    <button ${actions.length ? "" : "disabled"}>Save interpretation</button></form>`;
  node.querySelector("#restoration-jump").onclick = () => jumpToListingSectionOffset(state.project, item.section_index, item.source_offset);
  node.querySelector("#restoration-label").onclick = async () => { try { await restorationInspect({...item, row_kind: "label"}); } catch (_) { /* message displayed */ } };
  node.querySelectorAll("[data-restore-relation]").forEach(button => { button.onclick = async () => {
    restorationView.query = {kind: "functions", relation: button.dataset.restoreRelation, section_index: item.section_index, source_offset: item.source_offset, limit: 25};
    try { await restorationSearch(); } catch (_) { /* message displayed */ }
  }; });
  const form = node.querySelector("form");
  function fields() {
    const action = actions[Number(form.elements.command.value)];
    const values = Object.fromEntries(commandParameterSchemaFields(action).map(field => [field.name, defaultCommandParameterValue(action, field)]));
    node.querySelector("#restoration-parameters").innerHTML = commandParameterSchemaFields(action).map(field => renderCommandParameterField(field, {action, values, errors: {}})).join("");
  }
  form.elements.command.onchange = fields;
  fields();
  form.onsubmit = async event => {
    event.preventDefault();
    const action = actions[Number(form.elements.command.value)];
    const parameters = {};
    for (const field of commandParameterSchemaFields(action)) {
      const control = form.querySelector(`[data-command-parameter-name="${CSS.escape(field.name)}"]`);
      if (!control || (!field.required && control.value === "")) continue;
      parameters[field.name] = field.type === "boolean" ? control.checked : ["integer", "number"].includes(field.type) ? Number(control.value) : control.value;
    }
    try {
      const saved = await restorationRun("interpret", {expected_revision: result.revision, command_id: action.command_id || action.action_id, context: action.target_context || catalog.context, parameters,
        evidence: {question: form.elements.question.value, reason: form.elements.reason.value, source_evidence_status: form.elements.status.value, source_evidence_refs: form.elements.refs.value.split("\n").map(x => x.trim()).filter(Boolean)}});
      const actionId = saved.action_id || saved.actions?.at(-1)?.action_id;
      if (actionId) document.querySelector('#restoration-review [name="action_id"]').value = actionId;
      restorationView.verificationId = null;
      restorationView.probeId = null;
      await refreshAnalysisAfterManualMetadataAction(state.project, {});
      restorationMessage("Interpretation saved. Regenerate and verify before accepting.");
    } catch (_) { /* retain form and refusal */ }
  };
}

document.addEventListener("click", event => {
  if (event.target.closest?.("#open-restoration")) void openRestorationPanel();
  const review = event.target.closest?.("[data-restore-review]");
  if (review) {
    event.preventDefault();
    document.querySelector('#restoration-review [name="action_id"]').value = review.dataset.restoreReview;
    document.getElementById("restoration-review").scrollIntoView({block: "nearest"});
  }
});
