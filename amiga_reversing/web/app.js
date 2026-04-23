const state = {
  project: null,
  projectData: null,
  loadingToken: 0,
  homeDropCleanup: null,
  typeCatalog: null,
  listingRows: [],
  virtualListing: {
    start: 0,
    end: 0,
    totalRows: 0,
    rowHeight: 22,
    generation: null,
    requestSeq: 0,
    scrollTimer: null,
    scrollRaf: null,
    pendingWindow: null,
    inFlightWindow: null,
    fetchAbortController: null,
    suppressScrollFetch: false,
  },
  listingColumns: {
    offset: 64,
    bytes: 180,
    code: 520,
    drag: null,
  },
  navigation: {
    overlayOpen: false,
    selectedClass: "typed-data",
    selectedIndex: 0,
    appSlotSymbol: null,
    entries: null,
    generation: null,
    originEntry: null,
    currentPreviewEntry: null,
    currentLocation: null,
    historyBack: [],
    historyForward: [],
  },
  stats: {
    overlayOpen: false,
    selectedTab: "fetch",
    fetchSamples: [],
  },
  reproduction: {
    panelOpen: false,
    report: null,
    reportKey: null,
    job: null,
    selectedIssueEntry: null,
  },
  analysisStatus: {
    text: "",
    state: "idle",
    clearTimer: null,
  },
};

const LISTING_INITIAL_ROW_WINDOW = 240;
const LISTING_MIN_WINDOW_ROWS = 120;
const LISTING_MAX_WINDOW_ROWS = 600;
const LISTING_OVERSCAN_SCREENS = 2;
const STATS_MAX_FETCH_SAMPLES = 240;
const LISTING_COLUMN_MIN_WIDTHS = {
  offset: 48,
  bytes: 80,
  code: 260,
};
const APP_SLOT_ACCESS_ORDER = ["read", "write", "read-write", "address"];
const APP_SLOT_ACCESS_LABELS = {
  read: "R",
  write: "W",
  "read-write": "RW",
  address: "A",
};
const ENTITY_SUBTYPES = [
  "",
  "string",
  "pointer_table",
  "struct_instance",
  "lookup_table",
  "sprite",
  "bitmap",
  "palette",
  "copper_list",
  "tilemap",
  "sound_sample",
  "level_data",
];

const JOB_PHASE_LABELS = {
  listing: {
    queued: "Queued",
    build_session: "Building session",
    build_c_rows: "Building C-backed rows",
    emit_rows: "Rendering listing",
    done: "Done",
    error: "Failed",
  },
  basic_listing: {
    queued: "Queued",
    build_session: "Opening file",
    build_c_rows: "Building initial rows",
    emit_rows: "Rendering listing",
    done: "Done",
    error: "Failed",
  },
  full_listing: {
    queued: "Queued",
    build_session: "Opening file",
    build_basic_rows: "Building initial rows",
    emit_basic_rows: "Showing initial listing",
    build_c_rows: "Enriching analysis",
    emit_rows: "Updating listing",
    done: "Done",
    error: "Failed",
  },
  project_create: {
    queued: "Queued",
    write_media: "Saving media",
    analyze_disk: "Analyzing disk",
    create_bootblock_target: "Creating boot block target",
    import_targets: "Creating targets",
    write_manifest: "Writing manifest",
    parse_executable: "Parsing executable",
    create_target: "Creating target",
    finalize: "Finalizing project",
    done: "Done",
    error: "Failed",
  },
  reproduction: {
    queued: "Queued",
    prepare: "Preparing reproduction",
    assemble: "Assembling",
    diff: "Diffing",
    done: "Done",
    stale: "Stale",
    error: "Failed",
  },
};

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload.data;
}

function isAbortError(error) {
  return error instanceof DOMException && error.name === "AbortError";
}

function projectPath(projectId) {
  return `/${encodeURIComponent(projectId)}`;
}

function currentProjectId() {
  const path = window.location.pathname.replace(/^\/+|\/+$/g, "");
  return path || null;
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;");
}

function requireObject(value, description) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${description} is missing`);
  }
  return value;
}

function requireArray(value, description) {
  if (!Array.isArray(value)) {
    throw new Error(`${description} is missing`);
  }
  return value;
}

function formatProjectDetails(projectData) {
  if (projectData.project.kind === "disk") {
    const details = [];
    details.push(projectData.project.id);
    if (projectData.project.disk_type) {
      details.push(projectData.project.disk_type);
    }
    if (projectData.project.source_path) {
      details.push(projectData.project.source_path);
    }
    if (projectData.project.target_count !== undefined) {
      details.push(`${projectData.project.target_count} targets`);
    }
    const manifest = requireObject(projectData.disk_manifest, "Disk manifest");
    const analysis = requireObject(manifest.analysis, "Disk analysis");
    const filesystem = analysis.filesystem || null;
    const diskInfo = analysis.disk_info || null;
    if (diskInfo && diskInfo.variant) {
      details.push(`variant=${diskInfo.variant}`);
    }
    if (filesystem && filesystem.type) {
      details.push(`filesystem=${filesystem.type}`);
    }
    if (filesystem && filesystem.volume_name) {
      details.push(`volume=${filesystem.volume_name}`);
    }
    return details.join(" | ");
  }
  const details = [];
  details.push(projectData.project.id);
  if (projectData.project.binary_path) {
    details.push(projectData.project.binary_path);
  }
  if (!projectData.project.output_path) {
    details.push("No disassembly output");
  }
  if (!projectData.project.ready) {
    details.push("No executable loaded");
  }
  return details.join(" | ");
}

function buildProjectBadges(project, projectData = null) {
  const manifest = projectData && projectData.disk_manifest ? projectData.disk_manifest : null;
  const analysis = manifest && manifest.analysis ? manifest.analysis : null;
  const filesystem = analysis && analysis.filesystem ? analysis.filesystem : null;
  const diskInfo = analysis && analysis.disk_info ? analysis.disk_info : null;
  const badges = [];
  if (project.kind === "binary") {
    const targetType = project.target_type || "executable";
    badges.push({
      label: formatTargetTypeLabel(targetType),
      title: project.ready
        ? `${formatTargetTypeLabel(targetType)} target`
        : `${formatTargetTypeLabel(targetType)} target not ready`,
    });
    badges.push(reproductionBadge(project.ready, projectData?.reproduction || null));
  } else {
    badges.push({
      label: "disk",
      title: [
        "Disk project",
        diskInfo && diskInfo.variant ? `Variant: ${diskInfo.variant}` : null,
        project.target_count !== undefined ? `Targets: ${project.target_count}` : null,
      ].filter(Boolean).join("\n"),
    });
    if (project.disk_type) {
      badges.push({
        label: project.disk_type,
        title: [
          `Disk type: ${project.disk_type}`,
          filesystem && filesystem.type ? `Filesystem: ${filesystem.type}` : null,
          filesystem && filesystem.volume_name ? `Volume: ${filesystem.volume_name}` : null,
        ].filter(Boolean).join("\n"),
      });
    }
  }
  return badges;
}

function renderProjectBadges(project, projectData = null) {
  return buildProjectBadges(project, projectData)
    .map((badge) => (
      `<span class="project-badge${badge.className ? ` ${escapeHtml(badge.className)}` : ""}"${badge.title ? ` title="${escapeHtml(badge.title)}"` : ""}>${escapeHtml(badge.label)}</span>`
    ))
    .join("");
}

function reproductionBadge(ready, report) {
  if (!ready) {
    return {label: "Not ready", className: "project-badge-repro-not-ready", title: "Reproduction waits for a ready binary target"};
  }
  if (!report) {
    return {label: "Not ready", className: "project-badge-repro-not-ready", title: "No reproduction report yet"};
  }
  if (report.stale) {
    return {label: "Stale", className: "project-badge-repro-stale", title: "Reproduction inputs changed"};
  }
  if (report.status === "exact") {
    return {label: "Exact", className: "project-badge-repro-exact", title: "Rebuilt bytes match the original"};
  }
  if (report.status === "binary_mismatch") {
    return {label: "Diff", className: "project-badge-repro-diff", title: "Rebuilt bytes differ from the original"};
  }
  if (report.status === "content_match" || report.status === "semantic_match") {
    return {label: "Content", className: "project-badge-repro-diff", title: "Content comparison matched but file bytes are not exact"};
  }
  if (report.status === "assembler_error") {
    return {label: "Asm error", className: "project-badge-repro-error", title: "Assembler failed"};
  }
  if (report.status === "render_error") {
    return {label: "Render error", className: "project-badge-repro-error", title: "Source rendering failed"};
  }
  if (report.status === "tool_error") {
    return {label: "Tool error", className: "project-badge-repro-error", title: "Reproduction tooling failed"};
  }
  if (report.status === "unsupported") {
    return {label: "Unsupported", className: "project-badge-repro-not-ready", title: "Exact reproduction is not supported for this target"};
  }
  return {label: "Not ready", className: "project-badge-repro-not-ready", title: report.status || "No reproduction report yet"};
}

function refreshProjectBadges() {
  const detailsNode = document.getElementById("project-details");
  if (!detailsNode || !state.projectData) {
    return;
  }
  detailsNode.innerHTML = renderProjectBadges(state.projectData.project, state.projectData);
}

function formatProjectTimestamp(timestamp, emptyText) {
  if (!timestamp) {
    return {
      text: emptyText,
      title: emptyText,
    };
  }
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return {
      text: timestamp,
      title: timestamp,
    };
  }
  const pad = (value) => String(value).padStart(2, "0");
  const localText = [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
  ].join("-") + " " + [
    pad(date.getHours()),
    pad(date.getMinutes()),
    pad(date.getSeconds()),
  ].join(":");
  return {
    text: localText,
    title: `${timestamp}\nUTC: ${date.toUTCString()}`,
  };
}

async function fileToBase64(file) {
  const buffer = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (const value of bytes) {
    binary += String.fromCharCode(value);
  }
  return btoa(binary);
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function getJobPhaseLabel(job) {
  const labels = JOB_PHASE_LABELS[job.job_kind];
  if (!labels) {
    throw new Error(`Unknown job kind: ${job.job_kind}`);
  }
  const label = labels[job.phase_id];
  if (!label) {
    throw new Error(`Unknown ${job.job_kind} phase id: ${job.phase_id}`);
  }
  return label;
}

function formatJobProgress(job) {
  const phaseLabel = getJobPhaseLabel(job);
  if (job.progress_mode === "determinate") {
    return {
      percent: job.progress_percent,
      detail: `${phaseLabel} (${job.progress_current} / ${job.progress_total})`,
    };
  }
  if (job.progress_mode === "indeterminate") {
    return {
      percent: null,
      detail: phaseLabel,
    };
  }
  throw new Error(`Unknown progress mode: ${job.progress_mode}`);
}

function recordListingFetchSample(sample) {
  state.stats.fetchSamples.push(sample);
  if (state.stats.fetchSamples.length > STATS_MAX_FETCH_SAMPLES) {
    state.stats.fetchSamples.splice(0, state.stats.fetchSamples.length - STATS_MAX_FETCH_SAMPLES);
  }
  renderStatsOverlay();
}

function percentile(sortedValues, p) {
  if (!sortedValues.length) {
    return 0;
  }
  const index = (sortedValues.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) {
    return sortedValues[lower];
  }
  const weight = index - lower;
  return sortedValues[lower] * (1 - weight) + sortedValues[upper] * weight;
}

function fetchLatencyStats() {
  const values = state.stats.fetchSamples.map((sample) => sample.ms).sort((a, b) => a - b);
  if (!values.length) {
    return {count: 0, min: 0, max: 0, mean: 0, median: 0, p95: 0};
  }
  const total = values.reduce((sum, value) => sum + value, 0);
  return {
    count: values.length,
    min: values[0],
    max: values[values.length - 1],
    mean: total / values.length,
    median: percentile(values, 0.5),
    p95: percentile(values, 0.95),
  };
}

function formatMs(value) {
  return `${Math.round(value)} ms`;
}

function renderProgressOverlay(job, titleOverride = null) {
  const label = titleOverride || getJobPhaseLabel(job);
  const progress = formatJobProgress(job);
  const barStyle = progress.percent === null ? " indeterminate" : "";
  const fillStyle = progress.percent === null ? "" : ` style="width:${progress.percent}%"`;
  return `
    <div class="progress-overlay">
      <div class="progress-panel">
        <div class="progress-title">${escapeHtml(label)}</div>
        <div class="progress-bar${barStyle}">
          <div class="progress-fill"${fillStyle}></div>
        </div>
        <div class="progress-detail">${escapeHtml(progress.detail)}</div>
      </div>
    </div>
  `;
}

function analysisStatusTextForJob(job) {
  if (!job || !job.job_kind || !["basic_listing", "full_listing", "listing"].includes(job.job_kind)) {
    return "";
  }
  if (job.status === "failed") {
    return "Full analysis failed";
  }
  const labels = JOB_PHASE_LABELS[job.job_kind] || {};
  const phase = labels[job.phase_id] || labels[job.status] || "Analyzing";
  if (job.job_kind === "basic_listing") {
    return `Loading initial listing: ${phase}`;
  }
  if (job.job_kind === "full_listing") {
    return `Analyzing full listing: ${phase}`;
  }
  return `Analyzing listing: ${phase}`;
}

function renderAnalysisStatus() {
  const node = document.getElementById("analysis-status");
  if (!node) {
    return;
  }
  const text = state.analysisStatus.text || "";
  node.hidden = text === "";
  node.className = `analysis-status analysis-status-${state.analysisStatus.state || "idle"}`;
  node.innerHTML = text
    ? `<span class="analysis-status-spinner" aria-hidden="true"></span><span>${escapeHtml(text)}</span>`
    : "";
}

function setAnalysisStatus(text, statusState = "running", clearAfterMs = null) {
  if (state.analysisStatus.clearTimer) {
    window.clearTimeout(state.analysisStatus.clearTimer);
    state.analysisStatus.clearTimer = null;
  }
  state.analysisStatus.text = text || "";
  state.analysisStatus.state = statusState;
  renderAnalysisStatus();
  if (clearAfterMs !== null) {
    state.analysisStatus.clearTimer = window.setTimeout(() => {
      state.analysisStatus.text = "";
      state.analysisStatus.state = "idle";
      state.analysisStatus.clearTimer = null;
      renderAnalysisStatus();
    }, clearAfterMs);
  }
}

function updateAnalysisStatusFromJob(job) {
  const text = analysisStatusTextForJob(job);
  if (!text) {
    return;
  }
  if (job.status === "failed") {
    setAnalysisStatus(text, "failed");
  } else if (job.status === "queued" || job.status === "building") {
    setAnalysisStatus(text, "running");
  }
}

function renderFetchLatencyGraph() {
  const samples = state.stats.fetchSamples.slice(-80);
  if (!samples.length) {
    return '<div class="stats-empty">No listing fetches recorded yet.</div>';
  }
  const maxMs = Math.max(1, ...samples.map((sample) => sample.ms));
  const width = Math.max(320, samples.length * 5);
  const height = 120;
  const points = samples.map((sample, index) => {
    const x = samples.length === 1 ? 0 : (index / (samples.length - 1)) * width;
    const y = height - (sample.ms / maxMs) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return `
    <svg class="stats-latency-graph" viewBox="0 0 ${width} ${height}" role="img" aria-label="Listing fetch latency graph">
      <polyline points="${escapeHtml(points)}"></polyline>
    </svg>
  `;
}

function renderFetchStatsTab() {
  const stats = fetchLatencyStats();
  const latest = state.stats.fetchSamples[state.stats.fetchSamples.length - 1] || null;
  return `
    ${renderFetchLatencyGraph()}
    <div class="stats-grid">
      <div><span>Samples</span><strong>${stats.count}</strong></div>
      <div><span>Min</span><strong>${formatMs(stats.min)}</strong></div>
      <div><span>Median</span><strong>${formatMs(stats.median)}</strong></div>
      <div><span>Mean</span><strong>${formatMs(stats.mean)}</strong></div>
      <div><span>P95</span><strong>${formatMs(stats.p95)}</strong></div>
      <div><span>Max</span><strong>${formatMs(stats.max)}</strong></div>
    </div>
    <div class="stats-latest">
      ${latest ? `Latest: ${formatMs(latest.ms)} for rows ${latest.start}-${latest.end} (${escapeHtml(latest.generation || "unknown")})` : "Latest: none"}
    </div>
  `;
}

function renderStatsOverlay() {
  const existing = document.getElementById("stats-overlay");
  if (!state.stats.overlayOpen) {
    existing?.remove();
    return;
  }
  const app = document.getElementById("app");
  if (!app) {
    return;
  }
  const tab = state.stats.selectedTab;
  const html = `
    <div class="stats-overlay" id="stats-overlay">
      <div class="stats-panel">
        <div class="stats-header">
          <div class="stats-title">Stats</div>
          <button type="button" class="stats-close" data-stats-close="1">Close</button>
        </div>
        <div class="stats-tabs" role="tablist">
          <button type="button" class="stats-tab${tab === "fetch" ? " active" : ""}" data-stats-tab="fetch" role="tab" aria-selected="${tab === "fetch"}">Fetch</button>
          <button type="button" class="stats-tab${tab === "jobs" ? " active" : ""}" data-stats-tab="jobs" role="tab" aria-selected="${tab === "jobs"}">Jobs</button>
        </div>
        <div class="stats-body">
          ${tab === "fetch" ? renderFetchStatsTab() : '<div class="stats-empty">Job timing details can be added after fetch latency is stable.</div>'}
        </div>
      </div>
    </div>
  `;
  if (existing) {
    existing.outerHTML = html;
  } else {
    app.insertAdjacentHTML("beforeend", html);
  }
  bindStatsOverlay();
}

function openStatsOverlay() {
  state.stats.overlayOpen = true;
  renderStatsOverlay();
}

function closeStatsOverlay() {
  state.stats.overlayOpen = false;
  renderStatsOverlay();
}

function bindStatsOverlay() {
  const overlay = document.getElementById("stats-overlay");
  if (!overlay) {
    return;
  }
  overlay.querySelector("[data-stats-close='1']")?.addEventListener("click", closeStatsOverlay);
  overlay.querySelectorAll("[data-stats-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.stats.selectedTab = button.dataset.statsTab || "fetch";
      renderStatsOverlay();
    });
  });
}

async function loadReproductionReport(projectId) {
  const report = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/reproduction`);
  const reportKey = reproductionReportKey(report);
  const previousReportKey = state.reproduction.reportKey || reproductionReportKey(state.reproduction.report);
  if (previousReportKey && previousReportKey !== reportKey) {
    state.reproduction.selectedIssueEntry = null;
  }
  state.reproduction.report = report;
  state.reproduction.reportKey = reportKey;
  if (state.projectData) {
    state.projectData.reproduction = report;
  }
  refreshProjectBadges();
  renderReproPanel();
  return report;
}

