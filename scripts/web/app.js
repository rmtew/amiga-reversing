const state = {
  project: null,
  projectData: null,
  loadingToken: 0,
  homeDropCleanup: null,
  typeCatalog: null,
  listingRows: [],
  navigation: {
    overlayOpen: false,
    selectedClass: "typed-data",
    selectedIndex: 0,
    windowStart: 0,
    originEntry: null,
    currentPreviewEntry: null,
    historyBack: [],
    historyForward: [],
  },
};

const NAVIGATION_WINDOW_SIZE = 14;
const NAVIGATION_WINDOW_MARGIN = 3;

const JOB_PHASE_LABELS = {
  listing: {
    queued: "Queued",
    build_session: "Building session",
    emit_rows: "Rendering listing",
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
};

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload.data;
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
      `<span class="project-badge"${badge.title ? ` title="${escapeHtml(badge.title)}"` : ""}>${escapeHtml(badge.label)}</span>`
    ))
    .join("");
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
  let jobState = job;
  renderOverlay(jobState);
  while (jobState.status === "queued" || jobState.status === "building") {
    await sleep(250);
    if (token !== null && token !== state.loadingToken) {
      throw new Error("stale");
    }
    jobState = await fetchJson(statusUrl(job.job_id));
    if (token !== null && token !== state.loadingToken) {
      throw new Error("stale");
    }
    renderOverlay(jobState);
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

function formatRowBytes(hexBytes) {
  if (!hexBytes) {
    return "";
  }
  const parts = [];
  for (let index = 0; index < hexBytes.length; index += 2) {
    parts.push(hexBytes.slice(index, index + 2));
  }
  return parts.join(" ");
}

function renderListingCode(row) {
  if (row.kind === "instruction") {
    const opcode = row.opcode_or_directive || "";
    const operands = row.operand_text || "";
    return `    ${opcode}${operands ? ` ${operands}` : ""}`;
  }
  return row.text.replace(/\n$/, "");
}

function renderListingComment(row) {
  if (row.kind === "instruction" && row.comment_text) {
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

function renderListingRows(rows) {
  if (!rows.length) {
    return '<div class="empty listing-empty">No disassembly available.</div>';
  }
  return rows.map((row, rowIndex) => `
    <div
      class="listing-row listing-row-${escapeHtml(row.kind)}"
      data-row-addr="${row.addr === null || row.addr === undefined ? "" : escapeHtml(String(row.addr))}"
      data-row-kind="${escapeHtml(row.kind)}"
      data-row-code="${escapeHtml(renderListingCode(row))}"
    >
      <span class="listing-offset">${escapeHtml(formatRowOffset(row.addr))}</span>
      <span class="listing-bytes">${escapeHtml(formatRowBytes(row.bytes))}</span>
      <span class="listing-code">${escapeHtml(renderListingCode(row))}</span>
      <span class="listing-comment">${escapeHtml(renderListingComment(row))}${renderListingComment(row) && renderListingAnnotations(row) ? " " : ""}${renderListingAnnotations(row)}${renderApiTypeBadges(row)}${(renderListingAnnotations(row) || renderApiTypeBadges(row)) ? " " : ""}${renderApiEditButton(row, rowIndex)}</span>
    </div>
  `).join("");
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
  return row.kind !== "instruction" && Boolean(row.comment_text);
}

function rowHasComment(row) {
  return Boolean(row.comment_text) || (Array.isArray(row.view_annotations) && row.view_annotations.length > 0);
}

function summarizeNavigationRow(row, jumpClass) {
  if (jumpClass === "api-calls" && row.api_call) {
    return `${row.api_call.function} (${row.api_call.library})`;
  }
  if (jumpClass === "typed-data" && row.comment_text) {
    return row.comment_text;
  }
  if (jumpClass === "labels") {
    return renderListingCode(row).trim();
  }
  return renderListingCode(row).trim() || row.comment_text || row.kind;
}

function buildNavigationEntries(rows) {
  const groups = {
    "typed-data": [],
    "relocations": [],
    "api-calls": [],
    "labels": [],
    "comments": [],
  };
  rows.forEach((row, rowIndex) => {
    if (row.addr === null || row.addr === undefined) {
      return;
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
    if (row.api_call) {
      groups["api-calls"].push({
        addr: row.addr,
        rowIndex,
        summary: summarizeNavigationRow(row, "api-calls"),
        matchText: renderListingCode(row),
      });
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
  return groups;
}

function currentNavigationEntries() {
  const groups = buildNavigationEntries(state.listingRows || []);
  return groups[state.navigation.selectedClass] || [];
}

function clampNavigationWindow(entries, requestedStart) {
  const maxStart = Math.max(entries.length - NAVIGATION_WINDOW_SIZE, 0);
  return Math.max(0, Math.min(maxStart, requestedStart));
}

function syncNavigationWindow() {
  const entries = currentNavigationEntries();
  if (!entries.length) {
    state.navigation.windowStart = 0;
    state.navigation.selectedIndex = 0;
    return;
  }
  const maxIndex = entries.length - 1;
  state.navigation.selectedIndex = Math.max(0, Math.min(maxIndex, state.navigation.selectedIndex));
  let windowStart = clampNavigationWindow(entries, state.navigation.windowStart);
  const windowEnd = windowStart + NAVIGATION_WINDOW_SIZE - 1;
  if (state.navigation.selectedIndex < windowStart + NAVIGATION_WINDOW_MARGIN) {
    windowStart = clampNavigationWindow(
      entries,
      state.navigation.selectedIndex - NAVIGATION_WINDOW_MARGIN,
    );
  } else if (state.navigation.selectedIndex > windowEnd - NAVIGATION_WINDOW_MARGIN) {
    windowStart = clampNavigationWindow(
      entries,
      state.navigation.selectedIndex - NAVIGATION_WINDOW_SIZE + NAVIGATION_WINDOW_MARGIN + 1,
    );
  }
  state.navigation.windowStart = windowStart;
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
    matchText: candidate.dataset.rowCode || null,
  };
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
  syncNavigationWindow();
  const selectedClass = state.navigation.selectedClass;
  const windowStart = state.navigation.windowStart;
  const windowEntries = entries.slice(windowStart, windowStart + NAVIGATION_WINDOW_SIZE);
  const classOptions = [
    ["typed-data", "Typed Data"],
    ["relocations", "Relocations"],
    ["api-calls", "API Calls"],
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
        <div class="navigation-summary">${entries.length} entries</div>
        <div class="navigation-list" tabindex="0" data-navigation-list="1">
          ${entries.length
            ? windowEntries.map((entry, windowIndex) => {
              const index = windowStart + windowIndex;
              return `
              <button
                type="button"
                class="navigation-item${index === state.navigation.selectedIndex ? " active" : ""}"
                data-navigation-index="${index}"
              >
                <span class="navigation-item-addr">${escapeHtml(formatRowOffset(entry.addr))}</span>
                <span class="navigation-item-text">${escapeHtml(entry.summary)}</span>
              </button>
            `;
            }).join("")
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
}

async function previewNavigationEntry(entry) {
  if (!entry || !state.project) {
    return;
  }
  state.navigation.currentPreviewEntry = entry;
  await jumpToListingAddr(state.project, entry.addr, entry.matchText || null);
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
  state.navigation.windowStart = 0;
  renderNavigationOverlay();
  syncNavigationListFocus();
  const [first] = currentNavigationEntries();
  await previewNavigationEntry(first || null);
}

function commitNavigationPreview() {
  const origin = state.navigation.originEntry;
  const current = state.navigation.currentPreviewEntry;
  if (!origin || !current || origin.addr === current.addr) {
    return;
  }
  state.navigation.historyBack.push(origin);
  state.navigation.historyForward = [];
}

function closeNavigationOverlay() {
  commitNavigationPreview();
  state.navigation.overlayOpen = false;
  state.navigation.originEntry = null;
  state.navigation.currentPreviewEntry = null;
  renderNavigationOverlay();
}

async function openNavigationOverlay() {
  state.navigation.overlayOpen = true;
  state.navigation.originEntry = captureViewportAnchor();
  state.navigation.windowStart = 0;
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
  const current = captureViewportAnchor();
  if (current) {
    targetStack.push(current);
  }
  await jumpToListingAddr(state.project, target.addr, target.matchText || null);
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
  overlay.querySelectorAll("[data-navigation-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.navigation.selectedIndex = Number(button.dataset.navigationIndex);
      renderNavigationOverlay();
      syncNavigationListFocus();
      void previewNavigationEntry(currentNavigationEntries()[state.navigation.selectedIndex]);
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
  await loadListingWindow(projectId, null, 0, Number(jobState.total_rows || 0));
  if (addr !== null && addr !== undefined) {
    await jumpToListingAddr(projectId, addr);
  }
}

async function openApiEditDialog(projectId, row) {
  const catalog = await ensureTypeCatalog(projectId);
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  const existing = document.querySelector(".api-edit-dialog");
  if (existing) {
    existing.remove();
  }
  viewport.insertAdjacentHTML("beforeend", `
    <datalist id="api-struct-catalog">
      ${catalog.map((entry) => `<option value="${escapeHtml(entry.name)}">${escapeHtml(entry.name)} (${escapeHtml(entry.source)}, ${escapeHtml(String(entry.size))} bytes)</option>`).join("")}
    </datalist>
    ${renderApiEditDialog(projectId, row)}
  `);
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

function bindListingApiEditors(projectId, rows) {
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return;
  }
  viewport.querySelectorAll("[data-api-edit='1']").forEach((button, index) => {
    button.addEventListener("click", () => {
      const rowIndex = Number(button.dataset.rowIndex);
      void openApiEditDialog(projectId, rows[rowIndex]);
    });
  });
}

async function loadListingWindow(projectId, addr = null, before = 24, after = 80) {
  const params = new URLSearchParams();
  if (addr !== null && addr !== undefined) {
    params.set("addr", String(addr));
  }
  params.set("before", String(before));
  params.set("after", String(after));
  const listing = await fetchJson(
    `/api/projects/${encodeURIComponent(projectId)}/listing?${params.toString()}`
  );
  const viewport = document.getElementById("listing-viewport");
  if (!viewport) {
    return listing;
  }
  state.listingRows = listing.rows;
  viewport.innerHTML = renderListingRows(listing.rows);
  bindListingApiEditors(projectId, listing.rows);
  renderNavigationOverlay();
  return listing;
}

function normalizeJumpText(text) {
  return String(text || "")
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, "");
}

function selectBestListingRow(viewport, addr, matchText = null) {
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

function scrollRowIntoView(viewport, addr, block = "center", matchText = null) {
  const row = selectBestListingRow(viewport, addr, matchText);
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
  const files = requireArray(analysis.files, "Indexed disk files");
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
    await loadListingWindow(projectId, addr, 200, 200);
  }
  const row = selectBestListingRow(viewport, addr, matchText);
  if (!row) {
    return;
  }
  row.classList.add("listing-row-focus");
  window.setTimeout(() => row.classList.remove("listing-row-focus"), 1200);
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
        <div class="project-actions">
          <button id="navigation-back" type="button" title="Back">Back</button>
          <button id="navigation-forward" type="button" title="Forward">Forward</button>
          <button id="open-navigation" type="button" title="Navigate">Navigate</button>
          <button id="exit-project" type="button">Project</button>
        </div>
      </div>
      <div class="project-workspace">
        <div class="listing-viewport" id="listing-viewport">
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
  state.navigation.overlayOpen = false;
  renderNavigationOverlay();
  fetchJson(`/api/projects/${encodeURIComponent(projectId)}/open`, {method: "POST"})
    .catch(() => null);
  try {
    const projectData = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}`);
    if (token !== state.loadingToken) {
      return;
    }
    state.projectData = projectData;
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
    setViewportOverlay(loadingRowsOverlay());
    await loadListingWindow(projectId, null, 0, Number(jobState.total_rows || 0));
    if (token !== state.loadingToken) {
      return;
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

document.addEventListener("keydown", (event) => {
  if (!state.project) {
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
  if (!state.navigation.overlayOpen) {
    if (!event.altKey && !event.ctrlKey && !event.metaKey && (event.key === "n" || event.key === "N")) {
      event.preventDefault();
      void openNavigationOverlay();
    }
    return;
  }
  if (event.key === "Escape" || event.key === "Enter") {
    event.preventDefault();
    closeNavigationOverlay();
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
});

void route();
