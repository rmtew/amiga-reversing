const WEB_APP_CONTRACT_VERSION = 2;
const WEB_APP_CONTRACT_HEADER = "X-Amiga-Web-App-Contract";

const state = {
  project: null,
  projectData: null,
  loadingToken: 0,
  homeDropCleanup: null,
  homeView: "projects",
  diskBrowser: {
    payload: null,
    loading: false,
    error: null,
    requestKey: null,
    requestToken: 0,
    view: "entries",
    urlForPath: null,
  },
  corpus: {
    features: null,
    featuresLoading: false,
    featuresError: null,
    feature: "",
    group: "",
    platform: "",
    q: "",
    showTargetFacts: false,
    results: [],
    resultOffset: 0,
    resultLimit: 40,
    resultsHasMore: false,
    resultsLoading: false,
    resultsError: null,
    resultsLoaded: false,
    resultsQueryKey: "",
    resultRequestToken: 0,
    targetRequestToken: 0,
    selectedTargetId: null,
    xrefs: [],
    xrefOffset: 0,
    xrefLimit: 120,
    xrefsHasMore: false,
    selectedXrefId: null,
    snippet: null,
    snippetLoading: false,
    snippetError: null,
    variants: null,
    variantsLoading: false,
    variantsError: null,
    variantDiff: null,
    variantDiffLoading: false,
    variantDiffError: null,
    importMenuTargetId: null,
  },
  pendingCorpusFocus: null,
  uiPreferences: {
    payload: null,
    saveTimer: null,
    restoring: false,
    initialApplied: false,
  },
  typeCatalog: null,
  listingRows: [],
  listingSelection: null,
  virtualListing: {
    start: 0,
    end: 0,
    totalRows: 0,
    rowHeight: 22,
    generation: null,
    requestSeq: 0,
    scrollRaf: null,
    pendingWindow: null,
    inFlightWindow: null,
    fetchAbortController: null,
    suppressScrollFetch: false,
    scrollSuppressionToken: 0,
  },
  listingColumns: {
    offset: 64,
    runtime: 72,
    bytes: 180,
    code: 520,
    drag: null,
  },
  navigation: {
    overlayOpen: false,
    selectedClass: "typed-data",
    selectedIndex: 0,
    appSlotSymbol: null,
    labelSymbol: null,
    equateSymbol: null,
    entries: null,
    equateNameCacheRows: null,
    equateNameCache: null,
    appSlotAnalysis: null,
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
  manualReview: {
    panelOpen: false,
    filters: {
      kind: "",
      confidence: "",
      state: "open",
      section: "",
      source: "",
      range: "",
    },
  },
  manualEdit: {
    inFlight: false,
    pendingRanges: [],
    savedFlashRanges: [],
    savedFlashTimer: null,
  },
  parameterSession: null,
  commandPalette: {
    open: false,
    query: "",
    actions: [],
    selectedIndex: 0,
    loading: false,
    global: false,
    editor: null,
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
const LISTING_OVERSCAN_SCREENS = 4;
const STATS_MAX_FETCH_SAMPLES = 240;
const LISTING_COLUMN_MIN_WIDTHS = {
  offset: 48,
  runtime: 56,
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
const LABEL_ACCESS_ORDER = ["definition", "reference"];
const LABEL_ACCESS_LABELS = {
  definition: "D",
  reference: "R",
};
const CORPUS_GROUPS = [
  {id: "", label: "All"},
  {id: "os", label: "OS calls"},
  {id: "hardware", label: "Hardware"},
  {id: "devices", label: "Devices"},
  {id: "copper", label: "Copper"},
  {id: "display", label: "Display"},
  {id: "runtime", label: "Runtime"},
  {id: "app_slots", label: "App slots"},
  {id: "platform_types", label: "Types"},
  {id: "symbols", label: "Symbols"},
  {id: "data", label: "Data"},
  {id: "diagnostics", label: "Diagnostics"},
];
const CORPUS_GROUP_PREFIXES = {
  os: ["os_call", "os:"],
  hardware: ["hardware:", "hardware_register:", "value_domain:amiga.custom", "value_domain:amiga.cia"],
  devices: ["device:", "device_call"],
  copper: ["data:copper_list", "hardware:custom/copper", "value_domain:amiga.custom.copper"],
  display: ["display:", "hardware:custom/display", "value_domain:amiga.custom.display_config"],
  runtime: ["runtime:"],
  app_slots: [
    "app_slot:",
    "app_slot_region:",
    "app_slot_region_source:",
    "app_slot_field_path:",
    "app_slot_field_gap:",
    "app_slot_field_gap_path:",
  ],
  platform_types: [
    "platform_typed_access:",
    "platform_typed_access_struct:",
    "platform_typed_access_owner:",
    "platform_unresolved_typed_access:",
    "platform_unresolved_typed_access_struct:",
    "platform_prefix_extension_struct:",
    "platform_prefix_extension_candidate:",
    "platform_field:",
    "platform_struct_field:",
    "platform_field_expr:",
    "typed_base_unresolved_field",
    "struct:",
  ],
  symbols: ["label:", "xref:label", "xref:segment"],
  data: ["data:", "xref:data"],
  diagnostics: ["diagnostic:"],
};

const JOB_PHASE_LABELS = {
  listing_artifact: {
    queued: "Queued",
    build_c_artifact: "Building analysis",
    cache_artifact: "Caching listing",
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
  const response = await fetch(url, withWebAppContractHeaders(options));
  const payload = await response.json();
  assertWebAppContract(payload);
  if (!payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload.data;
}

function withWebAppContractHeaders(options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set(WEB_APP_CONTRACT_HEADER, String(WEB_APP_CONTRACT_VERSION));
  return {...options, headers};
}

function assertWebAppContract(payload) {
  const serverVersion = payload?.web_app_contract_version;
  if (serverVersion === WEB_APP_CONTRACT_VERSION) {
    return;
  }
  throw new Error(
    `Server/client version mismatch; hard refresh required (client=${WEB_APP_CONTRACT_VERSION}, server=${serverVersion ?? "missing"})`,
  );
}

async function verifyWebAppContract() {
  await fetchJson("/api/app-contract");
}

function isAbortError(error) {
  return Boolean(error && (
    error.name === "AbortError" ||
    String(error.message || error).toLowerCase().includes("aborted")
  ));
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
    const origin = formatProjectOrigin(projectData.project.origin);
    if (origin) {
      details.push(origin);
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
  const origin = formatProjectOrigin(projectData.project.origin);
  if (origin) {
    details.push(origin);
  }
  if (!projectData.project.output_path) {
    details.push("No disassembly output");
  }
  if (!projectData.project.ready) {
    details.push("No executable loaded");
  }
  return details.join(" | ");
}

function formatProjectOrigin(origin) {
  if (!origin || !origin.kind) {
    return "";
  }
  if (origin.kind === "corpus_file" || origin.kind === "corpus_disk") {
    const label = origin.in_image_path || origin.member_name || origin.display_name || origin.corpus_target_id;
    return label ? `corpus=${label}` : "corpus";
  }
  if (origin.kind === "user_upload") {
    return origin.filename ? `upload=${origin.filename}` : "upload";
  }
  if (origin.kind === "disk_child") {
    return origin.entry_path ? `disk-entry=${origin.entry_path}` : "disk child";
  }
  return String(origin.kind).replaceAll("_", " ");
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
    badges.push(reviewStateBadge(project));
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
  if (project.origin && String(project.origin.kind || "").startsWith("corpus_")) {
    badges.push({
      label: "corpus",
      title: project.origin.display_name || project.origin.in_image_path || project.origin.corpus_target_id || "Corpus import",
    });
  }
  return badges;
}

function reviewStateBadge(project) {
  const reviewState = project.review_state || "clear";
  const items = Array.isArray(project.review_items) ? project.review_items : [];
  const openItems = items.filter((item) => item && item.state === "open");
  const blockers = openItems.filter((item) => item.review_blocker === true);
  if (reviewState === "blocked") {
    return {
      label: "Blocked",
      className: "project-badge-review-blocked",
      title: `Review blocked by ${blockers.length || openItems.length} open item(s)`,
    };
  }
  if (reviewState === "needs_review") {
    return {
      label: "Needs review",
      className: "project-badge-review-needs-review",
      title: `Manual review has ${openItems.length} open item(s)`,
    };
  }
  return {
    label: "Review clear",
    className: "project-badge-review-clear",
    title: "No open manual review items",
  };
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
  if (report.refreshing || isRunningReproductionJob(report.active_job)) {
    return {label: "Repro running", className: "project-badge-repro-stale", title: "Reproduction is running for the current listing"};
  }
  if (report.stale) {
    return {label: "Needs repro", className: "project-badge-repro-stale", title: "Current listing has not been reproduced yet"};
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

function isRunningReproductionJob(job) {
  return Boolean(
    job
    && job.job_kind === "reproduction"
    && (job.status === "queued" || job.status === "building")
  );
}

function refreshProjectBadges() {
  const detailsNode = document.getElementById("project-details");
  if (!detailsNode || !state.projectData) {
    return;
  }
  detailsNode.innerHTML = renderProjectBadges(state.projectData.project, state.projectData);
}

async function refreshProjectPayload(projectId, token = null) {
  const projectData = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}`);
  if (token !== null && token !== state.loadingToken) {
    return null;
  }
  if (state.project !== projectId) {
    return null;
  }
  state.projectData = projectData;
  state.reproduction.report = projectData.reproduction || null;
  state.reproduction.reportKey = reproductionReportKey(state.reproduction.report);
  refreshProjectBadges();
  renderManualReviewPanel();
  renderReproPanel();
  return projectData;
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

function dispatchAppEvent(name, detail = {}) {
  window.__amigaEventSeq = (window.__amigaEventSeq || 0) + 1;
  window.__amigaLastEvents = window.__amigaLastEvents || {};
  const eventDetail = {...detail, seq: window.__amigaEventSeq};
  window.__amigaLastEvents[name] = eventDetail;
  window.dispatchEvent(new CustomEvent(name, {detail: eventDetail}));
}

function getJobPhaseLabel(job) {
  const jobKind = String(job.job_kind || "").trim();
  const phaseId = String(job.phase_id || "").trim();
  const labels = JOB_PHASE_LABELS[jobKind];
  if (!labels) {
    return jobKind ? jobKind.replaceAll("_", " ") : "Working";
  }
  const label = labels[phaseId];
  if (!label) {
    return phaseId ? phaseId.replaceAll("_", " ") : "Working";
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
  state.stats.fetchSamples.push({
    ...sample,
    ms: sample.totalMs ?? sample.ms ?? 0,
  });
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
  if (!job || job.job_kind !== "listing_artifact") {
    return "";
  }
  if (job.status === "failed") {
    return "Analysis build failed";
  }
  const labels = JOB_PHASE_LABELS[job.job_kind] || {};
  const phase = labels[job.phase_id] || labels[job.status] || "Analyzing";
  return `Building analysis: ${phase}`;
}

function renderAnalysisStatus() {
  const node = document.getElementById("analysis-status");
  if (!node) {
    return;
  }
  const text = state.analysisStatus.text || "";
  node.hidden = text === "";
  node.className = `analysis-status analysis-status-${state.analysisStatus.state || "idle"}`;
  const spinner = state.analysisStatus.state === "running"
    ? '<span class="analysis-status-spinner" aria-hidden="true"></span>'
    : "";
  node.innerHTML = text
    ? `${spinner}<span>${escapeHtml(text)}</span>`
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
  const latestBreakdown = latest
    ? `total ${formatMs(latest.ms)}; queue ${formatMs(latest.queueMs || 0)}, fetch ${formatMs(latest.fetchMs || 0)}, render ${formatMs(latest.renderMs || 0)}`
    : "";
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
        ${latest ? `Latest: ${latestBreakdown} for rows ${latest.start}-${latest.end} (${escapeHtml(latest.generation || "unknown")})` : "Latest: none"}
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
  if (isRunningReproductionJob(report?.active_job)) {
    state.reproduction.job = report.active_job;
  } else if (state.reproduction.job?.job_kind === "reproduction") {
    state.reproduction.job = null;
  }
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
    refreshing: Boolean(report.refreshing),
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

async function pollReproductionReport(projectId, token, attempts = 120) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (token !== state.loadingToken) {
      return;
    }
    const report = await refreshReproductionReport(projectId);
    if (token !== state.loadingToken) {
      return;
    }
    if (isRunningReproductionJob(report?.active_job)) {
      let finalReport = null;
      try {
        finalReport = await followReproductionJob(projectId, report.active_job, token);
      } catch (error) {
        if (String(error.message || error) === "stale") {
          return;
        }
        console.warn("Background reproduction failed", error);
        finalReport = await refreshReproductionReport(projectId);
      }
      if (finalReport?.status === "exact") {
        setAnalysisStatus("Reproduction exact", "ready", 2500);
      } else if (finalReport?.status && finalReport.status !== "not_ready") {
        setAnalysisStatus("Reproduction needs edits", "failed", 2500);
      }
      return;
    }
    if (report && report.status !== "not_ready" && !report.stale && !report.refreshing) {
      return;
    }
    await sleep(1000);
  }
}

function reproductionStatusText(report) {
  if (!report) {
    return "Not ready";
  }
  if (report.refreshing || isRunningReproductionJob(report.active_job)) {
    return "Running";
  }
  if (report.stale) {
    return "Needs repro";
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

function reviewItems() {
  const items = Array.isArray(state.projectData?.project?.review_items)
    ? state.projectData.project.review_items
    : [];
  return items.map((item, index) => ({
    ...item,
    review_index: index,
  }));
}

function reviewItemAddress(item) {
  const addr = Number(item?.start ?? item?.addr);
  return Number.isFinite(addr) ? addr : null;
}

function reviewItemEnd(item) {
  const end = Number(item?.end);
  return Number.isFinite(end) ? end : null;
}

function reviewItemSection(item) {
  const hunk = item?.hunk ?? item?.section_index;
  return Number.isInteger(hunk) ? `h${hunk}` : "";
}

function reviewItemSource(item) {
  return String(item?.source || item?.stronger_source || item?.record || "");
}

function reviewItemRangeText(item) {
  const addr = reviewItemAddress(item);
  const end = reviewItemEnd(item);
  if (!Number.isFinite(addr)) {
    return "target";
  }
  const section = reviewItemSection(item);
  const prefix = section ? `${section}:` : "";
  if (Number.isFinite(end) && end !== addr + 1) {
    return `${prefix}${formatRowOffset(addr)}..${formatRowOffset(end)}`;
  }
  return `${prefix}${formatRowOffset(addr)}`;
}

function reviewItemSeverityRank(item) {
  if (item?.state !== "open") {
    return 4;
  }
  if (item?.review_blocker === true) {
    return 0;
  }
  const kind = String(item?.kind || "");
  if (kind.includes("mismatch") || kind.includes("conflict") || kind.includes("malformed")) {
    return 1;
  }
  if (kind.includes("unreconciled") || kind.includes("suspicious") || kind.includes("orphan")) {
    return 2;
  }
  return 3;
}

function sortedReviewItems(items = reviewItems()) {
  return [...items].sort((left, right) => {
    const severity = reviewItemSeverityRank(left) - reviewItemSeverityRank(right);
    if (severity !== 0) {
      return severity;
    }
    const leftScope = String(left.scope || "");
    const rightScope = String(right.scope || "");
    if (leftScope !== rightScope) {
      return leftScope.localeCompare(rightScope);
    }
    const leftAddr = reviewItemAddress(left);
    const rightAddr = reviewItemAddress(right);
    if (Number.isFinite(leftAddr) && Number.isFinite(rightAddr) && leftAddr !== rightAddr) {
      return leftAddr - rightAddr;
    }
    return String(left.item_id || "").localeCompare(String(right.item_id || ""));
  });
}

function reviewFilterOptions(items, field) {
  const values = new Set();
  items.forEach((item) => {
    let value = "";
    if (field === "section") {
      value = reviewItemSection(item);
    } else if (field === "source") {
      value = reviewItemSource(item);
    } else if (field === "confidence") {
      value = String(item.review_confidence || "");
    } else {
      value = String(item[field] || "");
    }
    if (value) {
      values.add(value);
    }
  });
  return [...values].sort((left, right) => left.localeCompare(right));
}

function reviewItemMatchesFilters(item) {
  const filters = state.manualReview.filters;
  if (filters.kind && String(item.kind || "") !== filters.kind) {
    return false;
  }
  if (filters.confidence && String(item.review_confidence || "") !== filters.confidence) {
    return false;
  }
  if (filters.state && String(item.state || "") !== filters.state) {
    return false;
  }
  if (filters.section && reviewItemSection(item) !== filters.section) {
    return false;
  }
  if (filters.source && reviewItemSource(item) !== filters.source) {
    return false;
  }
  if (filters.range) {
    const haystack = [
      reviewItemRangeText(item),
      item.item_id,
      item.message,
      item.kind,
    ].map((value) => String(value || "").toLowerCase()).join(" ");
    if (!haystack.includes(filters.range.toLowerCase())) {
      return false;
    }
  }
  return true;
}

function renderReviewSelect(name, label, values, value) {
  const options = [`<option value="">All</option>`]
    .concat(values.map((option) => (
      `<option value="${escapeHtml(option)}"${option === value ? " selected" : ""}>${escapeHtml(option)}</option>`
    )));
  return `
    <label>${escapeHtml(label)}
      <select data-review-filter="${escapeHtml(name)}">${options.join("")}</select>
    </label>
  `;
}

function renderReviewSuggestedActions(item) {
  const actions = reviewItemCatalogActions(item).filter((action) => action.enabled !== false);
  if (!actions.length) {
    return "";
  }
  return `
    <div class="review-actions">
      ${actions.map((action) => (
        `<button type="button" data-review-action="${escapeHtml(action.action)}" data-catalog-action-id="${escapeHtml(action.action_id)}" data-review-index="${item.review_index}"${action.parameters?.seed_kind ? ` data-seed-kind="${escapeHtml(action.parameters.seed_kind)}"` : ""}${action.parameters?.data_role ? ` data-data-role="${escapeHtml(action.parameters.data_role)}"` : ""}${action.parameters?.unit ? ` data-unit="${escapeHtml(action.parameters.unit)}"` : ""}${action.parameters?.disposition ? ` data-disposition="${escapeHtml(action.parameters.disposition)}"` : ""}>${escapeHtml(action.label)}</button>`
      )).join("")}
    </div>
  `;
}

function reviewItemCatalogActions(item) {
  return Array.isArray(item?.catalog_actions) ? item.catalog_actions : [];
}

function renderReviewItem(item) {
  const blocker = item.review_blocker === true ? '<span class="review-pill blocker">Blocker</span>' : "";
  const changed = item.changed_since_resolution === true ? '<span class="review-pill changed">Changed</span>' : "";
  const acknowledged = item.acknowledged === true ? '<span class="review-pill">Acknowledged</span>' : "";
  const statePill = `<span class="review-pill">${escapeHtml(String(item.state || "open"))}</span>`;
  const confidence = item.review_confidence
    ? `<span class="review-pill">${escapeHtml(String(item.review_confidence))}</span>`
    : "";
  const source = reviewItemSource(item);
  return `
    <div class="review-item" data-review-index="${item.review_index}">
      <div class="review-item-main">
        <button type="button" class="review-item-title" data-review-navigate="${item.review_index}">
          <span>${escapeHtml(String(item.kind || "review_item").replaceAll("_", " "))}</span>
          <span>${escapeHtml(reviewItemRangeText(item))}</span>
        </button>
        <div class="review-message">${escapeHtml(String(item.message || item.item_id || ""))}</div>
        ${source ? `<div class="review-source">${escapeHtml(source)}</div>` : ""}
        ${renderReviewSuggestedActions(item)}
      </div>
      <div class="review-pills">${blocker}${acknowledged}${changed}${statePill}${confidence}</div>
    </div>
  `;
}

function renderManualReviewPanel() {
  const existing = document.getElementById("review-overlay");
  if (!state.manualReview.panelOpen) {
    existing?.remove();
    return;
  }
  const app = document.getElementById("app");
  if (!app) {
    return;
  }
  const items = sortedReviewItems();
  const visible = items.filter(reviewItemMatchesFilters);
  const filters = state.manualReview.filters;
  const html = `
    <div class="review-overlay" id="review-overlay">
      <div class="review-panel">
        <div class="review-header">
          <div class="review-title">Manual Review</div>
          <button type="button" class="review-close" data-review-close="1">Close</button>
        </div>
        <div class="review-summary">${visible.length} of ${items.length} items</div>
        <div class="review-filters">
          ${renderReviewSelect("kind", "Kind", reviewFilterOptions(items, "kind"), filters.kind)}
          ${renderReviewSelect("confidence", "Confidence", reviewFilterOptions(items, "confidence"), filters.confidence)}
          ${renderReviewSelect("state", "State", reviewFilterOptions(items, "state"), filters.state)}
          ${renderReviewSelect("section", "Section", reviewFilterOptions(items, "section"), filters.section)}
          ${renderReviewSelect("source", "Source", reviewFilterOptions(items, "source"), filters.source)}
          <label>Range
            <input type="search" data-review-filter="range" value="${escapeHtml(filters.range)}" placeholder="addr, kind, text">
          </label>
        </div>
        <div class="review-list">
          ${visible.length ? visible.map(renderReviewItem).join("") : '<div class="empty">No review items match.</div>'}
        </div>
      </div>
    </div>
  `;
  if (existing) {
    existing.outerHTML = html;
  } else {
    app.insertAdjacentHTML("beforeend", html);
  }
  bindManualReviewPanel();
}

function openManualReviewPanel() {
  state.manualReview.panelOpen = true;
  renderManualReviewPanel();
}

function closeManualReviewPanel() {
  state.manualReview.panelOpen = false;
  renderManualReviewPanel();
}

async function navigateToReviewItem(item) {
  if (!state.project || !item) {
    return;
  }
  const addr = reviewItemAddress(item);
  if (!Number.isFinite(addr)) {
    return;
  }
  const origin = captureViewportAnchor();
  let jumped = false;
  const sectionIndex = Number(item?.hunk ?? item?.section_index);
  if (Number.isInteger(sectionIndex)) {
    jumped = await jumpToListingSectionOffset(state.project, sectionIndex, addr);
  } else {
    jumped = await jumpToListingAddr(state.project, addr);
  }
  const current = captureViewportAnchor();
  if (jumped && origin && current && !navigationEntriesSameLocation(origin, current)) {
    state.navigation.historyBack.push(origin);
    state.navigation.historyForward = [];
    state.navigation.currentLocation = current;
  }
}

function reviewItemSeedPayload(item, button) {
  const addr = reviewItemAddress(item);
  if (!Number.isFinite(addr)) {
    return null;
  }
  const end = reviewItemEnd(item);
  const seedKind = button.dataset.seedKind || "data";
  const seed = {
    seed_id: `ui-${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 8)}`,
    kind: seedKind,
    mode: "required",
    hunk: Number.isInteger(item.hunk) ? item.hunk : 0,
    addr,
  };
  if (Number.isFinite(end) && end > addr) {
    seed.end = end;
  }
  if (seedKind === "data") {
    if (button.dataset.dataRole) {
      seed.data_role = button.dataset.dataRole;
    }
    if (button.dataset.unit) {
      seed.unit = button.dataset.unit;
    }
  }
  return seed;
}

function reviewResolutionPayload(item, disposition) {
  return {
    resolution_id: `ui-${Date.now().toString(36)}-${Math.random().toString(16).slice(2, 8)}`,
    item_id: String(item.item_id || ""),
    evidence_fingerprint: String(item.evidence_fingerprint || ""),
    disposition: disposition || "acknowledged",
  };
}

async function postManualReviewAction(payload, options = {}) {
  if (!state.project) {
    return null;
  }
  const result = await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/manual-actions`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });
  if (options.refreshProject !== false) {
    await refreshProjectPayload(state.project);
  }
  return result;
}

async function refreshAnalysisAfterManualMetadataAction(projectId, item, options = {}) {
  const token = state.loadingToken;
  const job = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/listing/open`, {
    method: "POST",
  });
  await waitForAsyncJob(
    (jobId) => `/api/projects/${encodeURIComponent(projectId)}/listing/status?job_id=${encodeURIComponent(jobId)}`,
    job,
    token,
    (currentJob) => setAnalysisStatus(getJobPhaseLabel(currentJob), "running"),
  );
  if (token !== state.loadingToken) {
    return;
  }
  await refreshListingAtCurrentAddressAnchor(projectId, token);
  if (token !== state.loadingToken) {
    return;
  }
  await refreshProjectPayload(projectId, token);
  if (token !== state.loadingToken) {
    return;
  }
  await loadNavigationEntries(projectId);
  renderNavigationOverlay();
  const addr = reviewItemAddress(item);
  const sectionIndex = Number(item?.hunk ?? item?.section_index);
  const focusTarget = options.focusTarget !== false;
  if (Number.isInteger(sectionIndex) && Number.isFinite(addr)) {
    await jumpToListingSectionOffset(projectId, sectionIndex, addr, {focus: focusTarget});
  } else if (Number.isFinite(addr)) {
    await jumpToListingAddr(projectId, addr, null, {focus: focusTarget});
  }
}

function reviewItemManualActionLocation(item) {
  const addr = reviewItemAddress(item);
  if (!Number.isFinite(addr)) {
    return null;
  }
  const end = reviewItemEnd(item);
  const sectionIndex = Number(item?.hunk ?? item?.section_index);
  return {
    hunk: Number.isInteger(sectionIndex) ? sectionIndex : null,
    addr,
    end: Number.isFinite(end) && end > addr ? end : null,
  };
}

function showManualReviewActionSaved(item, fallbackText) {
  if (!flashManualActionLocations([reviewItemManualActionLocation(item)])) {
    setAnalysisStatus(fallbackText, "ready", 1200);
  }
}

async function applyReviewAction(item, button) {
  const action = button.dataset.reviewAction || "";
  if (action === "navigate") {
    await navigateToReviewItem(item);
    return;
  }
  if (action === "open_reproduction_report") {
    await openReproPanel();
    return;
  }
  if (action === "rerun_round_trip_verification") {
    await runReproduction(state.project);
    return;
  }
  if (action === "create_manual_seed") {
    const seed = reviewItemSeedPayload(item, button);
    if (!seed) {
      return;
    }
    await postManualReviewAction({kind: "create_manual_seed", seed}, {refreshProject: false});
    await refreshAnalysisAfterManualMetadataAction(state.project, item, {focusTarget: false});
    showManualReviewActionSaved(item, "Manual seed saved");
    return;
  }
  if (action === "remove_manual_annotation") {
    if (item.label_id) {
      await postManualReviewAction({kind: "remove_manual_label", label_id: item.label_id}, {refreshProject: false});
    } else if (item.comment_id) {
      await postManualReviewAction({kind: "remove_manual_comment", comment_id: item.comment_id}, {refreshProject: false});
    }
    await refreshAnalysisAfterManualMetadataAction(state.project, item, {focusTarget: false});
    showManualReviewActionSaved(item, "Manual annotation removed");
    return;
  }
  if (action === "resolve_review_item") {
    await postManualReviewAction({
      kind: "resolve_review_item",
      resolution: reviewResolutionPayload(item, button.dataset.disposition),
    });
    setAnalysisStatus("Review item resolved", "ready", 2000);
  }
}

function bindManualReviewPanel() {
  const overlay = document.getElementById("review-overlay");
  if (!overlay) {
    return;
  }
  overlay.querySelector("[data-review-close]")?.addEventListener("click", closeManualReviewPanel);
  overlay.querySelectorAll("[data-review-filter]").forEach((control) => {
    control.addEventListener("change", () => {
      state.manualReview.filters[control.dataset.reviewFilter] = control.value;
      renderManualReviewPanel();
    });
    if (control instanceof HTMLInputElement) {
      control.addEventListener("input", () => {
        state.manualReview.filters[control.dataset.reviewFilter] = control.value;
        renderManualReviewPanel();
      });
    }
  });
  overlay.querySelectorAll("[data-review-navigate]").forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.reviewNavigate);
      const item = reviewItems().find((candidate) => candidate.review_index === index);
      void navigateToReviewItem(item);
    });
  });
  overlay.querySelectorAll("[data-review-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.reviewIndex);
      const item = reviewItems().find((candidate) => candidate.review_index === index);
      void applyReviewAction(item, button);
    });
  });
}

function commandPaletteMatches(action, query) {
  const context = action.target_context || {};
  const parameters = action.parameters || {};
  const text = [
    action.label,
    action.action_id,
    action.action,
    String(action.action_id || "").split(".")[0],
    context.kind,
    context.row_kind,
    context.element_kind,
    parameters.symbol,
    parameters.namespace,
    parameters.domain,
    parameters.struct_name,
    parameters.library_name,
    parameters.function,
    parameters.field,
  ].join(" ").toLowerCase();
  return text.includes(String(query || "").trim().toLowerCase());
}

function visibleCommandPaletteActions() {
  return state.commandPalette.actions
    .filter((action) => state.commandPalette.global || Number(action.palette_context_rank || 0) === 0)
    .filter((action) => commandPaletteMatches(action, state.commandPalette.query));
}

function commandPaletteRangeAvailabilityRank(action) {
  const availability = action?.range_availability || "applicable";
  if (availability === "applicable") {
    return 0;
  }
  if (availability === "partial") {
    return 1;
  }
  return 2;
}

function clampCommandPaletteSelection(actions) {
  if (!actions.length) {
    state.commandPalette.selectedIndex = 0;
    return 0;
  }
  const selected = Number(state.commandPalette.selectedIndex);
  const index = Number.isInteger(selected) ? selected : 0;
  state.commandPalette.selectedIndex = Math.max(0, Math.min(actions.length - 1, index));
  return state.commandPalette.selectedIndex;
}

function moveCommandPaletteSelection(delta) {
  const actions = visibleCommandPaletteActions();
  if (!actions.length || !delta) {
    return;
  }
  const selected = clampCommandPaletteSelection(actions);
  state.commandPalette.selectedIndex = Math.max(0, Math.min(actions.length - 1, selected + delta));
  renderCommandPalette();
}

function renderCommandPalette() {
  const existing = document.getElementById("command-palette-overlay");
  if (!state.commandPalette.open) {
    existing?.remove();
    return;
  }
  const app = document.getElementById("app");
  if (!app) {
    return;
  }
  const actions = visibleCommandPaletteActions();
  const selectedIndex = clampCommandPaletteSelection(actions);
  const editor = state.commandPalette.editor;
  const bodyHtml = editor ? renderCommandParameterEditor(editor) : `
        <div class="command-palette-search-row">
          <input id="command-palette-search" class="command-palette-search" type="text" value="${escapeHtml(state.commandPalette.query)}" autocomplete="off">
          <button type="button" class="command-palette-mode" data-command-palette-global="1">${state.commandPalette.global ? "All" : "Context"}</button>
        </div>
        <div class="command-palette-list">
          ${state.commandPalette.loading ? '<div class="command-palette-empty">Loading</div>' : ""}
          ${!state.commandPalette.loading && !actions.length ? '<div class="command-palette-empty">No commands</div>' : ""}
          ${actions.map((action, index) => `
            <button type="button" class="command-palette-item${index === selectedIndex ? " selected" : ""}${action.enabled === false ? " disabled" : ""}" data-command-palette-action="${escapeHtml(action.action_id)}" data-command-palette-index="${index}" aria-selected="${index === selectedIndex ? "true" : "false"}"${action.enabled === false ? " disabled" : ""}>
              <span>${escapeHtml(action.label || action.action_id)}${action.availability_reason ? `<small>${escapeHtml(action.availability_reason)}</small>` : ""}</span>
              ${action.default_key_binding ? `<kbd>${escapeHtml(action.default_key_binding)}</kbd>` : ""}
            </button>
          `).join("")}
        </div>
  `;
  const html = `
    <div class="command-palette-overlay" id="command-palette-overlay">
      <div class="command-palette-panel">
        ${bodyHtml}
      </div>
    </div>
  `;
  if (existing) {
    existing.outerHTML = html;
  } else {
    app.insertAdjacentHTML("beforeend", html);
  }
  if (editor) {
    bindCommandParameterEditor();
  } else {
    bindCommandPalette();
  }
  const selected = document.querySelector(".command-palette-item.selected");
  if (selected instanceof HTMLElement) {
    selected.scrollIntoView({block: "nearest"});
  }
}

function renderCommandParameterEditor(editor) {
  const action = editor.action || {};
  const fields = commandParameterSchemaFields(action);
  const interactionType = action?.interaction_schema?.type || "";
  const fieldHtml = interactionType === "choice_grid"
    ? renderParameterChoiceGrid(editor)
    : interactionType === "filtered_chooser"
      ? renderParameterFilteredChooser(editor)
      : fields.map((field) => renderCommandParameterField(field, editor)).join("");
  return `
    <form class="command-parameter-editor" id="command-parameter-editor">
      <div class="command-parameter-header">
        <div class="command-parameter-title">${escapeHtml(action.label || action.action_id || "Command")}</div>
        <button type="button" class="command-parameter-cancel" data-command-parameter-cancel="1">Cancel</button>
      </div>
      <div class="command-parameter-fields">
        ${fieldHtml}
      </div>
      ${editor.submitError ? `<div class="command-parameter-error">${escapeHtml(editor.submitError)}</div>` : ""}
      <div class="command-parameter-actions">
        <button type="submit" class="command-parameter-submit"${editor.submitting ? " disabled" : ""}>${editor.submitting ? "Saving" : "Apply"}</button>
      </div>
    </form>
  `;
}

function autofillIgnoreAttributes() {
  return ' autocomplete="off" autocapitalize="off" spellcheck="false" data-1p-ignore="true" data-lpignore="true" data-bwignore="true" data-protonpass-ignore="true" data-form-type="other"';
}

function renderParameterChoiceGrid(editor) {
  const interaction = editor.action?.interaction_schema || {};
  const parameter = interaction.parameter || "representation";
  const options = Array.isArray(interaction.options) ? interaction.options : [];
  const value = editor.values[parameter] || interaction.default || "";
  return `
    <div class="parameter-choice-grid" data-parameter-choice-grid="${escapeHtml(parameter)}">
      ${options.map((option) => {
        const selected = String(option.value) === String(value);
        const preview = option.preview?.text || "";
        return `
          <button type="button" class="parameter-choice${selected ? " selected" : ""}" data-parameter-choice-value="${escapeHtml(String(option.value))}" aria-pressed="${selected ? "true" : "false"}">
            <span>${escapeHtml(option.label || option.value)}</span>
            ${preview ? `<small>${escapeHtml(preview)}</small>` : ""}
          </button>
        `;
      }).join("")}
    </div>
  `;
}

function filteredChooserOptions(editor) {
  const interaction = editor.action?.interaction_schema || {};
  const options = Array.isArray(interaction.options) ? interaction.options : [];
  const query = String(editor.filter || "").trim().toLowerCase();
  if (!query) {
    return options;
  }
  return options.filter((option) => [
    option.label,
    option.value,
    option.parameters?.domain,
    option.parameters?.symbol,
  ].map((value) => String(value || "").toLowerCase()).join(" ").includes(query));
}

function renderParameterFilteredChooser(editor) {
  const options = filteredChooserOptions(editor);
  const selectedIndex = Math.max(0, Math.min(options.length - 1, Number(editor.selectedIndex || 0)));
  return `
    <div class="parameter-filtered-chooser">
      <input class="parameter-filter-input" data-parameter-filter-input="1" type="search" value="${escapeHtml(editor.filter || "")}"${autofillIgnoreAttributes()}>
      <div class="parameter-filter-options">
        ${options.length ? options.map((option, index) => `
          <button type="button" class="parameter-filter-option${index === selectedIndex ? " selected" : ""}" data-parameter-filter-index="${index}">
            <span>${escapeHtml(option.label || option.value)}</span>
            ${option.preview?.symbol ? `<small>${escapeHtml(String(option.preview.symbol))}</small>` : ""}
          </button>
        `).join("") : '<div class="command-palette-empty">No options</div>'}
      </div>
    </div>
  `;
}

function renderCommandParameterField(field, editor) {
  const value = editor.values[field.name];
  const error = editor.errors[field.name] || "";
  const required = field.required ? " data-required=\"1\"" : "";
  const label = `${escapeHtml(field.label)}${field.required ? " *" : ""}`;
  let control = "";
  if (field.type === "boolean") {
    control = `
      <label class="command-parameter-checkbox">
        <input type="checkbox" data-command-parameter-name="${escapeHtml(field.name)}"${value ? " checked" : ""}${required}>
        <span>${label}</span>
      </label>
    `;
  } else if (field.enumValues.length) {
    control = `
      <label>
        <span>${label}</span>
        <select data-command-parameter-name="${escapeHtml(field.name)}"${required}>
          ${field.required && !String(value) ? '<option value="" selected disabled></option>' : ""}
          ${field.required ? "" : '<option value=""></option>'}
          ${field.enumValues.map((option) => `<option value="${escapeHtml(option)}"${String(value) === option ? " selected" : ""}>${escapeHtml(option)}</option>`).join("")}
        </select>
      </label>
    `;
  } else if (field.type === "number" || field.type === "integer") {
    control = `
      <label>
        <span>${label}</span>
        <input type="number" data-command-parameter-name="${escapeHtml(field.name)}" value="${escapeHtml(value ?? "")}"${field.type === "integer" ? ' step="1"' : ""}${required}${autofillIgnoreAttributes()}>
      </label>
    `;
  } else if (field.type === "string") {
    control = `
      <label>
        <span>${label}</span>
        <input type="text" data-command-parameter-name="${escapeHtml(field.name)}" value="${escapeHtml(value ?? "")}"${required}${autofillIgnoreAttributes()}>
      </label>
    `;
  } else {
    control = `
      <label>
        <span>${label}</span>
        <input type="text" value="Unsupported parameter type: ${escapeHtml(field.type)}" disabled${autofillIgnoreAttributes()}>
      </label>
    `;
  }
  return `
    <div class="command-parameter-field${error ? " has-error" : ""}" data-command-parameter-field="${escapeHtml(field.name)}">
      ${control}
      ${error ? `<div class="command-parameter-field-error">${escapeHtml(error)}</div>` : ""}
    </div>
  `;
}

function bindCommandPalette() {
  const overlay = document.getElementById("command-palette-overlay");
  const input = document.getElementById("command-palette-search");
  if (!(overlay instanceof HTMLElement) || !(input instanceof HTMLInputElement)) {
    return;
  }
  input.focus();
  input.setSelectionRange(input.value.length, input.value.length);
  input.addEventListener("input", () => {
    state.commandPalette.query = input.value;
    state.commandPalette.selectedIndex = 0;
    renderCommandPalette();
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeCommandPalette();
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      moveCommandPaletteSelection(1);
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      moveCommandPaletteSelection(-1);
      return;
    }
    if (event.key === "Backspace" && !input.value && !state.commandPalette.global) {
      event.preventDefault();
      state.commandPalette.global = true;
      state.commandPalette.selectedIndex = 0;
      renderCommandPalette();
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const actions = visibleCommandPaletteActions();
      const action = actions[clampCommandPaletteSelection(actions)];
      if (action) {
        void executeCommandPaletteAction(action);
      }
    }
  });
  overlay.querySelector("[data-command-palette-global]")?.addEventListener("click", () => {
    state.commandPalette.global = true;
    state.commandPalette.selectedIndex = 0;
    renderCommandPalette();
  });
  overlay.querySelectorAll("[data-command-palette-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const index = Number(button.dataset.commandPaletteIndex);
      const action = visibleCommandPaletteActions()[Number.isInteger(index) ? index : 0];
      if (action) {
        void executeCommandPaletteAction(action);
      }
    });
  });
}

async function openCommandPalette() {
  if (!state.project) {
    return;
  }
  state.commandPalette.open = true;
  state.commandPalette.query = "";
  state.commandPalette.selectedIndex = 0;
  state.commandPalette.loading = true;
  state.commandPalette.global = false;
  state.commandPalette.editor = null;
  renderCommandPalette();
  try {
    const catalogs = await loadContextualCommandCatalogs();
    const actionMap = new Map();
    catalogs.forEach((catalog, catalogIndex) => {
      const catalogRank = catalog.context?.kind === "target" && catalogs.length > 1 ? 1 : 0;
      (Array.isArray(catalog.actions) ? catalog.actions : []).forEach((action) => {
        const key = commandPaletteActionIdentity(action);
        const existing = actionMap.get(key);
        const rankedAction = {...action, palette_context_rank: catalogRank, palette_catalog_index: catalogIndex};
        if (!existing || Number(existing.palette_context_rank || 0) > catalogRank) {
          actionMap.set(key, rankedAction);
        }
      });
    });
    state.commandPalette.actions = Array.from(actionMap.values()).sort((left, right) => (
      Number(left.palette_context_rank || 0) - Number(right.palette_context_rank || 0)
      || commandPaletteRangeAvailabilityRank(left) - commandPaletteRangeAvailabilityRank(right)
      || Number(left.palette_catalog_index || 0) - Number(right.palette_catalog_index || 0)
    ));
  } finally {
    state.commandPalette.loading = false;
    renderCommandPalette();
  }
}

function commandPaletteActionIdentity(action) {
  const actionId = action?.action_id || action?.action || "";
  if (action?.appends_to_manual_action_log !== true) {
    return `transient:${actionId}`;
  }
  return `${action?.target_context?.kind || "target"}:${actionId}`;
}

function catalogActionsFromCatalogs(catalogs) {
  return catalogs.flatMap((catalog) => Array.isArray(catalog.actions) ? catalog.actions : []);
}

function actionSupportsInlineSession(action) {
  const hosts = action?.interaction_schema?.hosts;
  return Array.isArray(hosts) && hosts.includes("inline");
}

function parameterActionPriority(action) {
  const rank = Number(action?.interaction_schema?.primary_rank);
  return Number.isFinite(rank) ? rank : 1000;
}

async function openInlineSessionForAction(action) {
  const rowIndex = currentListingSelectionRowIndex();
  if (!Number.isFinite(rowIndex) || !action) {
    return false;
  }
  if (!actionSupportsInlineSession(action)) {
    openCommandParameterEditor(action);
    return true;
  }
  openInlineParameterSession(action, rowIndex);
  return true;
}

async function invokeSelectedCatalogBinding(binding) {
  if (!state.project || state.manualEdit.inFlight || state.parameterSession) {
    return false;
  }
  const catalogs = await loadContextualCommandCatalogs();
  const actions = catalogActionsFromCatalogs(catalogs)
    .filter((action) => action.enabled !== false)
    .filter((action) => action.default_key_binding === binding);
  if (!actions.length) {
    return false;
  }
  actions.sort((left, right) => parameterActionPriority(left) - parameterActionPriority(right));
  return openInlineSessionForAction(actions[0]);
}

async function invokeEditSelectedCommand() {
  if (!state.project || state.manualEdit.inFlight || state.parameterSession) {
    return false;
  }
  const catalogs = await loadContextualCommandCatalogs();
  const actions = catalogActionsFromCatalogs(catalogs)
    .filter((action) => action.enabled !== false)
    .filter(actionSupportsInlineSession)
    .sort((left, right) => parameterActionPriority(left) - parameterActionPriority(right));
  if (!actions.length) {
    setAnalysisStatus("No editable selection", "ready", 2000);
    return false;
  }
  return openInlineSessionForAction(actions[0]);
}

function commandPaletteElementQuery(selection) {
  if (!selection || selection.precisionLost) {
    return null;
  }
  const elementSelector = selection.elementSelector || implicitElementSelectorForSelection(selection);
  if (!elementSelector) {
    return null;
  }
  const rowIndex = currentListingSelectionRowIndex(selection);
  if (!Number.isFinite(rowIndex)) {
    return null;
  }
  const params = new URLSearchParams();
  params.set("context", "element");
  params.set("row_index", String(rowIndex));
  appendCommandPaletteRowSnapshot(params, rowIndex);
  Object.entries(elementSelector).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  });
  return params.toString();
}

function commandPaletteRowQuery(rowIndex) {
  const params = new URLSearchParams();
  params.set("context", "row");
  params.set("row_index", String(rowIndex));
  appendCommandPaletteRowSnapshot(params, rowIndex);
  return params.toString();
}

function appendCommandPaletteRowSnapshot(params, rowIndex) {
  const row = listingRowDataForIndex(rowIndex);
  if (row) {
    params.set("rows", JSON.stringify([commandPaletteRowSnapshot({...row, row_index: rowIndex})]));
  }
}

function commandPaletteRowSnapshot(row) {
  return {
    row_index: row.row_index,
    row_id: row.row_id || null,
    stable_key: row.stable_key || null,
    kind: row.kind || null,
    addr: row.addr ?? null,
    section_index: row.section_index ?? null,
    start_offset: row.start_offset ?? null,
    end_offset: row.end_offset ?? null,
    bytes: row.bytes || null,
    label: row.label || null,
    manual_label_id: row.manual_label_id || null,
    manual_label_address_domain: row.manual_label_address_domain || null,
    opcode_or_directive: row.opcode_or_directive || null,
    operand_parts: row.operand_parts || null,
    operand_accesses: row.operand_accesses || null,
    operand_registers: row.operand_registers || null,
    app_slot_refs: row.app_slot_refs || null,
    typed_accesses: row.typed_accesses || null,
    unresolved_typed_accesses: row.unresolved_typed_accesses || null,
    data_class: row.data_class || null,
    structured_data: row.structured_data || null,
    comment_text: row.comment_text || "",
  };
}

function currentListingSelectionRowIndex(selection = state.listingSelection) {
  const rowIndex = Number(selection?.focusRowIndex ?? selection?.rowIndex);
  if (Number.isFinite(rowIndex)) {
    return rowIndex;
  }
  const selectedRow = document.querySelector(".listing-row-selected");
  const selectedIndex = Number(selectedRow?.dataset?.rowIndex);
  return Number.isFinite(selectedIndex) ? selectedIndex : NaN;
}

function implicitElementSelectorForSelection(selection) {
  const row = listingRowDataForSelection(selection);
  if (!row || row.kind !== "data" || !row.bytes) {
    if (row?.kind === "label" && row.label) {
      return {element_kind: "label", symbol: row.label};
    }
    return null;
  }
  return {element_kind: "data_literal"};
}

function listingRowDataForSelection(selection) {
  const rowIndex = Number(selection?.rowIndex);
  if (!Number.isFinite(rowIndex)) {
    return null;
  }
  return listingRowDataForIndex(rowIndex);
}

function listingRowDataForIndex(rowIndex) {
  const localIndex = rowIndex - Number(state.virtualListing?.start || 0);
  return Array.isArray(state.listingRows) && localIndex >= 0 && localIndex < state.listingRows.length
    ? state.listingRows[localIndex]
    : null;
}

function closeCommandPalette() {
  state.commandPalette.open = false;
  state.commandPalette.selectedIndex = 0;
  state.commandPalette.editor = null;
  renderCommandPalette();
}

async function executeCommandPaletteAction(action) {
  if (action?.enabled === false) {
    return;
  }
  if (action?.appends_to_manual_action_log === true && state.manualEdit.inFlight) {
    setAnalysisStatus("Manual edit already in progress", "running", 2500);
    return;
  }
  const command = String(action?.action || "");
  if (actionNeedsParameterEditor(action)) {
    openCommandParameterEditor(action);
    return;
  }
  const parameters = {};
  closeCommandPalette();
  if (action?.appends_to_manual_action_log === true) {
    await submitCommandPaletteCatalogAction(action, parameters);
  } else if (command === "open_review") {
    openManualReviewPanel();
  } else if (command === "open_navigation") {
    await openNavigationOverlay();
  } else if (command === "open_reproduction_report") {
    await openReproPanel();
  } else if (command === "export_source") {
    await exportSource(String(action?.parameters?.assembler_profile || "vasm"));
  } else if (command === "history_back") {
    await navigateHistory("back");
  } else if (command === "history_forward") {
    await navigateHistory("forward");
  } else if (command === "follow_reference") {
    await followSelectedReference(false);
  } else if (command === "previous_label") {
    await moveToRelativeLabel(-1);
  } else if (command === "next_label") {
    await moveToRelativeLabel(1);
  } else if (command === "previous_hunk") {
    await moveToRelativeHunk(-1);
  } else if (command === "next_hunk") {
    await moveToRelativeHunk(1);
  } else if (command === "selection_up") {
    await moveListingSelection(-1);
  } else if (command === "selection_down") {
    await moveListingSelection(1);
  } else if (command === "viewport_page_up") {
    scrollListingViewport(state.project, "up");
  } else if (command === "viewport_page_down") {
    scrollListingViewport(state.project, "down");
  }
}

async function loadContextualCommandCatalogs() {
  const catalogs = [];
  catalogs.push(await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/manual-action-catalog?context=target`));
  const rowIndex = currentListingSelectionRowIndex();
  if (Number.isFinite(rowIndex)) {
    const rangeQuery = commandPaletteRangeQuery(state.listingSelection);
    if (rangeQuery) {
      catalogs.push(await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/manual-action-catalog?${rangeQuery}`));
    } else {
      catalogs.push(await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/manual-action-catalog?${commandPaletteRowQuery(rowIndex)}`));
      const elementQuery = commandPaletteElementQuery(state.listingSelection);
      if (elementQuery) {
        catalogs.push(await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/manual-action-catalog?${elementQuery}`));
      }
    }
  }
  return catalogs;
}

async function submitCommandPaletteCatalogAction(action, parameters) {
  const command = String(action?.action || "");
  if (command === "set_reproduction_profile") {
    await setReproductionProfile(String(parameters.profile_id || ""));
    return;
  }
  if (command === "export_source") {
    await exportSource(String(parameters.assembler_profile || "vasm"));
    return;
  }
  if (action?.appends_to_manual_action_log === true) {
    if (state.manualEdit.inFlight) {
      setAnalysisStatus("Manual edit already in progress", "running", 2500);
      return;
    }
    const body = {
      action_id: action.action_id,
      context: action.target_context,
    };
    if (Object.keys(parameters).length) {
      body.parameters = parameters;
    }
    state.manualEdit.inFlight = true;
    try {
      const result = await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/manual-action-catalog/execute`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body),
      });
      const application = applyManualActionApplication(result?.application);
      if (application.refreshMode === "analysis" || application.reconciliationRequired) {
        await refreshAnalysisAfterManualMetadataAction(state.project, {});
      } else if (application.refreshMode === "project") {
        await refreshProjectPayload(state.project);
        renderCurrentListingWindow();
      } else {
        closeSubmittedParameterSurface();
        renderCurrentListingWindow();
      }
      if (!flashManualActionApplication(application)) {
        setAnalysisStatus("Manual action saved", "ready", 1200);
      }
    } finally {
      state.manualEdit.inFlight = false;
      state.manualEdit.pendingRanges = [];
      renderCurrentListingWindow();
    }
  }
}

function closeSubmittedParameterSurface() {
  if (state.parameterSession) {
    state.parameterSession = null;
    renderCurrentListingWindow();
    return true;
  }
  if (state.commandPalette.editor) {
    closeCommandPalette();
    return true;
  }
  return false;
}

function applyManualActionApplication(application) {
  const refreshMode = manualActionRefreshMode(application);
  const localEffects = Array.isArray(application?.local_effects) ? application.local_effects : [];
  const pendingRanges = Array.isArray(application?.pending_ranges) ? application.pending_ranges : [];
  let appliedLocalEffect = false;
  localEffects.forEach((effect) => {
    if (applyManualLocalEffect(effect)) {
      appliedLocalEffect = true;
    }
  });
  state.manualEdit.pendingRanges = pendingRanges;
  if (appliedLocalEffect || pendingRanges.length) {
    renderCurrentListingWindow();
  }
  return {
    appliedLocalEffect,
    localEffects,
    pendingRanges,
    reconciliationRequired: Boolean(application?.reconciliation?.required || pendingRanges.length),
    refreshMode,
  };
}

function flashManualActionApplication(application) {
  return flashManualActionLocations(manualActionFlashRanges(application));
}

function flashManualActionLocations(locations) {
  const ranges = Array.isArray(locations)
    ? locations.map(normalizeManualActionLocation).filter(Boolean)
    : [];
  if (!ranges.length) {
    return false;
  }
  if (state.manualEdit.savedFlashTimer) {
    window.clearTimeout(state.manualEdit.savedFlashTimer);
    state.manualEdit.savedFlashTimer = null;
  }
  state.manualEdit.savedFlashRanges = ranges;
  renderCurrentListingWindow();
  state.manualEdit.savedFlashTimer = window.setTimeout(() => {
    state.manualEdit.savedFlashRanges = [];
    state.manualEdit.savedFlashTimer = null;
    renderCurrentListingWindow();
  }, 1100);
  return true;
}

function manualActionFlashRanges(application) {
  const localEffects = Array.isArray(application?.localEffects) ? application.localEffects : [];
  const pendingRanges = Array.isArray(application?.pendingRanges) ? application.pendingRanges : [];
  return [
    ...localEffects.flatMap(manualActionEffectSubjects),
    ...pendingRanges,
  ];
}

function manualActionEffectSubjects(effect) {
  if (!effect || typeof effect !== "object") {
    return [];
  }
  if (effect.kind === "label_rename") {
    return [effect];
  }
  if (effect.kind === "comment") {
    return effect.comment ? [effect.comment] : [];
  }
  if (effect.kind === "representation") {
    return effect.representation ? [effect.representation] : [];
  }
  if (effect.kind === "review_note_add" || effect.kind === "review_note_edit") {
    return effect.note ? [effect.note] : [];
  }
  return [];
}

function normalizeManualActionLocation(subject) {
  if (!subject || typeof subject !== "object") {
    return null;
  }
  const rowIndexes = Array.isArray(subject.row_indexes)
    ? subject.row_indexes.map((value) => Number(value)).filter(Number.isFinite)
    : [];
  const rowIndex = Number(subject.row_index);
  if (Number.isFinite(rowIndex) && !rowIndexes.includes(rowIndex)) {
    rowIndexes.push(rowIndex);
  }
  const stableKey = String(subject.stable_key || "");
  const addr = Number(subject.addr);
  const end = Number(subject.end);
  const hunk = Number(subject.hunk ?? subject.section_index);
  if (!rowIndexes.length && !stableKey && !Number.isFinite(addr)) {
    return null;
  }
  return {
    row_indexes: rowIndexes,
    stable_key: stableKey || null,
    addr: Number.isFinite(addr) ? addr : null,
    end: Number.isFinite(end) ? end : null,
    hunk: Number.isFinite(hunk) ? hunk : null,
  };
}

function manualActionRefreshMode(application) {
  const mode = application?.refresh?.mode;
  if (mode === "none" || mode === "project" || mode === "analysis") {
    return mode;
  }
  throw new Error(`Server returned incompatible manual action refresh mode: ${mode || "missing"}`);
}

function applyManualLocalEffect(effect) {
  if (!effect || typeof effect !== "object") {
    return false;
  }
  if (effect.kind === "label_rename") {
    return applyManualLabelRenameEffect(effect);
  }
  if (effect.kind === "representation") {
    return applyManualRepresentationEffect(effect);
  }
  if (effect.kind === "comment") {
    return applyManualCommentEffect(effect);
  }
  if (effect.kind === "review_note_add") {
    return applyManualReviewNoteAddEffect(effect);
  }
  if (effect.kind === "review_note_edit") {
    return applyManualReviewNoteEditEffect(effect);
  }
  if (effect.kind === "review_note_clear") {
    return applyManualReviewNoteClearEffect(effect);
  }
  return false;
}

function applyManualLabelRenameEffect(effect) {
  const name = String(effect.name || "").trim();
  if (!name) {
    return false;
  }
  const rowIndex = Number(effect.row_index);
  const stableKey = String(effect.stable_key || "");
  const localIndex = Number.isFinite(rowIndex) ? rowIndex - Number(state.virtualListing.start || 0) : -1;
  const rows = Array.isArray(state.listingRows) ? state.listingRows.slice() : [];
  const existingIndex = localIndex >= 0 && localIndex < rows.length
    ? localIndex
    : rows.findIndex((row) => stableKey && row.stable_key === stableKey);
  if (existingIndex < 0) {
    return false;
  }
  rows[existingIndex] = {
    ...rows[existingIndex],
    kind: rows[existingIndex].kind || "label",
    label: name,
    text: `${name}:\n`,
    manual_label_id: effect.label_id || rows[existingIndex].manual_label_id || null,
    manual_label_address_domain: effect.address_domain || rows[existingIndex].manual_label_address_domain || null,
  };
  state.listingRows = rows;
  return true;
}

function applyManualRepresentationEffect(effect) {
  const representation = effect.representation;
  if (!representation || typeof representation !== "object") {
    return false;
  }
  const project = state.projectData?.project;
  if (!project) {
    return false;
  }
  if (!project.manual_state || typeof project.manual_state !== "object") {
    project.manual_state = {};
  }
  const existing = Array.isArray(project.manual_state.representations)
    ? project.manual_state.representations
    : [];
  project.manual_state.representations = [
    ...existing.filter((item) => item.representation_id !== representation.representation_id),
    representation,
  ];
  return true;
}

function applyManualCommentEffect(effect) {
  const comment = effect.comment;
  if (!comment || typeof comment !== "object") {
    return false;
  }
  const text = String(comment.text || "").trim();
  if (!text) {
    return false;
  }
  const rowIndex = Number(comment.row_index);
  const stableKey = String(comment.stable_key || "");
  const localIndex = Number.isFinite(rowIndex) ? rowIndex - Number(state.virtualListing.start || 0) : -1;
  const rows = Array.isArray(state.listingRows) ? state.listingRows.slice() : [];
  const existingIndex = localIndex >= 0 && localIndex < rows.length
    ? localIndex
    : rows.findIndex((row) => stableKey && row.stable_key === stableKey);
  if (existingIndex < 0) {
    return false;
  }
  rows[existingIndex] = {
    ...rows[existingIndex],
    comment_text: text,
  };
  state.listingRows = rows;
  return true;
}

function ensureManualReviewNotes() {
  const project = state.projectData?.project;
  if (!project) {
    return null;
  }
  if (!project.manual_state || typeof project.manual_state !== "object") {
    project.manual_state = {};
  }
  if (!Array.isArray(project.manual_state.review_notes)) {
    project.manual_state.review_notes = [];
  }
  return project.manual_state.review_notes;
}

function applyManualReviewNoteAddEffect(effect) {
  const note = effect.note;
  if (!note || typeof note !== "object") {
    return false;
  }
  const notes = ensureManualReviewNotes();
  if (!notes) {
    return false;
  }
  const nextNote = {...note};
  const noteId = String(nextNote.note_id || "");
  if (!noteId) {
    return false;
  }
  const index = notes.findIndex((item) => item.note_id === noteId);
  if (index >= 0) {
    notes[index] = nextNote;
  } else {
    notes.push(nextNote);
  }
  applyReviewNoteToListingRows(nextNote);
  return true;
}

function applyManualReviewNoteEditEffect(effect) {
  const patch = effect.note;
  const noteId = String(patch?.note_id || "");
  const notes = ensureManualReviewNotes();
  if (!noteId || !notes) {
    return false;
  }
  const index = notes.findIndex((item) => item.note_id === noteId);
  if (index < 0) {
    return false;
  }
  const updated = {...notes[index], ...patch};
  notes[index] = updated;
  removeReviewNoteFromListingRows(noteId);
  applyReviewNoteToListingRows(updated);
  return true;
}

function applyManualReviewNoteClearEffect(effect) {
  const noteId = String(effect.note_id || "");
  const notes = ensureManualReviewNotes();
  if (!noteId || !notes) {
    return false;
  }
  const index = notes.findIndex((item) => item.note_id === noteId);
  if (index >= 0) {
    notes.splice(index, 1);
  }
  removeReviewNoteFromListingRows(noteId);
  return true;
}

function noteMatchesListingRow(note, row, globalIndex) {
  const rowIndexes = Array.isArray(note.row_indexes) ? note.row_indexes : [];
  if (rowIndexes.includes(globalIndex)) {
    return true;
  }
  if (note.stable_key && row.stable_key && note.stable_key === row.stable_key) {
    return true;
  }
  const start = Number(note.addr);
  const end = Number(note.end);
  const rowStart = Number(row.start_offset ?? row.addr);
  if (!Number.isFinite(start) || !Number.isFinite(rowStart)) {
    return false;
  }
  return Number.isFinite(end) && end > start ? rowStart >= start && rowStart < end : rowStart === start;
}

function applyReviewNoteToListingRows(note) {
  state.listingRows = (Array.isArray(state.listingRows) ? state.listingRows : []).map((row, localIndex) => {
    const globalIndex = Number(state.virtualListing.start || 0) + localIndex;
    if (!noteMatchesListingRow(note, row, globalIndex)) {
      return row;
    }
    const existing = Array.isArray(row.review_notes) ? row.review_notes.filter((item) => item.note_id !== note.note_id) : [];
    return {...row, review_notes: [...existing, note]};
  });
}

function removeReviewNoteFromListingRows(noteId) {
  state.listingRows = (Array.isArray(state.listingRows) ? state.listingRows : []).map((row) => {
    if (!Array.isArray(row.review_notes)) {
      return row;
    }
    return {...row, review_notes: row.review_notes.filter((note) => note.note_id !== noteId)};
  });
}

function renderCurrentListingWindow() {
  if (!state.project) {
    return;
  }
  renderVirtualListingWindow(state.project, {
    rows: state.listingRows,
    start: state.virtualListing.start,
    end: state.virtualListing.end,
    total_rows: state.virtualListing.totalRows,
    analysis_generation: state.virtualListing.generation,
  }, true);
}

function actionNeedsParameterEditor(action) {
  const interactionType = action?.interaction_schema?.type || "";
  if (["choice_grid", "filtered_chooser"].includes(interactionType)) {
    return true;
  }
  const fields = commandParameterSchemaFields(action);
  return fields.length > 0;
}

function parameterSessionInitialValues(action) {
  const fields = commandParameterSchemaFields(action);
  const values = Object.fromEntries(fields.map((field) => [field.name, defaultCommandParameterValue(action, field)]));
  const interaction = action?.interaction_schema || {};
  if (interaction.parameter && values[interaction.parameter] === undefined) {
    values[interaction.parameter] = interaction.default || "";
  }
  return values;
}

function openCommandParameterEditor(action) {
  state.commandPalette.editor = {
    host: "palette",
    action,
    values: parameterSessionInitialValues(action),
    errors: {},
    submitError: "",
    submitting: false,
  };
  renderCommandPalette();
}

function cancelCommandParameterEditor() {
  state.commandPalette.editor = null;
  renderCommandPalette();
}

function openInlineParameterSession(action, rowIndex) {
  state.parameterSession = {
    host: "inline",
    action,
    rowIndex,
    values: parameterSessionInitialValues(action),
    errors: {},
    submitError: "",
    submitting: false,
    filter: "",
    selectedIndex: 0,
  };
  renderCurrentListingWindow();
}

function cancelInlineParameterSession() {
  state.parameterSession = null;
  renderCurrentListingWindow();
}

function commandParameterSchemaFields(action) {
  const schema = action?.parameter_schema || {};
  const required = Array.isArray(schema.required) ? schema.required : [];
  const properties = schema.properties && typeof schema.properties === "object" && !Array.isArray(schema.properties)
    ? schema.properties
    : {};
  return Object.entries(properties).map(([name, fieldSchema]) => {
    const field = fieldSchema && typeof fieldSchema === "object" && !Array.isArray(fieldSchema) ? fieldSchema : {};
    const enumValues = Array.isArray(field.enum)
      ? field.enum.filter((value) => value !== null && value !== undefined).map((value) => String(value))
      : [];
    const type = typeof field.type === "string" ? field.type : (enumValues.length ? "string" : "string");
    return {
      name,
      label: String(field.title || field.label || name.replaceAll("_", " ")),
      type,
      required: required.includes(name),
      enumValues,
      schema: field,
    };
  });
}

function defaultCommandParameterValue(action, field) {
  if (action?.parameters?.[field.name] !== undefined) {
    return action.parameters[field.name];
  }
  if (field.schema.default !== undefined) {
    return field.schema.default;
  }
  if (field.name === "name" && action?.target_context?.symbol) {
    return action.target_context.symbol;
  }
  if (field.type === "boolean") {
    return false;
  }
  return "";
}

function bindCommandParameterEditor() {
  const form = document.getElementById("command-parameter-editor");
  const editor = state.commandPalette.editor;
  if (!(form instanceof HTMLFormElement) || !editor) {
    return;
  }
  const fields = commandParameterSchemaFields(editor.action);
  form.querySelectorAll("[data-command-parameter-name]").forEach((control) => {
    control.addEventListener("input", () => updateCommandParameterValue(editor, control, fields));
    control.addEventListener("change", () => updateCommandParameterValue(editor, control, fields));
    control.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cancelCommandParameterEditor();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        void submitCommandParameterEditor();
      }
    });
  });
  form.querySelector("[data-command-parameter-cancel]")?.addEventListener("click", () => {
    cancelCommandParameterEditor();
  });
  bindParameterChoiceGrid(form, editor, () => renderCommandPalette());
  bindParameterFilteredChooser(form, editor, () => renderCommandPalette(), () => submitCommandParameterEditor());
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitCommandParameterEditor();
  });
  const firstControl = form.querySelector("[data-command-parameter-name]");
  if (firstControl instanceof HTMLInputElement || firstControl instanceof HTMLSelectElement) {
    firstControl.focus();
    if (firstControl instanceof HTMLInputElement && firstControl.type !== "checkbox") {
      firstControl.select();
    }
  }
}