function reproductionReportKey(report) {
  if (!report) {
    return "";
  }
  return JSON.stringify({
    status: report.status || "",
    stale: Boolean(report.stale),
    input_stamp: report.input_stamp || null,
    issue_count: Array.isArray(report.issues) ? report.issues.length : 0,
  });
}

async function refreshReproductionReport(projectId) {
  try {
    return await loadReproductionReport(projectId);
  } catch (error) {
    console.warn("Reproduction report unavailable", error);
    return null;
  }
}

async function pollReproductionReport(projectId, token, attempts = 12) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (token !== state.loadingToken) {
      return;
    }
    const report = await refreshReproductionReport(projectId);
    if (token !== state.loadingToken) {
      return;
    }
    if (report && report.status !== "not_ready") {
      return;
    }
    await sleep(1000);
  }
}

function reproductionStatusText(report) {
  if (!report) {
    return "Not ready";
  }
  if (report.stale) {
    return "Stale";
  }
  if (report.status === "exact") {
    return "Exact match";
  }
  if (report.status === "binary_mismatch") {
    return "Binary diff";
  }
  if (report.status === "content_match") {
    return "Content match";
  }
  if (report.status === "semantic_match") {
    return "Semantic match";
  }
  if (report.status === "assembler_error") {
    return "Assembler error";
  }
  if (report.status === "render_error") {
    return "Render error";
  }
  if (report.status === "tool_error") {
    return "Tool error";
  }
  if (report.status === "unsupported") {
    return "Unsupported";
  }
  return "Not ready";
}

function reproIssues() {
  const issues = Array.isArray(state.reproduction.report?.issues) ? state.reproduction.report.issues : [];
  return issues.map((issue, index) => ({
    ...issue,
    issue_index: issue.issue_index ?? index,
    issueIndex: issue.issueIndex ?? issue.issue_index ?? index,
  }));
}

function sameIssueField(left, right) {
  return left !== null
    && left !== undefined
    && right !== null
    && right !== undefined
    && String(left) === String(right);
}

function reproIssueMatchesEntry(issue, entry) {
  if (!issue || !entry) {
    return false;
  }
  const entryRowIndex = entry.row_index ?? entry.rowIndex;
  if (
    sameIssueField(issue.issue_index, entry.issue_index)
    || sameIssueField(issue.issue_index, entry.issueIndex)
  ) {
    if (sameIssueField(issue.stable_key, entry.stable_key ?? entry.stableKey)) {
      return true;
    }
    return sameIssueField(issue.row_index, entryRowIndex) && sameIssueField(issue.addr, entry.addr);
  }
  if (sameIssueField(issue.row_index, entryRowIndex)) {
    if (sameIssueField(issue.stable_key, entry.stable_key ?? entry.stableKey)) {
      return true;
    }
    return sameIssueField(issue.addr, entry.addr);
  }
  return false;
}

function reproIssueForNavigationEntry(entry) {
  return reproIssues().find((issue) => reproIssueMatchesEntry(issue, entry)) || null;
}

function currentReproIssue() {
  const selected = reproIssueForNavigationEntry(state.reproduction.selectedIssueEntry);
  if (selected) {
    return selected;
  }
  const issues = reproIssues();
  return issues.find((issue) => Number.isFinite(issue.addr)) || issues[0] || null;
}

function renderReproPanelBody(report) {
  const firstDiff = report?.first_diff || null;
  const diagnostics = Array.isArray(report?.assembler_diagnostics) ? report.assembler_diagnostics : [];
  const issue = currentReproIssue();
  const suggestedActions = issue && Number.isFinite(issue.addr)
    ? `
      <div class="repro-actions">
        <button type="button" data-repro-edit-kind="code_range">Code</button>
        <button type="button" data-repro-edit-kind="data_range">Data</button>
        <button type="button" data-repro-edit-kind="text_range">Text</button>
        <button type="button" data-repro-edit-kind="pointer_table">Ptrs</button>
        <button type="button" data-repro-edit-kind="jump_table">Jump</button>
        <button type="button" data-repro-edit-kind="entrypoint">Entry</button>
        <button type="button" data-repro-edit-kind="label">Label</button>
        <button type="button" data-repro-edit-kind="external_symbol">Ext Symbol</button>
        <button type="button" data-repro-edit-kind="suppress_inferred_code">No Code</button>
        <button type="button" data-repro-edit-kind="suppress_inferred_pointer">No Ptr</button>
      </div>
    `
    : "";
  return `
    <div class="repro-summary-grid">
      <div><span>Status</span><strong>${escapeHtml(reproductionStatusText(report))}</strong></div>
      <div><span>Original</span><strong>${escapeHtml(String(report?.original_size ?? report?.input_stamp?.original_size ?? "?"))}</strong></div>
      <div><span>Rebuilt</span><strong>${escapeHtml(String(report?.rebuilt_size ?? "?"))}</strong></div>
    </div>
    <div class="repro-detail">
      ${firstDiff ? `First diff: ${escapeHtml(formatRowOffset(firstDiff.offset))}` : "First diff: none"}
    </div>
    ${issue ? `<div class="repro-detail">Issue: ${escapeHtml(issue.summary || issue.message || issue.kind || "")}</div>` : ""}
    ${suggestedActions}
    ${diagnostics.length ? `
      <pre class="repro-diagnostics">${escapeHtml(diagnostics.slice(0, 12).map((item) => item.message || item.summary || String(item)).join("\n"))}</pre>
    ` : ""}
  `;
}

function renderReproPanel() {
  const existing = document.getElementById("repro-overlay");
  if (!state.reproduction.panelOpen) {
    existing?.remove();
    return;
  }
  const app = document.getElementById("app");
  if (!app) {
    return;
  }
  const job = state.reproduction.job;
  const jobProgress = job && (job.status === "queued" || job.status === "building")
    ? `<div class="repro-detail">${escapeHtml(formatJobProgress(job).detail)}</div>`
    : "";
  const html = `
    <div class="repro-overlay" id="repro-overlay">
      <div class="repro-panel">
        <div class="repro-header">
          <div class="repro-title">Repro</div>
          <button type="button" class="repro-close" data-repro-close="1">Close</button>
        </div>
        ${jobProgress}
        ${renderReproPanelBody(state.reproduction.report)}
        <button type="button" class="repro-run" data-repro-run="1">Run Repro</button>
      </div>
    </div>
  `;
  if (existing) {
    existing.outerHTML = html;
  } else {
    app.insertAdjacentHTML("beforeend", html);
  }
  bindReproPanel();
}

async function openReproPanel() {
  state.reproduction.panelOpen = true;
  renderReproPanel();
  if (state.project) {
    await refreshReproductionReport(state.project);
  }
}

function closeReproPanel() {
  state.reproduction.panelOpen = false;
  renderReproPanel();
}

async function runReproduction(projectId) {
  const job = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/reproduction/run`, {method: "POST"});
  state.reproduction.job = job;
  renderReproPanel();
  setAnalysisStatus("Running reproduction", "running");
  await waitForAsyncJob(
    (jobId) => `/api/projects/${encodeURIComponent(projectId)}/reproduction/status?job_id=${encodeURIComponent(jobId)}`,
    job,
    state.loadingToken,
    (currentJob) => {
      state.reproduction.job = currentJob;
      renderReproPanel();
    },
  );
  state.reproduction.job = null;
  const report = await loadReproductionReport(projectId);
  await loadNavigationEntries(projectId);
  renderNavigationOverlay();
  const editNeeded = report?.status === "binary_mismatch" || report?.status === "assembler_error";
  const statusText = report?.status === "exact"
    ? "Reproduction exact"
    : (editNeeded ? "Reproduction needs edits" : "Reproduction failed");
  setAnalysisStatus(statusText, report?.status === "exact" ? "ready" : "failed", 2500);
}

async function applyReproTargetEdit(kind) {
  if (!state.project) {
    return;
  }
  const issue = currentReproIssue();
  const anchor = captureViewportAnchor();
  const addr = Number.isFinite(issue?.addr) ? issue.addr : anchor?.addr;
  if (!Number.isFinite(addr)) {
    return;
  }
  const payload = {kind, addr};
  if (kind === "label" || kind === "external_symbol") {
    const name = window.prompt(
      kind === "label" ? "Label name" : "External symbol name",
      defaultReproSymbolName(issue, kind, addr),
    );
    if (!name || !name.trim()) {
      return;
    }
    payload.name = name.trim();
  }
  const hunk = Number.isInteger(issue?.hunk)
    ? issue.hunk
    : (Number.isInteger(issue?.section_index)
      ? issue.section_index
      : (Number.isInteger(anchor?.hunk) ? anchor.hunk : null));
  if (hunk !== null) {
    payload.hunk = hunk;
  }
  const length = Number(issue?.diff_range?.length || 0);
  if (length > 1 && kind !== "entrypoint" && !kind.startsWith("suppress_")) {
    payload.end = addr + length;
  }
  await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/target-edits`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  if (state.projectData) {
    state.projectData.reproduction = {
      ...(state.projectData.reproduction || {}),
      status: state.projectData.reproduction?.status || "not_ready",
      stale: true,
    };
  }
  state.navigation.entries = null;
  state.reproduction.selectedIssueEntry = null;
  refreshProjectBadges();
  renderReproPanel();
  setAnalysisStatus("Metadata edit saved", "ready", 2000);
}

function defaultReproSymbolName(issue, kind, addr) {
  const text = String(issue?.match_text || issue?.message || issue?.summary || "");
  const symbolMatch = text.match(/\b[A-Za-z_.$][A-Za-z0-9_.$]*\b/);
  if (symbolMatch && !/^(move|lea|jsr|jmp|bra|bsr|dc|section)$/i.test(symbolMatch[0])) {
    return symbolMatch[0].replace(/^\./, "local_");
  }
  const prefix = kind === "external_symbol" ? "ext" : "label";
  return `${prefix}_${Number(addr).toString(16)}`;
}

function bindReproPanel() {
  const overlay = document.getElementById("repro-overlay");
  if (!overlay) {
    return;
  }
  overlay.querySelector("[data-repro-close='1']")?.addEventListener("click", closeReproPanel);
  overlay.querySelector("[data-repro-run='1']")?.addEventListener("click", () => {
    if (state.project) {
      void runReproduction(state.project);
    }
  });
  overlay.querySelectorAll("[data-repro-edit-kind]").forEach((button) => {
    button.addEventListener("click", () => {
      void applyReproTargetEdit(button.dataset.reproEditKind || "");
    });
  });
}

function renderErrorOverlay(message) {
  return `
    <div class="progress-overlay">
      <div class="progress-panel progress-panel-error">
        <div class="progress-title">Load failed</div>
        <div class="error">${escapeHtml(message)}</div>
      </div>
    </div>
  `;
}

function loadingRowsOverlay() {
  return renderProgressOverlay({
    job_kind: "listing",
    phase_id: "emit_rows",
    progress_mode: "indeterminate",
    progress_current: 0,
    progress_total: 0,
    progress_percent: 0,
  }, "Loading rows");
}

function setViewportOverlay(html) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  viewport.innerHTML = html;
}

function setHomeOverlay(html) {
  const overlay = document.getElementById("home-overlay");
  if (!overlay) {
    return;
  }
  overlay.innerHTML = html;
  overlay.hidden = false;
}

function clearHomeOverlay() {
  const overlay = document.getElementById("home-overlay");
  if (!overlay) {
    return;
  }
  overlay.innerHTML = "";
  overlay.hidden = true;
}

async function waitForAsyncJob(statusUrl, job, token, renderOverlay) {
  if (window.EventSource && job?.job_id && !String(job.job_id).startsWith("cached-")) {
    try {
      return await waitForAsyncJobEvents(job, token, renderOverlay);
    } catch (error) {
      if (String(error.message || error) === "stale") {
        throw error;
      }
      console.warn("Job event stream failed; falling back to polling", error);
    }
  }
  return waitForAsyncJobPolling(statusUrl, job, token, renderOverlay);
}

