/* State */
const state = {
  responses: [], // loaded from responses.json
  problemsByName: new Map(), // name -> problem row
  problemsByIndex: new Map(), // 1-based index -> problem row
  difficulties: new Set(),
  types: new Set(),
  filters: { difficulty: '', type: '', search: '', category: '', showSubmitted: true },
  categories: [], // [{id, name}]
  annotations: {}, // responseId -> { description, categoryId, submittedAt? }
  pagination: { page: 1, size: 25 },
};

/* Elements */
const el = {
  responsesFile: document.getElementById('responsesFile'),
  csvFile: document.getElementById('csvFile'),
  demoLoad: document.getElementById('demoLoad'),
  difficultyFilter: document.getElementById('difficultyFilter'),
  typeFilter: document.getElementById('typeFilter'),
  categoryFilter: document.getElementById('categoryFilter'),
  searchInput: document.getElementById('searchInput'),
  responses: document.getElementById('responses'),
  stats: document.getElementById('stats'),
  prevPage: document.getElementById('prevPage'),
  nextPage: document.getElementById('nextPage'),
  pageInfo: document.getElementById('pageInfo'),
  pageSize: document.getElementById('pageSize'),
  exportData: document.getElementById('exportData'),
  importData: document.getElementById('importData'),
  toggleSubmittedBtn: document.getElementById('toggleSubmittedBtn'),
  categoryList: document.getElementById('categoryList'),
  addCategory: document.getElementById('addCategory'),
  newCategoryName: document.getElementById('newCategoryName'),
};

/* Utilities */
function saveLocal() {
  const payload = {
    categories: state.categories,
    annotations: state.annotations,
  };
  localStorage.setItem('llm-analyzer-store', JSON.stringify(payload));
  // Also attempt server save
  debounceServerSave(payload);
}

function loadLocal() {
  try {
    const raw = localStorage.getItem('llm-analyzer-store');
    if (!raw) return;
    const parsed = JSON.parse(raw);
    state.categories = Array.isArray(parsed.categories) ? parsed.categories : [];
    state.annotations = parsed.annotations || {};
  } catch (e) {
    console.warn('Failed to load local store', e);
  }
}

async function loadServerAnnotations() {
  try {
    const res = await fetch('/api/annotations', { cache: 'no-store' });
    if (!res.ok) return false;
    const data = await res.json();
    if (data && typeof data === 'object') {
      if (Array.isArray(data.categories)) state.categories = data.categories;
      if (data.annotations && typeof data.annotations === 'object') state.annotations = data.annotations;
      return true;
    }
  } catch (_) { /* ignore */ }
  return false;
}

let serverSaveTimer = null;
function debounceServerSave(payload) {
  if (serverSaveTimer) clearTimeout(serverSaveTimer);
  serverSaveTimer = setTimeout(async () => {
    try {
      await fetch('/api/annotations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (_) { /* ignore network errors */ }
  }, 400);
}

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function humanCount(n) {
  return n.toLocaleString();
}

function parseTagList(value) {
  if (Array.isArray(value)) return value;
  if (value == null) return [];
  const s = String(value).trim();
  if (!s) return [];
  // Try JSON first
  try {
    const maybe = JSON.parse(s);
    if (Array.isArray(maybe)) return maybe;
  } catch (_) { /* ignore */ }
  // Convert Python-like list with single quotes to JSON
  if (s.startsWith('[') && s.endsWith(']')) {
    try {
      const jsonish = s
        .replace(/'/g, '"')
        .replace(/None/g, 'null');
      const arr = JSON.parse(jsonish);
      if (Array.isArray(arr)) return arr;
    } catch (_) { /* ignore */ }
  }
  // Fallback: split by comma
  return s.split(',').map(x => x.trim()).filter(Boolean);
}

/* Data loading */
async function loadCsv(file) {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (res) => resolve(res.data),
      error: reject,
    });
  });
}

async function loadCsvUrl(url) {
  return new Promise((resolve, reject) => {
    Papa.parse(url, {
      header: true,
      skipEmptyLines: true,
      download: true,
      complete: (res) => resolve(res.data),
      error: reject,
    });
  });
}

async function readTextFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsText(file);
  });
}