function updateCommandParameterValue(editor, control, fields) {
  if (!editor || !(control instanceof HTMLInputElement || control instanceof HTMLSelectElement)) {
    return;
  }
  const name = control.dataset.commandParameterName;
  const field = fields.find((candidate) => candidate.name === name);
  if (!field) {
    return;
  }
  if (field.type === "boolean" && control instanceof HTMLInputElement) {
    editor.values[field.name] = control.checked;
  } else if (field.type === "number" || field.type === "integer") {
    editor.values[field.name] = control.value;
  } else {
    editor.values[field.name] = control.value;
  }
  delete editor.errors[field.name];
  editor.submitError = "";
}

function bindParameterChoiceGrid(root, editor, rerender) {
  root.querySelectorAll("[data-parameter-choice-value]").forEach((button) => {
    button.addEventListener("click", () => {
      const parameter = editor.action?.interaction_schema?.parameter || "representation";
      editor.values[parameter] = button.dataset.parameterChoiceValue || "";
      editor.errors = {};
      editor.submitError = "";
      rerender();
    });
  });
}

function bindParameterFilteredChooser(root, editor, rerender, submit) {
  const input = root.querySelector("[data-parameter-filter-input]");
  if (input instanceof HTMLInputElement) {
    input.addEventListener("input", () => {
      editor.filter = input.value;
      editor.selectedIndex = 0;
      rerender();
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        const options = filteredChooserOptions(editor);
        const delta = event.key === "ArrowDown" ? 1 : -1;
        editor.selectedIndex = Math.max(0, Math.min(options.length - 1, Number(editor.selectedIndex || 0) + delta));
        rerender();
      }
      if (event.key === "Enter") {
        event.preventDefault();
        submit();
      }
      if (event.key === "Escape") {
        event.preventDefault();
        editor.host === "inline" ? cancelInlineParameterSession() : cancelCommandParameterEditor();
      }
    });
  }
  root.querySelectorAll("[data-parameter-filter-index]").forEach((button) => {
    button.addEventListener("click", () => {
      editor.selectedIndex = Number(button.dataset.parameterFilterIndex || 0);
      submit();
    });
  });
}

async function submitCommandParameterEditor() {
  const editor = state.commandPalette.editor;
  if (!editor || editor.submitting) {
    return;
  }
  const fields = commandParameterSchemaFields(editor.action);
  const {parameters, errors} = commandParameterPayload(fields, editor.values, editor.action);
  editor.errors = errors;
  editor.submitError = "";
  if (Object.keys(errors).length) {
    renderCommandPalette();
    return null;
  }
  editor.submitting = true;
  renderCommandPalette();
  try {
    await submitCommandPaletteCatalogAction(editor.action, parameters);
    closeCommandPalette();
  } catch (error) {
    const activeEditor = state.commandPalette.editor;
    if (activeEditor) {
      activeEditor.submitting = false;
      activeEditor.submitError = String(error.message || error);
      renderCommandPalette();
    }
  }
}

function commandParameterPayload(fields, values, action = null) {
  const parameters = {};
  const errors = {};
  fields.forEach((field) => {
    const rawValue = values[field.name];
    if (!["string", "boolean", "number", "integer"].includes(field.type)) {
      errors[field.name] = `Unsupported parameter type: ${field.type}`;
      return;
    }
    if (field.type === "boolean") {
      parameters[field.name] = Boolean(rawValue);
      return;
    }
    if (field.type === "number" || field.type === "integer") {
      const text = String(rawValue ?? "").trim();
      if (!text) {
        if (field.required) {
          errors[field.name] = "Required";
        }
        return;
      }
      const value = Number(text);
      if (!Number.isFinite(value) || (field.type === "integer" && !Number.isInteger(value))) {
        errors[field.name] = field.type === "integer" ? "Enter a whole number" : "Enter a number";
        return;
      }
      parameters[field.name] = value;
      return;
    }
    const text = String(rawValue ?? "").trim();
    if (!text) {
      if (field.required) {
        errors[field.name] = "Required";
      }
      return;
    }
    if (field.enumValues.length && !field.enumValues.includes(text)) {
      errors[field.name] = "Choose a valid value";
      return;
    }
    const labelError = commandLabelValidationError(field, text, action);
    if (labelError) {
      errors[field.name] = labelError;
      return;
    }
    parameters[field.name] = text;
  });
  return {parameters, errors};
}