function waitForAsyncJobEvents(job, token, renderOverlay) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const source = new EventSource(`/api/jobs/events?job_id=${encodeURIComponent(job.job_id)}`);
    const cleanup = () => {
      source.close();
    };
    const settle = (callback, value) => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      callback(value);
    };
    const handleJobState = (jobState) => {
      if (token !== null && token !== state.loadingToken) {
        settle(reject, new Error("stale"));
        return;
      }
      const isListingJob = ["basic_listing", "full_listing", "listing"].includes(jobState.job_kind);
      updateAnalysisStatusFromJob(jobState);
      if (
        isListingJob
        && jobState.visible_generation === "basic"
        && jobState.project_id
        && jobState.visible_generation !== state.virtualListing.generation
      ) {
        void handleListingGenerationReady({
          project_id: jobState.project_id,
          generation: jobState.visible_generation,
          total_rows: jobState.total_rows || 0,
        }, token);
      }
      const hasVisibleListingRows = Boolean(
        state.virtualListing.generation
        && document.querySelector("#listing-viewport .listing-row")
      );
      if (
        !isListingJob
        || !hasVisibleListingRows
        || jobState.status === "failed"
      ) {
        renderOverlay(jobState);
      }
      if (jobState.status === "failed") {
        settle(reject, new Error(jobState.error || "Async job failed"));
      } else if (jobState.status !== "queued" && jobState.status !== "building") {
        settle(resolve, jobState);
      }
    };
    source.addEventListener("job", (event) => {
      try {
        handleJobState(JSON.parse(event.data));
      } catch (error) {
        settle(reject, error);
      }
    });
    source.addEventListener("listing_generation_ready", (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.generation === "basic") {
          void handleListingGenerationReady(payload, token);
        }
      } catch (error) {
        settle(reject, error);
      }
    });
    source.onerror = () => {
      settle(reject, new Error("job event stream failed"));
    };
    handleJobState(job);
  });
}

async function waitForAsyncJobPolling(statusUrl, job, token, renderOverlay) {
  let jobState = job;
  let pollDelayMs = 250;
  updateAnalysisStatusFromJob(jobState);
  renderOverlay(jobState);
  while (jobState.status === "queued" || jobState.status === "building") {
    await sleep(pollDelayMs);
    if (token !== null && token !== state.loadingToken) {
      throw new Error("stale");
    }
    jobState = await fetchJson(statusUrl(job.job_id));
    if (token !== null && token !== state.loadingToken) {
      throw new Error("stale");
    }
    updateAnalysisStatusFromJob(jobState);
    renderOverlay(jobState);
    pollDelayMs = Math.min(1000, Math.floor(pollDelayMs * 1.35));
  }
  if (jobState.status === "failed") {
    throw new Error(jobState.error || "Async job failed");
  }
  return jobState;
}