async function loadJsonUrl(url) {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to load ${url}: ${res.status}`);
  return await res.json();
}

function indexProblems(rows) {
  state.problemsByName.clear();
  state.problemsByIndex.clear();
  rows.forEach((row, idx) => {
    const name = (row.name || '').trim();
    const oneBased = idx + 1; // treat as problem_id
    state.problemsByIndex.set(String(oneBased), row);
    if (name) {
      state.problemsByName.set(name, row);
    }
    if (row.difficulty) state.difficulties.add(row.difficulty);
  });
}

function hydrateFilters() {
  // Difficulty
  const diffs = Array.from(state.difficulties).sort();
  el.difficultyFilter.innerHTML = '<option value="">All</option>' + diffs.map(d => `<option>${d}</option>`).join('');
  // Type
  const types = Array.from(state.types).sort();
  el.typeFilter.innerHTML = '<option value="">All</option>' + types.map(t => `<option>${t}</option>`).join('');
  // Categories
  rebuildCategoryFilter();
}

function rebuildCategoryFilter() {
  const current = el.categoryFilter.value;
  const options = ['<option value="">All</option>', '<option value="__uncategorized__">Uncategorized</option>']
    .concat(state.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`));
  el.categoryFilter.innerHTML = options.join('');
  if (current) el.categoryFilter.value = current;
}

function resolveDifficultyForResponse(resp) {
  // Prefer join by numeric/string index problem_id, else by problem name
  const idxKey = resp.problem_id || resp.problemId || '';
  if (idxKey && state.problemsByIndex.has(String(idxKey))) {
    const row = state.problemsByIndex.get(String(idxKey));
    return row.difficulty || '';
  }
  const problemName = resp.problem_name || resp.problem || '';
  if (problemName && state.problemsByName.has(problemName)) {
    const row = state.problemsByName.get(problemName);
    return row.difficulty || '';
  }
  return '';
}

function normalizeResponses(list) {
  // response: { id, problem_id, problem_name?, type, model, trace }
  state.types.clear();
  return list.map((r) => {
    const id = r.id || r.response_id || r.responseId || uid();
    const type = r.type || '';
    if (type) state.types.add(type);
    const difficulty = r.difficulty || resolveDifficultyForResponse(r) || '';
    // Attach problem details if available via index or name
    let problemRow = null;
    const idxKey = r.problem_id || r.problemId || '';
    if (idxKey && state.problemsByIndex.has(String(idxKey))) {
      problemRow = state.problemsByIndex.get(String(idxKey));
    } else {
      const problemName = r.problem_name || r.problem || '';
      if (problemName && state.problemsByName.has(problemName)) {
        problemRow = state.problemsByName.get(problemName);
      }
    }
    return {
      id,
      problemId: r.problem_id || r.problemId || '',
      problemName: r.problem_name || r.problem || '',
      type,
      model: r.model || '',
      trace: typeof r.trace === 'string' ? r.trace : JSON.stringify(r.trace, null, 2),
      difficulty,
      problem: problemRow ? {
        question: problemRow.question || '',
        tags: parseTagList(problemRow.tags || problemRow.raw_tags || ''),
        url: problemRow.url || '',
        time_limit: problemRow.time_limit || '',
        memory_limit: problemRow.memory_limit || '',
      } : null,
    };
  });
}