function commandLabelValidationError(field, text, action) {
  if (field.name !== "name" || action?.interaction_schema?.preview?.kind !== "label") {
    return "";
  }
  const validation = action.interaction_schema.validation || {};
  const messages = validation.messages || {};
  const pattern = validation.name_pattern ? new RegExp(validation.name_pattern) : null;
  if (pattern && !pattern.test(text)) {
    return messages.invalid_syntax || "Invalid label syntax";
  }
  if (text.startsWith(".") && validation.local_labels_supported === false) {
    return messages.local_disallowed || "Local labels are not allowed";
  }
  return "";
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

function reproductionPolicySummary(report) {
  const summary = report?.policy_summary;
  if (summary && typeof summary === "object") {
    return summary;
  }
  const options = report?.input_stamp?.reproduction_options || {};
  const policy = report?.input_stamp?.reproduction_policy || {};
  return {valid: true, profile_id: options.profile_id || null, profile: null, options, policy};
}

function renderReproductionPolicySummary(report) {
  const summary = reproductionPolicySummary(report);
  if (summary.valid === false) {
    return `<div class="repro-policy-error">Invalid policy: ${escapeHtml(summary.error || "unknown")}</div>`;
  }
  const options = summary.options || {};
  const policy = summary.policy || {};
  const profile = summary.profile || {};
  const profileLabel = profile.name || summary.profile_id || "Custom";
  const workflow = profile.workflow || "custom";
  const oracles = Array.isArray(options.oracle_modes) && options.oracle_modes.length
    ? options.oracle_modes.join(", ")
    : "none";
  const availability = Array.isArray(summary.tool_availability)
    ? summary.tool_availability.filter((record) => record && record.status !== "available")
    : [];
  return `
    <div class="repro-policy-summary">
      <div><span>Profile</span><strong>${escapeHtml(profileLabel)}</strong></div>
      <div><span>Workflow</span><strong>${escapeHtml(workflow)}</strong></div>
      <div><span>Mode</span><strong>${escapeHtml(policy.mode || options.mode || "?")}</strong></div>
      <div><span>Assembler</span><strong>${escapeHtml(options.assembler || "?")}</strong></div>
      <div><span>Backend</span><strong>${escapeHtml(options.backend || "?")}</strong></div>
      <div><span>CPU</span><strong>${escapeHtml(options.cpu || "?")}</strong></div>
      <div><span>Comparison</span><strong>${escapeHtml(policy.comparison || options.comparison || "?")}</strong></div>
      <div><span>Oracles</span><strong>${escapeHtml(oracles)}</strong></div>
    </div>
    ${availability.length ? `
      <div class="tool-availability-warning">
        ${availability.map((record) => `<div>${escapeHtml(record.tool_id || "tool")}: ${escapeHtml(record.message || record.status || "unavailable")}</div>`).join("")}
      </div>
    ` : ""}
  `;
}

function renderOracleCompatibility(report) {
  const oracles = Array.isArray(report?.oracle_compatibility) ? report.oracle_compatibility : [];
  if (!oracles.length) {
    return "";
  }
  return `
    <div class="oracle-compatibility">
      ${oracles.map((oracle) => {
        const diagnostics = [oracle.stderr_excerpt, oracle.stdout_excerpt].filter(Boolean).join("\n").trim();
        return `
          <div class="oracle-result">
            <div class="oracle-result-head">
              <span>${escapeHtml(oracle.oracle_id || "oracle")}</span>
              <strong>${escapeHtml(oracle.comparison_level || "oracle.not_run")}</strong>
            </div>
            <div class="oracle-result-meta">
              ${escapeHtml(oracle.source_profile || "?")} | ${escapeHtml(oracle.assembler_status || "?")} | ${escapeHtml(oracle.message || "")}
            </div>
            ${diagnostics ? `<pre class="oracle-diagnostics">${escapeHtml(diagnostics)}</pre>` : ""}
          </div>
        `;
      }).join("")}
    </div>
  `;
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
    ${renderReproductionPolicySummary(report)}
    ${renderOracleCompatibility(report)}
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

async function followReproductionJob(projectId, job, token, options = {}) {
  if (isRunningReproductionJob(job)) {
    state.reproduction.job = job;
    refreshProjectBadges();
    renderReproPanel();
    if (options.announce) {
      setAnalysisStatus("Running reproduction", "running");
    }
    await waitForAsyncJob(
      (jobId) => `/api/projects/${encodeURIComponent(projectId)}/reproduction/status?job_id=${encodeURIComponent(jobId)}`,
      job,
      token,
      (currentJob) => {
        state.reproduction.job = currentJob;
        refreshProjectBadges();
        renderReproPanel();
      },
    );
  }
  state.reproduction.job = null;
  refreshProjectBadges();
  renderReproPanel();
  const report = await loadReproductionReport(projectId);
  await loadNavigationEntries(projectId);
  renderNavigationOverlay();
  return report;
}

async function runReproduction(projectId) {
  const job = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/reproduction/run`, {method: "POST"});
  const report = await followReproductionJob(projectId, job, state.loadingToken, {announce: true});
  const editNeeded = report?.status === "binary_mismatch" || report?.status === "assembler_error";
  const statusText = report?.status === "exact"
    ? "Reproduction exact"
    : (editNeeded ? "Reproduction needs edits" : "Reproduction failed");
  setAnalysisStatus(statusText, report?.status === "exact" ? "ready" : "failed", 2500);
}

async function setReproductionProfile(profileId) {
  if (!state.project || !profileId) {
    return;
  }
  const payload = await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/reproduction/profile`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({profile_id: profileId}),
  });
  const report = payload.reproduction || null;
  state.reproduction.report = report;
  state.reproduction.reportKey = reproductionReportKey(report);
  state.reproduction.job = null;
  state.reproduction.selectedIssueEntry = null;
  if (state.projectData) {
    state.projectData.reproduction = report;
  }
  refreshProjectBadges();
  renderReproPanel();
  setAnalysisStatus("Reproduction profile saved", "ready", 2000);
}

async function exportSource(assemblerProfile) {
  if (!state.project) {
    return;
  }
  const profile = assemblerProfile || "vasm";
  const payload = await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/source-export?assembler_profile=${encodeURIComponent(profile)}`);
  if (payload.status === "refused") {
    setAnalysisStatus(`Source export refused: ${payload.message || "render failed"}`, "failed", 4000);
    return;
  }
  const sourceText = String(payload.source_text || "");
  const filename = String(payload.filename || `${state.project}-${profile}.s`);
  const blob = new Blob([sourceText], {type: "text/plain;charset=utf-8"});
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  const existing = state.uiPreferences.payload?.preferences || {};
  state.uiPreferences.payload = {
    ...(state.uiPreferences.payload || {}),
    preferences: {
      ...existing,
      source_export_assembler: profile,
    },
  };
  await saveUiPreferenceState();
  setAnalysisStatus("Source exported", "ready", 2500);
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
    job_kind: "listing_artifact",
    phase_id: "cache_artifact",
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
      const isListingJob = jobState.job_kind === "listing_artifact";
      updateAnalysisStatusFromJob(jobState);
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
    source.addEventListener("listing_artifact_ready", (event) => {
      try {
        const payload = JSON.parse(event.data);
        void handleListingArtifactReady(payload, token);
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
  state.project = null;
  state.projectData = null;
  if (state.homeDropCleanup) {
    state.homeDropCleanup();
    state.homeDropCleanup = null;
  }
  if (state.homeView === "corpus") {
    await renderCorpusHome();
    return;
  }
  const projects = await fetchJson("/api/projects");
  const app = document.getElementById("app");
  app.innerHTML = `
    <section class="page page-home">
      <div class="projects-header">
        <div class="home-tabs">
          <button type="button" class="home-tab active" data-home-view="projects">Projects</button>
          <button type="button" class="home-tab" data-home-view="corpus">Corpus</button>
        </div>
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

  document.querySelectorAll("[data-home-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.homeView = button.dataset.homeView || "projects";
      void renderHome();
    });
  });

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

async function renderCorpusHome() {
  const app = document.getElementById("app");
  ensureCorpusFeaturesLoading();
  ensureCorpusResultsLoading();
  app.innerHTML = `
    <section class="page page-home page-corpus">
      <div class="projects-header">
        <div class="home-tabs">
          <button type="button" class="home-tab" data-home-view="projects">Projects</button>
          <button type="button" class="home-tab active" data-home-view="corpus">Corpus</button>
        </div>
      </div>
      <div class="corpus-controls">
        <label class="corpus-control-feature">
          Feature
          <select id="corpus-feature"${state.corpus.featuresLoading ? " disabled" : ""}>
            ${renderCorpusFeatureOptions()}
          </select>
        </label>
        <label class="corpus-control-mode">
          Mode
          <select id="corpus-group">
            ${CORPUS_GROUPS.map((item) => {
              const selected = item.id === state.corpus.group ? " selected" : "";
              return `<option value="${escapeHtml(item.id)}"${selected}>${escapeHtml(item.label)}</option>`;
            }).join("")}
          </select>
        </label>
        <label class="corpus-control-platform">
          Platform
          <select id="corpus-platform">
            ${["", "amiga-hunk", "amiga-disk", "atari-st"].map((platform) => {
              const label = platform || "All platforms";
              const selected = platform === state.corpus.platform ? " selected" : "";
              return `<option value="${escapeHtml(platform)}"${selected}>${escapeHtml(label)}</option>`;
            }).join("")}
          </select>
        </label>
        <label class="corpus-control-search">
          Search
          <input id="corpus-search" type="search" value="${escapeHtml(state.corpus.q)}">
        </label>
        <button id="corpus-search-button" type="button">Search</button>
      </div>
      <div class="corpus-quick-filters">
        ${CORPUS_GROUPS.map((item) => {
          const active = item.id === state.corpus.group ? " active" : "";
          return `<button type="button" class="corpus-quick-filter${active}" data-corpus-group="${escapeHtml(item.id)}">${escapeHtml(item.label)}</button>`;
        }).join("")}
        <label class="corpus-facts-toggle">
          <input id="corpus-show-facts" type="checkbox"${state.corpus.showTargetFacts ? " checked" : ""}>
          Target facts
        </label>
      </div>
      <div id="home-error" class="error"></div>
      <div id="home-overlay" class="overlay-host" hidden></div>
      <div class="corpus-layout">
        <div class="corpus-results">
          ${renderCorpusResultsHtml(state.corpus.results)}
        </div>
        <div class="corpus-detail">
          ${renderCorpusDetailHtml()}
        </div>
      </div>
      ${renderCorpusSnippetOverlayHtml(state.corpus.snippet, state.corpus.snippetLoading, state.corpus.snippetError)}
      ${renderCorpusVariantDiffOverlayHtml(state.corpus.variantDiff, state.corpus.variantDiffLoading, state.corpus.variantDiffError)}
      ${renderDiskBrowserOverlayHtml()}
    </section>
  `;
  bindCorpusHome();
}

function ensureCorpusFeaturesLoading() {
  if (state.corpus.features || state.corpus.featuresLoading) {
    return;
  }
  state.corpus.featuresLoading = true;
  state.corpus.featuresError = null;
  void fetchJson("/api/corpus/features")
    .then((features) => {
      state.corpus.features = Array.isArray(features) ? features : [];
    })
    .catch((err) => {
      state.corpus.features = [];
      state.corpus.featuresError = String(err.message || err);
    })
    .finally(() => {
      state.corpus.featuresLoading = false;
      if (state.homeView === "corpus") {
        void renderHome();
      }
    });
}

function ensureCorpusResultsLoading() {
  const queryKey = corpusQueryUrl();
  if (state.corpus.resultsQueryKey === queryKey && (state.corpus.resultsLoading || state.corpus.resultsLoaded || state.corpus.resultsError)) {
    return;
  }
  state.corpus.resultsQueryKey = queryKey;
  state.corpus.results = [];
  state.corpus.resultsHasMore = false;
  state.corpus.resultsLoading = true;
  state.corpus.resultsError = null;
  state.corpus.resultsLoaded = false;
  const requestToken = state.corpus.resultRequestToken + 1;
  state.corpus.resultRequestToken = requestToken;
  void loadCorpusResults(queryKey, requestToken);
}

function renderCorpusFeatureOptions() {
  if (state.corpus.featuresLoading) {
    return '<option value="">Loading features</option>';
  }
  if (state.corpus.featuresError) {
    return `<option value="">${escapeHtml(state.corpus.featuresError)}</option>`;
  }
  return `
    <option value="">All features</option>
    ${corpusVisibleFeatures().map((item) => {
      const feature = item.feature || "";
      const selected = feature === state.corpus.feature ? " selected" : "";
      const sourceCount = Number(item.source_example_count || 0);
      const suffix = sourceCount > 0
        ? `${item.target_count || 0} targets, ${sourceCount} source`
        : `${item.target_count || 0} targets`;
      return `<option value="${escapeHtml(feature)}"${selected}>${escapeHtml(corpusFeatureLabel(feature))} (${escapeHtml(suffix)})</option>`;
    }).join("")}
  `;
}

function corpusVisibleFeatures() {
  const features = state.corpus.features || [];
  return features.filter((item) => {
    const feature = item.feature || "";
    if (state.corpus.group && !corpusFeatureMatchesGroup(feature, state.corpus.group)) {
      return feature === state.corpus.feature;
    }
    return state.corpus.showTargetFacts || Number(item.source_example_count || 0) > 0 || feature === state.corpus.feature;
  });
}

function corpusFeatureMatchesGroup(feature, group) {
  if (!group) {
    return true;
  }
  const prefixes = CORPUS_GROUP_PREFIXES[group] || [];
  return prefixes.some((prefix) => feature.startsWith(prefix));
}

function corpusFeatureLabel(feature) {
  const text = String(feature || "");
  if (text === "os_call:any") return "All OS calls";
  if (text.startsWith("os_call_library:")) return `Library calls: ${text.split(":", 2)[1]}`;
  if (text.startsWith("os:")) return text.split(":", 2)[1].replaceAll("/", " / ");
  if (text.startsWith("device:")) return `Device: ${text.split(":", 2)[1]}`;
  if (text.startsWith("device_call:")) return `Device call: ${text.split(":", 2)[1].replaceAll("/", " / ")}`;
  if (text.startsWith("device_call_function:")) return `Device call: ${text.split(":", 2)[1]}`;
  if (text.startsWith("os_library:")) return `Library: ${text.split(":", 2)[1]}`;
  if (text.startsWith("hardware_register:")) return `Register: ${text.split(":", 2)[1]}`;
  if (text.startsWith("hardware:")) return text.split(":", 2)[1].replaceAll("/", " / ");
  if (text.startsWith("copper_register:")) return `Copper register: ${text.split(":", 2)[1]}`;
  if (text.startsWith("display:bitplanes:")) return `Display: ${text.split(":").pop()} bitplanes`;
  if (text.startsWith("display:")) return `Display: ${text.split(":", 2)[1].replaceAll("_", " ")}`;
  if (text.startsWith("data:")) return text.split(":", 2)[1].replaceAll("_", " ");
  if (text.startsWith("app_slot:")) return `App slot: ${text.split(":", 2)[1]}`;
  if (text.startsWith("app_slot_region:")) return `App slot region: ${text.split(":", 2)[1]}`;
  if (text.startsWith("app_slot_region_source:")) return `App slot source: ${text.split(":", 2)[1].replaceAll("_", " ")}`;
  if (text.startsWith("app_slot_field_path:")) return `App slot field: ${text.split(":", 2)[1].replaceAll("_", ".")}`;
  if (text.startsWith("app_slot_field_gap:")) return `App slot field gap: ${text.split(":", 2)[1].replaceAll("_", " ")}`;
  if (text.startsWith("app_slot_field_gap_path:")) return `App slot field gap: ${text.split(":", 2)[1].replaceAll("_", ".")}`;
  if (text === "typed_base_unresolved_field") return "Typed base unresolved field";
  if (text.startsWith("platform_typed_access_struct:")) return `Typed struct: ${text.split(":", 2)[1]}`;
  if (text.startsWith("platform_typed_access_owner:")) return `Typed owner: ${text.split(":", 2)[1]}`;
  if (text.startsWith("platform_typed_access:")) return `Typed access: ${text.split(":", 2)[1].replaceAll("_", " ")}`;
  if (text.startsWith("platform_prefix_extension_candidate:")) return `Typed prefix candidate: ${text.split(":", 2)[1]}`;
  if (text.startsWith("platform_prefix_extension_struct:")) return `Typed prefix base: ${text.split(":", 2)[1]}`;
  if (text.startsWith("platform_unresolved_typed_access_struct:")) return `Typed field gap: ${text.split(":", 2)[1]}`;
  if (text.startsWith("platform_unresolved_typed_access:")) return `Typed field gap: ${text.split(":", 2)[1].replaceAll("_", " ")}`;
  if (text.startsWith("platform_struct_field:")) return `Struct field: ${text.split(":", 2)[1].replaceAll("_", ".")}`;
  if (text.startsWith("platform_field_expr:")) return `Field expr: ${text.split(":", 2)[1].replaceAll("_", ".")}`;
  if (text.startsWith("platform_field:")) return `Field: ${text.split(":", 2)[1]}`;
  if (text.startsWith("runtime:")) return text.split(":", 2)[1].replaceAll("_", " ");
  if (text.startsWith("label:")) return `Labels: ${text.split(":", 2)[1]}`;
  if (text.startsWith("xref:")) return text.split(":", 2)[1].replaceAll("_", " ");
  if (text.startsWith("diagnostic:")) return `Diagnostic: ${text.split(":", 2)[1].replaceAll("_", " ")}`;
  if (text.startsWith("analysis:")) return `Internal: ${text.split(":", 2)[1]}`;
  return text;
}

function corpusVisibleTags(tags) {
  return tags.filter((tag) => {
    const text = String(tag);
    return state.corpus.showTargetFacts || (
      !text.startsWith("analysis:")
      && !text.startsWith("analysis_generation:")
      && !text.startsWith("platform:")
      && !text.startsWith("status:")
      && !text.startsWith("file_platform:")
      && !text.startsWith("inspect_platform:")
    );
  });
}

function corpusQueryUrl() {
  const params = new URLSearchParams();
  if (state.corpus.feature) {
    params.set("feature", state.corpus.feature);
  }
  if (state.corpus.group) {
    params.set("group", state.corpus.group);
  }
  if (state.corpus.platform) {
    params.set("platform", state.corpus.platform);
  }
  if (state.corpus.q) {
    params.set("q", state.corpus.q);
  }
  if (!state.corpus.showTargetFacts) {
    params.set("source_only", "1");
  }
  params.set("offset", String(state.corpus.resultOffset || 0));
  params.set("limit", String((state.corpus.resultLimit || 40) + 1));
  const suffix = params.toString();
  return `/api/corpus/query${suffix ? `?${suffix}` : ""}`;
}

async function loadCorpusResults(queryUrl, requestToken) {
  const limit = state.corpus.resultLimit || 40;
  try {
    const rows = await fetchJson(queryUrl);
    if (state.corpus.resultRequestToken !== requestToken || state.corpus.resultsQueryKey !== queryUrl) {
      return;
    }
    state.corpus.resultsHasMore = rows.length > limit;
    state.corpus.results = rows.slice(0, limit);
    state.corpus.resultsLoaded = true;
  } catch (err) {
    if (state.corpus.resultRequestToken !== requestToken || state.corpus.resultsQueryKey !== queryUrl) {
      return;
    }
    state.corpus.results = [];
    state.corpus.resultsHasMore = false;
    state.corpus.resultsError = String(err.message || err);
    state.corpus.resultsLoaded = true;
  } finally {
    if (state.corpus.resultRequestToken === requestToken && state.corpus.resultsQueryKey === queryUrl) {
      state.corpus.resultsLoading = false;
    }
    if (state.homeView === "corpus") {
      void renderHome();
    }
  }
}

function renderCorpusResultsHtml(results) {
  if (state.corpus.resultsLoading) {
    return '<div class="empty">Loading corpus targets.</div>';
  }
  if (state.corpus.resultsError) {
    return `<div class="error">${escapeHtml(state.corpus.resultsError)}</div>`;
  }
  const rows = results || [];
  if (!rows.length) {
    return '<div class="empty">No corpus targets match these filters.</div>';
  }
  const resultHtml = rows.map((target) => {
    const targetId = target.id || "";
    const origin = target.origin || {};
    const sourceContext = target.source_context || {};
    const title = sourceContext.target_name || origin.in_image_path || origin.member_name || origin.display_name || targetId;
    const diskName = sourceContext.disk_name || "";
    const diskTargetId = sourceContext.disk_target_id || "";
    const count = target.count === undefined || target.count === null ? "" : `${target.count} uses`;
    const size = formatFileSize(target.size);
    const sourceCount = Number(target.source_example_count || 0);
    const sourceSummary = sourceCount > 0 ? ` | ${sourceCount} source examples` : " | 0 source examples";
    const variantCount = Number(target.variant_count || 0);
    const active = targetId === state.corpus.selectedTargetId ? " active" : "";
    const tags = corpusVisibleTags(target.tags || []).slice(0, 6).map((tag) => `<span class="project-badge">${escapeHtml(corpusFeatureLabel(tag))}</span>`).join("");
    return `
      <div class="corpus-card${active}">
        <button type="button" class="corpus-card-main" data-corpus-target="${escapeHtml(targetId)}">
          <span class="corpus-card-title">${escapeHtml(title)}</span>
          <span class="corpus-card-meta">${escapeHtml(target.platform || "")}${size ? ` | ${escapeHtml(size)}` : ""}${count ? ` | ${escapeHtml(count)}` : ""}${escapeHtml(sourceSummary)}</span>
          ${renderCorpusCoverageBadges(target)}
          ${variantCount > 1 ? `<span class="corpus-coverage-list"><span class="project-badge">${escapeHtml(`${variantCount} variants`)}</span></span>` : ""}
          <span class="corpus-tags">${tags}</span>
          ${diskName && diskName !== title ? renderCorpusDiskContext(diskName, diskTargetId) : ""}
        </button>
        ${renderCorpusImportControl(target)}
      </div>
    `;
  }).join("");
  return `
    ${resultHtml}
    <div class="corpus-pager">
      <button type="button" data-corpus-results-prev="1"${state.corpus.resultOffset <= 0 ? " disabled" : ""}>Previous</button>
      <span>${escapeHtml(String((state.corpus.resultOffset || 0) + 1))}-${escapeHtml(String((state.corpus.resultOffset || 0) + rows.length))}</span>
      <button type="button" data-corpus-results-next="1"${state.corpus.resultsHasMore ? "" : " disabled"}>More</button>
    </div>
  `;
}

function renderCorpusCoverageBadges(target) {
  const coverage = target.project_coverage || {};
  const badges = [];
  if (coverage.target_project_id) {
    badges.push(`<span class="project-badge" title="${escapeHtml(`Covered by ${coverage.target_project_id}`)}">File in projects</span>`);
  }
  if (coverage.disk_project_id) {
    badges.push(`<span class="project-badge" title="${escapeHtml(`Covered by ${coverage.disk_project_id}`)}">Disk in projects</span>`);
  }
  return badges.length ? `<span class="corpus-coverage-list">${badges.join("")}</span>` : "";
}

function renderCorpusDiskContext(diskName, diskTargetId) {
  if (!diskTargetId) {
    return `<span class="corpus-card-source">Disk: ${escapeHtml(diskName)}</span>`;
  }
  return `
    <span class="corpus-card-source-row">
      <span role="button" tabindex="0" class="corpus-card-source-button" data-corpus-related-target="${escapeHtml(diskTargetId)}">
        Disk: ${escapeHtml(diskName)}
      </span>
      <span role="button" tabindex="0" class="corpus-disk-browse-button" data-corpus-disk-browse="${escapeHtml(diskTargetId)}" title="Browse disk files" aria-label="Browse disk files">&#128190;</span>
    </span>
  `;
}

function renderCorpusImportControl(target) {
  const targetId = target.id || "";
  const coverage = target.project_coverage || {};
  const modes = Array.isArray(coverage.import_modes) ? coverage.import_modes : [];
  if (!modes.length) {
    return "";
  }
  const availableModes = modes.filter((mode) => mode.available);
  if (!availableModes.length) {
    return '<span class="corpus-coverage-badge" title="Already covered by a project">In Projects</span>';
  }
  const menuOpen = state.corpus.importMenuTargetId === targetId;
  return `
    <button type="button" class="corpus-add-button" data-corpus-import-menu="${escapeHtml(targetId)}" title="Promote to be a real project" aria-label="Promote to be a real project">&#128278;</button>
    ${menuOpen ? `
      <div class="corpus-import-menu">
        ${modes.map((mode) => `
          <button
            type="button"
            data-corpus-import="${escapeHtml(targetId)}"
            data-corpus-import-mode="${escapeHtml(mode.mode || "target")}"
            ${mode.available ? "" : " disabled"}
            title="${escapeHtml(mode.covered_project_id ? `Covered by ${mode.covered_project_id}` : mode.label || "")}"
          >${escapeHtml(mode.label || mode.mode || "Add")}</button>
        `).join("")}
      </div>
    ` : ""}
  `;
}

function renderCorpusDetailHtml() {
  if (!state.corpus.selectedTargetId) {
    return '<div class="empty">Select a corpus target to inspect examples.</div>';
  }
  const sourceXrefs = (state.corpus.xrefs || []).filter((xref) => Number.isInteger(xref.row_index));
  const targetFacts = (state.corpus.xrefs || []).filter((xref) => !Number.isInteger(xref.row_index));
  return `
    <div class="corpus-xrefs">
      ${renderCorpusVariantsHtml()}
      <div class="corpus-detail-title">Source Examples</div>
      ${renderCorpusSourceXrefsHtml(sourceXrefs)}
      ${state.corpus.showTargetFacts ? `
        <div class="corpus-detail-title">Target Facts</div>
        ${renderCorpusFactXrefsHtml(targetFacts)}
      ` : ""}
    </div>
  `;
}