async function renderHome() {
  if (state.homeDropCleanup) {
    state.homeDropCleanup();
    state.homeDropCleanup = null;
  }
  const projects = await fetchJson("/api/projects");
  const app = document.getElementById("app");
  app.innerHTML = `
    <section class="page page-home">
      <div class="projects-header">
        <h1>Projects</h1>
        <button id="add-project-button" type="button">Add Project</button>
      </div>
      <div class="drop-hint">Drop Amiga executables or ADF disk images anywhere on this page to create projects.</div>
      <input id="new-project-media" class="visually-hidden" type="file" multiple>
      <div id="home-error" class="error"></div>
      <div id="home-overlay" class="overlay-host" hidden></div>
      <div class="project-list">
        ${projects.map((project) => {
          const createdAt = formatProjectTimestamp(project.created_at, "Unknown");
          const updatedAt = formatProjectTimestamp(project.updated_at, "Unknown");
          return `
          <div class="project-item">
            <button class="project-open-button" data-project-id="${escapeHtml(project.id)}" type="button">
              <span class="project-name">${escapeHtml(project.name)} ${renderProjectBadges(project)}</span>
              <span class="project-meta">
                <span class="project-meta-line" title="${escapeHtml(createdAt.title)}">Created ${escapeHtml(createdAt.text)}</span>
                <span class="project-meta-line" title="${escapeHtml(updatedAt.title)}">Updated ${escapeHtml(updatedAt.text)}</span>
              </span>
            </button>
            <button
              class="project-delete-button"
              data-project-id="${escapeHtml(project.id)}"
              data-project-name="${escapeHtml(project.name)}"
              type="button"
              aria-label="Delete project ${escapeHtml(project.name)}"
            >Delete</button>
          </div>
        `;
        }).join("") || '<div class="empty">No projects.</div>'}
      </div>
    </section>
  `;

  document.querySelectorAll(".project-open-button").forEach((button) => {
    button.addEventListener("click", () => {
      navigateToProject(button.dataset.projectId);
    });
  });

  document.querySelectorAll(".project-delete-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const projectId = button.dataset.projectId;
      const projectName = button.dataset.projectName;
      if (!window.confirm(`Delete project "${projectName}" and all associated files?`)) {
        return;
      }
      const error = document.getElementById("home-error");
      error.textContent = "";
      try {
        await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/delete`, {
          method: "POST",
        });
        await renderHome();
      } catch (err) {
        error.textContent = String(err.message || err);
      }
    });
  });

  const homePage = app.querySelector(".page-home");
  const mediaInput = document.getElementById("new-project-media");
  const error = document.getElementById("home-error");

  async function createProjectsFromFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) {
      return;
    }
    error.textContent = "";
    let lastProjectId = null;
    for (let index = 0; index < files.length; index += 1) {
      const file = files[index];
      const job = await fetchJson("/api/projects", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          filename: file.name,
          media_base64: await fileToBase64(file),
        }),
      });
      const title = files.length === 1
        ? `Creating ${file.name}`
        : `Creating ${file.name} (${index + 1}/${files.length})`;
      const jobState = await waitForAsyncJob(
        (jobId) => `/api/projects/create/status?job_id=${encodeURIComponent(jobId)}`,
        job,
        null,
        (currentJob) => setHomeOverlay(renderProgressOverlay(currentJob, title)),
      );
      lastProjectId = jobState.result_project_id;
    }
    clearHomeOverlay();
    if (lastProjectId !== null) {
      navigateToProject(lastProjectId);
    }
  }

  document.getElementById("add-project-button").addEventListener("click", () => {
    mediaInput.click();
  });

  mediaInput.addEventListener("change", async () => {
    try {
      await createProjectsFromFiles(mediaInput.files);
    } catch (err) {
      clearHomeOverlay();
      error.textContent = String(err.message || err);
    } finally {
      mediaInput.value = "";
    }
  });

  const preventWindowDrop = (event) => {
    event.preventDefault();
  };
  const onDragEnter = (event) => {
    if (event.dataTransfer && event.dataTransfer.types.includes("Files")) {
      event.preventDefault();
      homePage.classList.add("drag-active");
    }
  };
  const onDragOver = (event) => {
    if (event.dataTransfer && event.dataTransfer.types.includes("Files")) {
      event.preventDefault();
      homePage.classList.add("drag-active");
      event.dataTransfer.dropEffect = "copy";
    }
  };
  const onDragLeave = (event) => {
    if (event.target === homePage || !homePage.contains(event.relatedTarget)) {
      homePage.classList.remove("drag-active");
    }
  };
  const onDrop = async (event) => {
    event.preventDefault();
    homePage.classList.remove("drag-active");
    try {
      await createProjectsFromFiles(event.dataTransfer.files);
    } catch (err) {
      clearHomeOverlay();
      error.textContent = String(err.message || err);
    }
  };

  window.addEventListener("dragenter", onDragEnter);
  window.addEventListener("dragover", onDragOver);
  window.addEventListener("drop", preventWindowDrop);
  homePage.addEventListener("dragover", onDragOver);
  homePage.addEventListener("dragleave", onDragLeave);
  homePage.addEventListener("drop", onDrop);
  state.homeDropCleanup = () => {
    window.removeEventListener("dragenter", onDragEnter);
    window.removeEventListener("dragover", onDragOver);
    window.removeEventListener("drop", preventWindowDrop);
    homePage.removeEventListener("dragover", onDragOver);
    homePage.removeEventListener("dragleave", onDragLeave);
    homePage.removeEventListener("drop", onDrop);
  };
}

function formatRowOffset(addr) {
  if (addr === null || addr === undefined) {
    return "";
  }
  return addr.toString(16).padStart(4, "0");
}

function navigationEntryHunkIndex(entry) {
  const value = entry.hunk_index ?? entry.hunkIndex ?? entry.section_index ?? entry.sectionIndex;
  return Number.isInteger(value) ? value : null;
}

function formatAppSlotDisplacement(entry) {
  const displacement = Number(entry?.displacement);
  if (!Number.isFinite(displacement)) {
    return "";
  }
  const sign = displacement < 0 ? "-" : "";
  return `${sign}$${Math.abs(displacement).toString(16).toUpperCase().padStart(4, "0")}`;
}

function formatNavigationEntryOffset(entry) {
  if (entry?.refs && entry?.symbol) {
    return formatAppSlotDisplacement(entry);
  }
  const offset = formatRowOffset(entry.addr);
  const hunkIndex = navigationEntryHunkIndex(entry);
  if (hunkIndex === null || !offset) {
    return offset;
  }
  return `h${hunkIndex}:${offset}`;
}

function formatRowBytes(hexBytes) {
  if (!hexBytes) {
    return "";
  }
  return String(hexBytes);
}

function renderListingCode(row) {
  if (row.kind === "instruction" || row.kind === "data") {
    const opcode = row.opcode_or_directive || "";
    const operands = row.operand_text || "";
    if (opcode) {
      return `    ${opcode}${operands ? ` ${operands}` : ""}`;
    }
  }
  const text = row.text.replace(/\n$/, "");
  if (!rowHasAddress(row) && !text.trimStart().startsWith("SECTION ")) {
    return text.trimStart();
  }
  return text;
}

function parseGlobalRsEquRow(row) {
  if (rowHasAddress(row) || row.kind !== "directive") {
    return null;
  }
  const text = renderListingCode(row).trim();
  const match = text.match(/^(?:(\S+)\s+)?(RSSET|RSRESET|RS\.[BWL]|EQU)\b(?:\s+(.*))?$/i);
  if (!match) {
    return null;
  }
  return {
    label: match[1] || "",
    directive: match[2] || "",
    operand: match[3] || "",
  };
}

function labelNameFromText(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed.endsWith(":")) {
    return null;
  }
  const name = trimmed.slice(0, -1).trim();
  return name || null;
}

function isAppSlotSymbolName(name) {
  return /^app_[A-Za-z0-9_]+$/.test(String(name || "")) && name !== "app_SIZEOF";
}

function rowHasAddress(row) {
  return row.addr !== null && row.addr !== undefined;
}

function rowUsesGlobalTextColumn(row) {
  if (rowHasAddress(row)) {
    return false;
  }
  return !renderListingCode(row).trimStart().startsWith("SECTION ");
}

function labelLinkCandidateFromOperandText(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) {
    return null;
  }
  const first = trimmed.split(/[,\s(]+/)[0] || "";
  const name = first.replace(/\.(b|w|l|s)$/i, "").replace(/[+\-].*$/, "");
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
    return null;
  }
  return name;
}

function labelNamesFromNavigation() {
  const labels = state.navigation.entries?.labels || [];
  return new Set(labels.map((entry) => {
    const text = String(entry.summary || entry.matchText || entry.match_text || "");
    return text.replace(/:$/, "");
  }).filter(Boolean));
}

function isKnownListingLabelName(name) {
  if (!name) {
    return false;
  }
  const labels = labelNamesFromNavigation();
  return labels.has(name);
}

function renderOperandAppSlotRefsHtml(row, operand, globalRowIndex) {
  const refs = Array.isArray(row.app_slot_refs) ? row.app_slot_refs : [];
  const ranges = [];
  const nextSearchBySymbol = new Map();
  refs.forEach((ref) => {
    const symbol = String(ref?.symbol || "");
    if (!symbol) {
      return;
    }
    const startAt = nextSearchBySymbol.get(symbol) || 0;
    const start = operand.indexOf(symbol, startAt);
    if (start < 0) {
      return;
    }
    const end = start + symbol.length;
    nextSearchBySymbol.set(symbol, end);
    ranges.push({
      start,
      end,
      symbol,
      operandIndex: Number(ref.operand_index ?? ref.operandIndex),
      access: String(ref.access || ""),
    });
  });
  if (!ranges.length) {
    return null;
  }
  ranges.sort((left, right) => left.start - right.start || left.end - right.end);
  let cursor = 0;
  let html = "";
  ranges.forEach((range) => {
    if (range.start < cursor) {
      return;
    }
    html += escapeHtml(operand.slice(cursor, range.start));
    html += `<button class="listing-symbol-link listing-symbol-reference listing-app-slot-reference" type="button" data-app-slot-symbol="${escapeHtml(range.symbol)}" data-row-index="${escapeHtml(String(globalRowIndex))}" data-app-slot-operand-index="${escapeHtml(String(range.operandIndex))}" data-app-slot-access="${escapeHtml(range.access)}">${escapeHtml(range.symbol)}</button>`;
    cursor = range.end;
  });
  html += escapeHtml(operand.slice(cursor));
  return html;
}

function renderListingCodeHtml(row, globalRowIndex = null) {
  const globalRsEqu = parseGlobalRsEquRow(row);
  if (globalRsEqu) {
    const labelTitle = globalRsEqu.label ? ` title="${escapeHtml(globalRsEqu.label)}"` : "";
    const labelHtml = isAppSlotSymbolName(globalRsEqu.label)
      ? `<button class="listing-symbol-link listing-global-label listing-app-slot-definition" type="button" data-app-slot-symbol="${escapeHtml(globalRsEqu.label)}"${labelTitle}>${escapeHtml(globalRsEqu.label)}</button>`
      : `<span class="listing-global-label"${labelTitle}>${escapeHtml(globalRsEqu.label)}</span>`;
    return `<span class="listing-global-structured">${labelHtml}<span class="listing-global-directive">${escapeHtml(globalRsEqu.directive)}</span><span class="listing-global-operand">${escapeHtml(globalRsEqu.operand)}</span></span>`;
  }
  const code = renderListingCode(row);
  const labelName = labelNameFromText(code);
  if (labelName && row.kind === "label" && rowHasAddress(row)) {
    return `<button class="listing-symbol-link listing-symbol-definition" type="button" data-symbol-name="${escapeHtml(labelName)}">${escapeHtml(code)}</button>`;
  }
  const appSlotCodeHtml = Number.isFinite(globalRowIndex)
    ? renderOperandAppSlotRefsHtml(row, code, globalRowIndex)
    : null;
  if (appSlotCodeHtml !== null) {
    return appSlotCodeHtml;
  }
  if (row.kind === "instruction" && rowHasAddress(row) && row.operand_text) {
    const opcode = row.opcode_or_directive || "";
    const operand = row.operand_text || "";
    const appSlotOperandHtml = Number.isFinite(globalRowIndex)
      ? renderOperandAppSlotRefsHtml(row, operand, globalRowIndex)
      : null;
    if (appSlotOperandHtml !== null) {
      return `    ${escapeHtml(opcode)} ${appSlotOperandHtml}`;
    }
    const candidate = labelLinkCandidateFromOperandText(operand);
    if (candidate && isKnownListingLabelName(candidate)) {
      const suffix = operand.slice(candidate.length);
      return `    ${escapeHtml(opcode)} <button class="listing-symbol-link listing-symbol-reference" type="button" data-symbol-name="${escapeHtml(candidate)}">${escapeHtml(candidate)}</button>${escapeHtml(suffix)}`;
    }
  }
  return escapeHtml(code);
}

function renderListingComment(row) {
  if ((row.kind === "instruction" || row.kind === "data") && row.comment_text) {
    return `; ${row.comment_text}`;
  }
  return "";
}

function renderListingAnnotations(row) {
  if (!Array.isArray(row.view_annotations) || !row.view_annotations.length) {
    return "";
  }
  return row.view_annotations
    .map((note) => `<span class="project-badge" title="${escapeHtml(note)}">${escapeHtml(note)}</span>`)
    .join("");
}

function renderApiEditButton(row, rowIndex) {
  if (!row.api_call) {
    return "";
  }
  return ` <button class="listing-api-edit" type="button" data-api-edit="1" data-row-index="${rowIndex}" title="Edit API argument types">Edit API</button>`;
}

function renderAnnotationEditButton(row, rowIndex) {
  const addr = row.entity_addr ?? row.addr;
  if (addr === null || addr === undefined) {
    return "";
  }
  return ` <button class="listing-annotation-edit" type="button" data-annotation-edit="1" data-row-index="${rowIndex}" title="Edit entity annotation" aria-label="Edit entity annotation">Annotate</button>`;
}

function renderApiTypeBadges(row) {
  if (!row.api_call || !Array.isArray(row.api_call.inputs)) {
    return "";
  }
  const highlighted = row.api_call.inputs.filter((input) => input.i_struct || input.source !== "parsed NDK");
  if (!highlighted.length) {
    return "";
  }
  return highlighted
    .map((input) => {
      const label = `${input.regs.join("/")} ${input.i_struct || input.type || input.name}`;
      const title = `${input.name}: ${input.type || "(untyped)"}\nsource: ${input.source}`;
      const sourceClass = `project-badge-source-${String(input.source || "unknown").toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}`;
      return `<span class="project-badge ${sourceClass}" title="${escapeHtml(title)}">${escapeHtml(label)}</span>`;
    })
    .join("");
}

function renderReproIssueBadges(row) {
  if (!Array.isArray(row.repro_issues) || !row.repro_issues.length) {
    return "";
  }
  return row.repro_issues
    .map((issue) => `<span class="project-badge project-badge-repro-issue" title="${escapeHtml(issue.message || issue.summary || "Repro issue")}">${escapeHtml(issue.kind || "repro")}</span>`)
    .join("");
}

function listingColumnStyle() {
  return `--listing-offset-width:${state.listingColumns.offset}px;--listing-bytes-width:${state.listingColumns.bytes}px;--listing-code-width:${state.listingColumns.code}px;`;
}

function applyListingColumnWidths() {
  document.querySelectorAll(".listing-row-layer, .listing-scroll-spacer").forEach((element) => {
    element.style.setProperty("--listing-offset-width", `${state.listingColumns.offset}px`);
    element.style.setProperty("--listing-bytes-width", `${state.listingColumns.bytes}px`);
    element.style.setProperty("--listing-code-width", `${state.listingColumns.code}px`);
  });
}

function renderListingRows(rows, globalStart = 0) {
  if (!rows.length) {
    return '<div class="empty listing-empty">No disassembly available.</div>';
  }
  return rows.map((row, rowIndex) => `
    <div
      class="listing-row listing-row-${escapeHtml(row.kind)}${rowUsesGlobalTextColumn(row) ? " listing-row-global" : ""}${Array.isArray(row.repro_issues) && row.repro_issues.length ? " listing-row-repro-issue" : ""}"
      data-row-addr="${row.addr === null || row.addr === undefined ? "" : escapeHtml(String(row.addr))}"
      data-row-index="${escapeHtml(String(globalStart + rowIndex))}"
      data-row-kind="${escapeHtml(row.kind)}"
      data-row-code="${escapeHtml(renderListingCode(row))}"
      ${row.stable_key ? `data-row-stable-key="${escapeHtml(row.stable_key)}"` : ""}
      ${row.analysis_generation ? `data-analysis-generation="${escapeHtml(row.analysis_generation)}"` : ""}
      ${row.analysis_phase ? `data-analysis-phase="${escapeHtml(row.analysis_phase)}"` : ""}
      ${row.section_index !== null && row.section_index !== undefined ? `data-section-index="${escapeHtml(String(row.section_index))}"` : ""}
      ${row.start_offset !== null && row.start_offset !== undefined ? `data-start-offset="${escapeHtml(String(row.start_offset))}"` : ""}
      ${row.end_offset !== null && row.end_offset !== undefined ? `data-end-offset="${escapeHtml(String(row.end_offset))}"` : ""}
      ${row.structured_data?.struct_name ? `data-struct-name="${escapeHtml(row.structured_data.struct_name)}"` : ""}
      ${row.structured_data?.field_name ? `data-struct-field="${escapeHtml(row.structured_data.field_name)}"` : ""}
    >
      <span class="listing-offset">${escapeHtml(formatRowOffset(row.addr))}</span>
      <span class="listing-bytes">${escapeHtml(formatRowBytes(row.bytes))}</span>
      <span class="listing-code">${renderListingCodeHtml(row, globalStart + rowIndex)}</span>
      <span class="listing-comment">${escapeHtml(renderListingComment(row))}${renderListingComment(row) && renderListingAnnotations(row) ? " " : ""}${renderListingAnnotations(row)}${renderReproIssueBadges(row)}${renderApiTypeBadges(row)}${(renderListingAnnotations(row) || renderReproIssueBadges(row) || renderApiTypeBadges(row)) ? " " : ""}${renderApiEditButton(row, rowIndex)}${renderAnnotationEditButton(row, rowIndex)}</span>
      <span class="listing-column-resizer listing-column-resizer-offset" data-listing-column-resize="offset" aria-hidden="true"></span>
      <span class="listing-column-resizer listing-column-resizer-bytes" data-listing-column-resize="bytes" aria-hidden="true"></span>
      <span class="listing-column-resizer listing-column-resizer-code" data-listing-column-resize="code" aria-hidden="true"></span>
    </div>
  `).join("");
}

function clampListingWindowCount(count) {
  return Math.max(LISTING_MIN_WINDOW_ROWS, Math.min(LISTING_MAX_WINDOW_ROWS, count));
}

function listingVisibleRowCount(viewport) {
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  const height = viewport?.clientHeight || window.innerHeight || 720;
  return Math.max(1, Math.ceil(height / rowHeight));
}

function listingFetchCount(viewport) {
  return clampListingWindowCount(listingVisibleRowCount(viewport) * (1 + LISTING_OVERSCAN_SCREENS));
}

function measureRenderedListingRowHeight(viewport) {
  const row = viewport?.querySelector(".listing-row");
  if (!(row instanceof HTMLElement)) {
    return state.virtualListing.rowHeight || 22;
  }
  const measured = row.getBoundingClientRect().height;
  if (measured > 0) {
    state.virtualListing.rowHeight = measured;
  }
  return state.virtualListing.rowHeight;
}

function renderVirtualListingWindow(projectId, listing, preserveScroll = false, forcedScrollTop = null) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  const scrollTop = viewport.scrollTop;
  state.listingRows = listing.rows;
  state.virtualListing.start = listing.start || 0;
  state.virtualListing.end = listing.end || state.virtualListing.start + listing.rows.length;
  state.virtualListing.totalRows = listing.total_rows || listing.rows.length;
  state.virtualListing.generation = listing.analysis_generation || state.virtualListing.generation;
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  const totalHeight = Math.max(rowHeight, state.virtualListing.totalRows * rowHeight);
  const top = state.virtualListing.start * rowHeight;
  viewport.innerHTML = `
    <div class="listing-scroll-spacer" style="height:${totalHeight}px;${listingColumnStyle()}">
      <div class="listing-row-layer" style="transform:translateY(${top}px);${listingColumnStyle()}">
        ${renderListingRows(listing.rows, state.virtualListing.start)}
      </div>
    </div>
  `;
  applyListingColumnWidths();
  measureRenderedListingRowHeight(viewport);
  bindListingEditors(projectId, listing.rows);
  bindVirtualListingScroller(projectId, viewport);
  if (forcedScrollTop !== null && Number.isFinite(forcedScrollTop)) {
    viewport.scrollTop = Math.max(0, forcedScrollTop);
  } else if (preserveScroll) {
    viewport.scrollTop = scrollTop;
  }
  renderNavigationOverlay();
}

function bindVirtualListingScroller(projectId, viewport) {
  if (!(viewport instanceof HTMLElement)) {
    return;
  }
  if (viewport._listingScrollHandler) {
    viewport.removeEventListener("scroll", viewport._listingScrollHandler);
  }
  viewport._listingScrollHandler = () => {
    if (state.virtualListing.suppressScrollFetch) {
      return;
    }
    if (state.virtualListing.scrollRaf !== null) {
      window.cancelAnimationFrame(state.virtualListing.scrollRaf);
    }
    state.virtualListing.scrollRaf = window.requestAnimationFrame(() => {
      state.virtualListing.scrollRaf = null;
      scheduleListingWindowForScroll(projectId, viewport, {delayMs: 120});
    });
  };
  viewport.addEventListener("scroll", viewport._listingScrollHandler);
}

function scrollListingViewport(projectId, direction) {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement)) {
    return false;
  }
  const pageStep = Math.max(1, Math.floor(viewport.clientHeight * 0.9));
  if (direction === "down") {
    viewport.scrollTop = Math.min(viewport.scrollTop + pageStep, viewport.scrollHeight);
  } else if (direction === "up") {
    viewport.scrollTop = Math.max(viewport.scrollTop - pageStep, 0);
  } else if (direction === "home") {
    viewport.scrollTop = 0;
  } else if (direction === "end") {
    viewport.scrollTop = viewport.scrollHeight;
  } else {
    return false;
  }
  scheduleListingWindowForScroll(projectId, viewport, {delayMs: 0});
  void flushPendingListingWindow();
  return true;
}

function currentListingIndexWindow(viewport) {
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  const visibleRows = listingVisibleRowCount(viewport);
  const firstVisible = Math.max(0, Math.floor((viewport?.scrollTop || 0) / rowHeight));
  const margin = visibleRows;
  const count = listingFetchCount(viewport);
  return {
    start: Math.max(0, firstVisible - margin),
    count,
  };
}

function captureListingAddressAnchor(viewport) {
  if (!(viewport instanceof HTMLElement)) {
    return null;
  }
  const viewportTop = viewport.getBoundingClientRect().top;
  const rows = Array.from(viewport.querySelectorAll(".listing-row"))
    .filter((row) => row instanceof HTMLElement);
  if (!rows.length) {
    return null;
  }
  let best = rows[0];
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const row of rows) {
    const rect = row.getBoundingClientRect();
    const distance = Math.abs(rect.top - viewportTop);
    if (distance < bestDistance) {
      best = row;
      bestDistance = distance;
    }
  }
  return {
    addr: best.dataset.rowAddr !== "" && best.dataset.rowAddr !== undefined
      ? Number(best.dataset.rowAddr)
      : null,
    stableKey: best.dataset.rowStableKey || null,
    rowCode: best.dataset.rowCode || "",
    topDelta: best.getBoundingClientRect().top - viewportTop,
  };
}

function selectListingAnchorRow(viewport, anchor) {
  if (!(viewport instanceof HTMLElement) || !anchor) {
    return null;
  }
  if (Number.isFinite(anchor.addr)) {
    const row = selectBestListingRow(viewport, anchor.addr, anchor.rowCode || null);
    if (row instanceof HTMLElement) {
      return row;
    }
  }
  if (anchor.stableKey) {
    const row = viewport.querySelector(`[data-row-stable-key="${CSS.escape(anchor.stableKey)}"]`);
    if (row instanceof HTMLElement) {
      return row;
    }
  }
  if (anchor.rowCode) {
    const rows = Array.from(viewport.querySelectorAll(".listing-row"));
    const row = rows.find((candidate) => (
      candidate instanceof HTMLElement && candidate.dataset.rowCode === anchor.rowCode
    ));
    if (row instanceof HTMLElement) {
      return row;
    }
  }
  return null;
}

function listingAnchorRowIndexInRows(rows, anchor) {
  if (!anchor) {
    return -1;
  }
  if (Number.isFinite(anchor.addr)) {
    const wantedCode = String(anchor.rowCode || "");
    const exactIndex = rows.findIndex((row) => (
      row.addr === anchor.addr && (!wantedCode || renderListingCode(row) === wantedCode)
    ));
    if (exactIndex >= 0) {
      return exactIndex;
    }
    const addrIndex = rows.findIndex((row) => row.addr === anchor.addr);
    if (addrIndex >= 0) {
      return addrIndex;
    }
  }
  if (anchor.stableKey) {
    const stableIndex = rows.findIndex((row) => row.stable_key === anchor.stableKey);
    if (stableIndex >= 0) {
      return stableIndex;
    }
  }
  if (anchor.rowCode) {
    const wanted = String(anchor.rowCode).trim();
    return rows.findIndex((row) => renderListingCode(row).trim() === wanted);
  }
  return -1;
}

function listingAnchorRowIndex(anchor) {
  return listingAnchorRowIndexInRows(state.listingRows, anchor);
}

function listingAnchorScrollTop(listing, anchor) {
  const rowIndex = listingAnchorRowIndexInRows(listing?.rows || [], anchor);
  if (rowIndex < 0) {
    return null;
  }
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  return (((listing.start || 0) + rowIndex) * rowHeight) - (anchor?.topDelta || 0);
}

function restoreListingAddressAnchor(viewport, anchor) {
  if (!(viewport instanceof HTMLElement) || !anchor) {
    return;
  }
  const rowIndex = listingAnchorRowIndex(anchor);
  if (rowIndex >= 0) {
    const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
    viewport.scrollTop = Math.max(0, ((state.virtualListing.start + rowIndex) * rowHeight) - anchor.topDelta);
    return;
  }
  const row = selectListingAnchorRow(viewport, anchor);
  if (!(row instanceof HTMLElement)) {
    return;
  }
  const viewportTop = viewport.getBoundingClientRect().top;
  const delta = row.getBoundingClientRect().top - viewportTop - anchor.topDelta;
  viewport.scrollTop += delta;
}

async function refreshListingAtCurrentAddressAnchor(projectId, token = null) {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement)) {
    return null;
  }
  const anchor = captureListingAddressAnchor(viewport);
  const visibleRows = listingVisibleRowCount(viewport);
  const count = listingFetchCount(viewport);
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  const isAtListingTop = state.virtualListing.start === 0 && viewport.scrollTop <= rowHeight * 2;
  const requestSeqBeforeRefresh = state.virtualListing.requestSeq;
  const shouldUseCodeAnchor = anchor?.rowCode && (isAtListingTop || !Number.isFinite(anchor.addr));
  const listing = shouldUseCodeAnchor
    ? await loadListingWindow(projectId, null, 0, count, {
        anchorCode: anchor.rowCode,
        count,
        preserveScroll: false,
        restoreAnchor: anchor,
      })
    : !isAtListingTop && anchor && Number.isFinite(anchor.addr)
    ? await loadListingWindow(projectId, anchor.addr, visibleRows, count - visibleRows, {
        preserveScroll: false,
        restoreAnchor: anchor,
      })
    : await loadListingWindow(projectId, null, 0, count, {
        ...(isAtListingTop ? {start: 0, count} : currentListingIndexWindow(viewport)),
        preserveScroll: false,
        restoreAnchor: anchor,
      });
  if (token !== null && token !== state.loadingToken) {
    return listing;
  }
  if (state.virtualListing.requestSeq !== requestSeqBeforeRefresh + 1) {
    return listing;
  }
  restoreListingAddressAnchor(document.getElementById("listing-viewport"), anchor);
  return listing;
}

async function handleListingGenerationReady(payload, token = null) {
  if (!state.project || payload.project_id !== state.project) {
    return;
  }
  if (token !== null && token !== state.loadingToken) {
    return;
  }
  if (payload.generation === "basic") {
    if (state.virtualListing.generation === "basic" || state.virtualListing.generation === "full") {
      return;
    }
    setAnalysisStatus("Loading initial listing", "running");
    await loadInitialListingWindow(state.project);
    if (token !== null && token !== state.loadingToken) {
      return;
    }
    setAnalysisStatus("Analyzing full listing", "running");
    return;
  }
  if (payload.generation === state.virtualListing.generation) {
    return;
  }
  setAnalysisStatus("Applying full analysis", "running");
  const listing = await refreshListingAtCurrentAddressAnchor(state.project, token);
  if (token !== null && token !== state.loadingToken) {
    return;
  }
  if (listing?.analysis_generation === payload.generation) {
    await loadNavigationEntries(state.project);
    renderNavigationOverlay();
    setAnalysisStatus("Full analysis ready", "ready", 2000);
  }
}

async function loadListingWindowForScroll(projectId, viewport) {
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  const visibleRows = listingVisibleRowCount(viewport);
  const firstVisible = Math.max(0, Math.floor(viewport.scrollTop / rowHeight));
  const lastVisible = firstVisible + visibleRows;
  const margin = visibleRows;
  if (
    firstVisible >= state.virtualListing.start + margin &&
    lastVisible <= state.virtualListing.end - margin
  ) {
    return;
  }
  const {start, count} = currentListingIndexWindow(viewport);
  await loadListingWindow(projectId, null, 0, count, {start, count, preserveScroll: true});
}

function desiredListingWindowForScroll(viewport) {
  if (!(viewport instanceof HTMLElement)) {
    return null;
  }
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  const visibleRows = listingVisibleRowCount(viewport);
  const firstVisible = Math.max(0, Math.floor(viewport.scrollTop / rowHeight));
  const lastVisible = firstVisible + visibleRows;
  const margin = visibleRows;
  if (
    firstVisible >= state.virtualListing.start + margin &&
    lastVisible <= state.virtualListing.end - margin
  ) {
    return null;
  }
  return currentListingIndexWindow(viewport);
}

function sameListingWindow(left, right) {
  return Boolean(left && right && left.start === right.start && left.count === right.count);
}

function scheduleListingWindowForScroll(projectId, viewport, {delayMs = 120} = {}) {
  const desired = desiredListingWindowForScroll(viewport);
  if (!desired) {
    return;
  }
  state.virtualListing.pendingWindow = {
    projectId,
    start: desired.start,
    count: desired.count,
  };
  if (state.virtualListing.scrollTimer !== null) {
    window.clearTimeout(state.virtualListing.scrollTimer);
    state.virtualListing.scrollTimer = null;
  }
  state.virtualListing.scrollTimer = window.setTimeout(() => {
    state.virtualListing.scrollTimer = null;
    void flushPendingListingWindow();
  }, Math.max(0, delayMs));
}

async function flushPendingListingWindow() {
  const pending = state.virtualListing.pendingWindow;
  if (!pending) {
    return null;
  }
  if (sameListingWindow(pending, state.virtualListing.inFlightWindow)) {
    return null;
  }
  state.virtualListing.pendingWindow = null;
  state.virtualListing.inFlightWindow = pending;
  try {
    return await loadListingWindow(pending.projectId, null, 0, pending.count, {
      start: pending.start,
      count: pending.count,
      preserveScroll: true,
      abortPrevious: true,
    });
  } catch (error) {
    if (!isAbortError(error)) {
      throw error;
    }
    return null;
  } finally {
    if (sameListingWindow(state.virtualListing.inFlightWindow, pending)) {
      state.virtualListing.inFlightWindow = null;
    }
    if (state.virtualListing.pendingWindow) {
      void flushPendingListingWindow();
    }
  }
}

function isEditableTarget(target) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  return Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
}

function isLabelRow(row) {
  return Boolean(row.label) || renderListingCode(row).trim().endsWith(":");
}

function rowHasSegmentReference(row) {
  if (!Array.isArray(row.operand_parts)) {
    return false;
  }
  return row.operand_parts.some((operand) => operand.segment_addr !== null && operand.segment_addr !== undefined);
}

function rowHasTypedData(row) {
  return row.kind !== "instruction" && row.kind !== "label" && (Boolean(row.comment_text) || Boolean(row.structured_data));
}

function rowHasComment(row) {
  return Boolean(row.comment_text) || (Array.isArray(row.view_annotations) && row.view_annotations.length > 0);
}

function rowApiCallHasNearLvoReference(rows, row, rowIndex) {
  const hunkIndex = rowHunkIndex(row);
  const start = Math.max(0, rowIndex - 8);
  for (let index = start; index < rowIndex; ++index) {
    const candidate = rows[index];
    if (
      candidate?.api_call
      && candidate.api_call.note_kind === 0
      && rowHunkIndex(candidate) === hunkIndex
      && candidate.addr >= row.addr - 8
      && candidate.addr < row.addr
      && candidate.api_call.library === row.api_call.library
      && candidate.api_call.function === row.api_call.function
    ) {
      return true;
    }
  }
  return false;
}

function rowApiCallIsNavigationTarget(rows, row, rowIndex) {
  if (!row.api_call || row.api_call.note_kind === 3) {
    return false;
  }
  if (row.api_call.note_kind === 1 && rowApiCallHasNearLvoReference(rows, row, rowIndex)) {
    return false;
  }
  return true;
}

function rowHunkIndex(row) {
  const context = row.source_context || row.sourceContext || {};
  const value = context.hunk_index ?? context.hunkIndex ?? row.section_index ?? row.sectionIndex;
  return Number.isInteger(value) ? value : null;
}

function summarizeNavigationRow(row, jumpClass) {
  if (jumpClass === "api-calls" && row.api_call) {
    if (row.api_call.note_kind === 1) {
      return `${row.api_call.function} dispatch (${row.api_call.library})`;
    }
    return `${row.api_call.function} (${row.api_call.library})`;
  }
  if (jumpClass === "typed-data" && (row.comment_text || row.structured_data)) {
    const item = row.structured_data || {};
    return row.comment_text || item.label || item.field_name || row.kind;
  }
  if (jumpClass === "labels") {
    return renderListingCode(row).trim();
  }
  return renderListingCode(row).trim() || row.comment_text || row.kind;
}

function normalizedAppSlotRef(rawRef) {
  if (!rawRef || typeof rawRef !== "object") {
    return null;
  }
  const symbol = rawRef.symbol;
  const displacement = Number(rawRef.displacement);
  const baseRegister = rawRef.base_register ?? rawRef.baseRegister;
  const operandIndex = Number(rawRef.operand_index ?? rawRef.operandIndex);
  const access = rawRef.access;
  if (
    typeof symbol !== "string" ||
    !Number.isFinite(displacement) ||
    typeof baseRegister !== "string" ||
    !Number.isInteger(operandIndex) ||
    typeof access !== "string" ||
    !APP_SLOT_ACCESS_ORDER.includes(access)
  ) {
    return null;
  }
  return {
    symbol,
    displacement,
    base_register: baseRegister,
    operand_index: operandIndex,
    access,
  };
}

function addAppSlotNavigationRef(appSlots, row, rowIndex, rawRef) {
  const ref = normalizedAppSlotRef(rawRef);
  if (!ref) {
    return;
  }
  let slot = appSlots.get(ref.symbol);
  if (!slot) {
    slot = {
      symbol: ref.symbol,
      summary: ref.symbol,
      match_text: ref.symbol,
      displacement: ref.displacement,
      ref_count: 0,
      access_counts: {},
      refs: [],
    };
    appSlots.set(ref.symbol, slot);
  }
  const hunkIndex = rowHunkIndex(row);
  const stableKey = row.stable_key ?? row.stableKey ?? null;
  const matchText = renderListingCode(row);
  slot.refs.push({
    addr: row.addr,
    rowIndex,
    row_index: rowIndex,
    hunkIndex,
    hunk_index: hunkIndex,
    stableKey,
    stable_key: stableKey,
    summary: matchText.trim() || ref.symbol,
    matchText,
    match_text: matchText,
    symbol: ref.symbol,
    displacement: ref.displacement,
    base_register: ref.base_register,
    operand_index: ref.operand_index,
    access: ref.access,
  });
  slot.ref_count += 1;
  slot.access_counts[ref.access] = (slot.access_counts[ref.access] || 0) + 1;
}

function sortedAppSlotNavigationEntries(appSlots) {
  return Array.from(appSlots.values())
    .map((slot) => {
      slot.refs.sort((left, right) => Number(left.row_index) - Number(right.row_index));
      return slot;
    })
    .sort((left, right) => (left.displacement - right.displacement) || left.symbol.localeCompare(right.symbol));
}

function buildNavigationEntries(rows) {
  const groups = {
    "repro-issues": [],
    "typed-data": [],
    "relocations": [],
    "api-calls": [],
    "app-slots": [],
    "labels": [],
    "comments": [],
  };
  const appSlots = new Map();
  rows.forEach((row, rowIndex) => {
    if (row.addr === null || row.addr === undefined) {
      return;
    }
    if (Array.isArray(row.repro_issues) && row.repro_issues.length) {
      const issue = row.repro_issues[0];
      groups["repro-issues"].push({
        addr: row.addr,
        issueIndex: issue.issue_index ?? issue.issueIndex ?? null,
        issue_index: issue.issue_index ?? issue.issueIndex ?? null,
        rowIndex,
        row_index: issue.row_index ?? rowIndex,
        section_index: issue.section_index ?? null,
        hunk: issue.hunk ?? null,
        stableKey: issue.stable_key ?? row.stable_key ?? null,
        stable_key: issue.stable_key ?? row.stable_key ?? null,
        summary: row.repro_issues[0].summary || row.repro_issues[0].message || "Repro issue",
        matchText: renderListingCode(row),
        match_text: issue.match_text || renderListingCode(row),
      });
    }
    if (rowHasTypedData(row)) {
      groups["typed-data"].push({
        addr: row.addr,
        rowIndex,
        summary: summarizeNavigationRow(row, "typed-data"),
        matchText: renderListingCode(row),
      });
    }
    if (rowHasSegmentReference(row)) {
      groups.relocations.push({
        addr: row.addr,
        rowIndex,
        summary: summarizeNavigationRow(row, "relocations"),
        matchText: renderListingCode(row),
      });
    }
    if (row.kind === "instruction" && rowApiCallIsNavigationTarget(rows, row, rowIndex)) {
      const hunkIndex = rowHunkIndex(row);
      const stableKey = row.stable_key ?? row.stableKey ?? null;
      const matchText = renderListingCode(row);
      groups["api-calls"].push({
        addr: row.addr,
        rowIndex,
        row_index: rowIndex,
        hunkIndex,
        hunk_index: hunkIndex,
        stableKey,
        stable_key: stableKey,
        summary: summarizeNavigationRow(row, "api-calls"),
        matchText,
        match_text: matchText,
      });
    }
    if (Array.isArray(row.app_slot_refs)) {
      row.app_slot_refs.forEach((ref) => addAppSlotNavigationRef(appSlots, row, rowIndex, ref));
    }
    if (isLabelRow(row)) {
      groups.labels.push({
        addr: row.addr,
        rowIndex,
        summary: summarizeNavigationRow(row, "labels"),
        matchText: renderListingCode(row),
      });
    }
    if (rowHasComment(row)) {
      groups.comments.push({
        addr: row.addr,
        rowIndex,
        summary: summarizeNavigationRow(row, "comments"),
        matchText: renderListingCode(row),
      });
    }
  });
  groups["app-slots"] = sortedAppSlotNavigationEntries(appSlots);
  return groups;
}

function currentNavigationEntries() {
  const groups = state.navigation.entries || buildNavigationEntries(state.listingRows || []);
  if (state.navigation.selectedClass === "app-slots" && state.navigation.appSlotSymbol) {
    const slot = (groups["app-slots"] || []).find((entry) => entry.symbol === state.navigation.appSlotSymbol);
    return slot?.refs || [];
  }
  return groups[state.navigation.selectedClass] || [];
}

async function loadNavigationEntries(projectId) {
  const payload = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/listing/navigation`);
  state.navigation.entries = payload.groups || null;
  state.navigation.generation = payload.analysis_generation || null;
  if (
    state.navigation.appSlotSymbol &&
    !((state.navigation.entries?.["app-slots"] || []).some((entry) => entry.symbol === state.navigation.appSlotSymbol))
  ) {
    state.navigation.appSlotSymbol = null;
  }
  return state.navigation.entries;
}

async function ensureNavigationEntries(projectId) {
  if (state.navigation.entries) {
    return state.navigation.entries;
  }
  return loadNavigationEntries(projectId);
}

function syncNavigationSelection() {
  const entries = currentNavigationEntries();
  if (!entries.length) {
    state.navigation.selectedIndex = 0;
    return;
  }
  const maxIndex = entries.length - 1;
  state.navigation.selectedIndex = Math.max(0, Math.min(maxIndex, state.navigation.selectedIndex));
}

function navigationEntryRowIndex(entry) {
  const value = Number(entry?.rowIndex ?? entry?.row_index);
  return Number.isFinite(value) ? value : null;
}

function navigationEntriesSameLocation(left, right) {
  if (!left || !right) {
    return false;
  }
  const leftStable = left.stableKey || left.stable_key || null;
  const rightStable = right.stableKey || right.stable_key || null;
  if (leftStable && rightStable) {
    return leftStable === rightStable;
  }
  const leftRowIndex = navigationEntryRowIndex(left);
  const rightRowIndex = navigationEntryRowIndex(right);
  if (leftRowIndex !== null && rightRowIndex !== null) {
    return leftRowIndex === rightRowIndex;
  }
  return left.addr === right.addr && navigationEntryHunkIndex(left) === navigationEntryHunkIndex(right);
}

function captureViewportAnchor() {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return null;
  }
  const rows = Array.from(viewport.querySelectorAll(".listing-row[data-row-addr]"));
  const threshold = 120;
  const visible = rows.find((row) => row.getBoundingClientRect().top >= threshold);
  const candidate = visible || rows[0] || null;
  if (!candidate) {
    return null;
  }
  const addrText = candidate.dataset.rowAddr;
  const addr = addrText === "" || addrText === undefined ? null : Number(addrText);
  if (addr === null || Number.isNaN(addr)) {
    return null;
  }
  return {
    addr,
    hunk: candidate.dataset.sectionIndex === undefined ? null : Number(candidate.dataset.sectionIndex),
    matchText: candidate.dataset.rowCode || null,
    rowIndex: candidate.dataset.rowIndex === undefined ? null : Number(candidate.dataset.rowIndex),
    row_index: candidate.dataset.rowIndex === undefined ? null : Number(candidate.dataset.rowIndex),
    stableKey: candidate.dataset.rowStableKey || null,
    stable_key: candidate.dataset.rowStableKey || null,
    scrollTop: viewport.scrollTop,
  };
}

