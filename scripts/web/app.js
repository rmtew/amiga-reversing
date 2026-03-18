const state = {
  project: null,
  projectData: null,
  loadingToken: 0,
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

function formatProjectDetails(projectData) {
  const details = [];
  if (projectData.project.binary_path) {
    details.push(projectData.project.binary_path);
  }
  if (!projectData.project.output_path) {
    details.push("No disassembly output");
  }
  if (!projectData.project.ready) {
    details.push("No binary loaded");
  }
  return details.join(" | ");
}

function setStatus(text) {
  const node = document.getElementById("status-text");
  if (node) {
    node.textContent = text;
  }
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function renderHome() {
  const projects = await fetchJson("/api/projects");
  const app = document.getElementById("app");
  app.innerHTML = `
    <section class="page page-home">
      <div class="projects-header">
        <h1>Projects</h1>
      </div>
      <form id="new-project-form" class="new-project-form">
        <input id="new-project-id" placeholder="new-project-id" autocomplete="off">
        <button type="submit">Add Project</button>
      </form>
      <div id="home-error" class="error"></div>
      <div class="project-list">
        ${projects.map((project) => `
          <button class="project-item" data-project-id="${escapeHtml(project.id)}" type="button">
            <span class="project-name">${escapeHtml(project.name)}</span>
            <span class="project-meta">${escapeHtml(project.last_opened || "Not opened yet")}</span>
          </button>
        `).join("") || '<div class="empty">No projects.</div>'}
      </div>
    </section>
  `;

  document.querySelectorAll(".project-item").forEach((button) => {
    button.addEventListener("click", () => {
      navigateToProject(button.dataset.projectId);
    });
  });

  document.getElementById("new-project-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("new-project-id");
    const error = document.getElementById("home-error");
    error.textContent = "";
    try {
      const project = await fetchJson("/api/projects", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id: input.value.trim()}),
      });
      navigateToProject(project.id);
    } catch (err) {
      error.textContent = String(err.message || err);
    }
  });
}

function renderListingRows(rows) {
  if (!rows.length) {
    return '<div class="empty listing-empty">No disassembly available.</div>';
  }
  return rows.map((row) => `
    <div class="listing-row">${escapeHtml(row.text.replace(/\n$/, ""))}</div>
  `).join("");
}

async function renderProject(projectId) {
  const app = document.getElementById("app");
  app.innerHTML = `
    <section class="page page-project">
      <div class="project-bar">
        <div class="project-title">${escapeHtml(projectId)}</div>
        <div class="project-details" id="project-details">Loading project...</div>
        <button id="exit-project" type="button">Exit</button>
      </div>
      <div class="status-bar" id="status-text">Loading project...</div>
      <div class="listing-viewport" id="listing-viewport">
        <div class="empty listing-empty">Loading disassembly...</div>
      </div>
    </section>
  `;

  document.getElementById("exit-project").addEventListener("click", () => {
    window.history.pushState({}, "", "/");
    void route();
  });

  const token = ++state.loadingToken;
  state.project = projectId;
  fetchJson(`/api/projects/${encodeURIComponent(projectId)}/open`, {method: "POST"})
    .catch(() => null);
  try {
    setStatus("Loading project...");
    const projectData = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}`);
    if (token !== state.loadingToken) {
      return;
    }
    state.projectData = projectData;
    document.getElementById("project-details").textContent = formatProjectDetails(projectData);

    if (!projectData.project.ready) {
      document.getElementById("listing-viewport").innerHTML =
        '<div class="empty listing-empty">No disassembly available.</div>';
      setStatus("Project has no loaded binary.");
      return;
    }

    setStatus("Queueing canonical listing...");
    const job = await fetchJson(`/api/projects/${encodeURIComponent(projectId)}/listing/open`, {
      method: "POST",
    });
    if (token !== state.loadingToken) {
      return;
    }

    let jobState = job;
    while (jobState.status === "queued" || jobState.status === "building") {
      setStatus(`Loading disassembly... ${jobState.phase}`);
      await sleep(250);
      if (token !== state.loadingToken) {
        return;
      }
      jobState = await fetchJson(
        `/api/projects/${encodeURIComponent(projectId)}/listing/status?job_id=${encodeURIComponent(job.job_id)}`
      );
      if (token !== state.loadingToken) {
        return;
      }
    }

    if (jobState.status === "failed") {
      throw new Error(jobState.error || "Canonical listing build failed");
    }

    setStatus("Loading disassembly window...");
    const listing = await fetchJson(
      `/api/projects/${encodeURIComponent(projectId)}/listing?before=80&after=200`
    );
    if (token !== state.loadingToken) {
      return;
    }
    document.getElementById("listing-viewport").innerHTML = renderListingRows(listing.rows);
    setStatus(`Loaded ${listing.rows.length} rows.`);
  } catch (error) {
    if (token !== state.loadingToken) {
      return;
    }
    document.getElementById("project-details").textContent = "Load failed";
    document.getElementById("listing-viewport").innerHTML =
      `<div class="error">${escapeHtml(String(error.message || error))}</div>`;
    setStatus("Load failed.");
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

void route();