function renderCorpusVariantsHtml() {
  if (state.corpus.variantsLoading) {
    return '<div class="corpus-variants"><div class="corpus-detail-title">Variants</div><div class="progress-detail">Loading variants</div></div>';
  }
  if (state.corpus.variantsError) {
    return `<div class="corpus-variants"><div class="corpus-detail-title">Variants</div><div class="error">${escapeHtml(state.corpus.variantsError)}</div></div>`;
  }
  const payload = state.corpus.variants || {};
  const variants = Array.isArray(payload.variants) ? payload.variants : [];
  if (variants.length <= 1) {
    return "";
  }
  const group = payload.group || {};
  return `
    <div class="corpus-variants">
      <div class="corpus-detail-title">Variants</div>
      <div class="corpus-card-meta">${escapeHtml(group.title_family || "")}${group.display_path ? ` | ${escapeHtml(group.display_path)}` : ""}</div>
      <div class="corpus-variant-list">
        ${variants.map((variant) => {
          const targetId = variant.target_id || "";
          const origin = variant.origin || {};
          const label = origin.display_name || origin.member_name || targetId;
          const selected = variant.selected ? " selected" : "";
          return `
            <button type="button" class="corpus-variant${selected}" data-corpus-variant-compare="${escapeHtml(targetId)}"${variant.selected ? " disabled" : ""}>
              <span>${escapeHtml(label)}</span>
              <span class="corpus-card-meta">${escapeHtml(String(variant.size ?? "?"))} bytes | ${escapeHtml(String(variant.sha256 || "").slice(0, 12))}</span>
            </button>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function renderCorpusSourceXrefsHtml(xrefs) {
  const rows = xrefs || [];
  if (!rows.length) {
    return '<div class="empty">No source-row examples for this filter.</div>';
  }
  const xrefHtml = rows.map((xref) => {
    const active = xref.id === state.corpus.selectedXrefId ? " active" : "";
    const hasSnippet = Number.isInteger(xref.row_index);
    const location = hasSnippet ? `row ${xref.row_index}` : "target";
    const access = xref.access ? `<span class="navigation-badge">${escapeHtml(APP_SLOT_ACCESS_LABELS[xref.access] || xref.access)}</span>` : "";
    const resolution = xref.resolution ? `<span class="navigation-badge">${escapeHtml(String(xref.resolution).replaceAll("_", " "))}</span>` : "";
    const inner = `
      <span class="corpus-xref-feature">${escapeHtml(corpusFeatureLabel(xref.feature || ""))}</span>
      <span class="corpus-xref-text">${escapeHtml(xref.text || xref.symbol || "")}</span>
      <span class="corpus-xref-meta">${escapeHtml(location)}${access}${resolution}</span>
    `;
    return `
      <button type="button" class="corpus-xref${active}" data-corpus-xref="${escapeHtml(xref.id)}">
        ${inner}
      </button>
    `;
  }).join("");
  return `
    ${xrefHtml}
    <div class="corpus-pager">
      <button type="button" data-corpus-xrefs-prev="1"${state.corpus.xrefOffset <= 0 ? " disabled" : ""}>Previous</button>
      <span>${escapeHtml(String((state.corpus.xrefOffset || 0) + 1))}-${escapeHtml(String((state.corpus.xrefOffset || 0) + rows.length))}</span>
      <button type="button" data-corpus-xrefs-next="1"${state.corpus.xrefsHasMore ? "" : " disabled"}>More</button>
    </div>
  `;
}

function renderCorpusFactXrefsHtml(xrefs) {
  const rows = (xrefs || []).slice(0, 80);
  if (!rows.length) {
    return '<div class="empty">No target facts for this filter.</div>';
  }
  return rows.map((xref) => {
    const access = xref.access ? `<span class="navigation-badge">${escapeHtml(APP_SLOT_ACCESS_LABELS[xref.access] || xref.access)}</span>` : "";
    const resolution = xref.resolution ? `<span class="navigation-badge">${escapeHtml(String(xref.resolution).replaceAll("_", " "))}</span>` : "";
    return `
      <div class="corpus-xref corpus-xref-static">
        <span class="corpus-xref-feature">${escapeHtml(corpusFeatureLabel(xref.feature || ""))}</span>
        <span class="corpus-xref-text">${escapeHtml(xref.text || xref.symbol || "")}</span>
        <span class="corpus-xref-meta">target${access}${resolution}</span>
      </div>
    `;
  }).join("");
}

function renderCorpusSnippetHtml(snippet) {
  if (!snippet) {
    return "";
  }
  const rows = snippet.rows || [];
  return `
    <div class="corpus-listing">
      ${rows.map((row, index) => {
        const rowIndex = Number.isInteger(row.row_index) ? row.row_index : Number(snippet.start || 0) + index;
        const active = rowIndex === snippet.highlighted_row_index ? " active" : "";
        const offset = row.start_offset ?? row.addr ?? row.offset ?? null;
        return `
          <div class="corpus-listing-row${active}">
            <span class="corpus-listing-offset">${escapeHtml(formatRowOffset(offset))}</span>
            <span class="corpus-listing-bytes">${escapeHtml(row.bytes || "")}</span>
            <span class="corpus-listing-code">${escapeHtml(row.text || "")}</span>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function renderCorpusSnippetOverlayHtml(snippet, loading = false, error = null) {
  if (!snippet && !loading && !error) {
    return "";
  }
  const selectedXref = (state.corpus.xrefs || []).find((item) => item.id === state.corpus.selectedXrefId) || {};
  const xref = snippet?.xref || selectedXref;
  const target = snippet?.target || {};
  const origin = target.origin || {};
  const title = origin.in_image_path || origin.member_name || origin.display_name || target.id || "Corpus example";
  const subtitle = `${xref.feature || ""}${xref.resolution ? ` | ${String(xref.resolution).replaceAll("_", " ")}` : ""}`;
  let body = "";
  if (loading) {
    body = `
      <div class="corpus-snippet-loading" role="status" aria-live="polite">
        <div class="progress-bar indeterminate"><div class="progress-fill"></div></div>
        <div class="progress-detail">Loading source context</div>
      </div>
    `;
  } else if (error) {
    body = `<div class="error corpus-snippet-error">${escapeHtml(error)}</div>`;
  } else {
    body = renderCorpusSnippetHtml(snippet);
  }
  return `
    <div class="corpus-snippet-overlay" id="corpus-snippet-overlay" role="dialog" aria-modal="true" aria-labelledby="corpus-snippet-title">
      <button type="button" class="corpus-snippet-backdrop" data-corpus-snippet-close="1" aria-label="Close snippet"></button>
      <div class="corpus-snippet-panel">
        <div class="corpus-snippet-header">
          <div>
            <div class="corpus-detail-title" id="corpus-snippet-title">${escapeHtml(title)}</div>
            <div class="corpus-snippet-subtitle">${escapeHtml(subtitle)}</div>
          </div>
          <button type="button" class="corpus-snippet-close" data-corpus-snippet-close="1">Close</button>
        </div>
        ${body}
      </div>
    </div>
  `;
}

function renderCorpusVariantDiffOverlayHtml(diff, loading = false, error = null) {
  if (!diff && !loading && !error) {
    return "";
  }
  const left = diff?.left || {};
  const right = diff?.right || {};
  const title = loading ? "Comparing variants" : `${left.display_name || "Left"} <> ${right.display_name || "Right"}`;
  let body = "";
  if (loading) {
    body = `
      <div class="corpus-snippet-loading" role="status" aria-live="polite">
        <div class="progress-bar indeterminate"><div class="progress-fill"></div></div>
        <div class="progress-detail">Loading variant diff</div>
      </div>
    `;
  } else if (error) {
    body = `<div class="error corpus-snippet-error">${escapeHtml(error)}</div>`;
  } else {
    body = renderCorpusByteDiff(diff.byte_diff || {});
  }
  return `
    <div class="corpus-snippet-overlay" id="corpus-variant-diff-overlay" role="dialog" aria-modal="true" aria-labelledby="corpus-variant-diff-title">
      <button type="button" class="corpus-snippet-backdrop" data-corpus-diff-close="1" aria-label="Close diff"></button>
      <div class="corpus-snippet-panel">
        <div class="corpus-snippet-header">
          <div>
            <div class="corpus-detail-title" id="corpus-variant-diff-title">${escapeHtml(title)}</div>
            <div class="corpus-snippet-subtitle">${escapeHtml([left.disk_name, right.disk_name].filter(Boolean).join(" <> "))}</div>
          </div>
          <button type="button" class="corpus-snippet-close" data-corpus-diff-close="1">Close</button>
        </div>
        ${body}
      </div>
    </div>
  `;
}

function renderDiskBrowserOverlayHtml() {
  const browser = state.diskBrowser.payload;
  const loading = state.diskBrowser.loading;
  const error = state.diskBrowser.error;
  const view = state.diskBrowser.view;
  if (!browser && !loading && !error) {
    return "";
  }
  const disk = browser?.disk || {};
  const entries = Array.isArray(browser?.entries) ? browser.entries : [];
  const selectedEntry = browser?.selected_entry || null;
  const selectedContent = selectedEntry?.content || null;
  const activeView = selectedContent ? view : "entries";
  const title = loading ? "Disk files" : (disk.display_name || "Disk files");
  const path = browser?.path || "";
  let body = "";
  if (loading) {
    body = `
      <div class="corpus-snippet-loading" role="status" aria-live="polite">
        <div class="progress-bar indeterminate"><div class="progress-fill"></div></div>
        <div class="progress-detail">Loading disk files</div>
      </div>
    `;
  } else if (error) {
    body = `<div class="error corpus-snippet-error">${escapeHtml(error)}</div>`;
  } else {
    body = `
      <div class="corpus-disk-browser-toolbar">
        ${browser.parent_path !== null && browser.parent_path !== undefined ? `<button type="button" data-disk-browser-path="${escapeHtml(browser.parent_path)}">Up</button>` : ""}
        <span>${escapeHtml(path || "/")}</span>
      </div>
      ${selectedEntry ? renderDiskEntryDetail(selectedEntry) : ""}
      ${selectedContent ? renderDiskViewTabs(activeView, selectedContent) : ""}
      ${activeView === "entries" ? renderDiskEntryList(entries) : renderDiskContentView(selectedContent, activeView)}
    `;
  }
  return `
    <div class="corpus-snippet-overlay" id="corpus-disk-browser-overlay" role="dialog" aria-modal="true" aria-labelledby="corpus-disk-browser-title">
      <button type="button" class="corpus-snippet-backdrop" data-disk-browser-close="1" aria-label="Close disk browser"></button>
      <div class="corpus-snippet-panel corpus-disk-browser-panel">
        <div class="corpus-snippet-header">
          <div>
            <div class="corpus-detail-title" id="corpus-disk-browser-title">${escapeHtml(title)}</div>
            <div class="corpus-snippet-subtitle">${escapeHtml([disk.disk_name, path].filter(Boolean).join(" / "))}</div>
          </div>
          ${renderDiskBrowserImportAction(disk)}
          <button type="button" class="corpus-snippet-close" data-disk-browser-close="1">Close</button>
        </div>
        ${body}
      </div>
    </div>
  `;
}

function renderDiskBrowserImportAction(disk) {
  const coverage = disk?.project_coverage || {};
  const modes = Array.isArray(coverage.import_modes) ? coverage.import_modes : [];
  const diskMode = modes.find((mode) => mode.mode === "disk");
  if (!diskMode) {
    return "";
  }
  const targetId = diskMode.corpus_target_id || disk.corpus_target_id || disk.id || "";
  if (!targetId) {
    return "";
  }
  if (diskMode.available) {
    return `
      <button
        type="button"
        class="corpus-disk-promote-button"
        data-corpus-import="${escapeHtml(targetId)}"
        data-corpus-import-mode="disk"
        title="Promote disk to be a real project"
      >Promote disk</button>
    `;
  }
  return `<span class="corpus-coverage-badge" title="${escapeHtml(diskMode.covered_project_id ? `Covered by ${diskMode.covered_project_id}` : "Already covered by a project")}">${escapeHtml(diskMode.label || "Disk in Projects")}</span>`;
}

function renderDiskEntryList(entries) {
  return `
    <div class="corpus-disk-entry-list">
      ${entries.map((entry) => renderDiskEntryRow(entry)).join("") || '<div class="empty">No entries.</div>'}
    </div>
  `;
}

function renderDiskViewTabs(view, content) {
  const tabs = [
    ["entries", "Entries", true],
    ["text", "Text", Boolean(content.text_available)],
    ["bytes", "Bytes", true],
    ["hexdump", "Hexdump", true],
  ];
  return `
    <div class="corpus-disk-view-tabs">
      ${tabs.map(([id, label, enabled]) => `
        <button type="button" data-disk-browser-view="${escapeHtml(id)}" class="${id === view ? "active" : ""}"${enabled ? "" : " disabled"}>
          ${escapeHtml(label)}
        </button>
      `).join("")}
    </div>
  `;
}

function renderDiskContentView(content, view) {
  if (!content) {
    return "";
  }
  if (content.error) {
    return `<div class="error corpus-disk-content-error">${escapeHtml(content.error)}</div>`;
  }
  const truncated = content.truncated ? '<div class="progress-detail">Preview truncated.</div>' : "";
  if (view === "text") {
    return `<div class="corpus-disk-content">${truncated}<pre>${escapeHtml(content.text || "")}</pre></div>`;
  }
  if (view === "bytes") {
    return `<div class="corpus-disk-content">${truncated}<pre>${escapeHtml(content.bytes || "")}</pre></div>`;
  }
  const rows = Array.isArray(content.hexdump) ? content.hexdump : [];
  return `
    <div class="corpus-disk-content">
      ${truncated}
      <div class="corpus-disk-hexdump">
        ${rows.map((row) => `
          <span class="corpus-disk-hexdump-offset">${escapeHtml(formatByteOffset(row.offset || 0))}</span>
          <span class="corpus-disk-hexdump-hex">${escapeHtml(row.hex || "")}</span>
          <span class="corpus-disk-hexdump-ascii">${escapeHtml(row.ascii || "")}</span>
        `).join("")}
      </div>
    </div>
  `;
}

function renderDiskEntryRow(entry) {
  const path = entry.path || "";
  const icon = entry.is_directory ? "\u{1F4C1}" : "\u{1F4C4}";
  const targetAction = entry.target_id
    ? `<span role="button" tabindex="0" class="corpus-disk-target-button" data-disk-browser-target="${escapeHtml(entry.target_id)}">Open</span>`
    : (entry.importable
      ? `<span role="button" tabindex="0" class="corpus-disk-target-button" data-disk-browser-import="${escapeHtml(path)}">Import</span>`
      : "");
  return `
    <button type="button" class="corpus-disk-entry${entry.is_directory ? " directory" : " file"}" data-disk-browser-path="${escapeHtml(path)}">
      <span class="corpus-disk-entry-name">${icon} ${escapeHtml(entry.name || path)}</span>
      <span class="corpus-disk-entry-type">${escapeHtml(entry.type || entry.kind_name || "")}</span>
      <span class="corpus-disk-entry-size">${escapeHtml(formatFileSize(entry.size))}</span>
      ${targetAction}
    </button>
  `;
}

function renderDiskEntryDetail(entry) {
  const targetId = entry.target_id || "";
  const importAction = targetId ? "" : (entry.importable
    ? `<span role="button" tabindex="0" class="corpus-disk-target-button" data-disk-browser-import="${escapeHtml(entry.path || "")}">Import</span>`
    : ""
  );
  return `
    <div class="corpus-disk-entry-detail">
      <span>${escapeHtml(entry.name || entry.path || "")}</span>
      <span>${escapeHtml(entry.type || "")}</span>
      <span>${escapeHtml(formatFileSize(entry.size))}</span>
      ${targetId ? `<span role="button" tabindex="0" data-disk-browser-target="${escapeHtml(targetId)}" class="corpus-disk-target-button">Open target</span>` : ""}
      ${importAction}
    </div>
  `;
}

function renderCorpusByteDiff(byteDiff) {
  const regions = byteDiff.regions || [];
  return `
    <div class="corpus-diff-summary">
      First diff: ${escapeHtml(formatByteOffset(byteDiff.first_diff))}
      | regions: ${escapeHtml(String(byteDiff.region_count || 0))}
      | sizes: ${escapeHtml(String(byteDiff.left_size || 0))} / ${escapeHtml(String(byteDiff.right_size || 0))}
      | space: ${escapeHtml(byteDiff.left_space || "file")} / ${escapeHtml(byteDiff.right_space || "file")}
      ${byteDiff.truncated_region_count ? ` | hidden: ${escapeHtml(String(byteDiff.truncated_region_count))}` : ""}
    </div>
    <div class="corpus-diff-legend">
      <span class="corpus-diff-chip corpus-diff-chip-shifted_address">shifted address</span>
      <span class="corpus-diff-chip corpus-diff-chip-address_only">address-only</span>
      <span class="corpus-diff-chip corpus-diff-chip-addressing_mode">address mode</span>
      <span class="corpus-diff-chip corpus-diff-chip-immediate_semantic">immediate value</span>
      <span class="corpus-diff-chip corpus-diff-chip-semantic">semantic</span>
    </div>
    <div class="corpus-byte-diff-list">
      ${regions.map((region) => renderCorpusByteDiffRegion(region)).join("") || '<div class="empty">No byte differences.</div>'}
      ${(byteDiff.trailing_skipped_left || byteDiff.trailing_skipped_right) ? `
        <div class="corpus-byte-skip">Skipped tail: left +${escapeHtml(String(byteDiff.trailing_skipped_left || 0))} bytes, right +${escapeHtml(String(byteDiff.trailing_skipped_right || 0))} bytes</div>
      ` : ""}
    </div>
  `;
}

function renderCorpusByteDiffRegion(region) {
  const leftLength = Number(region.left_length ?? region.length ?? 0);
  const rightLength = Number(region.right_length ?? region.length ?? 0);
  const skippedLeft = Number(region.skipped_left || 0);
  const skippedRight = Number(region.skipped_right || 0);
  return `
    ${(skippedLeft || skippedRight) ? `<div class="corpus-byte-skip">Skipped equal span: left +${escapeHtml(String(skippedLeft))} bytes, right +${escapeHtml(String(skippedRight))} bytes</div>` : ""}
    <div class="corpus-byte-region">
      <div class="corpus-byte-region-head">
        <span>${escapeHtml(region.kind || "change")}</span>
        <span>left ${escapeHtml(formatByteOffset(region.left_start ?? region.offset))} +${escapeHtml(String(leftLength))}</span>
        <span>right ${escapeHtml(formatByteOffset(region.right_start ?? region.offset))} +${escapeHtml(String(rightLength))}</span>
        ${renderCorpusDiffSummary(region.diff_summary || {})}
      </div>
      <div class="corpus-byte-hex-pair">
        <pre>${renderCorpusHexBytes(region.left_hex || "", region.left_start ?? region.offset, "left")}${region.left_hex_truncated ? ` <span class="corpus-byte-truncated">... +${escapeHtml(String(region.left_hex_truncated))} bytes</span>` : ""}</pre>
        <pre>${renderCorpusHexBytes(region.right_hex || "", region.right_start ?? region.offset, "right")}${region.right_hex_truncated ? ` <span class="corpus-byte-truncated">... +${escapeHtml(String(region.right_hex_truncated))} bytes</span>` : ""}</pre>
      </div>
      ${renderCorpusDiffContextPairs(region.context_pairs || [])}
    </div>
  `;
}

function renderCorpusDiffSummary(summary) {
  const classes = summary.classes || {};
  const entries = Object.entries(classes).filter(([, count]) => Number(count) > 0);
  if (!entries.length) {
    return "";
  }
  return `
    <span class="corpus-diff-class-summary">
      ${entries.map(([name, count]) => `<span class="corpus-diff-chip corpus-diff-chip-${escapeHtml(cssClassToken(name))}">${escapeHtml(diffClassLabel(name))}: ${escapeHtml(String(count))}</span>`).join("")}
    </span>
  `;
}

function renderCorpusHexBytes(hex, baseOffset, side) {
  const base = Number(baseOffset);
  if (!Number.isFinite(base)) {
    return escapeHtml(hex);
  }
  const bytes = [];
  for (let index = 0; index + 1 < hex.length; index += 2) {
    const offset = base + Math.floor(index / 2);
    const byteText = hex.slice(index, index + 2);
    bytes.push(`<span class="corpus-byte-byte" data-byte-side="${escapeHtml(side)}" data-byte-offset="${escapeHtml(String(offset))}">${escapeHtml(byteText)}</span>`);
  }
  return bytes.join("");
}

function renderCorpusDiffContextPairs(pairs) {
  if (!pairs.length) {
    return "";
  }
  return `
    <div class="corpus-byte-context-pairs">
      <div class="corpus-byte-context-head">
        <span>Left context</span>
        <span>Right context</span>
      </div>
      ${pairs.map((pair) => {
        const left = pair.left || {};
        const right = pair.right || {};
        const sameText = pair.same_text === true;
        const sameOffset = pair.same_offset === true;
        const diffClass = pair.diff_class || (sameText ? "unchanged" : "semantic");
        const comparedText = compareInlineSourceText((left.text || "").trim(), (right.text || "").trim(), diffClass);
        return `
        <div class="corpus-byte-context-pair corpus-diff-row-${escapeHtml(cssClassToken(diffClass))}${sameText ? "" : " text-diff"}${sameOffset ? "" : " offset-diff"}"
          data-left-start="${escapeHtml(String(contextRowHighlightStart(left)))}"
          data-left-end="${escapeHtml(String(contextRowHighlightEnd(left)))}"
          data-right-start="${escapeHtml(String(contextRowHighlightStart(right)))}"
          data-right-end="${escapeHtml(String(contextRowHighlightEnd(right)))}">
          <span class="corpus-byte-context-offset${sameOffset ? "" : " changed"}">${escapeHtml(formatByteOffset(contextRowStart(left)))}</span>
          <span class="corpus-byte-context-text${sameText ? "" : " changed"}">${comparedText.left}${renderContextDiffBadge(pair)}</span>
          <span class="corpus-byte-context-offset${sameOffset ? "" : " changed"}">${escapeHtml(formatByteOffset(contextRowStart(right)))}</span>
          <span class="corpus-byte-context-text${sameText ? "" : " changed"}">${comparedText.right}</span>
        </div>
      `; }).join("")}
    </div>
  `;
}

function renderContextDiffBadge(pair) {
  const diffClass = pair.diff_class || "semantic";
  if (diffClass === "unchanged") {
    return "";
  }
  const label = pair.diff_label || diffClassLabel(diffClass);
  return ` <span class="corpus-diff-chip corpus-diff-chip-${escapeHtml(cssClassToken(diffClass))}">${escapeHtml(label)}</span>`;
}

function compareInlineSourceText(leftText, rightText, diffClass = "semantic") {
  if (leftText === rightText) {
    return {left: escapeHtml(leftText), right: escapeHtml(rightText)};
  }
  const tokenClass = inlineDiffClass(diffClass);
  const leftTokens = tokenizeSourceText(leftText);
  const rightTokens = tokenizeSourceText(rightText);
  const table = Array.from({length: leftTokens.length + 1}, () => Array(rightTokens.length + 1).fill(0));
  for (let leftIndex = leftTokens.length - 1; leftIndex >= 0; leftIndex -= 1) {
    for (let rightIndex = rightTokens.length - 1; rightIndex >= 0; rightIndex -= 1) {
      table[leftIndex][rightIndex] = leftTokens[leftIndex] === rightTokens[rightIndex]
        ? table[leftIndex + 1][rightIndex + 1] + 1
        : Math.max(table[leftIndex + 1][rightIndex], table[leftIndex][rightIndex + 1]);
    }
  }
  const leftParts = [];
  const rightParts = [];
  let leftIndex = 0;
  let rightIndex = 0;
  while (leftIndex < leftTokens.length || rightIndex < rightTokens.length) {
    if (leftIndex < leftTokens.length && rightIndex < rightTokens.length && leftTokens[leftIndex] === rightTokens[rightIndex]) {
      leftParts.push(escapeHtml(leftTokens[leftIndex]));
      rightParts.push(escapeHtml(rightTokens[rightIndex]));
      leftIndex += 1;
      rightIndex += 1;
      continue;
    }
    if (rightIndex >= rightTokens.length || (leftIndex < leftTokens.length && table[leftIndex + 1][rightIndex] >= table[leftIndex][rightIndex + 1])) {
      leftParts.push(`<span class="${tokenClass}">${escapeHtml(leftTokens[leftIndex])}</span>`);
      leftIndex += 1;
    } else {
      rightParts.push(`<span class="${tokenClass}">${escapeHtml(rightTokens[rightIndex])}</span>`);
      rightIndex += 1;
    }
  }
  return {left: leftParts.join(""), right: rightParts.join("")};
}

function inlineDiffClass(diffClass) {
  return `corpus-inline-diff corpus-inline-diff-${cssClassToken(diffClass)}`;
}

function cssClassToken(value) {
  return String(value || "semantic").replace(/[^A-Za-z0-9_-]/g, "_");
}

function diffClassLabel(value) {
  const labels = {
    shifted_address: "shifted address",
    address_only: "address-only",
    target_change: "target change",
    addressing_mode: "address mode",
    immediate_semantic: "immediate value",
    semantic: "semantic",
    missing_row: "missing row",
  };
  return labels[value] || String(value || "semantic").replace(/_/g, " ");
}

function tokenizeSourceText(text) {
  return String(text || "").match(/\$[0-9A-Fa-f]+|[A-Za-z_][A-Za-z0-9_]*|\d+|\s+|./g) || [];
}

function contextRowStart(row) {
  const value = Number(row?.start_offset ?? row?.addr);
  return Number.isFinite(value) ? value : null;
}

function contextRowEnd(row) {
  const explicit = Number(row?.end_offset);
  if (Number.isFinite(explicit) && explicit > Number(contextRowStart(row))) {
    return explicit;
  }
  const start = contextRowStart(row);
  if (start === null) {
    return null;
  }
  const byteText = typeof row?.bytes === "string" ? row.bytes : "";
  return start + Math.max(1, Math.floor(byteText.length / 2));
}

function contextRowHighlightStart(row) {
  const value = Number(row?.diff_start_offset ?? row?.start_offset ?? row?.addr);
  return Number.isFinite(value) ? value : null;
}

function contextRowHighlightEnd(row) {
  const explicit = Number(row?.diff_end_offset);
  if (Number.isFinite(explicit) && explicit > Number(contextRowHighlightStart(row))) {
    return explicit;
  }
  const start = contextRowHighlightStart(row);
  if (start === null) {
    return null;
  }
  const byteText = typeof row?.bytes === "string" ? row.bytes : "";
  return start + Math.max(1, Math.floor(byteText.length / 2));
}

function setCorpusByteHighlight(row, enabled) {
  const region = row.closest(".corpus-byte-region");
  if (!region) {
    return;
  }
  [
    ["left", Number(row.dataset.leftStart), Number(row.dataset.leftEnd)],
    ["right", Number(row.dataset.rightStart), Number(row.dataset.rightEnd)],
  ].forEach(([side, start, end]) => {
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
      return;
    }
    region.querySelectorAll(`[data-byte-side="${side}"]`).forEach((byteNode) => {
      const offset = Number(byteNode.dataset.byteOffset);
      if (Number.isFinite(offset) && offset >= start && offset < end) {
        byteNode.classList.toggle("highlight", enabled);
      }
    });
  });
}

function bindCorpusHome() {
  document.querySelectorAll("[data-home-view]").forEach((button) => {
    button.addEventListener("click", () => {
      state.homeView = button.dataset.homeView || "projects";
      void renderHome();
    });
  });
  document.getElementById("corpus-search-button")?.addEventListener("click", () => {
    updateCorpusFiltersFromControls();
    resetCorpusResultPaging();
    void renderHome();
  });
  document.getElementById("corpus-feature")?.addEventListener("change", () => {
    updateCorpusFiltersFromControls();
    if (state.corpus.feature) {
      state.corpus.group = "";
    }
    state.corpus.selectedTargetId = null;
    state.corpus.xrefs = [];
    state.corpus.snippet = null;
    state.corpus.snippetError = null;
    resetCorpusResultPaging();
    void renderHome();
  });
  document.getElementById("corpus-group")?.addEventListener("change", () => {
    updateCorpusFiltersFromControls();
    if (state.corpus.feature && !corpusFeatureMatchesGroup(state.corpus.feature, state.corpus.group)) {
      state.corpus.feature = "";
    }
    state.corpus.selectedTargetId = null;
    state.corpus.xrefs = [];
    state.corpus.snippet = null;
    state.corpus.snippetError = null;
    resetCorpusResultPaging();
    void renderHome();
  });
  document.getElementById("corpus-platform")?.addEventListener("change", () => {
    updateCorpusFiltersFromControls();
    state.corpus.selectedTargetId = null;
    state.corpus.xrefs = [];
    state.corpus.snippet = null;
    state.corpus.snippetError = null;
    resetCorpusResultPaging();
    void renderHome();
  });
  document.getElementById("corpus-show-facts")?.addEventListener("change", () => {
    updateCorpusFiltersFromControls();
    state.corpus.snippet = null;
    state.corpus.snippetError = null;
    if (state.corpus.selectedTargetId) {
      void selectCorpusTarget(state.corpus.selectedTargetId);
    } else {
      void renderHome();
    }
  });
  document.querySelectorAll("[data-corpus-group]").forEach((button) => {
    button.addEventListener("click", () => {
      state.corpus.group = button.dataset.corpusGroup || "";
      state.corpus.feature = "";
      state.corpus.selectedTargetId = null;
      state.corpus.xrefs = [];
      state.corpus.snippet = null;
      state.corpus.snippetError = null;
      resetCorpusResultPaging();
      void renderHome();
    });
  });
  document.getElementById("corpus-search")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      updateCorpusFiltersFromControls();
      resetCorpusResultPaging();
      void renderHome();
    }
  });
  document.querySelector("[data-corpus-results-prev]")?.addEventListener("click", () => {
    state.corpus.resultOffset = Math.max(0, (state.corpus.resultOffset || 0) - (state.corpus.resultLimit || 40));
    state.corpus.selectedTargetId = null;
    state.corpus.xrefs = [];
    state.corpus.snippet = null;
    state.corpus.snippetError = null;
    void renderHome();
  });
  document.querySelector("[data-corpus-results-next]")?.addEventListener("click", () => {
    state.corpus.resultOffset = (state.corpus.resultOffset || 0) + (state.corpus.resultLimit || 40);
    state.corpus.selectedTargetId = null;
    state.corpus.xrefs = [];
    state.corpus.snippet = null;
    state.corpus.snippetError = null;
    void renderHome();
  });
  document.querySelector("[data-corpus-xrefs-prev]")?.addEventListener("click", () => {
    state.corpus.xrefOffset = Math.max(0, (state.corpus.xrefOffset || 0) - (state.corpus.xrefLimit || 120));
    void selectCorpusTarget(state.corpus.selectedTargetId || "");
  });
  document.querySelector("[data-corpus-xrefs-next]")?.addEventListener("click", () => {
    state.corpus.xrefOffset = (state.corpus.xrefOffset || 0) + (state.corpus.xrefLimit || 120);
    void selectCorpusTarget(state.corpus.selectedTargetId || "");
  });
  document.querySelectorAll("[data-corpus-target]").forEach((button) => {
    button.addEventListener("click", () => {
      void selectCorpusTarget(button.dataset.corpusTarget || "");
    });
  });
  document.querySelectorAll("[data-corpus-related-target]").forEach((button) => {
    const selectRelatedTarget = (event) => {
      event.stopPropagation();
      void selectCorpusTarget(button.dataset.corpusRelatedTarget || "");
    };
    button.addEventListener("click", selectRelatedTarget);
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectRelatedTarget(event);
      }
    });
  });
  document.querySelectorAll("[data-corpus-disk-browse]").forEach((button) => {
    const openDisk = (event) => {
      event.stopPropagation();
      void openCorpusDiskBrowser(button.dataset.corpusDiskBrowse || "", "");
    };
    button.addEventListener("click", openDisk);
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openDisk(event);
      }
    });
  });
  document.querySelectorAll("[data-corpus-xref]").forEach((button) => {
    button.addEventListener("click", () => {
      void selectCorpusXref(button.dataset.corpusXref || "");
    });
  });
  document.querySelectorAll("[data-corpus-variant-compare]").forEach((button) => {
    button.addEventListener("click", () => {
      void selectCorpusVariantDiff(button.dataset.corpusVariantCompare || "");
    });
  });
  document.querySelectorAll("[data-corpus-snippet-close]").forEach((button) => {
    button.addEventListener("click", () => {
      void closeCorpusSnippetOverlay();
    });
  });
  document.querySelectorAll("[data-corpus-diff-close]").forEach((button) => {
    button.addEventListener("click", () => {
      void closeCorpusVariantDiffOverlay();
    });
  });
  bindDiskBrowserControls();
  document.querySelectorAll(".corpus-byte-context-pair").forEach((row) => {
    row.addEventListener("mouseenter", () => setCorpusByteHighlight(row, true));
    row.addEventListener("mouseleave", () => setCorpusByteHighlight(row, false));
  });
  document.querySelectorAll("[data-corpus-import]").forEach((button) => {
    button.addEventListener("click", () => {
      void importCorpusTarget(button.dataset.corpusImport || "", button.dataset.corpusImportMode || "target");
    });
  });
  document.querySelectorAll("[data-corpus-import-menu]").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.dataset.corpusImportMenu || "";
      state.corpus.importMenuTargetId = state.corpus.importMenuTargetId === targetId ? null : targetId;
      void renderHome();
    });
  });
}

function bindDiskBrowserControls() {
  document.querySelectorAll("[data-disk-browser-path]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      void reopenDiskBrowser(button.dataset.diskBrowserPath || "");
    });
  });
  document.querySelectorAll("[data-disk-browser-view]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      state.diskBrowser.view = button.dataset.diskBrowserView || "entries";
      void renderDiskBrowserHost();
    });
  });
  document.querySelectorAll("[data-disk-browser-target]").forEach((button) => {
    const openTarget = (event) => {
      event.stopPropagation();
      const targetId = button.dataset.diskBrowserTarget || "";
      resetDiskBrowser();
      void selectCorpusTarget(targetId);
    };
    button.addEventListener("click", openTarget);
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openTarget(event);
      }
    });
  });
  document.querySelectorAll("[data-disk-browser-import]").forEach((button) => {
    const importEntry = () => {
      const requestKey = state.diskBrowser.requestKey || "";
      const prefix = "project:";
      if (!requestKey.startsWith(prefix)) {
        return;
      }
      const projectId = requestKey.slice(prefix.length);
      const path = button.dataset.diskBrowserImport || "";
      if (!projectId || !path) {
        return;
      }
      void importDiskProjectFile(projectId, path);
      resetDiskBrowser();
    };
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      importEntry();
    });
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        importEntry();
      }
    });
  });
  document.querySelectorAll("[data-disk-browser-close]").forEach((button) => {
    button.addEventListener("click", () => {
      void closeDiskBrowserOverlay();
    });
  });
}

function resetCorpusResultPaging() {
  state.corpus.resultOffset = 0;
  state.corpus.xrefOffset = 0;
  state.corpus.xrefsHasMore = false;
  state.corpus.resultsQueryKey = "";
  state.corpus.results = [];
  state.corpus.resultsHasMore = false;
  state.corpus.resultsError = null;
  state.corpus.resultsLoaded = false;
}

function updateCorpusFiltersFromControls() {
  state.corpus.feature = document.getElementById("corpus-feature")?.value || "";
  state.corpus.group = document.getElementById("corpus-group")?.value || "";
  state.corpus.platform = document.getElementById("corpus-platform")?.value || "";
  state.corpus.q = document.getElementById("corpus-search")?.value || "";
  state.corpus.showTargetFacts = Boolean(document.getElementById("corpus-show-facts")?.checked);
}

async function selectCorpusTarget(targetId) {
  if (!targetId) {
    return;
  }
  const requestToken = state.corpus.targetRequestToken + 1;
  state.corpus.targetRequestToken = requestToken;
  const previousTargetId = state.corpus.selectedTargetId;
  state.corpus.selectedTargetId = targetId;
  state.corpus.selectedXrefId = null;
  state.corpus.snippet = null;
  state.corpus.snippetLoading = false;
  state.corpus.snippetError = null;
  state.corpus.variants = null;
  const selectedTarget = (state.corpus.results || []).find((item) => item.id === targetId) || {};
  const shouldLoadVariants = Number(selectedTarget.variant_count || 0) > 1;
  state.corpus.variantsLoading = shouldLoadVariants;
  state.corpus.variantsError = null;
  state.corpus.variantDiff = null;
  state.corpus.variantDiffLoading = false;
  state.corpus.variantDiffError = null;
  if (previousTargetId !== targetId) {
    state.corpus.xrefOffset = 0;
  }
  const params = new URLSearchParams({target_id: targetId});
  if (state.corpus.feature) {
    params.set("feature", state.corpus.feature);
  }
  if (state.corpus.group) {
    params.set("group", state.corpus.group);
  }
  if (!state.corpus.showTargetFacts) {
    params.set("source_only", "1");
  }
  const limit = state.corpus.xrefLimit || 120;
  params.set("offset", String(state.corpus.xrefOffset || 0));
  params.set("limit", String(limit + 1));
  const rows = await fetchJson(`/api/corpus/xrefs?${params}`);
  if (state.corpus.targetRequestToken !== requestToken || state.corpus.selectedTargetId !== targetId) {
    return;
  }
  state.corpus.xrefsHasMore = rows.length > limit;
  state.corpus.xrefs = rows.slice(0, limit);
  if (shouldLoadVariants) {
    try {
      const variants = await fetchJson(`/api/corpus/variants?target_id=${encodeURIComponent(targetId)}`);
      if (state.corpus.targetRequestToken !== requestToken || state.corpus.selectedTargetId !== targetId) {
        return;
      }
      state.corpus.variants = variants;
    } catch (err) {
      if (state.corpus.targetRequestToken !== requestToken || state.corpus.selectedTargetId !== targetId) {
        return;
      }
      state.corpus.variants = null;
      state.corpus.variantsError = String(err.message || err);
    } finally {
      if (state.corpus.targetRequestToken === requestToken && state.corpus.selectedTargetId === targetId) {
        state.corpus.variantsLoading = false;
      }
    }
  }
  if (state.corpus.targetRequestToken !== requestToken || state.corpus.selectedTargetId !== targetId) {
    return;
  }
  await renderHome();
}

async function selectCorpusXref(xrefId) {
  if (!xrefId) {
    return;
  }
  const xref = (state.corpus.xrefs || []).find((item) => item.id === xrefId);
  if (!xref || !Number.isInteger(xref.row_index)) {
    state.corpus.selectedXrefId = null;
    state.corpus.snippet = null;
    state.corpus.snippetLoading = false;
    state.corpus.snippetError = null;
    await renderHome();
    return;
  }
  state.corpus.selectedXrefId = xrefId;
  state.corpus.snippet = null;
  state.corpus.snippetLoading = true;
  state.corpus.snippetError = null;
  await renderHome();
  try {
    state.corpus.snippet = await fetchJson(`/api/corpus/snippet?xref_id=${encodeURIComponent(xrefId)}&before=20&after=20`);
  } catch (err) {
    state.corpus.snippet = null;
    state.corpus.snippetError = String(err.message || err);
  } finally {
    state.corpus.snippetLoading = false;
  }
  await renderHome();
}

async function closeCorpusSnippetOverlay() {
  state.corpus.snippet = null;
  state.corpus.snippetLoading = false;
  state.corpus.snippetError = null;
  await renderHome();
}

async function selectCorpusVariantDiff(rightTargetId) {
  const leftTargetId = state.corpus.selectedTargetId || "";
  if (!leftTargetId || !rightTargetId || leftTargetId === rightTargetId) {
    return;
  }
  state.corpus.variantDiff = null;
  state.corpus.variantDiffLoading = true;
  state.corpus.variantDiffError = null;
  await renderHome();
  try {
    const params = new URLSearchParams({
      left_target_id: leftTargetId,
      right_target_id: rightTargetId,
    });
    state.corpus.variantDiff = await fetchJson(`/api/corpus/diff?${params}`);
  } catch (err) {
    state.corpus.variantDiff = null;
    state.corpus.variantDiffError = String(err.message || err);
  } finally {
    state.corpus.variantDiffLoading = false;
  }
  await renderHome();
}

async function closeCorpusVariantDiffOverlay() {
  state.corpus.variantDiff = null;
  state.corpus.variantDiffLoading = false;
  state.corpus.variantDiffError = null;
  await renderHome();
}

async function openCorpusDiskBrowser(targetId, path = "") {
  if (!targetId) {
    return;
  }
  await openDiskBrowser({
    requestKey: `corpus:${targetId}`,
    path,
    urlForPath: (entryPath) => {
      const params = new URLSearchParams({target_id: targetId});
      if (entryPath) {
        params.set("path", entryPath);
      }
      return `/api/corpus/disk?${params}`;
    },
  });
}

async function openProjectDiskBrowser(projectId, path = "") {
  if (!projectId) {
    return;
  }
  await openDiskBrowser({
    requestKey: `project:${projectId}`,
    path,
    urlForPath: (entryPath) => {
      const params = new URLSearchParams();
      if (entryPath) {
        params.set("path", entryPath);
      }
      const query = params.toString();
      return `/api/projects/${encodeURIComponent(projectId)}/disk-browser${query ? `?${query}` : ""}`;
    },
  });
}

async function openDiskBrowser({requestKey, path = "", urlForPath}) {
  const requestToken = state.diskBrowser.requestToken + 1;
  state.diskBrowser.requestToken = requestToken;
  state.diskBrowser.requestKey = requestKey;
  state.diskBrowser.urlForPath = urlForPath;
  state.diskBrowser.payload = null;
  state.diskBrowser.loading = true;
  state.diskBrowser.error = null;
  await renderDiskBrowserHost();
  try {
    const payload = await fetchJson(urlForPath(path));
    if (state.diskBrowser.requestToken !== requestToken || state.diskBrowser.requestKey !== requestKey) {
      return;
    }
    state.diskBrowser.payload = payload;
    state.diskBrowser.view = defaultDiskBrowserView(payload);
  } catch (err) {
    if (state.diskBrowser.requestToken !== requestToken || state.diskBrowser.requestKey !== requestKey) {
      return;
    }
    state.diskBrowser.payload = null;
    state.diskBrowser.error = String(err.message || err);
  } finally {
    if (state.diskBrowser.requestToken === requestToken && state.diskBrowser.requestKey === requestKey) {
      state.diskBrowser.loading = false;
    }
  }
  await renderDiskBrowserHost();
}

async function reopenDiskBrowser(path = "") {
  if (!state.diskBrowser.requestKey || typeof state.diskBrowser.urlForPath !== "function") {
    return;
  }
  await openDiskBrowser({
    requestKey: state.diskBrowser.requestKey,
    path,
    urlForPath: state.diskBrowser.urlForPath,
  });
}

async function closeDiskBrowserOverlay() {
  resetDiskBrowser();
  await renderDiskBrowserHost();
}

function resetDiskBrowser() {
  state.diskBrowser.payload = null;
  state.diskBrowser.loading = false;
  state.diskBrowser.error = null;
  state.diskBrowser.requestKey = null;
  state.diskBrowser.requestToken += 1;
  state.diskBrowser.view = "entries";
  state.diskBrowser.urlForPath = null;
}

async function renderDiskBrowserHost() {
  if (state.homeView === "corpus" && !state.project) {
    await renderHome();
    return;
  }
  if (state.projectData?.project?.kind === "disk") {
    renderDiskProject(state.projectData);
  }
}

function defaultDiskBrowserView(payload) {
  const content = payload?.selected_entry?.content || null;
  if (!content) {
    return "entries";
  }
  if (content.error) {
    return "hexdump";
  }
  return content.text_available ? "text" : "hexdump";
}

async function importCorpusTarget(targetId, mode = "target") {
  if (!targetId) {
    return;
  }
  const error = document.getElementById("home-error");
  error.textContent = "";
  try {
    const focus = corpusSelectedFocus();
    const job = await fetchJson("/api/corpus/import", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({target_id: targetId, mode}),
    });
    state.corpus.importMenuTargetId = null;
    const jobState = await waitForAsyncJob(
      (jobId) => `/api/projects/create/status?job_id=${encodeURIComponent(jobId)}`,
      job,
      null,
      (currentJob) => setHomeOverlay(renderProgressOverlay(currentJob, mode === "disk" ? "Adding corpus disk" : "Adding corpus target")),
    );
    clearHomeOverlay();
    if (jobState.result_project_id) {
      if (focus) {
        state.pendingCorpusFocus = {...focus, projectId: jobState.result_project_id};
      }
      navigateToProject(jobState.result_project_id);
    }
  } catch (err) {
    clearHomeOverlay();
    error.textContent = String(err.message || err);
  }
}

function corpusSelectedFocus() {
  const xref = (state.corpus.xrefs || []).find((item) => item.id === state.corpus.selectedXrefId);
  if (!xref || !Number.isInteger(xref.row_index)) {
    return null;
  }
  return {
    rowIndex: xref.row_index,
    addr: Number.isFinite(xref.offset) ? xref.offset : null,
    matchText: xref.text || null,
    stableKey: xref.stable_key || null,
  };
}

function formatRowOffset(addr) {
  if (addr === null || addr === undefined) {
    return "";
  }
  return addr.toString(16).padStart(4, "0");
}

function formatListingRuntimeAddress(row) {
  const address = Number(row?.runtime_address);
  if (!Number.isFinite(address)) {
    return "";
  }
  return address.toString(16).padStart(4, "0");
}

function parseListingAddress(text) {
  const raw = String(text || "").trim();
  if (!raw) {
    return null;
  }
  const normalized = raw.replace(/^[$]/, "").replace(/^0x/i, "");
  if (!/^[0-9a-f]+$/i.test(normalized)) {
    return null;
  }
  const value = Number.parseInt(normalized, 16);
  return Number.isSafeInteger(value) && value >= 0 ? value : null;
}

function formatByteOffset(addr) {
  const value = Number(addr);
  if (!Number.isFinite(value)) {
    return "";
  }
  return `$${Math.max(0, value).toString(16).toUpperCase().padStart(6, "0")}`;
}