function appSlotAccessBadgeLabel(access) {
  return APP_SLOT_ACCESS_LABELS[access] || access;
}

function renderNavigationAccessBadges(entry) {
  const badges = [];
  const accessCounts = entry.access_counts || entry.accessCounts || null;
  const refCount = Number(entry.ref_count ?? entry.refCount);
  if (Number.isFinite(refCount) && refCount > 0) {
    badges.push(`${refCount} ref${refCount === 1 ? "" : "s"}`);
  }
  if (accessCounts && typeof accessCounts === "object") {
    APP_SLOT_ACCESS_ORDER.forEach((access) => {
      const count = Number(accessCounts[access]);
      if (Number.isFinite(count) && count > 0) {
        badges.push(`${appSlotAccessBadgeLabel(access)} ${count}`);
      }
    });
  } else if (typeof entry.access === "string") {
    badges.push(appSlotAccessBadgeLabel(entry.access));
  }
  if (!badges.length) {
    return "";
  }
  return `<span class="navigation-item-badges">${badges.map((badge) => `<span class="navigation-access-badge">${escapeHtml(badge)}</span>`).join("")}</span>`;
}

function currentAppSlotNavigationSymbol() {
  if (state.navigation.selectedClass !== "app-slots") {
    return null;
  }
  return state.navigation.appSlotSymbol || null;
}

function navigationSummaryText(entries) {
  const appSlotSymbol = currentAppSlotNavigationSymbol();
  if (appSlotSymbol) {
    return `${appSlotSymbol}: ${entries.length} ref${entries.length === 1 ? "" : "s"}`;
  }
  return `${entries.length} entries`;
}

function navigationEntryHasRefs(entry) {
  return Array.isArray(entry?.refs);
}

function appSlotEntriesFromGroups(groups) {
  return groups?.["app-slots"] || [];
}

function appSlotEntryIndex(entries, symbolName) {
  return entries.findIndex((entry) => entry.symbol === symbolName);
}

