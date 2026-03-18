const state = {
  project: null,
  session: null,
  listing: null,
  selectedAddr: null,
  before: 80,
  after: 160,
};

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!payload.ok) {
    throw new Error(payload.error || `Request failed: ${response.status}`);
  }
  return payload.data;
}

function formatSession(session) {
  const lines = [
    `target: ${session.target_name}`,
    `binary: ${session.binary_path}`,
    `entities: ${session.entity_count}`,
    `hunks: ${session.hunk_count}`,
  ];
  for (const hunk of session.hunks) {
    lines.push(
      `hunk ${hunk.hunk_index}: ${hunk.code_size} bytes, ` +
      `${hunk.label_count} labels, ${hunk.core_block_count} core blocks`
    );
  }
  return lines.join("\n");
}

function renderListing(listing) {
  const view = document.getElementById("listing-view");
  view.innerHTML = "";
  for (const row of listing.rows) {
    const line = document.createElement("button");
    line.type = "button";
    line.className = "listing-row";
    if (row.addr != null && state.selectedAddr != null && row.addr === state.selectedAddr) {
      line.classList.add("selected");
    }
    line.textContent = row.text.replace(/\n$/, "");
    if (row.addr != null) {
      line.dataset.addr = `0x${row.addr.toString(16)}`;
      line.addEventListener("click", async () => {
        await selectAddress(line.dataset.addr);
      });
    } else {
      line.disabled = true;
    }
    view.appendChild(line);
  }
}

function renderXrefList(elementId, addrs) {
  const container = document.getElementById(elementId);
  container.innerHTML = "";
  const values = Array.isArray(addrs) ? addrs : [];
  if (values.length === 0) {
    container.textContent = "None";
    return;
  }
  for (const addr of values) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "xref-button";
    button.textContent = addr;
    button.addEventListener("click", async () => {
      document.getElementById("addr-input").value = addr;
      await loadListing(addr);
      await selectAddress(addr);
    });
    container.appendChild(button);
  }
}

function setEntityForm(entity) {
  document.getElementById("entity-addr").value = entity?.addr || "";
  document.getElementById("entity-name").value = entity?.name || "";
  document.getElementById("entity-subtype").value = entity?.subtype || "";
  document.getElementById("entity-comment").value = entity?.comment || "";
  document.getElementById("subtype-group").classList.toggle(
    "hidden",
    !entity || entity.type !== "data"
  );
  const meta = [];
  if (entity?.type) {
    meta.push(`type: ${entity.type}`);
  }
  if (entity?.subtype) {
    meta.push(`subtype: ${entity.subtype}`);
  }
  if (entity?.confidence) {
    meta.push(`confidence: ${entity.confidence}`);
  }
  document.getElementById("entity-meta").textContent = meta.join(" | ");
  renderXrefList("entity-calls", entity?.calls);
  renderXrefList("entity-called-by", entity?.called_by);
}

async function patchSelectedEntity(patch) {
  const addr = document.getElementById("entity-addr").value.trim();
  if (!addr) {
    return;
  }
  await fetchJson(`/api/projects/${state.project}/entities/${addr}`, {
    method: "PATCH",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(patch),
  });
  await selectAddress(addr);
  await loadListing(addr);
}

async function loadProjects() {
  const projects = await fetchJson("/api/projects");
  const select = document.getElementById("project-select");
  select.innerHTML = "";
  for (const project of projects) {
    const option = document.createElement("option");
    option.value = project.name;
    option.textContent = project.name;
    select.appendChild(option);
  }
  if (projects.length > 0) {
    state.project = projects[0].name;
    select.value = state.project;
    await loadProject(state.project);
  } else {
    document.getElementById("session-summary").textContent = "No projects found.";
    document.getElementById("listing-view").textContent = "";
  }
}

async function loadProject(projectName, addr = null) {
  state.project = projectName;
  state.selectedAddr = null;
  state.session = await fetchJson(`/api/projects/${projectName}/session`);
  document.getElementById("session-summary").textContent = formatSession(state.session);
  setEntityForm(null);
  await loadListing(addr);
}

async function loadListing(addr = null) {
  if (!state.project) {
    return;
  }
  const query = new URLSearchParams();
  query.set("before", String(state.before));
  query.set("after", String(state.after));
  if (addr) {
    query.set("addr", addr);
  }
  state.listing = await fetchJson(`/api/projects/${state.project}/listing?${query.toString()}`);
  renderListing(state.listing);
}

async function selectAddress(addr) {
  state.selectedAddr = parseInt(addr, 16);
  const entity = await fetchJson(`/api/projects/${state.project}/entities/${addr}`);
  setEntityForm(entity);
  renderListing(state.listing);
}

async function saveEntity(event) {
  event.preventDefault();
  const addr = document.getElementById("entity-addr").value.trim();
  if (!addr) {
    return;
  }
  const name = document.getElementById("entity-name").value;
  const subtype = document.getElementById("entity-subtype").value;
  const comment = document.getElementById("entity-comment").value;
  await patchSelectedEntity({name, subtype, comment});
}

function bindEvents() {
  document.getElementById("project-select").addEventListener("change", async (event) => {
    await loadProject(event.target.value);
  });

  document.getElementById("jump-button").addEventListener("click", async () => {
    const addr = document.getElementById("addr-input").value.trim();
    await loadListing(addr || null);
    if (addr) {
      await selectAddress(addr);
    }
  });

  document.getElementById("load-prev").addEventListener("click", async () => {
    if (!state.listing || state.listing.rows.length === 0) {
      return;
    }
    const first = state.listing.rows[0];
    const addr = first.addr != null ? `0x${first.addr.toString(16)}` : null;
    await loadListing(addr);
  });

  document.getElementById("load-next").addEventListener("click", async () => {
    if (!state.listing || state.listing.rows.length === 0) {
      return;
    }
    const last = state.listing.rows[state.listing.rows.length - 1];
    const nextAddr = last.addr != null ? `0x${(last.addr + 2).toString(16)}` : null;
    await loadListing(nextAddr);
  });

  document.getElementById("entity-form").addEventListener("submit", saveEntity);
  document.getElementById("mark-code").addEventListener("click", async () => {
    await patchSelectedEntity({type: "code"});
  });
  document.getElementById("mark-data").addEventListener("click", async () => {
    await patchSelectedEntity({type: "data"});
  });
  document.getElementById("mark-string").addEventListener("click", async () => {
    await patchSelectedEntity({type: "data", subtype: "string"});
  });
}

async function main() {
  bindEvents();
  try {
    await loadProjects();
  } catch (error) {
    document.getElementById("session-summary").textContent = String(error);
  }
}

main();