function formatFileSize(size) {
  const value = Number(size);
  if (!Number.isFinite(value) || value < 0) {
    return "";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${Math.round(value / 1024)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function formatBriefFileSize(size) {
  const value = Number(size);
  if (!Number.isFinite(value) || value < 0) {
    return "";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${Math.round(value / 1024)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} M`;
}

function formatAddressHex(value) {
  const address = Number(value);
  if (!Number.isFinite(address)) {
    return "";
  }
  return `$${address.toString(16).toUpperCase()}`;
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

function typedGapLabel(access) {
  const root = String(access?.root_struct_name || access?.rootStructName || "typed base");
  const displacement = Number(access?.displacement);
  const formatted = formatAppSlotDisplacement(access);
  if (!formatted || !Number.isFinite(displacement)) {
    return root;
  }
  return `${root}${displacement < 0 ? "" : "+"}${formatted}`;
}

function typedGapSummary(access) {
  const label = typedGapLabel(access);
  const classification = String(access?.classification || "");
  const container = String(access?.container_struct_name || access?.containerStructName || "");
  const fieldExpr = String(access?.container_field_expr || access?.containerFieldExpr || "");
  const refined = String(access?.refined_struct_name || access?.refinedStructName || "");
  const refinementApplied = Boolean(access?.refinement_applied ?? access?.refinementApplied);
  const candidateCount = Number(access?.container_candidate_count ?? access?.containerCandidateCount);
  if (classification === "prefix_extension") {
    if (refinementApplied && refined) return `${label} refines to ${refined}`;
    if (container && fieldExpr) return `${label} prefix extension: ${container}.${fieldExpr}`;
    if (container) return `${label} prefix extension: ${container}`;
    if (Number.isFinite(candidateCount) && candidateCount > 0) {
      return `${label} prefix extension (${candidateCount} candidates)`;
    }
    return `${label} prefix extension`;
  }
  if (classification === "custom_tail_or_mistyped_base") return `${label} unknown extension`;
  return `${label} field metadata gap`;
}

function typedGapProvenanceSummary(access) {
  const kind = String(access?.type_provenance_kind || access?.typeProvenanceKind || "");
  if (!kind) {
    return "";
  }
  const labels = {
    api_output: "API output",
    app_slot: "app slot",
    base_slot: "base slot",
    stack_slot: "stack slot",
    lookup_storage: "storage reload",
    prefix_refinement: "prefix refinement",
  };
  const label = labels[kind] || kind.replaceAll("_", " ");
  const section = Number(access?.type_provenance_section ?? access?.typeProvenanceSection);
  const offset = Number(access?.type_provenance_offset ?? access?.typeProvenanceOffset);
  if (Number.isFinite(offset)) {
    const location = `${Number.isFinite(section) ? `h${section}:` : ""}$${offset.toString(16).toUpperCase().padStart(8, "0")}`;
    return `type from ${label} at ${location}`;
  }
  return `type from ${label}`;
}

function appSlotTypedInfoForSymbol(symbol) {
  const analysis = state.navigation.appSlotAnalysis;
  const regions = Array.isArray(analysis?.regions) ? analysis.regions : [];
  for (const region of regions) {
    if (region?.source !== "platform_api_arg") {
      continue;
    }
    if (String(region.symbol || "") === symbol) {
      return {region, field: null};
    }
    const fieldRefs = Array.isArray(region.field_refs) ? region.field_refs : [];
    for (const field of fieldRefs) {
      if (String(field?.symbol || "") === symbol) {
        return {region, field};
      }
    }
  }
  return null;
}

function appSlotFieldPath(field, structName) {
  const path = Array.isArray(field?.field_path) ? field.field_path.filter((part) => typeof part === "string" && part) : [];
  if (path.length) {
    return [structName, ...path].join(".");
  }
  return field?.field_name ? `${structName}.${field.field_name}` : "";
}

function appSlotTypedInfoTitle(info) {
  const structName = String(info?.region?.struct_name || "typed app slot");
  if (info?.field) {
    const fieldName = appSlotFieldPath(info.field, structName) || info.field.symbol || "field";
    const fieldOffset = formatAppSlotDisplacement({displacement: Number(info.field.field_offset || 0)});
    const baseSymbol = String(info.field.base_symbol || info.region.symbol || "");
    const fieldExpr = String(info.field.field_expr || "");
    const sourceExpr = baseSymbol && fieldExpr ? `${baseSymbol}+${fieldExpr}` : "";
    return `${structName}${fieldOffset ? `+${fieldOffset}` : ""} ${fieldName}${sourceExpr ? ` (${sourceExpr})` : ""}`;
  }
  const offset = formatAppSlotDisplacement({displacement: Number(info?.region?.offset || 0)});
  const size = Number(info?.region?.size || 0);
  return `${structName} app slot ${offset}${size > 0 ? ` (${size} bytes)` : ""}`;
}

function formatNavigationEntryOffset(entry) {
  if (Number.isFinite(Number(entry?.start)) && Number.isFinite(Number(entry?.end))) {
    return `${formatAppSlotDisplacement({displacement: Number(entry.start)})}-${formatAppSlotDisplacement({displacement: Number(entry.end)})}`;
  }
  if (Number.isFinite(Number(entry?.offset)) && Number.isFinite(Number(entry?.end))) {
    return `${formatAppSlotDisplacement({displacement: Number(entry.offset)})}-${formatAppSlotDisplacement({displacement: Number(entry.end)})}`;
  }
  if (entry?.refs && entry?.symbol && entry?.displacement !== undefined) {
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
  const represented = renderManualRepresentationCode(row);
  if (represented !== null) {
    return represented;
  }
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

function rowManualRepresentation(row) {
  const representations = state.projectData?.project?.manual_state?.representations;
  if (!Array.isArray(representations) || row.kind !== "data") {
    return null;
  }
  return representations.find((representation) => (
    (representation.stable_key && row.stable_key && representation.stable_key === row.stable_key)
    || (
      Number.isInteger(representation.hunk)
      && Number.isFinite(representation.addr)
      && representation.hunk === row.section_index
      && representation.addr === row.start_offset
    )
    || (
      Number.isFinite(representation.row_index)
      && Number.isFinite(state.virtualListing.start)
      && representation.row_index >= state.virtualListing.start
      && state.listingRows[representation.row_index - state.virtualListing.start] === row
    )
  )) || null;
}

function listingRowByteValues(row) {
  const hex = String(row.bytes || "").replaceAll(/[^0-9a-f]/gi, "");
  if (!hex || hex.length % 2) {
    return [];
  }
  const values = [];
  for (let index = 0; index < hex.length; index += 2) {
    values.push(parseInt(hex.slice(index, index + 2), 16));
  }
  return values.filter((value) => Number.isInteger(value));
}

function quoteManualCharacter(value) {
  const char = String.fromCharCode(value);
  if (char === "'") return "'\\''";
  if (char === "\\") return "'\\\\'";
  if (value >= 32 && value < 127) return `'${char}'`;
  return `$${value.toString(16).toUpperCase().padStart(2, "0")}`;
}

function renderManualRepresentationCode(row) {
  const representation = rowManualRepresentation(row);
  if (!representation || row.kind !== "data") {
    return null;
  }
  const opcode = row.opcode_or_directive || "dc.b";
  const values = listingRowByteValues(row);
  if (!values.length || opcode.toLowerCase() !== "dc.b") {
    return null;
  }
  const style = String(representation.style || "");
  let operands = null;
  if (style === "binary") {
    operands = values.map((value) => `%${value.toString(2).padStart(8, "0")}`);
  } else if (style === "character") {
    operands = values.map(quoteManualCharacter);
  } else if (style === "hex") {
    operands = values.map((value) => `$${value.toString(16).toUpperCase().padStart(2, "0")}`);
  } else if (style === "string") {
    const printable = values.every((value) => value >= 32 && value < 127 && value !== 34 && value !== 92);
    if (printable) {
      operands = [`"${String.fromCharCode(...values)}"`];
    }
  }
  return operands ? `    ${opcode} ${operands.join(",")}` : null;
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

function equateDefinitionFromRow(row) {
  const parsed = parseGlobalRsEquRow(row);
  if (!parsed || parsed.directive.toUpperCase() !== "EQU" || !parsed.label) {
    return null;
  }
  return {
    symbol: parsed.label,
    operand: parsed.operand,
  };
}

function labelNameFromText(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed.endsWith(":")) {
    return null;
  }
  return normalizedLabelSymbol(trimmed);
}

function normalizedLabelSymbol(value) {
  const name = String(value || "").trim().replace(/:$/, "").trim();
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

function labelNamesFromNavigation() {
  const labels = state.navigation.entries?.labels || [];
  return new Set(labels.map((entry) => {
    const text = String(entry.summary || entry.matchText || entry.match_text || "");
    return text.replace(/:$/, "");
  }).filter(Boolean));
}

function equateNamesFromNavigation() {
  if (!state.navigation.entries && state.navigation.equateNameCacheRows === state.listingRows && state.navigation.equateNameCache) {
    return state.navigation.equateNameCache;
  }
  const groups = state.navigation.entries || buildNavigationEntries(state.listingRows || []);
  const equates = groups.equates || [];
  const names = new Set(equates.map((entry) => String(entry.symbol || "")).filter(Boolean));
  if (!state.navigation.entries) {
    state.navigation.equateNameCacheRows = state.listingRows;
    state.navigation.equateNameCache = names;
  }
  return names;
}

function isListingSymbolChar(char) {
  return /^[A-Za-z0-9_]$/.test(char || "");
}

function rowOperandSymbolNames(row) {
  return rowOperandSymbolRefs(row).map((ref) => ref.symbol);
}

function rowOperandSymbolRefs(row) {
  const refs = [];
  const seen = new Set();
  if (!Array.isArray(row?.operand_parts)) {
    return refs;
  }
  row.operand_parts.forEach((operand, fallbackIndex) => {
    const metadataSymbol = operand?.metadata && typeof operand.metadata.symbol === "string"
      ? operand.metadata.symbol
      : "";
    const symbol = metadataSymbol;
    if (!symbol || seen.has(symbol)) {
      return;
    }
    seen.add(symbol);
    refs.push({
      symbol,
      operandIndex: Number.isInteger(operand.operand_index) ? operand.operand_index : fallbackIndex,
      elementKind: operand.kind === "immediate" ? "immediate" : "symbol",
    });
  });
  return refs;
}

function listingOperandSymbolNames(row) {
  return rowOperandSymbolNames(row);
}

function listingLabelRefRanges(row, text) {
  const source = String(text || "");
  if (!source) {
    return [];
  }
  const labels = listingOperandSymbolNames(row)
    .filter((label) => label && source.includes(label));
  const refsBySymbol = new Map(rowOperandSymbolRefs(row).map((ref) => [ref.symbol, ref]));
  labels.sort((left, right) => right.length - left.length || left.localeCompare(right));
  const ranges = [];
  labels.forEach((label) => {
    let cursor = 0;
    while (cursor < source.length) {
      const start = source.indexOf(label, cursor);
      if (start < 0) {
        break;
      }
      const end = start + label.length;
      const before = start > 0 ? source[start - 1] : "";
      const after = end < source.length ? source[end] : "";
      if (!isListingSymbolChar(before) && !isListingSymbolChar(after)) {
        const ref = refsBySymbol.get(label) || {};
        ranges.push({start, end, symbol: label, operandIndex: ref.operandIndex, elementKind: ref.elementKind || "symbol"});
      }
      cursor = end;
    }
  });
  ranges.sort((left, right) => left.start - right.start || right.end - left.end);
  const filtered = [];
  let cursor = 0;
  ranges.forEach((range) => {
    if (range.start < cursor) {
      return;
    }
    filtered.push(range);
    cursor = range.end;
  });
  return filtered;
}

function renderListingLabelRefsHtml(row, text, globalRowIndex = null) {
  const source = String(text || "");
  const ranges = listingLabelRefRanges(row, source);
  if (!ranges.length) {
    return null;
  }
  let cursor = 0;
  let html = "";
  const equateNames = equateNamesFromNavigation();
  ranges.forEach((range) => {
    html += escapeHtml(source.slice(cursor, range.start));
    const rowIndex = Number.isFinite(globalRowIndex) ? ` data-row-index="${escapeHtml(String(globalRowIndex))}"` : "";
    const operandIndex = Number.isInteger(range.operandIndex) ? ` data-operand-index="${escapeHtml(String(range.operandIndex))}"` : "";
    const elementKind = ` data-element-kind="${escapeHtml(range.elementKind || "symbol")}"`;
    if (equateNames.has(range.symbol)) {
      html += `<button class="listing-symbol-link listing-symbol-reference listing-equate-reference" type="button" data-equate-symbol="${escapeHtml(range.symbol)}" data-equate-access="reference"${rowIndex}${operandIndex}${elementKind}>${escapeHtml(range.symbol)}</button>`;
    } else {
      html += `<button class="listing-symbol-link listing-symbol-reference" type="button" data-symbol-name="${escapeHtml(range.symbol)}" data-symbol-role="reference"${rowIndex}${operandIndex}${elementKind}>${escapeHtml(range.symbol)}</button>`;
    }
    cursor = range.end;
  });
  html += escapeHtml(source.slice(cursor));
  return html;
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
    const typedInfo = appSlotTypedInfoForSymbol(range.symbol);
    const typedClass = typedInfo ? " listing-app-slot-typed" : "";
    const title = typedInfo ? ` title="${escapeHtml(appSlotTypedInfoTitle(typedInfo))}"` : "";
    html += `<button class="listing-symbol-link listing-symbol-reference listing-app-slot-reference${typedClass}" type="button" data-element-kind="app_slot" data-app-slot-symbol="${escapeHtml(range.symbol)}" data-row-index="${escapeHtml(String(globalRowIndex))}" data-app-slot-operand-index="${escapeHtml(String(range.operandIndex))}" data-app-slot-access="${escapeHtml(range.access)}"${title}>${escapeHtml(range.symbol)}</button>`;
    cursor = range.end;
  });
  html += escapeHtml(operand.slice(cursor));
  return html;
}

function renderListingCodeHtml(row, globalRowIndex = null) {
  if (inlineParameterSessionMatches(globalRowIndex, "code")) {
    return renderInlineParameterSession(state.parameterSession);
  }
  const globalRsEqu = parseGlobalRsEquRow(row);
  if (globalRsEqu) {
    const typedInfo = isAppSlotSymbolName(globalRsEqu.label) ? appSlotTypedInfoForSymbol(globalRsEqu.label) : null;
    const labelTitle = typedInfo
      ? ` title="${escapeHtml(appSlotTypedInfoTitle(typedInfo))}"`
      : (globalRsEqu.label ? ` title="${escapeHtml(globalRsEqu.label)}"` : "");
    const typedClass = typedInfo ? " listing-app-slot-typed" : "";
    const labelHtml = isAppSlotSymbolName(globalRsEqu.label)
      ? `<button class="listing-symbol-link listing-global-label listing-app-slot-definition${typedClass}" type="button" data-app-slot-symbol="${escapeHtml(globalRsEqu.label)}"${labelTitle}>${escapeHtml(globalRsEqu.label)}</button>`
      : (globalRsEqu.directive.toUpperCase() === "EQU" && globalRsEqu.label
        ? `<button class="listing-symbol-link listing-global-label listing-equate-definition" type="button" data-element-kind="symbol" data-equate-symbol="${escapeHtml(globalRsEqu.label)}" data-equate-access="definition"${Number.isFinite(globalRowIndex) ? ` data-row-index="${escapeHtml(String(globalRowIndex))}"` : ""}${labelTitle}>${escapeHtml(globalRsEqu.label)}</button>`
        : `<span class="listing-global-label"${labelTitle}>${escapeHtml(globalRsEqu.label)}</span>`);
    return `<span class="listing-global-structured">${labelHtml}<span class="listing-global-directive">${escapeHtml(globalRsEqu.directive)}</span><span class="listing-global-operand">${escapeHtml(globalRsEqu.operand)}</span></span>`;
  }
  const code = renderListingCode(row);
  const labelName = labelSymbolFromRow(row);
  if (labelName && row.kind === "label" && rowHasAddress(row)) {
    const rowIndex = Number.isFinite(globalRowIndex) ? ` data-row-index="${escapeHtml(String(globalRowIndex))}"` : "";
    return `<button class="listing-symbol-link listing-symbol-definition" type="button" data-element-kind="label" data-symbol-name="${escapeHtml(labelName)}" data-symbol-role="definition"${rowIndex}>${escapeHtml(code)}</button>`;
  }
  const appSlotCodeHtml = Number.isFinite(globalRowIndex)
    ? renderOperandAppSlotRefsHtml(row, code, globalRowIndex)
    : null;
  if (appSlotCodeHtml !== null) {
    return appSlotCodeHtml;
  }
  if ((row.kind === "instruction" || row.kind === "data") && rowHasAddress(row) && row.operand_text) {
    const opcode = row.opcode_or_directive || "";
    const operand = row.operand_text || "";
    const appSlotOperandHtml = Number.isFinite(globalRowIndex)
      ? renderOperandAppSlotRefsHtml(row, operand, globalRowIndex)
      : null;
    if (appSlotOperandHtml !== null) {
      return `    ${escapeHtml(opcode)} ${appSlotOperandHtml}`;
    }
    const labelOperandHtml = renderListingLabelRefsHtml(row, operand, globalRowIndex);
    if (labelOperandHtml !== null) {
      return `    ${escapeHtml(opcode)} ${labelOperandHtml}`;
    }
  }
  return escapeHtml(code);
}

function renderListingComment(row) {
  if (row.comment_text) {
    return `; ${row.comment_text}`;
  }
  return "";
}

function renderListingCommentHtml(row, globalRowIndex = null) {
  if (inlineParameterSessionMatches(globalRowIndex, "comment")) {
    return renderInlineParameterSession(state.parameterSession);
  }
  return escapeHtml(renderListingComment(row));
}

function inlineParameterSessionMatches(globalRowIndex, slot) {
  const session = state.parameterSession;
  if (!session || session.host !== "inline" || !Number.isFinite(globalRowIndex) || session.rowIndex !== globalRowIndex) {
    return false;
  }
  const action = session.action || {};
  const interactionType = action.interaction_schema?.type || "";
  if (slot === "comment") {
    return action.action === "create_manual_comment";
  }
  return action.action !== "create_manual_comment" && ["text", "choice_grid", "filtered_chooser"].includes(interactionType);
}

function renderInlineParameterSession(session) {
  if (!session) {
    return "";
  }
  const action = session.action || {};
  const fields = commandParameterSchemaFields(action);
  const interactionType = action?.interaction_schema?.type || "";
  const body = interactionType === "choice_grid"
    ? renderParameterChoiceGrid(session)
    : interactionType === "filtered_chooser"
      ? renderParameterFilteredChooser(session)
      : fields.map((field) => renderCommandParameterField(field, session)).join("");
  return `
    <form class="inline-parameter-session" data-inline-parameter-session="1">
      ${body}
      <button type="submit" class="command-parameter-submit"${session.submitting ? " disabled" : ""}>${session.submitting ? "Saving" : "Apply"}</button>
      <button type="button" class="command-parameter-cancel" data-inline-parameter-cancel="1">Cancel</button>
      ${session.submitError ? `<div class="command-parameter-error">${escapeHtml(session.submitError)}</div>` : ""}
    </form>
  `;
}

function renderListingAnnotations(row) {
  const annotations = Array.isArray(row.view_annotations) ? row.view_annotations : [];
  const noteBadges = Array.isArray(row.review_notes) ? row.review_notes.map(renderReviewNoteBadge).join("") : "";
  if (!annotations.length) {
    return noteBadges;
  }
  return annotations
    .map((note) => `<span class="project-badge" title="${escapeHtml(note)}">${escapeHtml(note)}</span>`)
    .join("") + noteBadges;
}

function reviewNoteLabel(note) {
  const title = String(note?.title || "").trim();
  const body = String(note?.body || "").trim();
  return title || body.split(/\r?\n/)[0] || "Bookmark";
}

function renderReviewNoteBadge(note) {
  const tracking = note?.tracking === "needs_review" ? "needs_review" : "note_only";
  const label = tracking === "needs_review" ? `Review: ${reviewNoteLabel(note)}` : `Note: ${reviewNoteLabel(note)}`;
  const className = tracking === "needs_review" ? "project-badge-review-needs-review" : "project-badge-review-note";
  return `<button type="button" class="project-badge listing-review-note ${className}" data-review-note-id="${escapeHtml(String(note?.note_id || ""))}" title="${escapeHtml(label)}">${escapeHtml(label)}</button>`;
}

function renderApiEditButton(row, rowIndex) {
  if (!row.api_call) {
    return "";
  }
  return ` <button class="listing-api-edit" type="button" data-api-edit="1" data-row-index="${rowIndex}" title="Edit API argument types">Edit API</button>`;
}

function renderApiTypeBadges(row) {
  if (!row.api_call) {
    return "";
  }
  const inputs = Array.isArray(row.api_call.inputs) ? row.api_call.inputs : [];
  const outputs = Array.isArray(row.api_call.outputs) ? row.api_call.outputs : [];
  const highlighted = inputs
    .filter((input) => input.i_struct || input.source !== "parsed NDK")
    .map((input) => ({...input, direction: "in", struct: input.i_struct}));
  outputs
    .filter((output) => output.o_struct || output.source !== "parsed NDK")
    .forEach((output) => highlighted.push({...output, direction: "out", struct: output.o_struct}));
  if (!highlighted.length) {
    return "";
  }
  return highlighted
    .map((item) => {
      const label = `${item.direction}:${item.regs.join("/")} ${item.struct || item.type || item.name}`;
      const title = `${item.direction} ${item.name}: ${item.type || "(untyped)"}\nsource: ${item.source}`;
      const sourceClass = `project-badge-source-${String(item.source || "unknown").toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}`;
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

function renderUnresolvedTypedAccessBadges(row) {
  if (!rowHasUnresolvedTypedAccess(row)) {
    return "";
  }
  return row.unresolved_typed_accesses
    .map((access) => {
      const structSize = Number(access.struct_size ?? access.structSize);
      const candidateCount = Number(access.container_candidate_count ?? access.containerCandidateCount);
      const container = String(access.container_struct_name || access.containerStructName || "");
      const fieldExpr = String(access.container_field_expr || access.containerFieldExpr || "");
      const titleParts = [
        `Known typed base: ${typedGapSummary(access)}`,
        "Field metadata is not available; source operand remains numeric.",
      ];
      if (Number.isFinite(structSize)) {
        titleParts.push(`Struct size: $${structSize.toString(16).toUpperCase().padStart(4, "0")}`);
      }
      if (Number.isFinite(candidateCount) && candidateCount > 0) {
        titleParts.push(`Container candidates: ${candidateCount}`);
      }
      const provenance = typedGapProvenanceSummary(access);
      if (provenance) {
        titleParts.push(provenance);
      }
      if (container) {
        titleParts.push(`Candidate container: ${container}${fieldExpr ? `.${fieldExpr}` : ""}`);
      }
      if (access.refinement_applied || access.refinementApplied) {
        titleParts.push(`Analysis refinement: ${access.refined_struct_name || access.refinedStructName || container || "applied"}`);
      }
      return `<span class="project-badge project-badge-typed-gap" title="${escapeHtml(titleParts.join("\n"))}">${escapeHtml(`type gap ${typedGapSummary(access)}`)}</span>`;
    })
    .join("");
}

function listingColumnStyle() {
  return `--listing-offset-width:${state.listingColumns.offset}px;--listing-runtime-width:${state.listingColumns.runtime}px;--listing-bytes-width:${state.listingColumns.bytes}px;--listing-code-width:${state.listingColumns.code}px;`;
}

function applyListingColumnWidths() {
  document.querySelectorAll(".listing-row-layer, .listing-scroll-spacer").forEach((element) => {
    element.style.setProperty("--listing-offset-width", `${state.listingColumns.offset}px`);
    element.style.setProperty("--listing-runtime-width", `${state.listingColumns.runtime}px`);
    element.style.setProperty("--listing-bytes-width", `${state.listingColumns.bytes}px`);
    element.style.setProperty("--listing-code-width", `${state.listingColumns.code}px`);
  });
}

function listingRowRuntimeEnd(row) {
  const runtimeAddress = Number(row?.runtime_address);
  if (!Number.isFinite(runtimeAddress)) {
    return null;
  }
  const start = Number(row?.start_offset);
  const end = Number(row?.end_offset);
  if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
    return runtimeAddress + (end - start);
  }
  return runtimeAddress + 1;
}

function renderListingRows(rows, globalStart = 0) {
  if (!rows.length) {
    return '<div class="empty listing-empty">No disassembly available.</div>';
  }
  return rows.map((row, rowIndex) => `
    <div
      class="listing-row listing-row-${escapeHtml(row.kind)}${rowUsesGlobalTextColumn(row) ? " listing-row-global" : ""}${Array.isArray(row.repro_issues) && row.repro_issues.length ? " listing-row-repro-issue" : ""}${listingRowHasPendingManualEdit(row, globalStart + rowIndex) ? " listing-row-manual-pending" : ""}${listingRowHasSavedManualFlash(row, globalStart + rowIndex) ? " listing-row-manual-saved" : ""}${listingRowIsSelected(row, globalStart + rowIndex) ? " listing-row-selected" : ""}"
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
      ${row.runtime_address !== null && row.runtime_address !== undefined ? `data-runtime-address="${escapeHtml(String(row.runtime_address))}"` : ""}
      ${listingRowRuntimeEnd(row) !== null ? `data-runtime-end-address="${escapeHtml(String(listingRowRuntimeEnd(row)))}"` : ""}
      ${row.structured_data?.struct_name ? `data-struct-name="${escapeHtml(row.structured_data.struct_name)}"` : ""}
      ${row.structured_data?.field_name ? `data-struct-field="${escapeHtml(row.structured_data.field_name)}"` : ""}
    >
      <span class="listing-offset">${escapeHtml(formatRowOffset(row.addr))}</span>
      <span class="listing-runtime">${escapeHtml(formatListingRuntimeAddress(row))}</span>
      <span class="listing-bytes">${escapeHtml(formatRowBytes(row.bytes))}</span>
      <span class="listing-code">${renderListingCodeHtml(row, globalStart + rowIndex)}</span>
      <span class="listing-comment">${renderListingCommentHtml(row, globalStart + rowIndex)}${renderListingComment(row, globalStart + rowIndex) && renderListingAnnotations(row) ? " " : ""}${renderListingAnnotations(row)}${renderReproIssueBadges(row)}${renderApiTypeBadges(row)}${renderUnresolvedTypedAccessBadges(row)}${(renderListingAnnotations(row) || renderReproIssueBadges(row) || renderApiTypeBadges(row) || renderUnresolvedTypedAccessBadges(row)) ? " " : ""}${renderApiEditButton(row, globalStart + rowIndex)}</span>
      <span class="listing-column-resizer listing-column-resizer-offset" data-listing-column-resize="offset" aria-hidden="true"></span>
      <span class="listing-column-resizer listing-column-resizer-runtime" data-listing-column-resize="runtime" aria-hidden="true"></span>
      <span class="listing-column-resizer listing-column-resizer-bytes" data-listing-column-resize="bytes" aria-hidden="true"></span>
      <span class="listing-column-resizer listing-column-resizer-code" data-listing-column-resize="code" aria-hidden="true"></span>
    </div>
  `).join("");
}

function listingRowIsSelected(row, globalIndex) {
  const selection = state.listingSelection;
  if (!selection) {
    return false;
  }
  const bounds = listingSelectionRangeBounds(selection);
  if (bounds && listingSelectionIsRange(selection) && globalIndex >= bounds.start && globalIndex <= bounds.end) {
    return true;
  }
  if (selection.stableKey && row.stable_key && selection.stableKey === row.stable_key) {
    return true;
  }
  if (Number.isFinite(selection.rowIndex) && selection.rowIndex === globalIndex) {
    return true;
  }
  if (
    Number.isInteger(selection.sectionIndex)
    && Number.isFinite(selection.startOffset)
    && selection.sectionIndex === row.section_index
    && selection.startOffset === row.start_offset
  ) {
    return true;
  }
  return Number.isFinite(selection.addr)
    && selection.addr === row.addr
    && (!selection.rowCode || selection.rowCode === renderListingCode(row));
}

function listingRowHasPendingManualEdit(row, globalIndex) {
  const ranges = Array.isArray(state.manualEdit.pendingRanges) ? state.manualEdit.pendingRanges : [];
  return ranges.some((range) => manualActionLocationMatchesRow(normalizeManualActionLocation(range), row, globalIndex));
}

function listingRowHasSavedManualFlash(row, globalIndex) {
  const ranges = Array.isArray(state.manualEdit.savedFlashRanges) ? state.manualEdit.savedFlashRanges : [];
  return ranges.some((range) => manualActionLocationMatchesRow(range, row, globalIndex));
}

function manualActionLocationMatchesRow(location, row, globalIndex) {
  if (!location || !row) {
    return false;
  }
  if (location.stable_key) {
    return Boolean(row.stable_key && location.stable_key === row.stable_key);
  }
  const rowIndexes = Array.isArray(location.row_indexes) ? location.row_indexes : [];
  if (rowIndexes.includes(globalIndex)) {
    return true;
  }
  const start = Number(location.addr);
  const rowStart = Number(row.start_offset ?? row.addr);
  if (!Number.isFinite(start) || !Number.isFinite(rowStart)) {
    return false;
  }
  const hunk = Number(location.hunk);
  if (Number.isFinite(hunk) && Number.isInteger(row.section_index) && hunk !== row.section_index) {
    return false;
  }
  const end = Number(location.end);
  return Number.isFinite(end) && end > start ? rowStart >= start && rowStart < end : rowStart === start;
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

function listingWindowWithGenerationTransitionAnchor(viewport, listing) {
  const existingRow = viewport?.querySelector(".listing-row");
  const existingGeneration = existingRow instanceof HTMLElement ? existingRow.dataset.analysisGeneration : "";
  const nextGeneration = listing?.analysis_generation || "";
  if (!existingGeneration || !nextGeneration || existingGeneration === nextGeneration) {
    return listing;
  }
  const anchor = captureListingAddressAnchor(viewport);
  if (!anchor?.rowCode || Number.isFinite(anchor.addr)) {
    return listing;
  }
  const anchorIndex = listingAnchorRowIndexInRows(listing.rows || [], anchor);
  if (anchorIndex <= 0) {
    return listing;
  }
  return {
    ...listing,
    start: (listing.start || 0) + anchorIndex,
    rows: listing.rows.slice(anchorIndex),
  };
}

function renderVirtualListingWindow(projectId, listing, preserveScroll = false, forcedScrollTop = null) {
  const renderStartedAt = performance.now();
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return {renderMs: 0};
  }
  listing = listingWindowWithGenerationTransitionAnchor(viewport, listing);
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
  bindInlineParameterSession();
  bindListingSelection();
  applyRenderedListingSelection();
  bindVirtualListingScroller(projectId, viewport);
  if (forcedScrollTop !== null && Number.isFinite(forcedScrollTop)) {
    viewport.scrollTop = Math.max(0, forcedScrollTop);
  } else if (preserveScroll) {
    viewport.scrollTop = scrollTop;
  }
  renderNavigationOverlay();
  dispatchAppEvent("amiga:listing-window-rendered", {
    projectId,
    start: state.virtualListing.start,
    end: state.virtualListing.end,
    totalRows: state.virtualListing.totalRows,
    generation: state.virtualListing.generation,
    rowCount: listing.rows.length,
    requestSeq: state.virtualListing.requestSeq,
  });
  if (!state.listingSelection && listing.rows.length) {
    void maybeApplyInitialListingLocation(projectId);
  }
  return {renderMs: performance.now() - renderStartedAt};
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
      scheduleListingWindowForScroll(projectId, viewport);
      scheduleUiPreferenceSave();
    });
  };
  viewport.addEventListener("scroll", viewport._listingScrollHandler);
}

function cancelScheduledListingScrollFetch() {
  if (state.virtualListing.scrollRaf !== null) {
    window.cancelAnimationFrame(state.virtualListing.scrollRaf);
    state.virtualListing.scrollRaf = null;
  }
  state.virtualListing.pendingWindow = null;
}

function beginListingScrollSuppression() {
  cancelScheduledListingScrollFetch();
  state.virtualListing.suppressScrollFetch = true;
  state.virtualListing.scrollSuppressionToken += 1;
  return state.virtualListing.scrollSuppressionToken;
}

function releaseListingScrollSuppression(projectId, viewport, token) {
  window.setTimeout(() => {
    if (token !== state.virtualListing.scrollSuppressionToken) {
      return;
    }
    state.virtualListing.suppressScrollFetch = false;
    if (state.project === projectId && viewport instanceof HTMLElement && viewport.isConnected) {
      scheduleListingWindowForScroll(projectId, viewport);
    }
  }, 80);
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
  cancelScheduledListingScrollFetch();
  scheduleListingWindowForScroll(projectId, viewport);
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
    rowIndex: best.dataset.rowIndex !== "" && best.dataset.rowIndex !== undefined
      ? Number(best.dataset.rowIndex)
      : null,
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

async function handleListingArtifactReady(payload, token = null) {
  if (!state.project || payload.project_id !== state.project) {
    return;
  }
  if (token !== null && token !== state.loadingToken) {
    return;
  }
  setAnalysisStatus("Applying analysis", "running");
  const listing = await refreshListingAtCurrentAddressAnchor(state.project, token);
  if (token !== null && token !== state.loadingToken) {
    return;
  }
  await refreshProjectPayload(state.project, token);
  if (token !== null && token !== state.loadingToken) {
    return;
  }
  if (listing?.analysis_generation) {
    await loadNavigationEntries(state.project);
    renderNavigationOverlay();
    if (!state.listingSelection) {
      const uiPreferences = state.uiPreferences.payload || await loadUiPreferenceState(state.project);
      await applyInitialListingLocation(state.project, uiPreferences);
    }
    setAnalysisStatus("Analysis ready", "ready", 2000);
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

function scheduleListingWindowForScroll(projectId, viewport) {
  const desired = desiredListingWindowForScroll(viewport);
  if (!desired) {
    return;
  }
  state.virtualListing.pendingWindow = {
    projectId,
    start: desired.start,
    count: desired.count,
    requestedAt: performance.now(),
  };
  if (!state.virtualListing.inFlightWindow) {
    void flushPendingListingWindow();
  }
}

async function flushPendingListingWindow() {
  const pending = state.virtualListing.pendingWindow;
  let result = null;
  if (!pending) {
    return null;
  }
  if (sameListingWindow(pending, state.virtualListing.inFlightWindow)) {
    return null;
  }
  state.virtualListing.pendingWindow = null;
  state.virtualListing.inFlightWindow = pending;
  try {
    result = await loadListingWindow(pending.projectId, null, 0, pending.count, {
      start: pending.start,
      count: pending.count,
      preserveScroll: true,
      abortPrevious: true,
      requestedAt: pending.requestedAt,
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
  }
  if (state.virtualListing.pendingWindow) {
    return flushPendingListingWindow();
  }
  return result;
}

function isEditableTarget(target) {
  if (!(target instanceof HTMLElement)) {
    return false;
  }
  return Boolean(target.closest("input, textarea, select, [contenteditable='true']"));
}

function modalOrPanelHasKeyboardFocus() {
  return Boolean(
    state.navigation.overlayOpen ||
    document.getElementById("navigation-overlay") ||
    state.stats.overlayOpen ||
    document.getElementById("stats-overlay") ||
    state.reproduction.panelOpen ||
    state.manualReview.panelOpen ||
    state.commandPalette.open ||
    document.getElementById("review-overlay") ||
    document.getElementById("command-palette-overlay") ||
    document.getElementById("corpus-variant-diff-overlay") ||
    document.getElementById("corpus-disk-browser-overlay") ||
    document.getElementById("corpus-snippet-overlay")
  );
}

function listingScrollDirectionForKey(event) {
  if (event.altKey || event.metaKey || event.shiftKey) {
    return null;
  }
  if (event.ctrlKey) {
    if (event.key === "PageDown" || event.key === "End") return "end";
    if (event.key === "PageUp" || event.key === "Home") return "home";
    return null;
  }
  if (event.key === "PageDown") return "down";
  if (event.key === "PageUp") return "up";
  if (event.key === "Home") return "home";
  if (event.key === "End") return "end";
  return null;
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
  if (Array.isArray(row.typed_accesses) && row.typed_accesses.length > 0) {
    return true;
  }
  return row.kind !== "instruction" && row.kind !== "label"
    && (Boolean(row.comment_text) || Boolean(row.data_class) || Boolean(row.structured_data));
}

function rowHasUnresolvedTypedAccess(row) {
  return Array.isArray(row.unresolved_typed_accesses) && row.unresolved_typed_accesses.length > 0;
}

function rowHasComment(row) {
  return Boolean(row.comment_text);
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
  if (jumpClass === "typed-data" && Array.isArray(row.typed_accesses) && row.typed_accesses.length) {
    const access = row.typed_accesses[0];
    const owner = access.owner_struct_name || access.ownerStructName || access.root_struct_name || access.rootStructName || "";
    const field = access.field_expr || access.fieldExpr || access.field_name || access.fieldName || "";
    return owner && field ? `${owner}.${field}` : (field || owner || renderListingCode(row).trim());
  }
  if (jumpClass === "typed-gaps" && rowHasUnresolvedTypedAccess(row)) {
    return typedGapSummary(row.unresolved_typed_accesses[0]);
  }
  if (jumpClass === "typed-data" && (row.comment_text || row.data_class || row.structured_data)) {
    const item = row.structured_data || {};
    return row.comment_text || row.data_class || item.semantic_role || item.label || item.field_name || row.kind;
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

function labelSymbolFromRow(row) {
  if (row?.label) {
    return normalizedLabelSymbol(row.label);
  }
  return labelNameFromText(renderListingCode(row));
}

function addLabelNavigationEntry(labels, row, rowIndex) {
  const symbol = labelSymbolFromRow(row);
  if (!symbol) {
    return;
  }
  const hunkIndex = rowHunkIndex(row);
  const stableKey = row.stable_key ?? row.stableKey ?? null;
  const matchText = renderListingCode(row);
  labels.set(symbol, {
    symbol,
    summary: `${symbol}:`,
    matchText,
    match_text: matchText,
    addr: row.addr,
    rowIndex,
    row_index: rowIndex,
    hunkIndex,
    hunk_index: hunkIndex,
    stableKey,
    stable_key: stableKey,
    ref_count: 1,
    access_counts: {definition: 1},
    refs: [{
      symbol,
      addr: row.addr,
      rowIndex,
      row_index: rowIndex,
      hunkIndex,
      hunk_index: hunkIndex,
      stableKey,
      stable_key: stableKey,
      summary: matchText.trim() || `${symbol}:`,
      matchText,
      match_text: matchText,
      access: "definition",
    }],
  });
}

function addLabelNavigationRef(labels, row, rowIndex, symbol) {
  const label = labels.get(symbol);
  if (!label) {
    return;
  }
  const hunkIndex = rowHunkIndex(row);
  const stableKey = row.stable_key ?? row.stableKey ?? null;
  const matchText = renderListingCode(row);
  label.refs.push({
    symbol,
    addr: row.addr,
    rowIndex,
    row_index: rowIndex,
    hunkIndex,
    hunk_index: hunkIndex,
    stableKey,
    stable_key: stableKey,
    summary: matchText.trim() || symbol,
    matchText,
    match_text: matchText,
    access: "reference",
  });
  label.ref_count += 1;
  label.access_counts.reference = (label.access_counts.reference || 0) + 1;
}

function addEquateNavigationEntry(equates, row, rowIndex) {
  const equate = equateDefinitionFromRow(row);
  if (!equate) {
    return;
  }
  const hunkIndex = rowHunkIndex(row);
  const stableKey = row.stable_key ?? row.stableKey ?? null;
  const matchText = renderListingCode(row);
  equates.set(equate.symbol, {
    symbol: equate.symbol,
    operand: equate.operand,
    summary: `${equate.symbol} EQU${equate.operand ? ` ${equate.operand}` : ""}`,
    matchText,
    match_text: matchText,
    addr: row.addr ?? null,
    rowIndex,
    row_index: rowIndex,
    hunkIndex,
    hunk_index: hunkIndex,
    stableKey,
    stable_key: stableKey,
    ref_count: 1,
    access_counts: {definition: 1},
    refs: [{
      symbol: equate.symbol,
      addr: row.addr ?? null,
      rowIndex,
      row_index: rowIndex,
      hunkIndex,
      hunk_index: hunkIndex,
      stableKey,
      stable_key: stableKey,
      summary: matchText.trim() || equate.symbol,
      matchText,
      match_text: matchText,
      access: "definition",
    }],
  });
}

function addEquateNavigationRef(equates, row, rowIndex, symbol) {
  const equate = equates.get(symbol);
  if (!equate) {
    return;
  }
  const ownDefinition = equateDefinitionFromRow(row);
  if (ownDefinition?.symbol === symbol) {
    return;
  }
  const hunkIndex = rowHunkIndex(row);
  const stableKey = row.stable_key ?? row.stableKey ?? null;
  const matchText = renderListingCode(row);
  equate.refs.push({
    symbol,
    addr: row.addr ?? null,
    rowIndex,
    row_index: rowIndex,
    hunkIndex,
    hunk_index: hunkIndex,
    stableKey,
    stable_key: stableKey,
    summary: matchText.trim() || symbol,
    matchText,
    match_text: matchText,
    access: "reference",
  });
  equate.ref_count += 1;
  equate.access_counts.reference = (equate.access_counts.reference || 0) + 1;
}

function sortedAppSlotNavigationEntries(appSlots) {
  return Array.from(appSlots.values())
    .map((slot) => {
      slot.refs.sort((left, right) => Number(left.row_index) - Number(right.row_index));
      return slot;
    })
    .sort((left, right) => (left.displacement - right.displacement) || left.symbol.localeCompare(right.symbol));
}

function sortedLabelNavigationEntries(labels) {
  return Array.from(labels.values()).map((label) => {
    label.refs.sort((left, right) => Number(left.row_index) - Number(right.row_index));
    return label;
  }).sort((left, right) => Number(left.row_index) - Number(right.row_index) || left.symbol.localeCompare(right.symbol));
}

function sortedEquateNavigationEntries(equates) {
  return Array.from(equates.values()).map((equate) => {
    equate.refs.sort((left, right) => Number(left.row_index) - Number(right.row_index));
    return equate;
  }).sort((left, right) => Number(left.row_index) - Number(right.row_index) || left.symbol.localeCompare(right.symbol));
}

function buildNavigationEntries(rows) {
  const groups = {
    "repro-issues": [],
    "typed-data": [],
    "typed-gaps": [],
    "relocations": [],
    "api-calls": [],
    "app-slots": [],
    "app-slot-regions": [],
    "app-slot-gaps": [],
    "app-slot-field-gaps": [],
    "app-slot-api-args": [],
    "labels": [],
    "equates": [],
    "comments": [],
    "review-notes": [],
  };
  const appSlots = new Map();
  const labels = new Map();
  const equates = new Map();
  const typedDataSeen = new Set();
  rows.forEach((row, rowIndex) => {
    addEquateNavigationEntry(equates, row, rowIndex);
    if (row.addr === null || row.addr === undefined) {
      return;
    }
    if (isLabelRow(row)) {
      addLabelNavigationEntry(labels, row, rowIndex);
    }
  });
  rows.forEach((row, rowIndex) => {
    rowOperandSymbolNames(row).forEach((symbol) => addEquateNavigationRef(equates, row, rowIndex, symbol));
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
      const summary = summarizeNavigationRow(row, "typed-data");
      const hunkIndex = rowHunkIndex(row);
      const key = `${hunkIndex ?? ""}:${row.addr}:${summary}`;
      if (!typedDataSeen.has(key)) {
        typedDataSeen.add(key);
        groups["typed-data"].push({
          addr: row.addr,
          rowIndex,
          row_index: rowIndex,
          stableKey: row.stable_key ?? row.stableKey ?? null,
          stable_key: row.stable_key ?? row.stableKey ?? null,
          summary,
          matchText: renderListingCode(row),
          match_text: renderListingCode(row),
        });
      }
    }
    if (rowHasUnresolvedTypedAccess(row)) {
      const hunkIndex = rowHunkIndex(row);
      const stableKey = row.stable_key ?? row.stableKey ?? null;
      const matchText = renderListingCode(row);
      row.unresolved_typed_accesses.forEach((access) => {
        groups["typed-gaps"].push({
          addr: row.addr,
          rowIndex,
          row_index: rowIndex,
          hunkIndex,
          hunk_index: hunkIndex,
          stableKey,
          stable_key: stableKey,
          summary: typedGapSummary(access),
          matchText,
          match_text: matchText,
          root_struct_name: access.root_struct_name ?? access.rootStructName ?? null,
          base_register: access.base_register ?? access.baseRegister ?? null,
          operand_index: access.operand_index ?? access.operandIndex ?? null,
          displacement: access.displacement,
          struct_size: access.struct_size ?? access.structSize ?? null,
          classification: access.classification ?? null,
          container_candidate_count: access.container_candidate_count ?? access.containerCandidateCount ?? null,
          container_struct_name: access.container_struct_name ?? access.containerStructName ?? null,
          container_field_expr: access.container_field_expr ?? access.containerFieldExpr ?? null,
          refinement_applied: access.refinement_applied ?? access.refinementApplied ?? false,
          refined_struct_name: access.refined_struct_name ?? access.refinedStructName ?? null,
          type_provenance_kind: access.type_provenance_kind ?? access.typeProvenanceKind ?? null,
          type_provenance_section: access.type_provenance_section ?? access.typeProvenanceSection ?? null,
          type_provenance_offset: access.type_provenance_offset ?? access.typeProvenanceOffset ?? null,
        });
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
    rowOperandSymbolNames(row).forEach((symbol) => addLabelNavigationRef(labels, row, rowIndex, symbol));
    if (rowHasComment(row)) {
      groups.comments.push({
        addr: row.addr,
        rowIndex,
        summary: summarizeNavigationRow(row, "comments"),
        matchText: renderListingCode(row),
      });
    }
    if (Array.isArray(row.review_notes)) {
      row.review_notes.forEach((note) => {
        groups["review-notes"].push({
          addr: note.addr ?? row.addr,
          rowIndex: note.row_index ?? rowIndex,
          row_index: note.row_index ?? rowIndex,
          stableKey: note.stable_key ?? row.stable_key ?? null,
          stable_key: note.stable_key ?? row.stable_key ?? null,
          summary: reviewNoteLabel(note),
          matchText: note.body || note.title || renderListingCode(row),
          match_text: note.body || note.title || renderListingCode(row),
          note_id: note.note_id,
          tracking: note.tracking || "note_only",
          status: "open",
        });
      });
    }
  });
  groups["app-slots"] = sortedAppSlotNavigationEntries(appSlots);
  groups.labels = sortedLabelNavigationEntries(labels);
  groups.equates = sortedEquateNavigationEntries(equates);
  return groups;
}

function currentNavigationEntries() {
  const groups = state.navigation.entries || buildNavigationEntries(state.listingRows || []);
  if (state.navigation.selectedClass === "app-slots" && state.navigation.appSlotSymbol) {
    const slot = (groups["app-slots"] || []).find((entry) => entry.symbol === state.navigation.appSlotSymbol);
    return slot?.refs || [];
  }
  if (state.navigation.selectedClass === "labels" && state.navigation.labelSymbol) {
    const label = (groups.labels || []).find((entry) => entry.symbol === state.navigation.labelSymbol);
    return label?.refs || [];
  }
  if (state.navigation.selectedClass === "equates" && state.navigation.equateSymbol) {
    const equate = (groups.equates || []).find((entry) => entry.symbol === state.navigation.equateSymbol);
    return equate?.refs || [];
  }
  return groups[state.navigation.selectedClass] || [];
}

async function loadNavigationEntries(projectId) {
  const payload = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/listing/navigation`);
  state.navigation.entries = payload.groups || null;
  state.navigation.appSlotAnalysis = payload.app_slot_analysis || null;
  state.navigation.generation = payload.analysis_generation || null;
  if (
    state.navigation.appSlotSymbol &&
    !((state.navigation.entries?.["app-slots"] || []).some((entry) => entry.symbol === state.navigation.appSlotSymbol))
  ) {
    state.navigation.appSlotSymbol = null;
  }
  if (
    state.navigation.labelSymbol &&
    !((state.navigation.entries?.labels || []).some((entry) => entry.symbol === state.navigation.labelSymbol))
  ) {
    state.navigation.labelSymbol = null;
  }
  if (
    state.navigation.equateSymbol &&
    !((state.navigation.entries?.equates || []).some((entry) => entry.symbol === state.navigation.equateSymbol))
  ) {
    state.navigation.equateSymbol = null;
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

function navigationEntryHasJumpTarget(entry) {
  if (!entry || entry.navigable === false) {
    return false;
  }
  if (navigationEntryRowIndex(entry) !== null) {
    return true;
  }
  return entry.addr !== null && entry.addr !== undefined && Number.isFinite(Number(entry.addr));
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

function labelAccessBadgeLabel(access) {
  return LABEL_ACCESS_LABELS[access] || access;
}

function navigationUsesLabelAccessBadges() {
  return state.navigation.selectedClass === "labels" || state.navigation.selectedClass === "equates";
}

function renderNavigationAccessBadges(entry) {
  const badges = [];
  const accessCounts = entry.access_counts || entry.accessCounts || null;
  const refCount = Number(entry.ref_count ?? entry.refCount);
  if (Number.isFinite(refCount) && refCount > 0) {
    badges.push(`${refCount} ref${refCount === 1 ? "" : "s"}`);
  }
  if (accessCounts && typeof accessCounts === "object") {
    const accessOrder = navigationUsesLabelAccessBadges() ? LABEL_ACCESS_ORDER : APP_SLOT_ACCESS_ORDER;
    const labelForAccess = navigationUsesLabelAccessBadges() ? labelAccessBadgeLabel : appSlotAccessBadgeLabel;
    accessOrder.forEach((access) => {
      const count = Number(accessCounts[access]);
      if (Number.isFinite(count) && count > 0) {
        badges.push(`${labelForAccess(access)} ${count}`);
      }
    });
  } else if (typeof entry.access === "string") {
    badges.push(navigationUsesLabelAccessBadges() ? labelAccessBadgeLabel(entry.access) : appSlotAccessBadgeLabel(entry.access));
  }
  if (state.navigation.selectedClass === "app-slots" && entry.width_counts && typeof entry.width_counts === "object") {
    [["byte", "B"], ["word", "W"], ["long", "L"], ["unknown", "?"]].forEach(([width, label]) => {
      const count = Number(entry.width_counts[width]);
      if (Number.isFinite(count) && count > 0) {
        badges.push(`${label} ${count}`);
      }
    });
  }
  if (state.navigation.selectedClass === "app-slots" && Array.isArray(entry.containing_regions) && entry.containing_regions.length) {
    badges.push("typed");
  }
  if (state.navigation.selectedClass === "app-slot-regions") {
    if (entry.struct_name) {
      badges.push(String(entry.struct_name));
    }
    const fieldRefCount = Number(entry.field_ref_count);
    if (Number.isFinite(fieldRefCount) && fieldRefCount > 0) {
      badges.push(`${fieldRefCount} field${fieldRefCount === 1 ? "" : "s"}`);
    }
  }
  if (state.navigation.selectedClass === "app-slot-api-args") {
    if (entry.register) {
      badges.push(String(entry.register));
    }
    if (entry.type_name) {
      badges.push(String(entry.type_name));
    }
    if (entry.reason) {
      badges.push(String(entry.reason).replaceAll("_", " "));
    }
  }
  if (state.navigation.selectedClass === "typed-gaps") {
    if (entry.base_register) {
      badges.push(String(entry.base_register));
    }
    if (entry.root_struct_name) {
      badges.push(String(entry.root_struct_name));
    }
    const structSize = Number(entry.struct_size ?? entry.structSize);
    if (Number.isFinite(structSize)) {
      badges.push(`size $${structSize.toString(16).toUpperCase().padStart(4, "0")}`);
    }
    const provenance = typedGapProvenanceSummary(entry);
    if (provenance) {
      badges.push(provenance);
    }
  }
  if (state.navigation.selectedClass === "review-notes") {
    badges.push(entry.tracking === "needs_review" ? "needs review" : "note");
    if (entry.status) {
      badges.push(String(entry.status));
    }
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

function currentLabelNavigationSymbol() {
  if (state.navigation.selectedClass !== "labels") {
    return null;
  }
  return state.navigation.labelSymbol || null;
}

function currentEquateNavigationSymbol() {
  if (state.navigation.selectedClass !== "equates") {
    return null;
  }
  return state.navigation.equateSymbol || null;
}

function navigationSummaryText(entries) {
  const appSlotSymbol = currentAppSlotNavigationSymbol();
  if (appSlotSymbol) {
    return `${appSlotSymbol}: ${entries.length} ref${entries.length === 1 ? "" : "s"}`;
  }
  const labelSymbol = currentLabelNavigationSymbol();
  if (labelSymbol) {
    return `${labelSymbol}: ${entries.length} ref${entries.length === 1 ? "" : "s"}`;
  }
  const equateSymbol = currentEquateNavigationSymbol();
  if (equateSymbol) {
    return `${equateSymbol}: ${entries.length} ref${entries.length === 1 ? "" : "s"}`;
  }
  if (state.navigation.selectedClass === "app-slots" && state.navigation.appSlotAnalysis) {
    const analysis = state.navigation.appSlotAnalysis;
    const slots = Number(analysis.slot_count || 0);
    const refs = Number(analysis.ref_count || 0);
    const typed = Number(analysis.typed_region_count || 0);
    const gaps = Number(analysis.gap_count || 0);
    const suggestions = Number(analysis.suggestion_count || 0);
    const untyped = Number(analysis.untyped_api_arg_count || 0);
    if (slots || refs || typed || gaps || suggestions || untyped) {
      return `${slots} slots, ${refs} refs, ${typed} typed regions, ${gaps} gaps, ${suggestions} suggestions, ${untyped} untyped API args`;
    }
  }
  return `${entries.length} entries`;
}

function navigationEntryHasRefs(entry) {
  return Array.isArray(entry?.refs);
}

function appSlotEntriesFromGroups(groups) {
  return groups?.["app-slots"] || [];
}

function labelEntriesFromGroups(groups) {
  return groups?.labels || [];
}

function equateEntriesFromGroups(groups) {
  return groups?.equates || [];
}

function appSlotEntryIndex(entries, symbolName) {
  return entries.findIndex((entry) => entry.symbol === symbolName);
}

function labelEntryIndex(entries, symbolName) {
  return entries.findIndex((entry) => entry.symbol === symbolName);
}

function equateEntryIndex(entries, symbolName) {
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

function labelRefEntryIndex(refs, rowIndex, access) {
  const wantedRow = Number(rowIndex);
  const wantedAccess = String(access || "");
  if (Number.isFinite(wantedRow)) {
    const exact = refs.findIndex((ref) => (
      navigationEntryRowIndex(ref) === wantedRow && (!wantedAccess || ref.access === wantedAccess)
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

const equateRefEntryIndex = labelRefEntryIndex;

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

async function selectLabelNavigationRef(projectId, symbolName, rowIndex = null, access = null) {
  const symbol = String(symbolName || "").replace(/:$/, "");
  if (!symbol) {
    return;
  }
  const groups = await ensureNavigationEntries(projectId);
  const entries = labelEntriesFromGroups(groups);
  const labelIndex = labelEntryIndex(entries, symbol);
  if (labelIndex < 0) {
    return;
  }
  const refs = entries[labelIndex].refs || [];
  const refIndex = labelRefEntryIndex(refs, rowIndex, access);
  if (!state.navigation.overlayOpen) {
    state.navigation.originEntry = captureViewportAnchor();
  }
  state.navigation.overlayOpen = true;
  state.navigation.selectedClass = "labels";
  state.navigation.labelSymbol = symbol;
  state.navigation.selectedIndex = Math.max(0, refIndex);
  state.navigation.currentPreviewEntry = refs[state.navigation.selectedIndex] || null;
  renderNavigationOverlay();
  syncNavigationListFocus();
  focusVisibleListingRowByIndex(rowIndex);
}

async function selectEquateNavigationRef(projectId, symbolName, rowIndex = null, access = null) {
  const symbol = String(symbolName || "").trim();
  if (!symbol) {
    return;
  }
  const groups = await ensureNavigationEntries(projectId);
  const entries = equateEntriesFromGroups(groups);
  const equateIndex = equateEntryIndex(entries, symbol);
  if (equateIndex < 0) {
    return;
  }
  const refs = entries[equateIndex].refs || [];
  const refIndex = equateRefEntryIndex(refs, rowIndex, access);
  if (!state.navigation.overlayOpen) {
    state.navigation.originEntry = captureViewportAnchor();
  }
  state.navigation.overlayOpen = true;
  state.navigation.selectedClass = "equates";
  state.navigation.equateSymbol = symbol;
  state.navigation.selectedIndex = Math.max(0, refIndex);
  state.navigation.currentPreviewEntry = refs[state.navigation.selectedIndex] || null;
  renderNavigationOverlay();
  syncNavigationListFocus();
  focusVisibleListingRowByIndex(rowIndex);
}

async function jumpToListingEquate(projectId, symbolName) {
  const symbol = String(symbolName || "").trim();
  if (!symbol) {
    return;
  }
  const groups = await ensureNavigationEntries(projectId);
  const equates = equateEntriesFromGroups(groups);
  const target = equates.find((entry) => entry.symbol === symbol);
  if (!target) {
    return;
  }
  await jumpToListingIndex(
    projectId,
    target.rowIndex ?? target.row_index,
    target.addr,
    target.matchText || target.match_text || `${symbol} EQU`,
    target.stableKey || target.stable_key || null,
  );
}

async function handleListingSymbolButtonAction(projectId, button, event) {
  const symbol = button?.dataset?.symbolName || "";
  if (!symbol) {
    return false;
  }
  event?.preventDefault?.();
  event?.stopPropagation?.();
  const groups = await ensureNavigationEntries(projectId);
  const labelExists = labelEntryIndex(labelEntriesFromGroups(groups), symbol.replace(/:$/, "")) >= 0;
  const equateExists = equateEntryIndex(equateEntriesFromGroups(groups), symbol) >= 0;
  const role = button.dataset.symbolRole || "";
  const rowIndex = button.dataset.rowIndex ?? null;
  if (role === "definition" && labelExists) {
    void selectLabelNavigationRef(projectId, symbol, rowIndex, "definition");
    return true;
  }
  if (role === "reference" && (event?.ctrlKey || event?.metaKey) && labelExists) {
    void selectLabelNavigationRef(projectId, symbol, rowIndex, "reference");
    return true;
  }
  if (equateExists) {
    if (role === "reference" && (event?.ctrlKey || event?.metaKey)) {
      void selectEquateNavigationRef(projectId, symbol, rowIndex, "reference");
    } else {
      await jumpToListingEquate(projectId, symbol);
    }
    return true;
  }
  void jumpToListingSymbol(projectId, symbol);
  return true;
}

function renderNavigationBack() {
  if (currentAppSlotNavigationSymbol()) {
    return '<button type="button" class="navigation-back-to-slots" data-navigation-app-slots-root="1">All App Slots</button>';
  }
  if (currentLabelNavigationSymbol()) {
    return '<button type="button" class="navigation-back-to-slots" data-navigation-labels-root="1">All Labels</button>';
  }
  if (currentEquateNavigationSymbol()) {
    return '<button type="button" class="navigation-back-to-slots" data-navigation-equates-root="1">All Equates</button>';
  }
  return "";
}

function captureNavigationListScrollTop() {
  const list = document.querySelector("#navigation-overlay [data-navigation-list='1']");
  return list instanceof HTMLElement ? list.scrollTop : null;
}

function restoreNavigationListScrollTop(scrollTop) {
  if (scrollTop === null) {
    return;
  }
  const list = document.querySelector("#navigation-overlay [data-navigation-list='1']");
  if (list instanceof HTMLElement) {
    list.scrollTop = scrollTop;
  }
}

function renderNavigationOverlay() {
  const existing = document.getElementById("navigation-overlay");
  const listScrollTop = captureNavigationListScrollTop();
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
    ["typed-gaps", "Typed Gaps"],
    ["relocations", "Relocations"],
    ["api-calls", "API Calls"],
    ["app-slots", "App Slots"],
    ["app-slot-regions", "App Regions"],
    ["app-slot-gaps", "App Gaps"],
    ["app-slot-field-gaps", "App Field Gaps"],
    ["app-slot-api-args", "App API Args"],
    ["app-slot-suggestions", "App Suggestions"],
    ["review-notes", "Review Notes"],
    ["labels", "Labels"],
    ["equates", "Equates"],
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
        <form class="navigation-address-form" data-navigation-address-form="1">
          <label class="navigation-address-label">
            <span>Runtime Address</span>
            <input class="navigation-address-input" data-navigation-address-input="1" type="text" inputmode="text" placeholder="$6102">
          </label>
          <button type="submit" class="navigation-address-submit">Jump</button>
        </form>
        <div class="navigation-summary-row">
          <div class="navigation-summary">${escapeHtml(navigationSummaryText(entries))}</div>
          ${renderNavigationBack()}
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
  restoreNavigationListScrollTop(listScrollTop);
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
  if (state.navigation.selectedClass === "app-slots" && navigationEntryHasRefs(entry)) {
    return;
  }
  if (state.navigation.selectedClass === "repro-issues") {
    state.reproduction.selectedIssueEntry = entry;
    renderReproPanel();
  }
  if (await jumpToNavigationEntry(state.project, entry)) {
    state.navigation.currentPreviewEntry = entry;
  } else {
    state.navigation.currentPreviewEntry = null;
  }
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
  state.navigation.labelSymbol = null;
  state.navigation.equateSymbol = null;
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

async function openNavigationOverlay(selectedClass = null, selectedNoteId = null) {
  if (state.project) {
    await ensureNavigationEntries(state.project);
  }
  state.navigation.overlayOpen = true;
  state.navigation.originEntry = captureViewportAnchor();
  if (selectedClass) {
    state.navigation.selectedClass = selectedClass;
    state.navigation.selectedIndex = 0;
    state.navigation.appSlotSymbol = null;
    state.navigation.labelSymbol = null;
    state.navigation.equateSymbol = null;
  }
  renderNavigationOverlay();
  syncNavigationListFocus();
  const entries = currentNavigationEntries();
  if (!entries.length) {
    return;
  }
  const originAddr = state.navigation.originEntry?.addr ?? null;
  const noteIndex = selectedNoteId ? entries.findIndex((entry) => entry.note_id === selectedNoteId) : -1;
  const initialIndex = noteIndex >= 0
    ? noteIndex
    : originAddr === null ? 0 : Math.max(0, entries.findIndex((entry) => entry.addr >= originAddr));
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
  overlay.querySelector("[data-navigation-address-form='1']")?.addEventListener("submit", (event) => {
    event.preventDefault();
    const input = overlay.querySelector("[data-navigation-address-input='1']");
    const address = parseListingAddress(input instanceof HTMLInputElement ? input.value : "");
    if (address === null || !state.project) {
      return;
    }
    void jumpToListingRuntimeAddress(state.project, address);
  });
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
  overlay.querySelector("[data-navigation-labels-root='1']")?.addEventListener("click", () => {
    const entries = labelEntriesFromGroups(state.navigation.entries || buildNavigationEntries(state.listingRows || []));
    const labelIndex = labelEntryIndex(entries, state.navigation.labelSymbol || "");
    state.navigation.labelSymbol = null;
    state.navigation.selectedIndex = labelIndex >= 0 ? labelIndex : 0;
    state.navigation.currentPreviewEntry = null;
    renderNavigationOverlay();
    syncNavigationListFocus();
  });
  overlay.querySelector("[data-navigation-equates-root='1']")?.addEventListener("click", () => {
    const entries = equateEntriesFromGroups(state.navigation.entries || buildNavigationEntries(state.listingRows || []));
    const equateIndex = equateEntryIndex(entries, state.navigation.equateSymbol || "");
    state.navigation.equateSymbol = null;
    state.navigation.selectedIndex = equateIndex >= 0 ? equateIndex : 0;
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
  dispatchAppEvent("amiga:api-edit-dialog-opened", {
    projectId,
    addr: row.addr ?? null,
    library: row.api_call?.library || "",
    function: row.api_call?.function || "",
  });
}

function listingWindowRowByGlobalIndex(rows, rowIndex) {
  const globalIndex = Number(rowIndex);
  if (!Number.isFinite(globalIndex)) {
    return null;
  }
  const localIndex = globalIndex - (state.virtualListing.start || 0);
  if (Number.isInteger(localIndex) && localIndex >= 0 && localIndex < rows.length) {
    return rows[localIndex];
  }
  if (Number.isInteger(globalIndex) && globalIndex >= 0 && globalIndex < rows.length) {
    return rows[globalIndex];
  }
  return null;
}

function bindListingEditors(projectId, rows) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  viewport.querySelectorAll("[data-symbol-name]").forEach((button) => {
    button.addEventListener("click", (event) => {
      handleListingSymbolButtonAction(projectId, button, event);
    });
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        handleListingSymbolButtonAction(projectId, button, event);
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
  viewport.querySelectorAll("[data-equate-symbol]").forEach((button) => {
    button.addEventListener("click", () => {
      void selectEquateNavigationRef(
        projectId,
        button.dataset.equateSymbol || "",
        button.dataset.rowIndex ?? null,
        button.dataset.equateAccess ?? null,
      );
    });
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        void selectEquateNavigationRef(
          projectId,
          button.dataset.equateSymbol || "",
          button.dataset.rowIndex ?? null,
          button.dataset.equateAccess ?? null,
        );
      }
    });
  });
  viewport.querySelectorAll("[data-api-edit='1']").forEach((button, index) => {
    button.addEventListener("click", () => {
      const rowIndex = Number(button.dataset.rowIndex);
      const row = listingWindowRowByGlobalIndex(rows, rowIndex);
      if (row) {
        void openApiEditDialog(projectId, row);
      }
    });
  });
  viewport.querySelectorAll("[data-review-note-id]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const noteId = button.dataset.reviewNoteId || "";
      if (event.ctrlKey || event.metaKey) {
        state.navigation.entries = null;
        void openNavigationOverlay("review-notes", noteId);
        return;
      }
      const row = button.closest(".listing-row");
      if (row instanceof HTMLElement) {
        setListingSelectionFromRow(row);
      }
    });
  });
}

function bindInlineParameterSession() {
  const form = document.querySelector("[data-inline-parameter-session]");
  const editor = state.parameterSession;
  if (!(form instanceof HTMLFormElement) || !editor) {
    return;
  }
  const fields = commandParameterSchemaFields(editor.action);
  form.querySelectorAll("[data-command-parameter-name]").forEach((control) => {
    control.addEventListener("input", () => updateCommandParameterValue(editor, control, fields));
    control.addEventListener("change", () => updateCommandParameterValue(editor, control, fields));
    control.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        cancelInlineParameterSession();
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        void submitInlineParameterSession();
      }
    });
  });
  bindParameterChoiceGrid(form, editor, () => renderCurrentListingWindow());
  bindParameterFilteredChooser(form, editor, () => renderCurrentListingWindow(), () => submitInlineParameterSession());
  form.querySelector("[data-inline-parameter-cancel]")?.addEventListener("click", () => {
    cancelInlineParameterSession();
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitInlineParameterSession();
  });
  const firstControl = form.querySelector("[data-command-parameter-name], [data-parameter-filter-input]");
  if (firstControl instanceof HTMLInputElement || firstControl instanceof HTMLSelectElement) {
    firstControl.focus();
    if (firstControl instanceof HTMLInputElement && firstControl.type !== "checkbox") {
      firstControl.select();
    }
  }
}

async function submitInlineParameterSession() {
  const editor = state.parameterSession;
  if (!editor || editor.submitting) {
    return;
  }
  const fields = commandParameterSchemaFields(editor.action);
  const {parameters, errors} = commandParameterPayload(fields, editor.values, editor.action);
  editor.errors = errors;
  editor.submitError = "";
  if (Object.keys(errors).length) {
    renderCurrentListingWindow();
    return;
  }
  editor.submitting = true;
  renderCurrentListingWindow();
  try {
    await submitCommandPaletteCatalogAction(editor.action, parameters);
    applyInlineSubmittedFallback(editor, parameters);
    state.parameterSession = null;
    renderCurrentListingWindow();
  } catch (error) {
    const activeEditor = state.parameterSession;
    if (activeEditor) {
      activeEditor.submitting = false;
      activeEditor.submitError = String(error.message || error);
      renderCurrentListingWindow();
    }
  }
}

function applyInlineSubmittedFallback(editor, parameters) {
  if (!editor || editor.action?.action !== "create_manual_comment") {
    return;
  }
  const text = String(parameters.text || "").trim();
  const rowIndex = Number(editor.rowIndex);
  const localIndex = rowIndex - Number(state.virtualListing.start || 0);
  if (!text || localIndex < 0 || localIndex >= state.listingRows.length) {
    return;
  }
  const rows = state.listingRows.slice();
  rows[localIndex] = {...rows[localIndex], comment_text: text};
  state.listingRows = rows;
}

function normalizeListingProjectionPayload(listing) {
  if (!listing || !Array.isArray(listing.rows)) {
    return listing;
  }
  return {
    ...listing,
    rows: listing.rows.map((row) => {
      const rowKey = row.row_key || row.stable_key || row.stableKey || null;
      if (!rowKey) {
        return row;
      }
      return {
        ...row,
        stable_key: row.stable_key || rowKey,
        stableKey: row.stableKey || rowKey,
      };
    }),
  };
}

async function loadListingWindow(projectId, addr = null, before = 24, after = 80, options = {}) {
  const requestSeq = ++state.virtualListing.requestSeq;
  if (options.abortPrevious && state.virtualListing.fetchAbortController) {
    try {
      state.virtualListing.fetchAbortController.abort();
    } catch (error) {
      if (!isAbortError(error)) {
        throw error;
      }
    }
  }
  const abortController = new AbortController();
  state.virtualListing.fetchAbortController = abortController;
  const params = new URLSearchParams();
  if (options.anchorCode) {
    params.set("anchor_code", String(options.anchorCode).trim());
    params.set("count", String(options.count || after || LISTING_INITIAL_ROW_WINDOW));
  } else if (Number.isInteger(options.sectionIndex) && Number.isFinite(options.sourceOffset)) {
    params.set("section_index", String(options.sectionIndex));
    params.set("source_offset", String(options.sourceOffset));
    params.set("before", String(before));
    params.set("after", String(after));
  } else if (Number.isFinite(options.runtimeAddress)) {
    params.set("runtime_address", String(options.runtimeAddress));
    params.set("before", String(before));
    params.set("after", String(after));
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
  const requestedAt = Number.isFinite(options.requestedAt) ? options.requestedAt : performance.now();
  const startedAt = performance.now();
  let listing;
  try {
    listing = await fetchJson(
      `/api/projects/${encodeURIComponent(projectId)}/listing?${params.toString()}`,
      {signal: abortController.signal},
    );
  } catch (error) {
    if (isAbortError(error)) {
      return null;
    }
    throw error;
  } finally {
    if (state.virtualListing.fetchAbortController === abortController) {
      state.virtualListing.fetchAbortController = null;
    }
  }
  if (!listing) {
    return null;
  }
  listing = normalizeListingProjectionPayload(listing);
  const fetchedAt = performance.now();
  const fetchMs = fetchedAt - startedAt;
  if (requestSeq !== state.virtualListing.requestSeq) {
    return listing;
  }
  if (options.render === false || (options.renderEmpty === false && !listing.rows.length)) {
    return listing;
  }
  const renderMetrics = renderVirtualListingWindow(
    projectId,
    listing,
    options.preserveScroll === true,
    options.restoreAnchor ? listingAnchorScrollTop(listing, options.restoreAnchor) : null,
  );
  recordListingFetchSample({
    totalMs: performance.now() - requestedAt,
    queueMs: Math.max(0, startedAt - requestedAt),
    fetchMs,
    renderMs: renderMetrics.renderMs || 0,
    start: listing.start || 0,
    end: listing.end || (listing.rows ? listing.rows.length : 0),
    totalRows: listing.total_rows || 0,
    generation: listing.analysis_generation || state.virtualListing.generation,
  });
  return listing;
}

async function loadInitialListingWindow(projectId) {
  const viewport = document.getElementById("listing-viewport");
  const count = viewport ? listingFetchCount(viewport) : LISTING_INITIAL_ROW_WINDOW;
  return loadListingWindow(projectId, null, 0, count, {start: 0, count});
}

async function loadUiPreferenceState(projectId) {
  try {
    const payload = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/ui-preferences`);
    state.uiPreferences.payload = payload;
    return payload;
  } catch (error) {
    state.uiPreferences.payload = null;
    return null;
  }
}

function explicitListingLocationFromUrl() {
  const params = new URLSearchParams(window.location.search || "");
  const hashParams = new URLSearchParams(String(window.location.hash || "").replace(/^#/, ""));
  const value = (name) => params.get(name) ?? hashParams.get(name);
  const numericValue = (name) => {
    const text = value(name);
    return text === null ? NaN : Number(text);
  };
  const rowIndex = numericValue("row_index");
  const sectionIndex = numericValue("section_index");
  const sourceOffset = numericValue("source_offset");
  const runtimeAddress = numericValue("runtime_address");
  const addr = numericValue("addr");
  if (Number.isFinite(rowIndex)) {
    return {kind: "row", rowIndex};
  }
  if (Number.isInteger(sectionIndex) && Number.isFinite(sourceOffset)) {
    return {kind: "source", sectionIndex, sourceOffset};
  }
  if (Number.isFinite(runtimeAddress)) {
    return {kind: "runtime", runtimeAddress};
  }
  if (Number.isFinite(addr)) {
    return {kind: "addr", addr};
  }
  return null;
}

function preferenceListingLocation(payload) {
  const location = payload?.preferences?.listing_location;
  if (!location || typeof location !== "object" || payload?.preferences?.stale === true) {
    return null;
  }
  return {
    kind: "preference",
    rowIndex: Number(location.row_index),
    addr: Number(location.addr),
    sectionIndex: Number(location.section_index),
    sourceOffset: Number(location.start_offset),
    stableKey: location.stable_key || null,
    rowCode: location.row_code || "",
    scrollTop: Number(location.scroll_top),
    windowStart: Number(location.window_start),
  };
}

function entrypointListingLocations(payload) {
  const entrypoint = payload?.source_entrypoint;
  if (!entrypoint || typeof entrypoint !== "object") {
    return [];
  }
  const locations = [];
  const sourceOffset = Number(entrypoint.source_offset);
  if (Number.isFinite(sourceOffset)) {
    locations.push({kind: "source", sectionIndex: 0, sourceOffset});
  }
  const runtimeAddress = Number(entrypoint.runtime_address);
  if (Number.isFinite(runtimeAddress)) {
    locations.push({kind: "runtime", runtimeAddress});
  }
  const addr = Number(entrypoint.addr);
  if (Number.isFinite(addr)) {
    locations.push({kind: "addr", addr});
  }
  return locations;
}

async function loadInitialListingLocation(projectId, uiPreferences) {
  await loadInitialListingWindow(projectId);
  await applyInitialListingLocation(projectId, uiPreferences);
}

async function applyInitialListingLocation(projectId, uiPreferences) {
  if (!state.listingRows.length) {
    return false;
  }
  const explicit = explicitListingLocationFromUrl();
  if (explicit && await jumpToListingLocation(projectId, explicit)) {
    state.uiPreferences.initialApplied = true;
    return true;
  }
  const preference = preferenceListingLocation(uiPreferences);
  if (preference && await jumpToListingLocation(projectId, preference)) {
    state.uiPreferences.initialApplied = true;
    return true;
  }
  const entrypoints = entrypointListingLocations(uiPreferences);
  if (entrypoints.length) {
    for (const entrypoint of entrypoints) {
      if (await jumpToListingLocation(projectId, entrypoint)) {
        state.uiPreferences.initialApplied = true;
        return true;
      }
    }
    state.uiPreferences.initialApplied = true;
    return false;
  }
  state.uiPreferences.initialApplied = true;
  return false;
}

async function maybeApplyInitialListingLocation(projectId) {
  if (
    state.uiPreferences.initialApplied
    || state.uiPreferences.restoring
    || state.project !== projectId
    || state.listingSelection
    || !state.listingRows.length
  ) {
    return;
  }
  const uiPreferences = state.uiPreferences.payload || await loadUiPreferenceState(projectId);
  if (state.project !== projectId || state.listingSelection) {
    return;
  }
  const applied = await applyInitialListingLocation(projectId, uiPreferences);
  if (!applied && !state.uiPreferences.initialApplied && state.project === projectId) {
    window.setTimeout(() => {
      void maybeApplyInitialListingLocation(projectId);
    }, 100);
  }
}

async function jumpToListingLocation(projectId, location) {
  state.uiPreferences.restoring = true;
  try {
    if (location.kind === "row" || location.kind === "preference") {
      if (Number.isFinite(location.rowIndex)) {
        const ok = await jumpToListingIndex(
          projectId,
          location.rowIndex,
          location.addr,
          location.rowCode,
          location.stableKey,
        );
        if (ok) {
          restorePreferenceScrollTop(location);
          return true;
        }
      }
      if (Number.isInteger(location.sectionIndex) && Number.isFinite(location.sourceOffset)) {
        const ok = await jumpToListingSectionOffset(projectId, location.sectionIndex, location.sourceOffset);
        restorePreferenceScrollTop(location);
        return ok;
      }
      if (Number.isFinite(location.addr)) {
        const ok = await jumpToListingAddr(projectId, location.addr, location.rowCode || null);
        restorePreferenceScrollTop(location);
        return ok;
      }
      return false;
    }
    if (location.kind === "source") {
      return jumpToListingSectionOffset(projectId, location.sectionIndex, location.sourceOffset);
    }
    if (location.kind === "runtime") {
      return jumpToListingRuntimeAddress(projectId, location.runtimeAddress);
    }
    if (location.kind === "addr") {
      return jumpToListingAddr(projectId, location.addr);
    }
    return false;
  } finally {
    state.uiPreferences.restoring = false;
  }
}

function restorePreferenceScrollTop(location) {
  const viewport = document.getElementById("listing-viewport");
  if (location?.kind !== "preference" || !(viewport instanceof HTMLElement) || !Number.isFinite(location.scrollTop)) {
    return;
  }
  viewport.scrollTop = Math.max(0, location.scrollTop);
}

function currentUiListingLocation() {
  const viewport = document.getElementById("listing-viewport");
  const selection = state.listingSelection || {};
  const anchor = captureListingAddressAnchor(viewport);
  const location = {};
  const rowIndex = Number(selection.rowIndex ?? anchor?.rowIndex);
  if (Number.isFinite(rowIndex)) {
    location.row_index = Math.floor(rowIndex);
  }
  for (const [from, to] of [
    ["stableKey", "stable_key"],
    ["rowCode", "row_code"],
  ]) {
    const value = selection[from] || anchor?.[from];
    if (value) {
      location[to] = String(value);
    }
  }
  for (const [from, to] of [
    ["addr", "addr"],
    ["sectionIndex", "section_index"],
    ["startOffset", "start_offset"],
  ]) {
    const value = Number(selection[from]);
    if (Number.isFinite(value)) {
      location[to] = Math.floor(value);
    }
  }
  if (viewport instanceof HTMLElement) {
    location.scroll_top = Math.floor(viewport.scrollTop);
    location.window_start = Math.floor(Number(state.virtualListing.start || 0));
  }
  return Object.keys(location).length ? location : null;
}

function scheduleUiPreferenceSave() {
  if (!state.project) {
    return;
  }
  if (state.uiPreferences.saveTimer !== null) {
    window.clearTimeout(state.uiPreferences.saveTimer);
  }
  state.uiPreferences.saveTimer = window.setTimeout(() => {
    state.uiPreferences.saveTimer = null;
    if (state.uiPreferences.restoring) {
      scheduleUiPreferenceSave();
      return;
    }
    void saveUiPreferenceState();
  }, 250);
}

async function saveUiPreferenceState() {
  if (!state.project) {
    return;
  }
  const existing = state.uiPreferences.payload?.preferences || {};
  const payload = {
    ...existing,
    listing_location: currentUiListingLocation(),
  };
  try {
    state.uiPreferences.payload = await fetchJson(`/api/projects/${encodeURIComponent(state.project)}/ui-preferences`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
  } catch (error) {
    setAnalysisStatus("UI preference save failed", "failed", 2500);
  }
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

function selectListingRowBySectionOffset(viewport, sectionIndex, offset) {
  if (!viewport || !Number.isInteger(sectionIndex) || !Number.isFinite(offset)) {
    return null;
  }
  const rows = Array.from(viewport.querySelectorAll(`[data-section-index="${String(sectionIndex)}"]`));
  for (const row of rows) {
    const start = Number(row.dataset.startOffset);
    const end = Number(row.dataset.endOffset);
    if (!Number.isFinite(start)) {
      continue;
    }
    if ((Number.isFinite(end) && start <= offset && offset < end) || start === offset) {
      return row;
    }
  }
  return null;
}

function selectListingRowByRuntimeAddress(viewport, address) {
  if (!viewport || !Number.isFinite(address)) {
    return null;
  }
  const rows = Array.from(viewport.querySelectorAll("[data-runtime-address]"));
  for (const row of rows) {
    const start = Number(row.dataset.runtimeAddress);
    const end = Number(row.dataset.runtimeEndAddress);
    if (!Number.isFinite(start)) {
      continue;
    }
    if ((Number.isFinite(end) && start <= address && address < end) || start === address) {
      return row;
    }
  }
  return null;
}

function scrollRowIntoView(viewport, addr, block = "center", matchText = null, stableKey = null, rowIndex = null) {
  const row = selectBestListingRow(viewport, addr, matchText, stableKey, rowIndex);
  if (!row) {
    return false;
  }
  row.scrollIntoView({block, behavior: "smooth"});
  return true;
}

function listingSelectionFromRow(row) {
  if (!(row instanceof HTMLElement)) {
    return null;
  }
  const rowIndex = Number(row.dataset.rowIndex);
  const addr = row.dataset.rowAddr !== "" && row.dataset.rowAddr !== undefined
    ? Number(row.dataset.rowAddr)
    : null;
  const sectionIndex = row.dataset.sectionIndex !== "" && row.dataset.sectionIndex !== undefined
    ? Number(row.dataset.sectionIndex)
    : null;
  const startOffset = row.dataset.startOffset !== "" && row.dataset.startOffset !== undefined
    ? Number(row.dataset.startOffset)
    : null;
  return {
    rowIndex: Number.isFinite(rowIndex) ? rowIndex : null,
    focusRowIndex: Number.isFinite(rowIndex) ? rowIndex : null,
    anchorRowIndex: Number.isFinite(rowIndex) ? rowIndex : null,
    rangeStartRowIndex: Number.isFinite(rowIndex) ? rowIndex : null,
    rangeEndRowIndex: Number.isFinite(rowIndex) ? rowIndex : null,
    focusStableKey: row.dataset.rowStableKey || null,
    anchorStableKey: row.dataset.rowStableKey || null,
    rangeStartStableKey: row.dataset.rowStableKey || null,
    rangeEndStableKey: row.dataset.rowStableKey || null,
    stableKey: row.dataset.rowStableKey || null,
    addr: Number.isFinite(addr) ? addr : null,
    sectionIndex: Number.isInteger(sectionIndex) ? sectionIndex : null,
    startOffset: Number.isFinite(startOffset) ? startOffset : null,
    rowCode: row.dataset.rowCode || "",
    elementKind: null,
    elementText: "",
    elementSelector: null,
    precisionLost: false,
  };
}

function listingSelectionRangeBounds(selection = state.listingSelection) {
  const start = Number(selection?.rangeStartRowIndex);
  const end = Number(selection?.rangeEndRowIndex);
  if (!Number.isFinite(start) || !Number.isFinite(end)) {
    return null;
  }
  return {start: Math.min(start, end), end: Math.max(start, end)};
}

function listingSelectionIsRange(selection = state.listingSelection) {
  const bounds = listingSelectionRangeBounds(selection);
  return Boolean(bounds && bounds.end > bounds.start);
}

function selectedListingRangeRows(selection = state.listingSelection) {
  const bounds = listingSelectionRangeBounds(selection);
  if (!bounds) {
    return [];
  }
  const rows = [];
  for (let index = bounds.start; index <= bounds.end; index += 1) {
    const row = listingRowDataForSelection({rowIndex: index});
    if (!row) {
      return [];
    }
    rows.push({...row, row_index: index});
  }
  return rows;
}

function commandPaletteRangeQuery(selection = state.listingSelection) {
  if (!listingSelectionIsRange(selection)) {
    return null;
  }
  const rows = selectedListingRangeRows(selection);
  if (rows.length < 2) {
    return null;
  }
  const params = new URLSearchParams();
  params.set("context", "range");
  params.set("row_indexes", rows.map((row) => String(row.row_index)).join(","));
  params.set("rows", JSON.stringify(rows.map(commandPaletteRowSnapshot)));
  return params.toString();
}

function rowMatchesSelectionAddress(row, selection) {
  if (!(row instanceof HTMLElement) || !selection) {
    return false;
  }
  const sectionIndex = row.dataset.sectionIndex !== "" && row.dataset.sectionIndex !== undefined
    ? Number(row.dataset.sectionIndex)
    : null;
  const startOffset = row.dataset.startOffset !== "" && row.dataset.startOffset !== undefined
    ? Number(row.dataset.startOffset)
    : null;
  if (
    Number.isInteger(selection.sectionIndex)
    && Number.isFinite(selection.startOffset)
    && sectionIndex === selection.sectionIndex
    && startOffset === selection.startOffset
  ) {
    return true;
  }
  const addr = row.dataset.rowAddr !== "" && row.dataset.rowAddr !== undefined
    ? Number(row.dataset.rowAddr)
    : null;
  return Number.isFinite(selection.addr) && addr === selection.addr && (!selection.rowCode || row.dataset.rowCode === selection.rowCode);
}

function rowContainsSelectedElement(row, selection) {
  if (!selection?.elementSelector && !selection?.elementKind) {
    return true;
  }
  const text = String(selection.elementText || "");
  const candidates = row.querySelectorAll(".listing-symbol-link");
  return Array.from(candidates).some((candidate) => {
    if (text && candidate.textContent !== text) {
      return false;
    }
    const selector = listingElementSelector(candidate, row);
    if (!selection.elementSelector || !selector) {
      return true;
    }
    return Object.entries(selection.elementSelector).every(([key, value]) => String(selector[key] ?? "") === String(value));
  });
}

function renderedRowForListingSelection(viewport, selection) {
  if (!(viewport instanceof HTMLElement) || !selection) {
    return {row: null, precise: false};
  }
  if (selection.stableKey) {
    const stable = viewport.querySelector(`[data-row-stable-key="${CSS.escape(selection.stableKey)}"]`);
    if (stable instanceof HTMLElement) {
      return {row: stable, precise: rowContainsSelectedElement(stable, selection)};
    }
  }
  const rows = Array.from(viewport.querySelectorAll(".listing-row"));
  const addressMatch = rows.find((row) => rowMatchesSelectionAddress(row, selection));
  if (addressMatch instanceof HTMLElement) {
    return {row: addressMatch, precise: !selection.stableKey && rowContainsSelectedElement(addressMatch, selection)};
  }
  if (Number.isFinite(selection.rowIndex)) {
    const indexed = viewport.querySelector(`[data-row-index="${String(selection.rowIndex)}"]`);
    if (indexed instanceof HTMLElement) {
      return {row: indexed, precise: !selection.stableKey && rowContainsSelectedElement(indexed, selection)};
    }
  }
  return {row: null, precise: false};
}

function renderedRowIndexForStableKey(viewport, stableKey) {
  if (!(viewport instanceof HTMLElement) || !stableKey) {
    return null;
  }
  const row = viewport.querySelector(`[data-row-stable-key="${CSS.escape(stableKey)}"]`);
  if (!(row instanceof HTMLElement)) {
    return null;
  }
  const rowIndex = Number(row.dataset.rowIndex);
  return Number.isFinite(rowIndex) ? rowIndex : null;
}

function resolveRenderedListingRangeSelection(viewport, selection) {
  if (!(viewport instanceof HTMLElement) || !selection) {
    return selection;
  }
  const replacements = {};
  [
    ["focusRowIndex", "focusStableKey"],
    ["anchorRowIndex", "anchorStableKey"],
    ["rangeStartRowIndex", "rangeStartStableKey"],
    ["rangeEndRowIndex", "rangeEndStableKey"],
  ].forEach(([indexKey, stableKey]) => {
    const resolved = renderedRowIndexForStableKey(viewport, selection[stableKey]);
    if (Number.isFinite(resolved) && resolved !== selection[indexKey]) {
      replacements[indexKey] = resolved;
    }
  });
  if (!Object.keys(replacements).length) {
    return selection;
  }
  return {
    ...selection,
    ...replacements,
    rowIndex: Number.isFinite(Number(replacements.focusRowIndex)) ? replacements.focusRowIndex : selection.rowIndex,
  };
}

function applyRenderedListingSelection() {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement)) {
    return;
  }
  viewport.querySelectorAll(".listing-row-selected, .listing-row-range-focus").forEach((row) => {
    row.classList.remove("listing-row-selected");
    row.classList.remove("listing-row-range-focus");
  });
  const selection = state.listingSelection;
  if (!selection) {
    return;
  }
  state.listingSelection = resolveRenderedListingRangeSelection(viewport, selection);
  const resolvedSelection = state.listingSelection;
  const bounds = listingSelectionRangeBounds(resolvedSelection);
  if (bounds && listingSelectionIsRange(resolvedSelection)) {
    const focusIndex = Number.isFinite(Number(resolvedSelection.focusRowIndex)) ? Number(resolvedSelection.focusRowIndex) : Number(resolvedSelection.rowIndex);
    viewport.querySelectorAll(".listing-row").forEach((candidate) => {
      if (!(candidate instanceof HTMLElement)) {
        return;
      }
      const rowIndex = Number(candidate.dataset.rowIndex);
      if (Number.isFinite(rowIndex) && rowIndex >= bounds.start && rowIndex <= bounds.end) {
        candidate.classList.add("listing-row-selected");
      }
      if (Number.isFinite(rowIndex) && rowIndex === focusIndex) {
        candidate.classList.add("listing-row-range-focus");
      }
    });
    return;
  }
  const {row, precise} = renderedRowForListingSelection(viewport, resolvedSelection);
  if (row instanceof HTMLElement) {
    row.classList.add("listing-row-selected");
    if (!precise && !resolvedSelection.precisionLost) {
      state.listingSelection = {
        ...listingSelectionFromRow(row),
        precisionLost: true,
      };
      setAnalysisStatus("Selection precision lost", "ready", 2500);
    }
  }
}

function setListingSelectionFromRow(row, element = null) {
  const selection = listingSelectionFromRow(row);
  if (!selection) {
    return;
  }
  if (element instanceof HTMLElement) {
    selection.elementSelector = listingElementSelector(element, row);
    selection.elementKind = selection.elementSelector?.element_kind || listingElementKind(element);
    selection.elementText = element.textContent || "";
  }
  state.listingSelection = selection;
  applyRenderedListingSelection();
  dispatchAppEvent("amiga:listing-row-selected", selection);
  scheduleUiPreferenceSave();
}

function listingElementKind(element) {
  if (element.dataset.elementKind) {
    return element.dataset.elementKind;
  }
  if (element.matches("[data-equate-symbol], [data-symbol-name]")) {
    return "symbol";
  }
  if (element.matches("[data-app-slot-symbol]")) {
    return "app_slot";
  }
  return "data_literal";
}

function listingElementSelector(element, row = null) {
  if (!(element instanceof HTMLElement)) {
    return null;
  }
  const selector = {};
  const kind = listingElementKind(element);
  if (kind) {
    selector.element_kind = kind;
  }
  const operandIndex = Number(element.dataset.operandIndex ?? element.dataset.appSlotOperandIndex);
  if (Number.isInteger(operandIndex)) {
    selector.operand_index = operandIndex;
  }
  const symbol = element.dataset.appSlotSymbol || element.dataset.equateSymbol || element.dataset.symbolName || "";
  if (symbol) {
    selector.symbol = symbol;
  }
  const access = element.dataset.appSlotAccess || element.dataset.equateAccess || "";
  if (access) {
    selector.access = access;
  }
  if (row instanceof HTMLElement && kind === "label" && row.dataset.rowKind !== "label") {
    return null;
  }
  return Object.keys(selector).length ? selector : null;
}

function setListingSelectionIndex(rowIndex) {
  state.listingSelection = {
    rowIndex,
    focusRowIndex: rowIndex,
    anchorRowIndex: rowIndex,
    rangeStartRowIndex: rowIndex,
    rangeEndRowIndex: rowIndex,
    stableKey: null,
    focusStableKey: null,
    anchorStableKey: null,
    rangeStartStableKey: null,
    rangeEndStableKey: null,
    addr: null,
    sectionIndex: null,
    startOffset: null,
    rowCode: "",
    precisionLost: true,
  };
  applyRenderedListingSelection();
}

function extendListingSelectionToRow(row, targetIndex) {
  const target = listingSelectionFromRow(row) || {rowIndex: targetIndex, stableKey: null};
  const current = state.listingSelection || {};
  const anchor = Number.isFinite(Number(current.anchorRowIndex))
    ? Number(current.anchorRowIndex)
    : Number(current.rowIndex);
  const anchorIndex = Number.isFinite(anchor) ? anchor : targetIndex;
  const start = Math.min(anchorIndex, targetIndex);
  const end = Math.max(anchorIndex, targetIndex);
  state.listingSelection = {
    ...target,
    rowIndex: targetIndex,
    focusRowIndex: targetIndex,
    anchorRowIndex: anchorIndex,
    rangeStartRowIndex: start,
    rangeEndRowIndex: end,
    focusStableKey: target.stableKey || null,
    anchorStableKey: current.anchorStableKey || current.stableKey || null,
    rangeStartStableKey: start === targetIndex ? target.stableKey || null : current.anchorStableKey || current.stableKey || null,
    rangeEndStableKey: end === targetIndex ? target.stableKey || null : current.anchorStableKey || current.stableKey || null,
    elementKind: null,
    elementText: "",
    elementSelector: null,
  };
  applyRenderedListingSelection();
  dispatchAppEvent("amiga:listing-row-selected", state.listingSelection);
  scheduleUiPreferenceSave();
}

function bindListingSelection() {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement)) {
    return;
  }
  viewport.querySelectorAll(".listing-row").forEach((row) => {
    row.addEventListener("click", (event) => {
      const element = event.target instanceof HTMLElement ? event.target.closest(".listing-symbol-link") : null;
      if (element instanceof HTMLElement) {
        setListingSelectionFromRow(row, element);
        return;
      }
      if (event.target instanceof HTMLElement && event.target.closest("button, input, select, textarea, a")) {
        return;
      }
      setListingSelectionFromRow(row);
    });
  });
}

async function moveListingSelection(delta, extend = false) {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement) || !state.project) {
    return false;
  }
  let currentIndex = Number(extend ? state.listingSelection?.focusRowIndex : state.listingSelection?.rowIndex);
  if (!Number.isFinite(currentIndex)) {
    const firstRow = viewport.querySelector(".listing-row");
    currentIndex = firstRow instanceof HTMLElement ? Number(firstRow.dataset.rowIndex) : 0;
  }
  if (!Number.isFinite(currentIndex)) {
    currentIndex = 0;
  }
  const maxIndex = Math.max(0, (state.virtualListing.totalRows || 1) - 1);
  const targetIndex = Math.max(0, Math.min(maxIndex, Math.floor(currentIndex) + delta));
  if (!extend) {
    setListingSelectionIndex(targetIndex);
  }
  let row = viewport.querySelector(`[data-row-index="${String(targetIndex)}"]`);
  if (!(row instanceof HTMLElement)) {
    const visibleRows = listingVisibleRowCount(viewport);
    const count = listingFetchCount(viewport);
    const start = Math.max(0, targetIndex - visibleRows);
    await loadListingWindow(state.project, null, 0, count, {start, count});
    row = viewport.querySelector(`[data-row-index="${String(targetIndex)}"]`);
  }
  if (row instanceof HTMLElement) {
    if (extend) {
      extendListingSelectionToRow(row, targetIndex);
    } else {
      setListingSelectionFromRow(row);
    }
    row.scrollIntoView({block: "nearest", behavior: "auto"});
    return true;
  }
  return false;
}

function focusListingRow(row) {
  if (!(row instanceof HTMLElement)) {
    return;
  }
  setListingSelectionFromRow(row);
  row.classList.add("listing-row-focus");
  dispatchAppEvent("amiga:listing-row-focused", {
    addr: row.dataset.rowAddr !== "" && row.dataset.rowAddr !== undefined ? Number(row.dataset.rowAddr) : null,
    rowIndex: row.dataset.rowIndex !== "" && row.dataset.rowIndex !== undefined ? Number(row.dataset.rowIndex) : null,
    stableKey: row.dataset.rowStableKey || null,
    rowCode: row.dataset.rowCode || "",
  });
  window.setTimeout(() => row.classList.remove("listing-row-focus"), 1200);
}

function formatHunkSubkind(content) {
  if (!content || typeof content !== "object") {
    return "executable";
  }
  const explicitType = String(
    content.target_type
    || content.import_target_type
    || (content.import_target && content.import_target.target_type)
    || (content.import_target && content.import_target.target_metadata && content.import_target.target_metadata.target_type)
    || "",
  ).toLowerCase();
  if (explicitType === "library") {
    return "library";
  }
  if (explicitType === "device") {
    return "device";
  }
  const residentType = String(
    (content.resident && (content.resident.node_type_name || content.resident.node_type))
    || "",
  ).toLowerCase();
  if (residentType === "library") {
    return "library";
  }
  if (residentType === "device") {
    return "device";
  }
  if (content.library) {
    return "library";
  }
  return "executable";
}

function formatFileKind(entry) {
  const content = entry.content;
  if (!content) {
    throw new Error(`Indexed file is missing content metadata: ${entry.full_path}`);
  }
  if (content.kind === "amiga_hunk_executable") {
    const hunkCount = Number(content.hunk_count);
    const count = Number.isFinite(hunkCount) ? `x${hunkCount}` : "";
    return `HUNK ${formatHunkSubkind(content)} ${count}`.trim();
  }
  if (content.kind === "iff_container") {
    return `IFF ${content.group_id || "container"} ${content.form_id || ""}`.trim();
  }
  if (content.kind) {
    return content.kind;
  }
  return "unknown";
}

function renderDiskTargetEntryIcon(entry, target) {
  const content = entry && typeof entry === "object" ? entry.content : null;
  const kind = content && typeof content.kind === "string" ? content.kind : "";
  if (kind === "text") {
    return "&#128195;";
  }
  if ((kind === "amiga_hunk_executable" && content.is_executable) || kind === "amiga_hunk_executable") {
    return "&#62;";
  }
  if (kind === "iff_container") {
    const formId = content.form_id ? String(content.form_id).toUpperCase() : "";
    const groupId = content.group_id ? String(content.group_id).toUpperCase() : "";
    if (formId === "8SVX" || groupId === "8SVX") {
      return "&#128266;";
    }
    if (formId === "ILBM" || groupId === "ILBM") {
      return "&#128065;";
    }
  }
  if (target && target.entry_path === "bootblock") {
    return "";
  }
  return "&#63;";
}

function renderDiskSourcePathIcon(path) {
  const normalized = String(path || "").trim().toLowerCase();
  if (!normalized) {
    return "&#63;";
  }
  if (normalized === "s/startup-sequence" || normalized === "startup-sequence" || normalized === "s:startup-sequence") {
    return "&#128195;";
  }
  return "&#63;";
}

function formatTargetTypeLabel(targetType) {
  return targetType.replaceAll("_", " ");
}

function formatRelationshipValue(value) {
  return String(value).replaceAll("_", " ");
}

function renderInlineBadges(labels) {
  return labels
    .filter((label) => label)
    .map((label) => `<span class="project-badge">${escapeHtml(label)}</span>`)
    .join("");
}

function payloadRelationshipTooltip(relationship) {
  const details = [];
  if (!relationship) {
    return "";
  }
  if (relationship.payload_role) {
    details.push(`role: ${formatRelationshipValue(relationship.payload_role)}`);
  }
  if (relationship.payload_role_confidence) {
    details.push(`confidence: ${formatRelationshipValue(relationship.payload_role_confidence)}`);
  }
  if (relationship.parent_remains_active !== null && relationship.parent_remains_active !== undefined) {
    const active = String(relationship.parent_remains_active).toLowerCase();
    if (active === "true") {
      details.push("parent remains active");
    } else if (active === "false") {
      details.push("parent replaced");
    } else {
      details.push(`parent active: ${formatRelationshipValue(relationship.parent_remains_active)}`);
    }
  }
  return details.join(" | ");
}

function renderTargetTypeBadgeLabel(targetType) {
  if (targetType === "raw_binary") {
    return "RAW";
  }
  return formatTargetTypeLabel(targetType).toUpperCase();
}

function decompressedDerivedTargets(target) {
  const derivedTargets = target && Array.isArray(target.derived_targets) ? target.derived_targets : [];
  return derivedTargets.filter((item) => item && item.kind === "decompressed_payload");
}

function isStandardDecompressionStubTarget(target) {
  const derivedTargets = target && Array.isArray(target.derived_targets) ? target.derived_targets : [];
  const decompressedTargets = decompressedDerivedTargets(target);
  if (derivedTargets.length !== 1 || decompressedTargets.length !== 1) {
    return false;
  }
  const relationship = decompressedTargets[0];
  return relationship.payload_role === "primary_program"
    && String(relationship.parent_remains_active).toLowerCase() === "false";
}

function renderDiskTargetBadgeLabels(target) {
  const badges = [renderTargetTypeBadgeLabel(target.target_type)];
  if (isStandardDecompressionStubTarget(target)) {
    badges.push("stub");
  }
  return badges;
}

function appendDerivedTargetSummary(details, target) {
  const derivedTargets = target.derived_targets;
  if (!Array.isArray(derivedTargets) || !derivedTargets.length) {
    return;
  }
  const decompressedTargets = decompressedDerivedTargets(target);
  if (!decompressedTargets.length) {
    details.push(`${derivedTargets.length} derived targets`);
    return;
  }
}

function derivedTargetsRelationshipTooltip(target) {
  const derivedTargets = target.derived_targets;
  if (!Array.isArray(derivedTargets) || !derivedTargets.length) {
    return "";
  }
  const decompressedTargets = decompressedDerivedTargets(target);
  const lines = [];
  if (decompressedTargets.length) {
    lines.push(`${decompressedTargets.length} decompressed payload${decompressedTargets.length === 1 ? "" : "s"}`);
  }
  const relationshipLines = derivedTargets
    .map((item) => payloadRelationshipTooltip(item))
    .filter((item) => item);
  lines.push(...relationshipLines);
  return lines.join(" | ");
}

function renderBootBlockTarget(bootBlock, filesystem, bootblockTargetName) {
  const details = [
    `${formatBriefFileSize(bootBlock.bootcode_size)} bootcode`,
    bootBlock.is_dos ? `fs type ${bootBlock.fs_type}` : "non-DOS boot block",
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

function renderDiskTargetMetadata(target, entry, payloadNode = null) {
  if (target.derived_from && typeof target.derived_from === "object") {
    const origin = target.derived_from;
    const payloadMeta = payloadNode && typeof payloadNode === "object" ? payloadNode : null;
    const details = [];
    const relationshipKind = String(origin.kind || "").toLowerCase();
    const isPayloadRelationship = relationshipKind.includes("decompressed_payload");
    const payloadSize = Number(origin.decompressed_size);
    const size = Number.isFinite(payloadSize)
      ? payloadSize
      : Number(entry ? entry.size : undefined);
    if (Number.isFinite(size)) {
      details.push(formatBriefFileSize(size));
    }
    const payloadBadges = [renderTargetTypeBadgeLabel(target.target_type)];
    if (isPayloadRelationship) {
      payloadBadges.unshift("decompressed");
    }
    if (origin.payload_role === "primary_program") {
      payloadBadges.push("PRIMARY");
    }
    if (origin.compressor) {
      const compressor = typeof origin.compressor === "string"
        ? origin.compressor
        : (origin.compressor.id || origin.compressor.name);
      if (compressor) {
        details.push(compressor);
      }
    }
    const fileOffsetValue = payloadMeta?.source_file_offset ?? origin.packed_file_offset;
    const hunkOffset = Number(payloadMeta?.source_hunk_offset ?? origin.packed_section_offset);
    const sourceSection = Number(origin.source_section ?? (payloadMeta && payloadMeta.source_section));
    const includeHunk = Number.isFinite(sourceSection) && Number.isInteger(sourceSection);
    const fileOffset = Number(fileOffsetValue);
    if (Number.isFinite(fileOffset)) {
      const offsetText = `offset ${formatAddressHex(fileOffset)}`;
      details.push(
        isPayloadRelationship && includeHunk && Number.isFinite(hunkOffset)
          ? `${offsetText} hunk ${sourceSection}@${formatAddressHex(hunkOffset)}`
          : offsetText
      );
    }
    const loadAddress = Number(origin.load_address);
    const entryAddress = Number(origin.entrypoint);
    const hasLoadAddress = Number.isFinite(loadAddress);
    const hasEntryAddress = Number.isFinite(entryAddress);
    if (hasLoadAddress || hasEntryAddress) {
      if (hasLoadAddress && hasEntryAddress && loadAddress === entryAddress) {
        details.push(`load/enter @ ${formatAddressHex(loadAddress)}`);
      } else {
        if (hasLoadAddress) {
          details.push(`load @ ${formatAddressHex(loadAddress)}`);
        }
        if (hasEntryAddress) {
          details.push(`enter @ ${formatAddressHex(entryAddress)}`);
        }
      }
    }
    const payloadTooltip = payloadRelationshipTooltip(origin);
    const metaText = `${renderInlineBadges(payloadBadges)} ${escapeHtml(details.join(" | "))}`.trim();
    return {
      metadata: metaText || "",
      tooltip: payloadTooltip || "",
    };
  }
  if (
    !entry
    && (target.entry_path === "bootblock" || String(target.entry_path || "").startsWith("bootloader/"))
  ) {
    const details = [target.binary_path || target.entry_path];
    const tooltip = derivedTargetsRelationshipTooltip(target);
    appendDerivedTargetSummary(details, target);
    return {
      metadata: `${renderInlineBadges(renderDiskTargetBadgeLabels(target))} ${escapeHtml(details.join(" | "))}`.trim(),
      tooltip: tooltip || "",
    };
  }
  if (!entry) {
    throw new Error(`Missing indexed file entry for imported target: ${target.entry_path}`);
  }
  const content = entry.content;
  if (!content) {
    throw new Error(`Target entry is missing content metadata: ${entry.full_path}`);
  }
  const details = [formatBriefFileSize(entry.size), formatFileKind(entry)];
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
  appendDerivedTargetSummary(details, target);
  return {
    metadata: `${renderInlineBadges(renderDiskTargetBadgeLabels(target))} ${escapeHtml(details.join(" | "))}`.trim(),
    tooltip: derivedTargetsRelationshipTooltip(target),
  };
}

function renderDiskTargetStateSummary(targetState) {
  const state = targetState && typeof targetState === "object" ? targetState : {};
  const startupParse = state.startup_sequence_parse && typeof state.startup_sequence_parse === "object"
    ? state.startup_sequence_parse
    : null;
  const candidateRejects = Array.isArray(state.candidate_rejects) ? state.candidate_rejects : [];
  const startupSequenceLines = startupParse && Array.isArray(startupParse.startup_sequence_lines)
    ? startupParse.startup_sequence_lines
    : [];
  const startupSequenceEntries = startupParse && Array.isArray(startupParse.startup_sequence_entries)
    ? startupParse.startup_sequence_entries
    : [];
  const startupLineStatus = new Map();
  if (startupSequenceEntries.length) {
    for (const entry of startupSequenceEntries) {
      if (!entry || typeof entry !== "object") {
        continue;
      }
      const line = Number(entry.line);
      if (!Number.isFinite(line)) {
        continue;
      }
      const lineNumber = Number(line);
      const list = startupLineStatus.get(lineNumber) || [];
      list.push(entry);
      startupLineStatus.set(lineNumber, list);
    }
  }
  if (!startupParse && !candidateRejects.length) {
    return "";
  }
  const details = [];
  if (startupParse && startupParse.status) {
    const parseLine = Number.isFinite(startupParse.line) ? ` @ line ${startupParse.line}` : "";
    details.push(`status=${startupParse.status}${parseLine}`);
  }
  if (startupParse && startupParse.reason) {
    details.push(`reason=${startupParse.reason}`);
  }
  const sourcePath = startupParse && typeof startupParse.source_path === "string" ? startupParse.source_path : "s/startup-sequence";
  details.push(`source=${sourcePath}`);
  if (startupParse && startupParse.command) {
    details.push(`command=${startupParse.command}`);
  }
  if (startupParse && startupParse.reason && startupParse.status === "parse_error" && Number.isFinite(startupParse.line)) {
    details.push(`failed_line=${startupParse.line}`);
  }
  const rejectRows = candidateRejects.map((reject) => {
    const path = typeof reject.path === "string" ? reject.path : "unknown";
    const reason = typeof reject.reason_code === "string" ? reject.reason_code : "reject";
    const detail = typeof reject.reason_detail === "string" ? reject.reason_detail : "";
    const line = Number.isFinite(reject.line) ? ` line ${reject.line}` : "";
    const command = typeof reject.command === "string" ? ` (${reject.command})` : "";
    return `<li><span class="disk-reject-code">${escapeHtml(reason)}</span> ${escapeHtml(path)}${escapeHtml(line)}${escapeHtml(command)}${detail ? `: ${escapeHtml(detail)}` : ""}</li>`;
  });
  const startupLinesMarkup = startupSequenceLines.length
    ? `<div class="disk-startup-lines" aria-label="Startup sequence">
        <div class="disk-startup-seq-content">
        ${startupSequenceLines.map((rawLine, index) => {
          const lineNumber = index + 1;
          const lineRecords = startupLineStatus.get(lineNumber) || [];
          const failedRecord = lineRecords.find((record) => {
            const status = typeof record.status === "string" ? record.status.toLowerCase() : "";
            return status && status !== "pending" && status !== "imported";
          });
          const importedRecord = lineRecords.find((record) => {
            const status = typeof record.status === "string" ? record.status.toLowerCase() : "";
            return status === "imported";
          });
          const failedReasons = [];
          for (const record of lineRecords) {
            const reason = typeof record.reason_detail === "string" && record.reason_detail ? record.reason_detail : "";
            if (reason) {
              failedReasons.push(reason);
            }
          }
          const suffix = importedRecord ? " <span class=\"disk-startup-line-check\">&#x2713;</span>" : "";
          const statusLine = failedReasons.length ? ` ${escapeHtml(Array.from(new Set(failedReasons)).join(" | "))}` : "";
          const cls = failedRecord ? "disk-startup-line disk-startup-line-failed" : "disk-startup-line";
          return `<div class="${cls}">${escapeHtml(typeof rawLine === "string" ? rawLine : "")}${statusLine}${suffix}</div>`;
        }).join("")}
        </div>
      </div>`
    : "";
  const startupSummaryHasDetail = Boolean(startupLinesMarkup);
  const startupStateCollapsed = startupParse && startupParse.status === "ok";
  const caret = startupStateCollapsed ? "&#9654;" : "&#9660;";
  return `
    <div class="disk-state-summary">
      <button type="button" class="disk-state-summary-title" data-project-startup-state-toggle="1" aria-expanded="${startupStateCollapsed ? "false" : "true"}">
        <span class="disk-state-summary-caret" aria-hidden="true">${caret}</span>
        Startup import state
      </button>
      <div class="disk-startup-state-body${startupStateCollapsed ? " disk-startup-state-body-collapsed" : ""}" data-project-startup-state-body="1">
        <div class="disk-state-summary-detail">${escapeHtml(details.join(" | "))}</div>
        ${startupSummaryHasDetail ? startupLinesMarkup : ""}
        ${rejectRows.length ? `
        <ul class="disk-reject-list">
          ${rejectRows.join("")}
        </ul>` : ""}
      </div>
    </div>
  `;
}

function renderDiskTargetItem(target, entry, targetState, indentLevel = 0, extraBadges = null, payloadNode = null) {
  const normalizedIndentLevel = Number.isFinite(indentLevel) ? Math.max(0, Math.floor(indentLevel)) : 0;
  const stateEntry = targetState && typeof targetState.stateById?.get === "function"
    ? targetState.stateById.get(target.target_name)
    : null;
  const metadataPayload = renderDiskTargetMetadata(target, entry, payloadNode);
  const metadata = metadataPayload && typeof metadataPayload === "object" ? metadataPayload.metadata || "" : "";
  const metadataTooltip = metadataPayload && typeof metadataPayload === "object" ? metadataPayload.tooltip || "" : "";
  const stateBadges = [];
  if (stateEntry && typeof stateEntry.origin === "string") {
    stateBadges.push(stateEntry.origin);
  }
  const explicitBadges = Array.isArray(extraBadges) ? extraBadges.filter((badge) => typeof badge === "string" && badge.trim()) : [];
  const allBadges = [...stateBadges, ...explicitBadges];
  const extra = allBadges.length ? `<span class="disk-item-state">${renderInlineBadges(allBadges)}</span>` : "";
  const icon = renderDiskTargetEntryIcon(entry, target);
  const title = target.entry_path === "bootblock" ? "Boot Block" : (target.entry_path || target.target_name);
  const tooltip = metadataTooltip ? ` title="${escapeHtml(metadataTooltip)}"` : "";
  const indentClass = normalizedIndentLevel === 0
    ? ""
    : normalizedIndentLevel === 1
      ? " disk-target-child"
      : normalizedIndentLevel === 2
        ? " disk-target-child disk-target-child-nested"
        : ` disk-target-child disk-target-child-nested disk-target-child-nested-${normalizedIndentLevel}`;
  return `
    <button class="disk-item disk-target-button${indentClass}" data-project-id="${escapeHtml(target.target_name)}" type="button">
      <span class="disk-item-main">${icon ? `<span class="disk-target-entry-icon">${icon}</span>` : ""}${escapeHtml(title)}</span>
      <span class="disk-item-meta"${tooltip}>${metadata}${extra ? ` ${extra}` : ""}</span>
    </button>
  `;
}

function renderDiskStartupSourceNode(sourcePath, childCount) {
  const childText = Number.isFinite(childCount) ? `${escapeHtml(childCount.toString())} auto target${childCount === 1 ? "" : "s"}` : "";
  const sourceIcon = renderDiskSourcePathIcon(sourcePath);
  return `
    <div class="disk-item">
      <span class="disk-item-main"><span class="disk-target-entry-icon">${sourceIcon}</span>${escapeHtml(sourcePath)}</span>
      <span class="disk-item-meta">${renderInlineBadges(["source"])}${childText ? `<span class="disk-item-state">(${childText})</span>` : ""}</span>
    </div>
  `;
}

function renderDiskTargets(manifest, targetState = null) {
  const analysis = requireObject(manifest.analysis, "Disk analysis");
  const bootBlock = requireObject(analysis.boot_block, "Boot block analysis");
  const filesystem = analysis.filesystem || null;
  const bootblockTargetName = manifest.bootblock_target_name || null;
  const importedTargets = requireArray(manifest.imported_targets, "Imported targets");
  const stateById = new Map();
  const payloadState = targetState && typeof targetState === "object"
    ? targetState
    : {};
  if (Array.isArray(payloadState.subtargets)) {
    for (const item of payloadState.subtargets) {
      const targetId = typeof item.id === "string" ? item.id : "";
      if (!targetId) {
        continue;
      }
      stateById.set(targetId, item);
    }
  }
  const statePayload = {stateById};
  if (!importedTargets.length) {
    return `
      <div class="disk-list">
        ${renderBootBlockTarget(bootBlock, filesystem, bootblockTargetName)}
        ${renderDiskTargetStateSummary(targetState)}
      </div>
    `;
  }
  const files = analysis.files === null || analysis.files === undefined
    ? []
    : requireArray(analysis.files, "Indexed disk files");
  const fileByPath = new Map(files.map((entry) => [entry.full_path, entry]));
  const entryPathByTargetId = new Map();
  const payloadParentByTargetId = new Map();
  const payloadNodes = Array.isArray(payloadState.payload_nodes)
    ? payloadState.payload_nodes
    : [];
  const payloadNodeByTargetId = new Map();
  for (const node of payloadNodes) {
    if (!node || typeof node !== "object") {
      continue;
    }
    const payloadId = typeof node.id === "string" ? node.id : "";
    const parentId = typeof node.parent_file_id === "string" ? node.parent_file_id : "";
    if (payloadId && parentId) {
      payloadParentByTargetId.set(payloadId, parentId);
    }
    if (payloadId) {
      payloadNodeByTargetId.set(payloadId, node);
    }
  }
  for (const target of importedTargets) {
    const targetId = typeof target.target_name === "string" ? target.target_name : "";
    const entryPath = typeof target.entry_path === "string" ? target.entry_path : "";
    if (!targetId || !entryPath) {
      continue;
    }
    const normalizedPath = entryPath.toLowerCase();
    entryPathByTargetId.set(normalizedPath, targetId);
  }
  const childTargetIdByEntryPath = new Map();
  for (const [entryPath, targetId] of entryPathByTargetId.entries()) {
    const parentPath = entryPath.split("::")[0];
    if (parentPath) {
      childTargetIdByEntryPath.set(parentPath, targetId);
    }
  }
  const resolveDecompressedParentId = (target) => {
    if (!target || typeof target !== "object") {
      return "";
    }
    const entryPath = typeof target.entry_path === "string" ? target.entry_path : "";
    const targetId = typeof target.target_name === "string" ? target.target_name : "";
    const parentFromPayloadNode = payloadParentByTargetId.get(targetId);
    if (parentFromPayloadNode) {
      return parentFromPayloadNode;
    }
    const relationship = target.derived_from;
    if (relationship && typeof relationship === "object") {
      const parentRef = relationship.kind;
      if (parentRef === "decompressed_payload" || parentRef === "derived_decompressed_payload") {
        const parentTarget = typeof relationship.parent_target === "string" ? relationship.parent_target : "";
        const parentTargetId = parentTarget || (typeof relationship.parent_target_id === "string" ? relationship.parent_target_id : "");
        if (parentTargetId) {
          return parentTargetId;
        }
      }
    }
    if (target.target_type === "raw_binary" && entryPath.includes("::")) {
      const parentEntryPath = entryPath.split("::")[0].trim().toLowerCase();
      return childTargetIdByEntryPath.get(parentEntryPath) || "";
    }
    return "";
  };
  const childrenByParent = new Map();
  const rootTargets = [];
  const targetById = new Map();
  for (const target of importedTargets) {
    const targetId = typeof target.target_name === "string" ? target.target_name : "";
    if (!targetId) {
      continue;
    }
    targetById.set(targetId, target);
    const parentId = resolveDecompressedParentId(target);
    if (parentId) {
      const list = childrenByParent.get(parentId) || [];
      list.push(target);
      childrenByParent.set(parentId, list);
    } else {
      rootTargets.push(target);
    }
  }
  const renderedChildren = (parentId, childIndentLevel = 0) => {
    const children = childrenByParent.get(parentId) || [];
    if (!children.length) {
      return "";
    }
    return children.map((child) => {
      const entry = fileByPath.get(child.entry_path) || null;
      const nextLevel = childIndentLevel + 1;
      const payloadNode = payloadNodeByTargetId.get(child.target_name) || null;
      return `${renderDiskTargetItem(child, entry, statePayload, nextLevel, null, payloadNode)}${
        renderedChildren(child.target_name, nextLevel)
      }`;
    }).join("");
  };
  const startupParse = payloadState.startup_sequence_parse && typeof payloadState.startup_sequence_parse === "object"
    ? payloadState.startup_sequence_parse
    : null;
  const startupSequenceEntries = startupParse && Array.isArray(startupParse.startup_sequence_entries)
    ? startupParse.startup_sequence_entries
    : [];
  const startupDefaultSource = startupParse && typeof startupParse.source_path === "string"
    ? startupParse.source_path
    : "s/startup-sequence";
  const startupSourceGroups = [];
  const startupGroupTargets = new Set();
  if (startupSequenceEntries.length) {
    const grouped = new Map();
    for (const startupEntry of startupSequenceEntries) {
      if (!startupEntry || typeof startupEntry !== "object") {
        continue;
      }
      const status = typeof startupEntry.status === "string" ? startupEntry.status.toLowerCase() : "";
      if (!status || status === "filtered" || status === "reject" || status === "failed" || status === "skip") {
        continue;
      }
      const targetName = typeof startupEntry.target_name === "string" ? startupEntry.target_name : "";
      const target = targetName ? targetById.get(targetName) : null;
      if (!target) {
        continue;
      }
      if (startupGroupTargets.has(targetName)) {
        continue;
      }
      const source = typeof startupEntry.source_path === "string" ? startupEntry.source_path : startupDefaultSource;
      const group = grouped.get(source) || [];
      group.push(targetName);
      grouped.set(source, group);
      startupGroupTargets.add(targetName);
    }
    for (const [sourcePath, targetNames] of grouped.entries()) {
      if (!targetNames.length) {
        continue;
      }
      startupSourceGroups.push({
        sourcePath,
        targetNames,
      });
    }
  }
  const groupedStartupMarkup = startupSourceGroups.map((group) => {
    const children = group.targetNames.map((targetName) => {
      const target = targetById.get(targetName);
      if (!target) {
        return "";
      }
      const entry = fileByPath.get(target.entry_path) || null;
      const payloadNode = payloadNodeByTargetId.get(target.target_name) || null;
      return `${renderDiskTargetItem(target, entry, statePayload, 1, null, payloadNode)}${
        renderedChildren(target.target_name, 1)
      }`;
    }).join("");
    return `
      ${renderDiskStartupSourceNode(group.sourcePath, group.targetNames.length)}
      ${children}
    `;
  }).join("");
  const manualTargets = rootTargets.filter((target) => (
    target.entry_path !== "bootblock"
    && target.target_type !== "bootblock"
    && !startupGroupTargets.has(target.target_name)
  ));
  return `
    <div class="disk-list">
      ${renderDiskTargetStateSummary(targetState)}
      ${renderBootBlockTarget(bootBlock, filesystem, bootblockTargetName)}
      ${groupedStartupMarkup}
      ${manualTargets.map((target) => `
        ${renderDiskTargetItem(
          target,
          fileByPath.get(target.entry_path),
          statePayload,
          0,
          null,
          payloadNodeByTargetId.get(target.target_name) || null
        )}
        ${renderedChildren(target.target_name, 0)}
      `).join("")}
    </div>
  `;
}

function renderDiskFiles(files, targetIndex = new Map(), addedTargetIds = new Set()) {
  if (!files.length) {
    return '<div class="empty">No files indexed.</div>';
  }
  const toPathKey = (value) => String(value || "").toLowerCase();
  const isImportable = (entry) => entry && typeof entry === "object"
    && (entry.importable === true
      || (entry.content && typeof entry.content === "object" && entry.content.import_target !== null && entry.content.import_target !== undefined));
  return `
    <div class="disk-list">
      <button class="disk-file-browse" data-project-disk-path="" type="button">Browse disk files</button>
      <table class="disk-file-table" aria-label="Disk file contents">
        <thead>
          <tr>
            <th class="disk-file-header-name">File</th>
            <th class="disk-file-header-size">Size</th>
            <th class="disk-file-header-type">Type</th>
            <th class="disk-file-header-details">Notes</th>
            <th class="disk-file-header-action">Action</th>
          </tr>
        </thead>
        <tbody>
          ${files.map((entry) => {
            const path = entry.full_path || entry.path || entry.name || "";
            const targetId = targetIndex.get(toPathKey(path));
            const isAdded = targetId ? addedTargetIds.has(targetId) : false;
            const importable = isImportable(entry);
            const action = targetId
              ? (isAdded
                ? `<span role="button" tabindex="0" class="disk-item-action" data-project-disk-open-target="${escapeHtml(targetId)}">Open</span>`
                : (importable ? `<span role="button" tabindex="0" class="disk-item-action" data-project-disk-import="${escapeHtml(path)}">Import</span>` : ""))
              : (importable ? `<span role="button" tabindex="0" class="disk-item-action" data-project-disk-import="${escapeHtml(path)}">Import</span>` : "");
            const size = formatFileSize(entry.size);
            const type = formatFileKind(entry);
            const details = "";
            return `
            <tr class="disk-file-entry-row" data-project-disk-path="${escapeHtml(path)}" tabindex="0" role="row">
              <td class="disk-file-name" title="${escapeHtml(path)}">${escapeHtml(path)}</td>
              <td class="disk-file-size">${escapeHtml(size)}</td>
              <td class="disk-file-type">${escapeHtml(type)}</td>
              <td class="disk-file-details">${escapeHtml(details)}</td>
              <td class="disk-file-action">${action || ""}</td>
            </tr>
          `;
          }).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderDiskProject(projectData) {
  const manifest = requireObject(projectData.disk_manifest, "Disk manifest");
  const analysis = requireObject(manifest.analysis, "Disk analysis");
  const hasIndexedFiles = analysis.files !== null && analysis.files !== undefined;
  const files = hasIndexedFiles ? requireArray(analysis.files, "Indexed disk files") : null;
  const targetState = projectData.target_state && typeof projectData.target_state === "object"
    ? projectData.target_state
    : null;
  const stateById = new Map();
  const addedTargetIds = new Set();
  const targetIndex = new Map();
  const importedTargets = requireArray(manifest.imported_targets, "Imported targets");
  for (const item of importedTargets) {
    const path = typeof item.entry_path === "string" ? item.entry_path : "";
    const targetId = typeof item.target_name === "string" ? item.target_name : "";
    if (!path || !targetId) {
      continue;
    }
    targetIndex.set(path.trim().toLowerCase().replace(/\\/g, "/"), targetId);
  }
  for (const subtarget of requireArray(targetState && targetState.subtargets ? targetState.subtargets : null, "Target subtargets")) {
    const targetId = typeof subtarget.id === "string" ? subtarget.id : "";
    if (targetId) {
      addedTargetIds.add(targetId);
    }
    if (typeof subtarget.state !== "string" || subtarget.state !== "added") {
      continue;
    }
    if (targetId) {
      stateById.set(targetId, subtarget);
    }
  }
  const app = document.getElementById("listing-viewport");

  app.innerHTML = `
    <section class="disk-view">
      <div class="disk-tabs" role="tablist" aria-label="Disk project sections">
        <button class="disk-tab-button active" type="button" data-tab="targets" role="tab" aria-selected="true">Targets</button>
        ${files ? '<button class="disk-tab-button" type="button" data-tab="contents" role="tab" aria-selected="false">Disk Contents</button>' : ""}
      </div>
      <div class="disk-tab-panel active" data-tab-panel="targets" role="tabpanel">
        <div class="disk-section">
          ${renderDiskTargets(manifest, targetState)}
        </div>
      </div>
      ${files ? `
      <div class="disk-tab-panel" data-tab-panel="contents" role="tabpanel" hidden>
        <div class="disk-section">
          ${renderDiskFiles(files, targetIndex, addedTargetIds)}
        </div>
      </div>` : ""}
    </section>
    ${renderDiskBrowserOverlayHtml()}
  `;

  document.querySelectorAll(".disk-target-button").forEach((button) => {
    button.addEventListener("click", () => {
      navigateToProject(button.dataset.projectId);
    });
  });
  document.querySelectorAll("[data-project-startup-state-toggle]").forEach((button) => {
    const summaryNode = button.closest(".disk-state-summary");
    if (!summaryNode) {
      return;
    }
    const body = summaryNode.querySelector("[data-project-startup-state-body]");
    if (!body) {
      return;
    }
    const caret = button.querySelector(".disk-state-summary-caret");
    const setState = (expanded) => {
      const isExpanded = !!expanded;
      body.classList.toggle("disk-startup-state-body-collapsed", !isExpanded);
      button.setAttribute("aria-expanded", isExpanded ? "true" : "false");
      if (caret) {
        caret.innerHTML = isExpanded ? "&#9660;" : "&#9654;";
      }
    };
    button.addEventListener("click", () => {
      const currentlyExpanded = !body.classList.contains("disk-startup-state-body-collapsed");
      setState(!currentlyExpanded);
    });
  });
  document.querySelectorAll("[data-project-disk-path]").forEach((button) => {
    button.addEventListener("click", () => {
      void openProjectDiskBrowser(projectData.project.id, button.dataset.projectDiskPath || "");
    });
  });
  document.querySelectorAll("[data-project-disk-open-target]").forEach((button) => {
    const openTarget = () => {
      const targetId = button.dataset.projectDiskOpenTarget || "";
      void selectCorpusTarget(targetId);
    };
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      openTarget();
    });
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openTarget();
      }
    });
  });
  document.querySelectorAll("[data-project-disk-import]").forEach((button) => {
      const importEntry = () => {
        button.dataset.projectDiskImportBusy = "1";
        const path = button.dataset.projectDiskImport || "";
        void importDiskProjectFile(projectData.project.id, path).finally(() => {
          button.removeAttribute("data-project-disk-import-busy");
        });
      };
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        importEntry();
      });
    button.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        importEntry();
      }
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
  bindDiskBrowserControls();
}

async function importDiskProjectFile(projectId, entryPath) {
  if (!projectId || !entryPath) {
    return;
  }
  const importTarget = String(entryPath);
  try {
    setAnalysisStatus(`Importing ${importTarget}`, "running");
    await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/disk/import-entry`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({path: importTarget}),
    });
    const projectData = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}`);
    state.projectData = projectData;
    await Promise.resolve(renderDiskProject(projectData));
    setAnalysisStatus("Import complete", "ready", 2000);
  } catch (error) {
    setAnalysisStatus(`Import failed: ${String(error.message || error)}`, "failed", 6000);
  }
}

async function jumpToListingAddr(projectId, addr, matchText = null, options = {}) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return false;
  }
  if (!scrollRowIntoView(viewport, addr, "center", matchText)) {
    const visibleRows = listingVisibleRowCount(viewport);
    const count = clampListingWindowCount(visibleRows * 3);
    await loadListingWindow(projectId, addr, visibleRows, count - visibleRows, {renderEmpty: false});
    if (!scrollRowIntoView(viewport, addr, "center", matchText)) {
      await loadListingWindow(projectId, addr, count, count, {renderEmpty: false});
      scrollRowIntoView(viewport, addr, "center", matchText);
    }
  }
  const row = selectBestListingRow(viewport, addr, matchText);
  if (!row) {
    return false;
  }
  if (options.focus !== false) {
    focusListingRow(row);
  }
  return true;
}

async function jumpToListingSectionOffset(projectId, sectionIndex, offset, options = {}) {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement) || !Number.isInteger(sectionIndex) || !Number.isFinite(offset)) {
    return false;
  }
  const suppressionToken = beginListingScrollSuppression();
  try {
    let row = selectListingRowBySectionOffset(viewport, sectionIndex, offset);
    if (!row) {
      const visibleRows = listingVisibleRowCount(viewport);
      const count = clampListingWindowCount(visibleRows * 3);
      await loadListingWindow(projectId, null, visibleRows, count - visibleRows, {
        sectionIndex,
        sourceOffset: offset,
        renderEmpty: false,
      });
      row = selectListingRowBySectionOffset(viewport, sectionIndex, offset);
    }
    if (!row) {
      return false;
    }
    const rowIndex = Number(row.dataset.rowIndex);
    if (Number.isFinite(rowIndex)) {
      const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
      viewport.scrollTop = Math.max(0, (rowIndex * rowHeight) - Math.floor(viewport.clientHeight / 2));
    } else {
      row.scrollIntoView({block: "center", behavior: "auto"});
    }
    if (options.focus !== false) {
      focusListingRow(row);
    }
    return true;
  } finally {
    releaseListingScrollSuppression(projectId, viewport, suppressionToken);
  }
}

async function jumpToListingRuntimeAddress(projectId, address) {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement) || !Number.isFinite(address)) {
    return false;
  }
  const suppressionToken = beginListingScrollSuppression();
  try {
    let row = selectListingRowByRuntimeAddress(viewport, address);
    if (!row) {
      const visibleRows = listingVisibleRowCount(viewport);
      const count = clampListingWindowCount(visibleRows * 3);
      await loadListingWindow(projectId, null, visibleRows, count - visibleRows, {
        runtimeAddress: address,
        renderEmpty: false,
      });
      row = selectListingRowByRuntimeAddress(viewport, address);
    }
    if (!row) {
      return false;
    }
    const rowIndex = Number(row.dataset.rowIndex);
    if (Number.isFinite(rowIndex)) {
      const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
      viewport.scrollTop = Math.max(0, (rowIndex * rowHeight) - Math.floor(viewport.clientHeight / 2));
    } else {
      row.scrollIntoView({block: "center", behavior: "auto"});
    }
    focusListingRow(row);
    return true;
  } finally {
    releaseListingScrollSuppression(projectId, viewport, suppressionToken);
  }
}