function appSlotRefEntryIndex(refs, rowIndex, operandIndex, access) {
  const wantedRow = Number(rowIndex);
  const wantedOperand = Number(operandIndex);
  const wantedAccess = String(access || "");
  if (Number.isFinite(wantedRow)) {
    const exact = refs.findIndex((ref) => (
      navigationEntryRowIndex(ref) === wantedRow
      && (!Number.isFinite(wantedOperand) || Number(ref.operand_index ?? ref.operandIndex) === wantedOperand)
      && (!wantedAccess || ref.access === wantedAccess)
    ));
    if (exact >= 0) {
      return exact;
    }
    const sameRow = refs.findIndex((ref) => navigationEntryRowIndex(ref) === wantedRow);
    if (sameRow >= 0) {
      return sameRow;
    }
  }
  return refs.length ? 0 : -1;
}

function focusVisibleListingRowByIndex(rowIndex) {
  const viewport = document.getElementById("listing-viewport");
  const value = Number(rowIndex);
  if (!(viewport instanceof HTMLElement) || !Number.isFinite(value)) {
    return;
  }
  const row = viewport.querySelector(`[data-row-index="${String(Math.floor(value))}"]`);
  if (!(row instanceof HTMLElement)) {
    return;
  }
  row.classList.add("listing-row-focus");
  window.setTimeout(() => row.classList.remove("listing-row-focus"), 1200);
}

async function selectAppSlotNavigationRef(projectId, symbolName, rowIndex = null, operandIndex = null, access = null) {
  const symbol = String(symbolName || "");
  if (!isAppSlotSymbolName(symbol)) {
    return;
  }
  const groups = await ensureNavigationEntries(projectId);
  const entries = appSlotEntriesFromGroups(groups);
  const slotIndex = appSlotEntryIndex(entries, symbol);
  if (slotIndex < 0) {
    return;
  }
  const refs = entries[slotIndex].refs || [];
  const refIndex = appSlotRefEntryIndex(refs, rowIndex, operandIndex, access);
  if (!state.navigation.overlayOpen) {
    state.navigation.originEntry = captureViewportAnchor();
  }
  state.navigation.overlayOpen = true;
  state.navigation.selectedClass = "app-slots";
  state.navigation.appSlotSymbol = symbol;
  state.navigation.selectedIndex = Math.max(0, refIndex);
  state.navigation.currentPreviewEntry = refs[state.navigation.selectedIndex] || null;
  renderNavigationOverlay();
  syncNavigationListFocus();
  focusVisibleListingRowByIndex(rowIndex);
}

function renderAppSlotNavigationBack() {
  if (!currentAppSlotNavigationSymbol()) {
    return "";
  }
  return '<button type="button" class="navigation-back-to-slots" data-navigation-app-slots-root="1">All App Slots</button>';
}

function renderNavigationOverlay() {
  const existing = document.getElementById("navigation-overlay");
  if (!state.navigation.overlayOpen) {
    existing?.remove();
    return;
  }
  const app = document.getElementById("app");
  if (!app) {
    return;
  }
  const entries = currentNavigationEntries();
  syncNavigationSelection();
  const selectedClass = state.navigation.selectedClass;
  const classOptions = [
    ["repro-issues", "Repro Issues"],
    ["typed-data", "Typed Data"],
    ["relocations", "Relocations"],
    ["api-calls", "API Calls"],
    ["app-slots", "App Slots"],
    ["labels", "Labels"],
    ["comments", "Comments"],
  ];
  const html = `
    <div class="navigation-overlay" id="navigation-overlay">
      <div class="navigation-panel">
        <div class="navigation-header">
          <div class="navigation-title">Navigate</div>
          <button type="button" class="navigation-close" data-navigation-close="1">Close</button>
        </div>
        <label class="navigation-class-label">
          <span>Jump Class</span>
          <select class="navigation-class-select" data-navigation-class="1">
            ${classOptions.map(([value, label]) => `<option value="${escapeHtml(value)}"${value === selectedClass ? " selected" : ""}>${escapeHtml(label)}</option>`).join("")}
          </select>
        </label>
        <div class="navigation-summary-row">
          <div class="navigation-summary">${escapeHtml(navigationSummaryText(entries))}</div>
          ${renderAppSlotNavigationBack()}
        </div>
        <div class="navigation-list" tabindex="0" data-navigation-list="1">
          ${entries.length
            ? entries.map((entry, index) => `
              <button
                type="button"
                class="navigation-item${index === state.navigation.selectedIndex ? " active" : ""}"
                data-navigation-index="${index}"
              >
                <span class="navigation-item-addr">${escapeHtml(formatNavigationEntryOffset(entry))}</span>
                <span class="navigation-item-text">${escapeHtml(entry.summary)}</span>
                ${renderNavigationAccessBadges(entry)}
              </button>
            `).join("")
            : '<div class="navigation-empty">No entries in this class.</div>'}
        </div>
      </div>
    </div>
  `;
  if (existing) {
    existing.outerHTML = html;
  } else {
    app.insertAdjacentHTML("beforeend", html);
  }
  bindNavigationOverlay();
}

function syncNavigationListFocus() {
  const list = document.querySelector("[data-navigation-list='1']");
  const selected = document.querySelector(".navigation-item.active");
  if (!(list instanceof HTMLElement)) {
    return;
  }
  list.focus();
  if (selected instanceof HTMLElement) {
    selected.scrollIntoView({ block: "nearest" });
  }
}

async function previewNavigationEntry(entry) {
  if (!entry || !state.project) {
    return;
  }
  if (navigationEntryHasRefs(entry)) {
    return;
  }
  state.navigation.currentPreviewEntry = entry;
  if (state.navigation.selectedClass === "repro-issues") {
    state.reproduction.selectedIssueEntry = entry;
    renderReproPanel();
  }
  await jumpToNavigationEntry(state.project, entry);
}

async function activateNavigationEntry(entry) {
  if (!entry) {
    return;
  }
  if (state.navigation.selectedClass === "app-slots" && navigationEntryHasRefs(entry)) {
    state.navigation.appSlotSymbol = entry.symbol || null;
    state.navigation.selectedIndex = 0;
    state.navigation.currentPreviewEntry = null;
    renderNavigationOverlay();
    syncNavigationListFocus();
    return;
  }
  await previewNavigationEntry(entry);
}

async function moveNavigationSelection(delta) {
  const entries = currentNavigationEntries();
  if (!entries.length) {
    return;
  }
  const nextIndex = Math.max(0, Math.min(entries.length - 1, state.navigation.selectedIndex + delta));
  if (nextIndex === state.navigation.selectedIndex && state.navigation.currentPreviewEntry) {
    return;
  }
  state.navigation.selectedIndex = nextIndex;
  renderNavigationOverlay();
  syncNavigationListFocus();
  await previewNavigationEntry(entries[nextIndex]);
}

async function setNavigationClass(value) {
  state.navigation.selectedClass = value;
  state.navigation.selectedIndex = 0;
  state.navigation.appSlotSymbol = null;
  state.navigation.currentPreviewEntry = null;
  renderNavigationOverlay();
  syncNavigationListFocus();
  const [first] = currentNavigationEntries();
  await previewNavigationEntry(first || null);
}

function commitNavigationPreview() {
  const origin = state.navigation.originEntry;
  const current = state.navigation.currentPreviewEntry;
  if (!origin || !current || navigationEntriesSameLocation(origin, current)) {
    return;
  }
  state.navigation.historyBack.push(origin);
  state.navigation.historyForward = [];
  state.navigation.currentLocation = current;
}

function closeNavigationOverlay() {
  commitNavigationPreview();
  state.navigation.overlayOpen = false;
  state.navigation.originEntry = null;
  state.navigation.currentPreviewEntry = null;
  renderNavigationOverlay();
}

async function openNavigationOverlay() {
  if (state.project) {
    await ensureNavigationEntries(state.project);
  }
  state.navigation.overlayOpen = true;
  state.navigation.originEntry = captureViewportAnchor();
  renderNavigationOverlay();
  syncNavigationListFocus();
  const entries = currentNavigationEntries();
  if (!entries.length) {
    return;
  }
  const originAddr = state.navigation.originEntry?.addr ?? null;
  const initialIndex = originAddr === null ? 0 : Math.max(0, entries.findIndex((entry) => entry.addr >= originAddr));
  state.navigation.selectedIndex = initialIndex < 0 ? 0 : initialIndex;
  renderNavigationOverlay();
  syncNavigationListFocus();
  await previewNavigationEntry(entries[state.navigation.selectedIndex]);
}

async function navigateHistory(direction) {
  const sourceStack = direction === "back" ? state.navigation.historyBack : state.navigation.historyForward;
  const targetStack = direction === "back" ? state.navigation.historyForward : state.navigation.historyBack;
  const target = sourceStack.pop();
  if (!target || !state.project) {
    return;
  }
  const current = state.navigation.currentLocation || captureViewportAnchor();
  if (current) {
    targetStack.push(current);
  }
  await jumpToNavigationEntry(state.project, target);
  state.navigation.currentLocation = target;
}

function bindNavigationOverlay() {
  const overlay = document.getElementById("navigation-overlay");
  if (!overlay) {
    return;
  }
  overlay.querySelector("[data-navigation-close='1']")?.addEventListener("click", () => {
    closeNavigationOverlay();
  });
  overlay.querySelector("[data-navigation-class='1']")?.addEventListener("change", (event) => {
    void setNavigationClass(event.target.value);
  });
  overlay.querySelector("[data-navigation-app-slots-root='1']")?.addEventListener("click", () => {
    const entries = appSlotEntriesFromGroups(state.navigation.entries || buildNavigationEntries(state.listingRows || []));
    const slotIndex = appSlotEntryIndex(entries, state.navigation.appSlotSymbol || "");
    state.navigation.appSlotSymbol = null;
    state.navigation.selectedIndex = slotIndex >= 0 ? slotIndex : 0;
    state.navigation.currentPreviewEntry = null;
    renderNavigationOverlay();
    syncNavigationListFocus();
  });
  overlay.querySelectorAll("[data-navigation-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.navigation.selectedIndex = Number(button.dataset.navigationIndex);
      renderNavigationOverlay();
      syncNavigationListFocus();
      void activateNavigationEntry(currentNavigationEntries()[state.navigation.selectedIndex]);
    });
  });
}

async function ensureTypeCatalog(projectId) {
  if (state.typeCatalog !== null) {
    return state.typeCatalog;
  }
  state.typeCatalog = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/api/type-catalog`);
  return state.typeCatalog;
}

function renderTypeCatalogOptions(catalog) {
  return catalog.map((entry) => `<option value="${escapeHtml(entry.name)}">${escapeHtml(entry.name)} (${escapeHtml(entry.source)}, ${escapeHtml(String(entry.size))} bytes)</option>`).join("");
}

function renderApiEditDialog(projectId, row) {
  const apiCall = row.api_call;
  if (!apiCall) {
    return "";
  }
  const editableInputs = apiCall.inputs.filter((input) => (input.type || "").includes("*") && !(input.type || "").includes("**"));
  if (!editableInputs.length) {
    return "";
  }
  const rowsHtml = editableInputs.map((input, index) => `
    <div class="api-edit-row">
      <div class="api-edit-summary">${escapeHtml(input.regs.join("/"))} ${escapeHtml(input.name)} <span class="project-badge project-badge-source-${escapeHtml(String(input.source || "unknown").toLowerCase().replaceAll(/[^a-z0-9]+/g, "-"))}">${escapeHtml(input.source)}</span></div>
      <div class="api-edit-current">${escapeHtml(input.type || "(untyped)")}</div>
      <input class="api-edit-input" list="api-struct-catalog" data-input-name="${escapeHtml(input.name)}" value="${escapeHtml(input.i_struct || "")}" placeholder="Select struct name">
      <button type="button" class="api-edit-apply" data-input-name="${escapeHtml(input.name)}">Apply</button>
    </div>
  `).join("");
  return `
    <dialog class="api-edit-dialog" open>
      <form method="dialog" class="api-edit-panel">
        <div class="api-edit-title">${escapeHtml(apiCall.library)} / ${escapeHtml(apiCall.function)}</div>
        <div class="api-edit-subtitle">Pick an existing struct. The backend applies pointer decoration for single-pointer args only.</div>
        ${rowsHtml}
        <div class="api-edit-actions">
          <button type="button" class="api-edit-close">Close</button>
        </div>
      </form>
    </dialog>
  `;
}

async function refreshListingAfterApiEdit(projectId, addr) {
  state.navigation.overlayOpen = false;
  const job = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/listing/open`, {
    method: "POST",
  });
  const jobState = await waitForAsyncJob(
    (jobId) => `/api/projects/${encodeURIComponent(projectId)}/listing/status?job_id=${encodeURIComponent(jobId)}`,
    job,
    null,
    (currentJob) => setViewportOverlay(renderProgressOverlay(currentJob, "Refreshing listing")),
  );
  setViewportOverlay(loadingRowsOverlay());
  await loadInitialListingWindow(projectId);
  await loadNavigationEntries(projectId);
  if (addr !== null && addr !== undefined) {
    await jumpToListingAddr(projectId, addr);
  }
}

async function openApiEditDialog(projectId, row) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  const existing = document.querySelector(".api-edit-dialog");
  if (existing) {
    existing.remove();
  }
  viewport.insertAdjacentHTML("beforeend", `
    <datalist id="api-struct-catalog"></datalist>
    ${renderApiEditDialog(projectId, row)}
  `);
  void ensureTypeCatalog(projectId).then((catalog) => {
    const datalist = document.getElementById("api-struct-catalog");
    if (datalist) {
      datalist.innerHTML = renderTypeCatalogOptions(catalog);
    }
  }).catch((error) => {
    console.warn("Type catalog unavailable", error);
  });
  const dialog = document.querySelector(".api-edit-dialog");
  if (!dialog) {
    return;
  }
  dialog.querySelector(".api-edit-close")?.addEventListener("click", () => dialog.remove());
  dialog.querySelectorAll(".api-edit-apply").forEach((button) => {
    button.addEventListener("click", async () => {
      const inputName = button.dataset.inputName;
      const input = dialog.querySelector(`.api-edit-input[data-input-name="${CSS.escape(inputName)}"]`);
      const structName = input?.value?.trim();
      if (!structName) {
        window.alert("Select a struct name first.");
        return;
      }
      await fetchJson(
        `/api/projects/${encodeURIComponent(projectId)}/api/functions/${encodeURIComponent(row.api_call.library)}/${encodeURIComponent(row.api_call.function)}/inputs/${encodeURIComponent(inputName)}/struct`,
        {
          method: "PATCH",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({struct_name: structName}),
        },
      );
      dialog.remove();
      await refreshListingAfterApiEdit(projectId, row.addr);
    });
  });
}

function renderAnnotationEditDialog(entity) {
  return `
    <dialog class="annotation-edit-dialog" open>
      <form method="dialog" class="api-edit-panel">
        <div class="api-edit-title">${escapeHtml(entity.addr)}</div>
        <label class="annotation-edit-field">Name <input class="annotation-edit-name" value="${escapeHtml(entity.name || "")}"></label>
        <label class="annotation-edit-field">Comment <textarea class="annotation-edit-comment">${escapeHtml(entity.comment || "")}</textarea></label>
        <label class="annotation-edit-field">Type <select class="annotation-edit-type">
          ${["code", "data", "bss", "unknown"].map((value) => `<option value="${value}"${value === entity.type ? " selected" : ""}>${value}</option>`).join("")}
        </select></label>
        <label class="annotation-edit-field">Subtype <select class="annotation-edit-subtype">
          ${ENTITY_SUBTYPES.map((value) => `<option value="${escapeHtml(value)}"${value === (entity.subtype || "") ? " selected" : ""}>${escapeHtml(value || "(none)")}</option>`).join("")}
        </select></label>
        <label class="annotation-edit-field">Confidence <select class="annotation-edit-confidence">
          ${["tool-inferred", "llm-guessed", "verified"].map((value) => `<option value="${value}"${value === entity.confidence ? " selected" : ""}>${value}</option>`).join("")}
        </select></label>
        <div class="api-edit-actions">
          <button type="button" class="annotation-edit-apply">Apply</button>
          <button type="button" class="annotation-edit-close">Close</button>
        </div>
      </form>
    </dialog>
  `;
}