/* Rendering */
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function render() {
  const { page, size } = state.pagination;
  const filtered = state.responses.filter(applyFilters);
  const total = filtered.length;
  const start = (page - 1) * size;
  const end = Math.min(start + size, total);
  const pageItems = filtered.slice(start, end);

  el.stats.textContent = `${humanCount(total)} responses • showing ${start + 1}-${end}`;
  el.pageInfo.textContent = `Page ${page} / ${Math.max(1, Math.ceil(total / size))}`;

  el.responses.innerHTML = '';
  const tpl = document.getElementById('responseItemTemplate');
  pageItems.forEach((item) => {
    const node = tpl.content.cloneNode(true);
    node.querySelector('[data-field="responseId"]').textContent = item.id;
    node.querySelector('[data-field="problemId"]').textContent = item.problemId || item.problemName || '';
    node.querySelector('[data-field="difficulty"]').textContent = item.difficulty || '';
    node.querySelector('[data-field="type"]').textContent = item.type || '';
    node.querySelector('[data-field="model"]').textContent = item.model || '';
    node.querySelector('[data-field="trace"]').textContent = item.trace || '';

    // problem details
    const questionEl = node.querySelector('[data-field="problemQuestion"]');
    const tagsEl = node.querySelector('[data-field="problemTags"]');
    const urlEl = node.querySelector('[data-field="problemUrl"]');
    const tlEl = node.querySelector('[data-field="problemTimeLimit"]');
    const mlEl = node.querySelector('[data-field="problemMemoryLimit"]');
    if (item.problem) {
      // render markdown safely
      const rawMd = item.problem.question || '';
      try {
        const html = DOMPurify.sanitize(marked.parse(rawMd));
        questionEl.innerHTML = `<div class="markdown">${html}</div>`;
      } catch (_) {
        questionEl.textContent = rawMd;
      }
      tagsEl.textContent = Array.isArray(item.problem.tags) ? item.problem.tags.join(', ') : String(item.problem.tags || '');
      urlEl.textContent = item.problem.url || '';
      urlEl.href = item.problem.url || '#';
      tlEl.textContent = item.problem.time_limit || '';
      mlEl.textContent = item.problem.memory_limit || '';
    } else {
      questionEl.textContent = '';
      tagsEl.textContent = '';
      urlEl.textContent = '';
      urlEl.removeAttribute('href');
      tlEl.textContent = '';
      mlEl.textContent = '';
    }

    // annotations
    const ann = state.annotations[item.id] || { description: '', categoryId: '' };
    const descEl = node.querySelector('[data-field="description"]');
    descEl.value = ann.description || '';
    descEl.addEventListener('input', () => {
      state.annotations[item.id] = { ...(state.annotations[item.id] || {}), description: descEl.value };
      saveLocal();
    });

    const catSelect = node.querySelector('[data-field="category"]');
    const catOptions = ['<option value="">(none)</option>'].concat(state.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`));
    catSelect.innerHTML = catOptions.join('');
    catSelect.value = ann.categoryId || '';
    catSelect.addEventListener('change', () => {
      state.annotations[item.id] = { ...(state.annotations[item.id] || {}), categoryId: catSelect.value };
      saveLocal();
      // keep category filter selection stable
      renderCategoryList();
    });

    // submitted flag and submit action
    const submitBtn = node.querySelector('[data-action="submit"]');
    const submittedFlag = node.querySelector('[data-field="submittedFlag"]');
    const submittedAt = ann.submittedAt ? new Date(ann.submittedAt) : null;
    if (submittedAt) {
      submittedFlag.textContent = `Submitted ${submittedAt.toLocaleString()}`;
      submitBtn.textContent = 'Unsubmit';
    } else {
      submittedFlag.textContent = '';
      submitBtn.textContent = 'Submit analysis';
    }
    submitBtn.addEventListener('click', () => {
      const current = state.annotations[item.id] || {};
      const now = new Date().toISOString();
      if (current.submittedAt) {
        // unsubmit
        delete current.submittedAt;
      } else {
        current.submittedAt = now;
      }
      state.annotations[item.id] = { ...current };
      saveLocal();
      render();
    });

    el.responses.appendChild(node);
  });
}

function applyFilters(r) {
  const { difficulty, type, search, category } = state.filters;
  if (difficulty && (r.difficulty || '') !== difficulty) return false;
  if (type && (r.type || '') !== type) return false;
  if (category) {
    const ann = state.annotations[r.id] || {};
    if (category === '__uncategorized__') {
      if (ann.categoryId) return false;
    } else {
      if ((ann.categoryId || '') !== category) return false;
    }
  }
  if (!state.filters.showSubmitted) {
    const ann = state.annotations[r.id] || {};
    if (ann.submittedAt) return false;
  }
  if (search) {
    const ann = state.annotations[r.id] || {};
    const hay = `${r.id}\n${r.problemId}\n${r.problemName}\n${r.model}\n${r.type}\n${ann.description || ''}`.toLowerCase();
    if (!hay.includes(search.toLowerCase())) return false;
  }
  return true;
}

/* Categories */
function renderCategoryList() {
  el.categoryList.innerHTML = '';
  state.categories.forEach((cat) => {
    const li = document.createElement('li');
    const title = document.createElement('span');
    title.textContent = cat.name;
    const actions = document.createElement('span');
    const renameBtn = document.createElement('button');
    renameBtn.textContent = 'Rename';
    renameBtn.className = 'secondary';
    renameBtn.addEventListener('click', () => {
      const next = prompt('Rename category', cat.name);
      if (next && next.trim()) {
        cat.name = next.trim();
        saveLocal();
        rebuildCategoryFilter();
        renderCategoryList();
        render();
      }
    });
    const delBtn = document.createElement('button');
    delBtn.textContent = 'Delete';
    delBtn.className = 'danger';
    delBtn.addEventListener('click', () => {
      if (!confirm('Delete this category?')) return;
      // remove from list and clear annotations referencing it
      state.categories = state.categories.filter(c => c.id !== cat.id);
      Object.keys(state.annotations).forEach((rid) => {
        if ((state.annotations[rid] || {}).categoryId === cat.id) {
          state.annotations[rid] = { ...(state.annotations[rid] || {}), categoryId: '' };
        }
      });
      saveLocal();
      rebuildCategoryFilter();
      renderCategoryList();
      render();
    });
    actions.appendChild(renameBtn);
    actions.appendChild(delBtn);
    li.appendChild(title);
    li.appendChild(actions);
    el.categoryList.appendChild(li);
  });
}

/* Events */
el.responsesFile.addEventListener('change', async (e) => {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  try {
    const text = await readTextFile(file);
    const json = JSON.parse(text);
    state.responses = normalizeResponses(json);
    hydrateFilters();
    state.pagination.page = 1;
    render();
  } catch (err) {
    alert('Failed to read responses.json: ' + err.message);
  }
});

el.csvFile.addEventListener('change', async (e) => {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  try {
    const rows = await loadCsv(file);
    indexProblems(rows);
    // enrich difficulties of existing responses
    state.responses = normalizeResponses(state.responses);
    hydrateFilters();
    render();
  } catch (err) {
    alert('Failed to read output.csv: ' + err.message);
  }
});

el.demoLoad.addEventListener('click', () => {
  // minimal demo dataset
  const demoResponses = [
    { id: 'r1', problem_id: 'p1', problem_name: 'nth-fibonacci-number1335', type: 'solution', model: 'gpt-4', trace: 'Reasoning trace here...' },
    { id: 'r2', problem_id: 'p2', problem_name: 'file-extension-check', type: 'explanation', model: 'gpt-4o', trace: 'Another trace...' },
  ];
  const demoProblems = [
    { name: 'nth-fibonacci-number1335', difficulty: 'EASY' },
    { name: 'file-extension-check', difficulty: 'EASY' },
  ];
  indexProblems(demoProblems);
  state.responses = normalizeResponses(demoResponses);
  hydrateFilters();
  state.pagination.page = 1;
  render();
});

el.difficultyFilter.addEventListener('change', () => {
  state.filters.difficulty = el.difficultyFilter.value;
  state.pagination.page = 1;
  render();
});
el.typeFilter.addEventListener('change', () => {
  state.filters.type = el.typeFilter.value;
  state.pagination.page = 1;
  render();
});
el.categoryFilter.addEventListener('change', () => {
  state.filters.category = el.categoryFilter.value;
  state.pagination.page = 1;
  render();
});
el.searchInput.addEventListener('input', () => {
  state.filters.search = el.searchInput.value;
  state.pagination.page = 1;
  render();
});

el.prevPage.addEventListener('click', () => {
  if (state.pagination.page > 1) {
    state.pagination.page -= 1;
    render();
  }
});
el.nextPage.addEventListener('click', () => {
  const filtered = state.responses.filter(applyFilters);
  const max = Math.max(1, Math.ceil(filtered.length / state.pagination.size));
  if (state.pagination.page < max) {
    state.pagination.page += 1;
    render();
  }
});
el.pageSize.addEventListener('change', () => {
  state.pagination.size = parseInt(el.pageSize.value, 10) || 25;
  state.pagination.page = 1;
  render();
});

function refreshSubmittedBtnLabel() {
  el.toggleSubmittedBtn.textContent = state.filters.showSubmitted ? 'Hide submitted' : 'Show submitted';
}

el.toggleSubmittedBtn.addEventListener('click', () => {
  state.filters.showSubmitted = !state.filters.showSubmitted;
  state.pagination.page = 1;
  refreshSubmittedBtnLabel();
  render();
});

el.exportData.addEventListener('click', () => {
  const payload = {
    categories: state.categories,
    annotations: state.annotations,
    exportedAt: new Date().toISOString(),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'llm-annotations.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});

el.importData.addEventListener('change', async (e) => {
  const file = e.target.files && e.target.files[0];
  if (!file) return;
  try {
    const text = await readTextFile(file);
    const data = JSON.parse(text);
    if (Array.isArray(data.categories)) state.categories = data.categories;
    if (data.annotations && typeof data.annotations === 'object') state.annotations = data.annotations;
    saveLocal();
    rebuildCategoryFilter();
    renderCategoryList();
    render();
  } catch (err) {
    alert('Failed to import data: ' + err.message);
  }
});

el.addCategory.addEventListener('click', () => {
  const name = (el.newCategoryName.value || '').trim();
  if (!name) return;
  const item = { id: uid(), name };
  state.categories.push(item);
  el.newCategoryName.value = '';
  saveLocal();
  rebuildCategoryFilter();
  renderCategoryList();
  render();
});

/* Init */
loadLocal();
rebuildCategoryFilter();
renderCategoryList();
render();

// Attempt to auto-load local files if available
(async function attemptAutoLoad() {
  let csvLoaded = false;
  let jsonLoaded = false;
  try {
    // Prefer output_with_ids.csv if it exists; else fallback to output.csv
    let rows;
    try {
      rows = await loadCsvUrl('output_with_ids.csv');
    } catch (_) {
      rows = await loadCsvUrl('output.csv');
    }
    indexProblems(rows);
    csvLoaded = true;
  } catch (_) { /* ignore */ }

  try {
    const json = await loadJsonUrl('responses.json');
    state.responses = normalizeResponses(json);
    jsonLoaded = true;
  } catch (_) { /* ignore */ }

  if (csvLoaded || jsonLoaded) {
    // try load server-side annotations to override local
    await loadServerAnnotations();
    hydrateFilters();
    state.pagination.page = 1;
    // initialize toggle button label
    refreshSubmittedBtnLabel();
    render();
  }
})();