async function jumpToListingIndex(projectId, rowIndex, addr, matchText = null, stableKey = null) {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement) || !Number.isFinite(rowIndex)) {
    return jumpToListingAddr(projectId, addr, matchText);
  }
  const visibleRows = listingVisibleRowCount(viewport);
  const count = listingFetchCount(viewport);
  const targetIndex = Math.floor(rowIndex);
  const start = Math.max(0, targetIndex - visibleRows);
  const rowHeight = Math.max(1, state.virtualListing.rowHeight || 22);
  const suppressionToken = beginListingScrollSuppression();
  try {
    viewport.scrollTop = Math.max(0, (targetIndex * rowHeight) - Math.floor(viewport.clientHeight / 2));
    await loadListingWindow(projectId, null, 0, count, {start, count, preserveScroll: true, renderEmpty: false});
    scrollRowIntoView(viewport, addr, "center", matchText, stableKey, targetIndex);
    const row = selectBestListingRow(viewport, addr, matchText, stableKey, targetIndex);
    if (!row) {
      return false;
    }
    focusListingRow(row);
    return true;
  } finally {
    releaseListingScrollSuppression(projectId, viewport, suppressionToken);
  }
}

async function jumpToNavigationEntry(projectId, entry) {
  if (!navigationEntryHasJumpTarget(entry)) {
    return false;
  }
  const matchText = entry.matchText || entry.match_text || null;
  const stableKey = entry.stableKey || entry.stable_key || null;
  const rowIndex = navigationEntryRowIndex(entry);
  if (rowIndex !== null) {
    return jumpToListingIndex(projectId, rowIndex, entry.addr, matchText, stableKey);
  }
  return jumpToListingAddr(projectId, entry.addr, matchText);
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

function selectedListingRowElement() {
  const viewport = document.getElementById("listing-viewport");
  if (!(viewport instanceof HTMLElement)) {
    return null;
  }
  const selection = state.listingSelection;
  if (selection?.stableKey) {
    const stable = viewport.querySelector(`[data-row-stable-key="${CSS.escape(selection.stableKey)}"]`);
    if (stable instanceof HTMLElement) {
      return stable;
    }
  }
  if (Number.isFinite(selection?.rowIndex)) {
    const indexed = viewport.querySelector(`[data-row-index="${String(selection.rowIndex)}"]`);
    if (indexed instanceof HTMLElement) {
      return indexed;
    }
  }
  return viewport.querySelector(".listing-row-selected");
}

async function followSelectedReference(openDetails = false) {
  if (!state.project) {
    return false;
  }
  const row = selectedListingRowElement();
  if (!(row instanceof HTMLElement)) {
    return false;
  }
  const origin = captureViewportAnchor();
  const symbol = row.querySelector(".listing-symbol-reference[data-symbol-name]");
  let followed = false;
  if (symbol instanceof HTMLElement) {
    followed = await handleListingSymbolButtonAction(state.project, symbol, {
      ctrlKey: openDetails,
      metaKey: false,
      preventDefault() {},
      stopPropagation() {},
    });
  } else {
    const equate = row.querySelector(".listing-equate-reference[data-equate-symbol]");
    if (equate instanceof HTMLElement) {
      const equateSymbol = equate.dataset.equateSymbol || "";
      if (openDetails) {
        await selectEquateNavigationRef(state.project, equateSymbol, equate.dataset.rowIndex ?? null, "reference");
      } else {
        await jumpToListingEquate(state.project, equateSymbol);
      }
      followed = true;
    }
  }
  const current = captureViewportAnchor();
  if (followed && origin && current && !navigationEntriesSameLocation(origin, current)) {
    state.navigation.historyBack.push(origin);
    state.navigation.historyForward = [];
    state.navigation.currentLocation = current;
  }
  return followed;
}

async function moveToRelativeLabel(delta) {
  if (!state.project || !delta) {
    return false;
  }
  const groups = await ensureNavigationEntries(state.project);
  const labels = labelEntriesFromGroups(groups)
    .map((entry) => ({...entry, rowIndex: navigationEntryRowIndex(entry)}))
    .filter((entry) => Number.isFinite(entry.rowIndex))
    .sort((left, right) => left.rowIndex - right.rowIndex);
  if (!labels.length) {
    return false;
  }
  const current = Number(state.listingSelection?.rowIndex);
  const currentIndex = Number.isFinite(current) ? current : state.virtualListing.start;
  const target = delta > 0
    ? labels.find((entry) => entry.rowIndex > currentIndex)
    : labels.toReversed().find((entry) => entry.rowIndex < currentIndex);
  if (!target) {
    return false;
  }
  return jumpToListingIndex(
    state.project,
    target.rowIndex,
    target.addr,
    target.matchText || target.match_text || target.summary,
    target.stableKey || target.stable_key || null,
  );
}

function currentListingSectionIndex() {
  const selectionHunk = Number(state.listingSelection?.sectionIndex);
  if (Number.isInteger(selectionHunk)) {
    return selectionHunk;
  }
  const row = selectedListingRowElement();
  const rowHunk = Number(row?.dataset?.sectionIndex);
  return Number.isInteger(rowHunk) ? rowHunk : null;
}

async function moveToRelativeHunk(delta) {
  if (!state.project || !delta) {
    return false;
  }
  const current = currentListingSectionIndex();
  if (!Number.isInteger(current)) {
    return false;
  }
  const target = current + delta;
  if (target < 0) {
    return false;
  }
  const content = state.projectData?.project?.content || state.projectData?.content || {};
  const hunkCount = Number(content.hunk_count);
  if (Number.isInteger(hunkCount) && target >= hunkCount) {
    return false;
  }
  return jumpToListingSectionOffset(state.project, target, 0);
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
          <button id="open-review" type="button" title="Manual Review">Review</button>
          <button id="open-stats" type="button" title="Stats">Stats</button>
          <button id="open-repro" type="button" title="Repro">Repro</button>
          <button id="exit-project" type="button">Project</button>
        </div>
      </div>
      <div class="project-workspace">
        <div class="listing-viewport" id="listing-viewport" tabindex="0">
          ${renderProgressOverlay({
            job_kind: "listing_artifact",
            phase_id: "build_c_artifact",
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
  resetDiskBrowser();
  state.listingRows = [];
  state.listingSelection = null;
  state.virtualListing.start = 0;
  state.virtualListing.end = 0;
  state.virtualListing.totalRows = 0;
  state.virtualListing.generation = null;
  state.virtualListing.requestSeq = 0;
  state.virtualListing.pendingWindow = null;
  state.virtualListing.inFlightWindow = null;
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
  state.navigation.appSlotAnalysis = null;
  state.navigation.generation = null;
  state.navigation.appSlotSymbol = null;
  state.navigation.labelSymbol = null;
  state.navigation.equateSymbol = null;
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
  state.manualReview.panelOpen = false;
  state.manualReview.filters = {
    kind: "",
    confidence: "",
    state: "open",
    section: "",
    source: "",
    range: "",
  };
  state.commandPalette.open = false;
  state.commandPalette.query = "";
  state.commandPalette.actions = [];
  state.commandPalette.selectedIndex = 0;
  state.commandPalette.loading = false;
  state.commandPalette.global = false;
  state.commandPalette.editor = null;
  if (state.uiPreferences.saveTimer !== null) {
    window.clearTimeout(state.uiPreferences.saveTimer);
  }
  state.uiPreferences.payload = null;
  state.uiPreferences.saveTimer = null;
  state.uiPreferences.restoring = false;
  state.uiPreferences.initialApplied = false;
  setAnalysisStatus("");
  renderStatsOverlay();
  renderReproPanel();
  renderManualReviewPanel();
  renderCommandPalette();
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
    document.getElementById("open-review")?.addEventListener("click", openManualReviewPanel);
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
    await refreshProjectPayload(projectId, token);
    if (token !== state.loadingToken) {
      return;
    }
    if (state.virtualListing.generation && state.virtualListing.generation !== "full") {
      await refreshListingAtCurrentAddressAnchor(projectId, token);
    } else if (state.virtualListing.generation !== "full") {
      setViewportOverlay(loadingRowsOverlay());
      const uiPreferences = await loadUiPreferenceState(projectId);
      await loadInitialListingLocation(projectId, uiPreferences);
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
    if (!state.listingSelection) {
      const uiPreferences = state.uiPreferences.payload || await loadUiPreferenceState(projectId);
      await applyInitialListingLocation(projectId, uiPreferences);
    }
    await focusPendingCorpusExample(projectId);
    if (state.virtualListing.generation === "full") {
      void pollReproductionReport(projectId, token);
      setAnalysisStatus("Analysis ready", "ready", 2000);
    }
    dispatchAppEvent("amiga:project-rendered", {
      projectId,
      generation: state.virtualListing.generation,
      totalRows: state.virtualListing.totalRows,
    });
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

async function focusPendingCorpusExample(projectId) {
  const focus = state.pendingCorpusFocus;
  if (!focus || focus.projectId !== projectId) {
    return;
  }
  state.pendingCorpusFocus = null;
  if (Number.isFinite(focus.rowIndex)) {
    await jumpToListingIndex(projectId, focus.rowIndex, focus.addr, focus.matchText, focus.stableKey);
  } else if (Number.isFinite(focus.addr)) {
    await jumpToListingAddr(projectId, focus.addr, focus.matchText);
  }
}

function navigateToProject(projectId) {
  window.history.pushState({}, "", projectPath(projectId));
  void route();
}

async function route() {
  const projectId = currentProjectId();
  try {
    await verifyWebAppContract();
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
        ["runtime", rect.left + state.listingColumns.offset + state.listingColumns.runtime],
        ["bytes", rect.left + state.listingColumns.offset + state.listingColumns.runtime + state.listingColumns.bytes],
        ["code", rect.left + state.listingColumns.offset + state.listingColumns.runtime + state.listingColumns.bytes + state.listingColumns.code],
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
  if (event.key === "Escape") {
    if (state.parameterSession) {
      event.preventDefault();
      cancelInlineParameterSession();
      return;
    }
    if (state.commandPalette.open || document.getElementById("command-palette-overlay")) {
      event.preventDefault();
      if (state.commandPalette.editor) {
        cancelCommandParameterEditor();
        return;
      }
      closeCommandPalette();
      return;
    }
    if (document.getElementById("corpus-variant-diff-overlay")) {
      event.preventDefault();
      void closeCorpusVariantDiffOverlay();
      return;
    }
    if (document.getElementById("corpus-disk-browser-overlay")) {
      event.preventDefault();
      void closeDiskBrowserOverlay();
      return;
    }
    if (document.getElementById("corpus-snippet-overlay")) {
      event.preventDefault();
      void closeCorpusSnippetOverlay();
      return;
    }
    if (state.stats.overlayOpen || document.getElementById("stats-overlay")) {
      event.preventDefault();
      closeStatsOverlay();
      return;
    }
    if (state.navigation.overlayOpen || document.getElementById("navigation-overlay")) {
      event.preventDefault();
      closeNavigationOverlay();
      return;
    }
    if (state.reproduction.panelOpen) {
      event.preventDefault();
      closeReproPanel();
      return;
    }
  }
  if (!state.project) {
    return;
  }
  const symbolLink = event.target instanceof HTMLElement
    ? event.target.closest("[data-symbol-name]")
    : null;
  if (symbolLink && event.key === "Enter") {
    handleListingSymbolButtonAction(state.project, symbolLink, event);
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
  if (isEditableTarget(event.target)) {
    return;
  }
  if (!modalOrPanelHasKeyboardFocus() && !event.altKey && !event.ctrlKey && !event.metaKey) {
    if (event.key === ".") {
      event.preventDefault();
      void invokeEditSelectedCommand();
      return;
    }
    if (event.key === "F2") {
      event.preventDefault();
      void invokeSelectedCatalogBinding("F2");
      return;
    }
    if (event.key === ";") {
      event.preventDefault();
      void invokeSelectedCatalogBinding(";");
      return;
    }
    if (!event.shiftKey && (event.key === "r" || event.key === "R")) {
      event.preventDefault();
      void invokeSelectedCatalogBinding("r").then((handled) => {
        if (!handled) openManualReviewPanel();
      });
      return;
    }
    if (!event.shiftKey && (event.key === "s" || event.key === "S")) {
      event.preventDefault();
      void invokeSelectedCatalogBinding("s").then((handled) => {
        if (!handled) openStatsOverlay();
      });
      return;
    }
  }
  if (!modalOrPanelHasKeyboardFocus() && !event.altKey && !event.metaKey && event.ctrlKey && event.key === "ArrowUp") {
    event.preventDefault();
    void moveToRelativeLabel(-1);
    return;
  }
  if (!modalOrPanelHasKeyboardFocus() && !event.altKey && !event.metaKey && event.ctrlKey && event.key === "ArrowDown") {
    event.preventDefault();
    void moveToRelativeLabel(1);
    return;
  }
  if (!modalOrPanelHasKeyboardFocus() && !event.altKey && !event.metaKey && event.ctrlKey && event.key === "ArrowRight") {
    event.preventDefault();
    void followSelectedReference(true);
    return;
  }
  if (
    !modalOrPanelHasKeyboardFocus()
    && !event.altKey
    && !event.ctrlKey
    && !event.metaKey
    && !event.shiftKey
    && event.key === "ArrowRight"
  ) {
    event.preventDefault();
    void followSelectedReference(false);
    return;
  }
  if (
    !modalOrPanelHasKeyboardFocus()
    && !event.altKey
    && !event.ctrlKey
    && !event.metaKey
    && !event.shiftKey
    && event.key === "ArrowLeft"
  ) {
    event.preventDefault();
    void navigateHistory("back");
    return;
  }
  if (
    !modalOrPanelHasKeyboardFocus()
    && !event.altKey
    && !event.ctrlKey
    && !event.metaKey
    && (event.key === "ArrowDown" || event.key === "ArrowUp")
  ) {
    event.preventDefault();
    void moveListingSelection(event.key === "ArrowDown" ? 1 : -1, event.shiftKey);
    return;
  }
  const listingScrollDirection = listingScrollDirectionForKey(event);
  if (listingScrollDirection && !modalOrPanelHasKeyboardFocus()) {
    event.preventDefault();
    scrollListingViewport(state.project, listingScrollDirection);
    return;
  }
  if (!modalOrPanelHasKeyboardFocus()) {
    if (!event.altKey && !event.ctrlKey && !event.metaKey && (event.key === "p" || event.key === "P")) {
      event.preventDefault();
      void openCommandPalette();
      return;
    }
    if (!event.altKey && !event.ctrlKey && !event.metaKey && (event.key === "n" || event.key === "N")) {
      event.preventDefault();
      void openNavigationOverlay();
      return;
    }
    return;
  }
  if (!state.navigation.overlayOpen) {
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