async function refreshListingAfterAnnotationEdit(projectId, addr) {
  await loadListingWindow(projectId, null, 0, state.listingRows.length || 80, {
    start: state.virtualListing.start,
    count: state.listingRows.length || 80,
    preserveScroll: true,
  });
  await loadNavigationEntries(projectId);
  if (addr !== null && addr !== undefined) {
    await jumpToListingAddr(projectId, addr);
  }
}

async function openAnnotationEditDialog(projectId, row) {
  const addr = row.entity_addr ?? row.addr;
  if (addr === null || addr === undefined) {
    return;
  }
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  const addrText = formatRowOffset(addr);
  let entity;
  try {
    entity = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/entities/${encodeURIComponent(addrText)}`);
  } catch (err) {
    const fallbackEntity = row.entity && typeof row.entity === "object" ? row.entity : {};
    entity = {
      addr: addrText,
      name: fallbackEntity.name || "",
      comment: fallbackEntity.comment || "",
      type: fallbackEntity.type || (row.kind === "instruction" || row.kind === "label" ? "code" : row.kind === "data" ? "data" : "unknown"),
      subtype: fallbackEntity.subtype || "",
      confidence: fallbackEntity.confidence || "tool-inferred",
    };
  }
  document.querySelector(".annotation-edit-dialog")?.remove();
  viewport.insertAdjacentHTML("beforeend", renderAnnotationEditDialog(entity));
  const dialog = document.querySelector(".annotation-edit-dialog");
  if (!dialog) return;
  dialog.querySelector(".annotation-edit-close")?.addEventListener("click", () => dialog.remove());
  dialog.querySelector(".annotation-edit-apply")?.addEventListener("click", async () => {
    await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/entities/${encodeURIComponent(addrText)}`, {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        name: dialog.querySelector(".annotation-edit-name")?.value || "",
        comment: dialog.querySelector(".annotation-edit-comment")?.value || "",
        type: dialog.querySelector(".annotation-edit-type")?.value || "unknown",
        subtype: dialog.querySelector(".annotation-edit-subtype")?.value || "",
        confidence: dialog.querySelector(".annotation-edit-confidence")?.value || "tool-inferred",
      }),
    });
    dialog.remove();
    await refreshListingAfterAnnotationEdit(projectId, addr);
  });
}

function bindListingEditors(projectId, rows) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  viewport.querySelectorAll("[data-symbol-name]").forEach((button) => {
    button.addEventListener("click", () => {
      void jumpToListingSymbol(projectId, button.dataset.symbolName || "");
    });
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        void jumpToListingSymbol(projectId, button.dataset.symbolName || "");
      }
    });
  });
  viewport.querySelectorAll("[data-app-slot-symbol]").forEach((button) => {
    button.addEventListener("click", () => {
      void selectAppSlotNavigationRef(
        projectId,
        button.dataset.appSlotSymbol || "",
        button.dataset.rowIndex ?? null,
        button.dataset.appSlotOperandIndex ?? null,
        button.dataset.appSlotAccess ?? null,
      );
    });
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        void selectAppSlotNavigationRef(
          projectId,
          button.dataset.appSlotSymbol || "",
          button.dataset.rowIndex ?? null,
          button.dataset.appSlotOperandIndex ?? null,
          button.dataset.appSlotAccess ?? null,
        );
      }
    });
  });
  viewport.querySelectorAll("[data-api-edit='1']").forEach((button, index) => {
    button.addEventListener("click", () => {
      const rowIndex = Number(button.dataset.rowIndex);
      void openApiEditDialog(projectId, rows[rowIndex]);
    });
  });
  viewport.querySelectorAll("[data-annotation-edit='1']").forEach((button) => {
    button.addEventListener("click", () => {
      const rowIndex = Number(button.dataset.rowIndex);
      void openAnnotationEditDialog(projectId, rows[rowIndex]);
    });
  });
}

async function loadListingWindow(projectId, addr = null, before = 24, after = 80, options = {}) {
  const requestSeq = ++state.virtualListing.requestSeq;
  if (options.abortPrevious && state.virtualListing.fetchAbortController) {
    state.virtualListing.fetchAbortController.abort();
  }
  const abortController = new AbortController();
  state.virtualListing.fetchAbortController = abortController;
  const params = new URLSearchParams();
  if (options.anchorCode) {
    params.set("anchor_code", String(options.anchorCode).trim());
    params.set("count", String(options.count || after || LISTING_INITIAL_ROW_WINDOW));
  } else if (options.start !== null && options.start !== undefined) {
    params.set("start", String(options.start));
    params.set("count", String(options.count || after || LISTING_INITIAL_ROW_WINDOW));
  } else if (addr !== null && addr !== undefined) {
    params.set("addr", String(addr));
    params.set("before", String(before));
    params.set("after", String(after));
  } else {
    params.set("start", "0");
    params.set("count", String(options.count || after || LISTING_INITIAL_ROW_WINDOW));
  }
  const startedAt = performance.now();
  let listing;
  try {
    listing = await fetchJson(
      `/api/projects/${encodeURIComponent(projectId)}/listing?${params.toString()}`,
      {signal: abortController.signal},
    );
  } finally {
    if (state.virtualListing.fetchAbortController === abortController) {
      state.virtualListing.fetchAbortController = null;
    }
  }
  const elapsedMs = performance.now() - startedAt;
  if (requestSeq !== state.virtualListing.requestSeq) {
    return listing;
  }
  recordListingFetchSample({
    ms: elapsedMs,
    start: listing.start || 0,
    end: listing.end || (listing.rows ? listing.rows.length : 0),
    totalRows: listing.total_rows || 0,
    generation: listing.analysis_generation || state.virtualListing.generation,
  });
  renderVirtualListingWindow(
    projectId,
    listing,
    options.preserveScroll === true,
    options.restoreAnchor ? listingAnchorScrollTop(listing, options.restoreAnchor) : null,
  );
  return listing;
}

async function loadInitialListingWindow(projectId) {
  const viewport = document.getElementById("listing-viewport");
  const count = viewport ? listingFetchCount(viewport) : LISTING_INITIAL_ROW_WINDOW;
  return loadListingWindow(projectId, 0, 0, count);
}

function normalizeJumpText(text) {
  return String(text || "")
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, "");
}

function selectBestListingRow(viewport, addr, matchText = null, stableKey = null, rowIndex = null) {
  if (!viewport) {
    return null;
  }
  if (Number.isFinite(rowIndex)) {
    const indexed = viewport.querySelector(`[data-row-index="${String(Math.floor(rowIndex))}"]`);
    if (indexed) {
      return indexed;
    }
  }
  if (stableKey) {
    const stable = viewport.querySelector(`[data-row-stable-key="${CSS.escape(stableKey)}"]`);
    if (stable) {
      return stable;
    }
  }
  const rows = Array.from(viewport.querySelectorAll(`[data-row-addr="${String(addr)}"]`));
  if (!rows.length) {
    return null;
  }
  const labelRows = rows.filter((row) => String(row.dataset.rowCode || "").trim().endsWith(":"));
  if (matchText) {
    const wanted = normalizeJumpText(matchText);
    const matched = rows.find((row) => normalizeJumpText(row.dataset.rowCode || "").includes(wanted));
    if (matched) {
      return matched;
    }
    if (labelRows.length) {
      return labelRows[0];
    }
  }
  return labelRows[0] || rows[0];
}

function scrollRowIntoView(viewport, addr, block = "center", matchText = null, stableKey = null, rowIndex = null) {
  const row = selectBestListingRow(viewport, addr, matchText, stableKey, rowIndex);
  if (!row) {
    return false;
  }
  row.scrollIntoView({block, behavior: "smooth"});
  return true;
}

function formatFileKind(entry) {
  const content = entry.content;
  if (!content) {
    throw new Error(`Indexed file is missing content metadata: ${entry.full_path}`);
  }
  if (content.kind === "amiga_hunk_executable" && content.is_executable) {
    return `HUNK executable${content.hunk_count ? ` (${content.hunk_count} hunks)` : ""}`;
  }
  if (content.kind === "iff_container") {
    return `IFF ${content.group_id || "container"} ${content.form_id || ""}`.trim();
  }
  if (content.kind) {
    return content.kind;
  }
  return "unknown";
}

function formatTargetTypeLabel(targetType) {
  return targetType.replaceAll("_", " ");
}

function renderInlineBadges(labels) {
  return labels
    .filter((label) => label)
    .map((label) => `<span class="project-badge">${escapeHtml(label)}</span>`)
    .join("");
}

function renderBootBlockTarget(bootBlock, filesystem, bootblockTargetName) {
  const details = [
    `${bootBlock.bootcode_size} bytes`,
    bootBlock.is_dos ? `${bootBlock.fs_type} boot block` : "non-DOS boot block",
    bootBlock.bootcode_has_code ? "boot code present" : "no boot code",
  ];
  if (bootBlock.rootblock_ptr) {
    details.push(`root block ${bootBlock.rootblock_ptr}`);
  }
  if (filesystem && filesystem.volume_name) {
    details.push(filesystem.volume_name);
  }
  const itemTag = bootblockTargetName ? "button" : "div";
  const itemAttributes = bootblockTargetName
    ? ` class="disk-item disk-target-button" data-project-id="${escapeHtml(bootblockTargetName)}" type="button"`
    : ` class="disk-item"`;
  return `
    <${itemTag}${itemAttributes}>
      <span class="disk-item-main">Boot Block</span>
      <span class="disk-item-meta">${renderInlineBadges(["bootblock"])} ${escapeHtml(details.join(" | "))}</span>
    </${itemTag}>
  `;
}

function renderDiskTargetMetadata(target, entry) {
  if (!entry && String(target.entry_path || "").startsWith("bootloader/")) {
    return `${renderInlineBadges([formatTargetTypeLabel(target.target_type)])} ${escapeHtml(target.binary_path || target.entry_path)}`;
  }
  if (!entry) {
    throw new Error(`Missing indexed file entry for imported target: ${target.entry_path}`);
  }
  const content = entry.content;
  if (!content) {
    throw new Error(`Target entry is missing content metadata: ${entry.full_path}`);
  }
  const details = [`${entry.size} bytes`, formatFileKind(entry)];
  if (content.library) {
    details.push(content.library.library_name);
    details.push(`v${content.library.version}`);
    if (content.library.public_function_count !== null && content.library.public_function_count !== undefined) {
      details.push(`${content.library.public_function_count} public funcs`);
    }
    if (content.library.total_lvo_count !== null && content.library.total_lvo_count !== undefined) {
      details.push(`${content.library.total_lvo_count} LVOs`);
    }
  } else if (content.resident) {
    details.push(`resident v${content.resident.version}`);
    details.push(content.resident.node_type_name);
  }
  return `${renderInlineBadges([formatTargetTypeLabel(target.target_type)])} ${escapeHtml(details.join(" | "))}`;
}

function renderDiskTargets(manifest) {
  const analysis = requireObject(manifest.analysis, "Disk analysis");
  const bootBlock = requireObject(analysis.boot_block, "Boot block analysis");
  const filesystem = analysis.filesystem || null;
  const bootblockTargetName = manifest.bootblock_target_name || null;
  const importedTargets = requireArray(manifest.imported_targets, "Imported targets");
  if (!importedTargets.length) {
    return `
      <div class="disk-list">
        ${renderBootBlockTarget(bootBlock, filesystem, bootblockTargetName)}
      </div>
    `;
  }
  const files = analysis.files === null || analysis.files === undefined
    ? []
    : requireArray(analysis.files, "Indexed disk files");
  const fileByPath = new Map(files.map((entry) => [entry.full_path, entry]));
  return `
    <div class="disk-list">
      ${renderBootBlockTarget(bootBlock, filesystem, bootblockTargetName)}
      ${importedTargets.map((target) => {
        const entry = fileByPath.get(target.entry_path);
        return `
        <button class="disk-item disk-target-button" data-project-id="${escapeHtml(target.target_name)}" type="button">
          <span class="disk-item-main">${escapeHtml(target.entry_path)}</span>
          <span class="disk-item-meta">${renderDiskTargetMetadata(target, entry)}</span>
        </button>
      `;
      }).join("")}
    </div>
  `;
}

function renderDiskFiles(files) {
  if (!files.length) {
    return '<div class="empty">No files indexed.</div>';
  }
  return `
    <div class="disk-list">
      ${files.map((entry) => `
        <div class="disk-item">
          <span class="disk-item-main">${escapeHtml(entry.full_path)}</span>
          <span class="disk-item-meta">${escapeHtml(`${entry.size} bytes | ${formatFileKind(entry)}`)}</span>
        </div>
      `).join("")}
    </div>
  `;
}

function renderDiskProject(projectData) {
  const manifest = requireObject(projectData.disk_manifest, "Disk manifest");
  const analysis = requireObject(manifest.analysis, "Disk analysis");
  const hasIndexedFiles = analysis.files !== null && analysis.files !== undefined;
  const files = hasIndexedFiles ? requireArray(analysis.files, "Indexed disk files") : null;
  const app = document.getElementById("listing-viewport");

  app.innerHTML = `
    <section class="disk-view">
      <div class="disk-tabs" role="tablist" aria-label="Disk project sections">
        <button class="disk-tab-button active" type="button" data-tab="targets" role="tab" aria-selected="true">Targets</button>
        ${files ? '<button class="disk-tab-button" type="button" data-tab="contents" role="tab" aria-selected="false">Disk Contents</button>' : ""}
      </div>
      <div class="disk-tab-panel active" data-tab-panel="targets" role="tabpanel">
        <div class="disk-section">
          <h2>Targets</h2>
          ${renderDiskTargets(manifest)}
        </div>
      </div>
      ${files ? `
      <div class="disk-tab-panel" data-tab-panel="contents" role="tabpanel" hidden>
        <div class="disk-section">
          <h2>Disk Contents</h2>
          ${renderDiskFiles(files)}
        </div>
      </div>` : ""}
    </section>
  `;

  document.querySelectorAll(".disk-target-button").forEach((button) => {
    button.addEventListener("click", () => {
      navigateToProject(button.dataset.projectId);
    });
  });

  const tabButtons = Array.from(document.querySelectorAll(".disk-tab-button"));
  const tabPanels = Array.from(document.querySelectorAll(".disk-tab-panel"));
  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const selectedTab = button.dataset.tab;
      tabButtons.forEach((item) => {
        const active = item.dataset.tab === selectedTab;
        item.classList.toggle("active", active);
        item.setAttribute("aria-selected", active ? "true" : "false");
      });
      tabPanels.forEach((panel) => {
        const active = panel.dataset.tabPanel === selectedTab;
        panel.classList.toggle("active", active);
        panel.hidden = !active;
      });
    });
  });
}

async function jumpToListingAddr(projectId, addr, matchText = null) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  if (!scrollRowIntoView(viewport, addr, "center", matchText)) {
    const visibleRows = listingVisibleRowCount(viewport);
    const count = clampListingWindowCount(visibleRows * 3);
    await loadListingWindow(projectId, addr, visibleRows, count - visibleRows);
    if (!scrollRowIntoView(viewport, addr, "center", matchText)) {
      await loadListingWindow(projectId, addr, count, count);
      scrollRowIntoView(viewport, addr, "center", matchText);
    }
  }
  const row = selectBestListingRow(viewport, addr, matchText);
  if (!row) {
    return;
  }
  row.classList.add("listing-row-focus");
  window.setTimeout(() => row.classList.remove("listing-row-focus"), 1200);
}

async function jumpToListingIndex(projectId, rowIndex, addr, matchText = null, stableKey = null) {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement) || !Number.isFinite(rowIndex)) {
    await jumpToListingAddr(projectId, addr, matchText);
    return;
  }
  const visibleRows = listingVisibleRowCount(viewport);
  const count = listingFetchCount(viewport);
  const targetIndex = Math.floor(rowIndex);
  const start = Math.max(0, targetIndex - visibleRows);
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  state.virtualListing.suppressScrollFetch = true;
  try {
    viewport.scrollTop = Math.max(0, (targetIndex * rowHeight) - Math.floor(viewport.clientHeight / 2));
    await loadListingWindow(projectId, null, 0, count, {start, count, preserveScroll: true});
    scrollRowIntoView(viewport, addr, "center", matchText, stableKey, targetIndex);
    const row = selectBestListingRow(viewport, addr, matchText, stableKey, targetIndex);
    if (!row) {
      return;
    }
    row.classList.add("listing-row-focus");
    window.setTimeout(() => row.classList.remove("listing-row-focus"), 1200);
  } finally {
    window.setTimeout(() => {
      state.virtualListing.suppressScrollFetch = false;
    }, 80);
  }
}

async function jumpToNavigationEntry(projectId, entry) {
  const matchText = entry.matchText || entry.match_text || null;
  const stableKey = entry.stableKey || entry.stable_key || null;
  const rowIndex = navigationEntryRowIndex(entry);
  if (rowIndex !== null) {
    await jumpToListingIndex(projectId, rowIndex, entry.addr, matchText, stableKey);
    return;
  }
  await jumpToListingAddr(projectId, entry.addr, matchText);
}

async function jumpToListingSymbol(projectId, symbolName) {
  const wanted = String(symbolName || "").replace(/:$/, "");
  if (!wanted) {
    return;
  }
  const groups = await ensureNavigationEntries(projectId);
  const labels = groups.labels || [];
  const target = labels.find((entry) => String(entry.summary || entry.matchText || "").replace(/:$/, "") === wanted);
  if (!target) {
    return;
  }
  await jumpToListingIndex(
    projectId,
    target.rowIndex ?? target.row_index,
    target.addr,
    target.matchText || target.match_text || `${wanted}:`,
    target.stableKey || target.stable_key || null,
  );
}

async function renderProject(projectId) {
  if (state.homeDropCleanup) {
    state.homeDropCleanup();
    state.homeDropCleanup = null;
  }
  const app = document.getElementById("app");
  app.innerHTML = `
    <section class="page page-project">
      <div class="project-bar">
        <div class="project-title" id="project-title">${escapeHtml(projectId)}</div>
        <div class="project-details" id="project-details">Loading project...</div>
        <div class="analysis-status" id="analysis-status" aria-live="polite" hidden></div>
        <div class="project-actions">
          <button id="navigation-back" type="button" title="Back">Back</button>
          <button id="navigation-forward" type="button" title="Forward">Forward</button>
          <button id="open-navigation" type="button" title="Navigate">Navigate</button>
          <button id="open-stats" type="button" title="Stats">Stats</button>
          <button id="open-repro" type="button" title="Repro">Repro</button>
          <button id="exit-project" type="button">Project</button>
        </div>
      </div>
      <div class="project-workspace">
        <div class="listing-viewport" id="listing-viewport" tabindex="0">
          ${renderProgressOverlay({
            job_kind: "listing",
            phase_id: "build_session",
            progress_mode: "indeterminate",
            progress_current: 0,
            progress_total: 0,
            progress_percent: 0,
          }, "Loading project")}
        </div>
      </div>
    </section>
  `;

  const token = ++state.loadingToken;
  state.project = projectId;
  state.listingRows = [];
  state.virtualListing.start = 0;
  state.virtualListing.end = 0;
  state.virtualListing.totalRows = 0;
  state.virtualListing.generation = null;
  state.virtualListing.requestSeq = 0;
  state.virtualListing.pendingWindow = null;
  state.virtualListing.inFlightWindow = null;
  if (state.virtualListing.scrollTimer !== null) {
    window.clearTimeout(state.virtualListing.scrollTimer);
    state.virtualListing.scrollTimer = null;
  }
  if (state.virtualListing.scrollRaf !== null) {
    window.cancelAnimationFrame(state.virtualListing.scrollRaf);
    state.virtualListing.scrollRaf = null;
  }
  if (state.virtualListing.fetchAbortController) {
    state.virtualListing.fetchAbortController.abort();
    state.virtualListing.fetchAbortController = null;
  }
  state.navigation.overlayOpen = false;
  state.navigation.entries = null;
  state.navigation.generation = null;
  state.navigation.appSlotSymbol = null;
  state.navigation.originEntry = null;
  state.navigation.currentPreviewEntry = null;
  state.navigation.currentLocation = null;
  state.navigation.historyBack = [];
  state.navigation.historyForward = [];
  state.stats.overlayOpen = false;
  state.stats.selectedTab = "fetch";
  state.stats.fetchSamples = [];
  state.reproduction.panelOpen = false;
  state.reproduction.report = null;
  state.reproduction.reportKey = null;
  state.reproduction.job = null;
  state.reproduction.selectedIssueEntry = null;
  setAnalysisStatus("");
  renderStatsOverlay();
  renderReproPanel();
  renderNavigationOverlay();
  fetchJson(`/api/projects/${encodeURIComponent(projectId)}/open`, {method: "POST"})
    .catch(() => null);
  try {
    const projectData = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}`);
    if (token !== state.loadingToken) {
      return;
    }
    state.projectData = projectData;
    state.reproduction.report = projectData.reproduction || null;
    state.reproduction.reportKey = reproductionReportKey(state.reproduction.report);
    const detailsText = formatProjectDetails(projectData);
    const detailsNode = document.getElementById("project-details");
    const titleNode = document.getElementById("project-title");
    detailsNode.innerHTML = renderProjectBadges(projectData.project, projectData);
    const titleTooltip = projectData.project.source_path
      || projectData.project.binary_path
      || detailsText;
    titleNode.title = titleTooltip;
    document.getElementById("exit-project").addEventListener("click", () => {
      const parentProjectId = projectData.project.parent_project_id;
      if (parentProjectId) {
        navigateToProject(parentProjectId);
        return;
      }
      window.history.pushState({}, "", "/");
      void route();
    });
    document.getElementById("open-navigation")?.addEventListener("click", () => {
      void openNavigationOverlay();
    });
    document.getElementById("open-stats")?.addEventListener("click", openStatsOverlay);
    document.getElementById("open-repro")?.addEventListener("click", () => {
      void openReproPanel();
    });
    document.getElementById("navigation-back")?.addEventListener("click", () => {
      void navigateHistory("back");
    });
    document.getElementById("navigation-forward")?.addEventListener("click", () => {
      void navigateHistory("forward");
    });

    if (projectData.project.kind === "disk") {
      renderDiskProject(projectData);
      return;
    }

    if (!projectData.project.ready) {
      document.getElementById("listing-viewport").innerHTML =
        '<div class="empty listing-empty">No disassembly available.</div>';
      return;
    }

    const job = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/listing/open`, {
      method: "POST",
    });
    if (token !== state.loadingToken) {
      return;
    }

    const jobState = await waitForAsyncJob(
      (jobId) => `/api/projects/${encodeURIComponent(projectId)}/listing/status?job_id=${encodeURIComponent(jobId)}`,
      job,
      token,
      (currentJob) => setViewportOverlay(renderProgressOverlay(currentJob)),
    );
    if (state.virtualListing.generation && state.virtualListing.generation !== "full") {
      await refreshListingAtCurrentAddressAnchor(projectId, token);
    } else if (state.virtualListing.generation !== "full") {
      setViewportOverlay(loadingRowsOverlay());
      await loadInitialListingWindow(projectId);
    }
    await loadNavigationEntries(projectId);
    if (token !== state.loadingToken) {
      return;
    }
    renderVirtualListingWindow(projectId, {
      rows: state.listingRows,
      start: state.virtualListing.start,
      end: state.virtualListing.end,
      total_rows: state.virtualListing.totalRows,
      analysis_generation: state.virtualListing.generation,
    }, true);
    if (jobState.visible_generation === "full") {
      void pollReproductionReport(projectId, token);
      setAnalysisStatus("Full analysis ready", "ready", 2000);
    }
  } catch (error) {
    if (String(error.message || error) === "stale") {
      return;
    }
    if (token !== state.loadingToken) {
      return;
    }
    document.getElementById("project-details").textContent = "Load failed";
    document.getElementById("listing-viewport").innerHTML = renderErrorOverlay(String(error.message || error));
  }
}

function navigateToProject(projectId) {
  window.history.pushState({}, "", projectPath(projectId));
  void route();
}

async function route() {
  const projectId = currentProjectId();
  try {
    if (projectId) {
      await renderProject(projectId);
    } else {
      await renderHome();
    }
  } catch (error) {
    const app = document.getElementById("app");
    app.innerHTML = `<div class="page"><div class="error">${escapeHtml(String(error.message || error))}</div></div>`;
  }
}

window.addEventListener("popstate", () => {
  void route();
});

function beginListingColumnResize(event) {
  let handle = event.target instanceof HTMLElement
    ? event.target.closest("[data-listing-column-resize]")
    : null;
  let column = handle instanceof HTMLElement ? handle.dataset.listingColumnResize : null;
  if (!(handle instanceof HTMLElement)) {
    handle = Array.from(document.querySelectorAll("[data-listing-column-resize]"))
      .find((candidate) => {
        if (!(candidate instanceof HTMLElement)) {
          return false;
        }
        const rect = candidate.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        return event.clientY >= rect.top
          && event.clientY <= rect.bottom
          && Math.abs(event.clientX - centerX) <= 10;
      }) || null;
    column = handle instanceof HTMLElement ? handle.dataset.listingColumnResize : null;
  }
  if (!(handle instanceof HTMLElement)) {
    const rowLayer = document.querySelector(".listing-row-layer");
    if (rowLayer instanceof HTMLElement) {
      const rect = rowLayer.getBoundingClientRect();
      const boundaries = [
        ["offset", rect.left + state.listingColumns.offset],
        ["bytes", rect.left + state.listingColumns.offset + state.listingColumns.bytes],
        ["code", rect.left + state.listingColumns.offset + state.listingColumns.bytes + state.listingColumns.code],
      ];
      const nearest = boundaries.find(([_column, x]) => Math.abs(event.clientX - x) <= 16);
      if (nearest && event.clientY >= rect.top && event.clientY <= rect.bottom) {
        column = nearest[0];
      }
    }
  }
  if (state.listingColumns.drag) {
    return false;
  }
  if (!column || !Object.prototype.hasOwnProperty.call(LISTING_COLUMN_MIN_WIDTHS, column)) {
    return false;
  }
  event.preventDefault();
  state.listingColumns.drag = {
    column,
    startX: event.clientX,
    startWidth: state.listingColumns[column],
  };
  document.body.classList.add("listing-column-resizing");
  return true;
}

function updateListingColumnResize(event) {
  const drag = state.listingColumns.drag;
  if (!drag) {
    return false;
  }
  const minWidth = LISTING_COLUMN_MIN_WIDTHS[drag.column] || 48;
  state.listingColumns[drag.column] = Math.max(minWidth, drag.startWidth + event.clientX - drag.startX);
  applyListingColumnWidths();
  return true;
}

function endListingColumnResize() {
  if (!state.listingColumns.drag) {
    return false;
  }
  state.listingColumns.drag = null;
  document.body.classList.remove("listing-column-resizing");
  return true;
}

document.addEventListener("pointerdown", beginListingColumnResize);
document.addEventListener("pointermove", updateListingColumnResize);
document.addEventListener("pointerup", endListingColumnResize);
document.addEventListener("mousedown", beginListingColumnResize);
document.addEventListener("mousemove", updateListingColumnResize);
document.addEventListener("mouseup", endListingColumnResize);

document.addEventListener("keydown", (event) => {
  if (!state.project) {
    return;
  }
  const symbolLink = event.target instanceof HTMLElement
    ? event.target.closest("[data-symbol-name]")
    : null;
  if (symbolLink && event.key === "Enter") {
    event.preventDefault();
    void jumpToListingSymbol(state.project, symbolLink.dataset.symbolName || "");
    return;
  }
  if (event.altKey && !event.shiftKey && !event.ctrlKey && !event.metaKey && event.key === "ArrowLeft") {
    event.preventDefault();
    void navigateHistory("back");
    return;
  }
  if (event.altKey && !event.shiftKey && !event.ctrlKey && !event.metaKey && event.key === "ArrowRight") {
    event.preventDefault();
    void navigateHistory("forward");
    return;
  }
  if (state.navigation.overlayOpen && event.key === "Escape") {
    event.preventDefault();
    closeNavigationOverlay();
    return;
  }
  if (state.stats.overlayOpen && event.key === "Escape") {
    event.preventDefault();
    closeStatsOverlay();
    return;
  }
  if (state.reproduction.panelOpen && event.key === "Escape") {
    event.preventDefault();
    closeReproPanel();
    return;
  }
  if (isEditableTarget(event.target)) {
    return;
  }
  if (!state.navigation.overlayOpen) {
    if (!event.altKey && !event.ctrlKey && !event.metaKey && (event.key === "n" || event.key === "N")) {
      event.preventDefault();
      void openNavigationOverlay();
      return;
    }
    if (!event.altKey && !event.ctrlKey && !event.metaKey && (event.key === "s" || event.key === "S")) {
      event.preventDefault();
      openStatsOverlay();
      return;
    }
    if (!event.altKey && !event.ctrlKey && !event.metaKey && event.key === "PageDown") {
      event.preventDefault();
      scrollListingViewport(state.project, "down");
      return;
    }
    if (!event.altKey && !event.ctrlKey && !event.metaKey && event.key === "PageUp") {
      event.preventDefault();
      scrollListingViewport(state.project, "up");
      return;
    }
    if (!event.altKey && !event.ctrlKey && !event.metaKey && event.key === "Home") {
      event.preventDefault();
      scrollListingViewport(state.project, "home");
      return;
    }
    if (!event.altKey && !event.ctrlKey && !event.metaKey && event.key === "End") {
      event.preventDefault();
      scrollListingViewport(state.project, "end");
    }
    return;
  }
  if (event.key === "Enter") {
    event.preventDefault();
    const entry = currentNavigationEntries()[state.navigation.selectedIndex];
    if (navigationEntryHasRefs(entry)) {
      void activateNavigationEntry(entry);
      return;
    }
    void activateNavigationEntry(entry).then(() => closeNavigationOverlay());
    return;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    void moveNavigationSelection(1);
    return;
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    void moveNavigationSelection(-1);
    return;
  }
  if (event.key === "PageDown") {
    event.preventDefault();
    void moveNavigationSelection(10);
    return;
  }
  if (event.key === "PageUp") {
    event.preventDefault();
    void moveNavigationSelection(-10);
    return;
  }
  if (event.key === "Home") {
    event.preventDefault();
    state.navigation.selectedIndex = 0;
    renderNavigationOverlay();
    syncNavigationListFocus();
    void previewNavigationEntry(currentNavigationEntries()[0]);
    return;
  }
  if (event.key === "End") {
    event.preventDefault();
    const entries = currentNavigationEntries();
    state.navigation.selectedIndex = Math.max(entries.length - 1, 0);
    renderNavigationOverlay();
    syncNavigationListFocus();
    void previewNavigationEntry(entries[state.navigation.selectedIndex]);
  }
}, true);

document.addEventListener("keyup", (event) => {
  if (state.project && state.navigation.overlayOpen && event.key === "Escape") {
    event.preventDefault();
    closeNavigationOverlay();
  }
}, true);

void route();
