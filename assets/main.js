const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("visible");
      entry.target
        .querySelectorAll("[data-chart]")
        .forEach((chart) => chart.classList.add("active"));
    });
  },
  { threshold: 0.12 },
);

document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));

const copyBib = document.getElementById("copyBib");
if (copyBib) {
  copyBib.addEventListener("click", async (event) => {
    const text = document.querySelector(".citation-box code")?.textContent ?? "";
    await navigator.clipboard.writeText(text);
    event.currentTarget.textContent = "Copied!";
    setTimeout(() => {
      event.currentTarget.textContent = "Copy";
    }, 1600);
  });
}

const DATASET_BASE = "data/vistahop/";
const PAGE_SIZE = 12;

const datasetUI = {
  featured: document.getElementById("featuredExamples"),
  grid: document.getElementById("datasetGrid"),
  count: document.getElementById("datasetCount"),
  search: document.getElementById("datasetSearch"),
  difficulty: document.getElementById("datasetDifficulty"),
  category: document.getElementById("datasetCategory"),
  reasoning: document.getElementById("datasetReasoning"),
  reset: document.getElementById("datasetReset"),
  loadMore: document.getElementById("datasetLoadMore"),
  dialog: document.getElementById("datasetDialog"),
  dialogClose: document.getElementById("datasetDialogClose"),
  dialogImage: document.getElementById("datasetDialogImage"),
  dialogBadges: document.getElementById("datasetDialogBadges"),
  dialogId: document.getElementById("datasetDialogId"),
  dialogQuery: document.getElementById("datasetDialogQuery"),
  dialogReference: document.getElementById("datasetDialogReference"),
};

let datasetRecords = [];
let filteredRecords = [];
let visibleRecords = PAGE_SIZE;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function titleCase(value) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function reasoningLabel(record) {
  return record.chain_count === 1
    ? "Single-chain"
    : `${record.chain_count}-chain fusion`;
}

function createBadge(label, modifier = "") {
  return element("span", `case-badge ${modifier}`.trim(), label);
}

function appendBadges(container, record) {
  container.append(
    createBadge(record.difficulty, record.difficulty.toLowerCase()),
    createBadge(titleCase(record.category)),
    createBadge(reasoningLabel(record)),
  );
}

function openCase(record) {
  if (!datasetUI.dialog) return;

  datasetUI.dialogImage.src = `${DATASET_BASE}${record.image}`;
  datasetUI.dialogImage.alt = `VistaHop case ${record.uid}: ${record.scenario}`;
  datasetUI.dialogBadges.replaceChildren();
  appendBadges(datasetUI.dialogBadges, record);
  datasetUI.dialogId.textContent = `${record.uid} · ${record.task_id}`;
  datasetUI.dialogQuery.textContent = record.task_query;
  datasetUI.dialogReference.textContent = record.reference;

  if (typeof datasetUI.dialog.showModal === "function") {
    datasetUI.dialog.showModal();
  } else {
    datasetUI.dialog.setAttribute("open", "");
  }
}

function createCaseCard(record, featured = false) {
  const article = element(
    "article",
    featured ? "dataset-card featured-case" : "dataset-card",
  );

  const imageButton = element("button", "case-image");
  imageButton.type = "button";
  imageButton.setAttribute("aria-label", `Open ${record.uid}`);
  imageButton.addEventListener("click", () => openCase(record));

  const image = document.createElement("img");
  image.src = `${DATASET_BASE}${record.image}`;
  image.alt = `VistaHop case ${record.uid}: ${record.scenario}`;
  image.loading = featured ? "eager" : "lazy";
  image.decoding = "async";
  imageButton.append(image);

  const content = element("div", "case-content");
  const badges = element("div", "case-badges");
  appendBadges(badges, record);

  const identifier = element(
    "p",
    "case-id",
    `${record.uid} · ${titleCase(record.scenario)}`,
  );
  const queryLabel = element("p", "case-label", "Task query");
  const query = element("p", "case-query", record.task_query);

  const reference = document.createElement("details");
  reference.className = "case-reference";
  const referenceSummary = document.createElement("summary");
  referenceSummary.textContent = "Reveal reference";
  reference.append(referenceSummary, element("p", "", record.reference));

  const actions = element("div", "case-actions");
  const inspect = element("button", "inspect-case", "Inspect full case");
  inspect.type = "button";
  inspect.addEventListener("click", () => openCase(record));
  actions.append(inspect);

  content.append(
    badges,
    identifier,
    queryLabel,
    query,
    reference,
    actions,
  );
  article.append(imageButton, content);
  return article;
}

function renderFeatured() {
  const featured = datasetRecords.filter((record) => record.featured);
  datasetUI.featured.replaceChildren(
    ...featured.map((record) => createCaseCard(record, true)),
  );
}

function searchText(record) {
  return [
    record.uid,
    record.task_id,
    record.task_query,
    record.reference,
    record.category,
    record.scenario,
  ]
    .join(" ")
    .toLowerCase();
}

function applyFilters() {
  const search = datasetUI.search.value.trim().toLowerCase();
  const difficulty = datasetUI.difficulty.value;
  const category = datasetUI.category.value;
  const reasoning = datasetUI.reasoning.value;

  filteredRecords = datasetRecords.filter((record) => {
    if (search && !searchText(record).includes(search)) return false;
    if (difficulty && record.difficulty !== difficulty) return false;
    if (category && record.category !== category) return false;
    if (reasoning === "single" && record.chain_count !== 1) return false;
    if (reasoning === "multi" && record.chain_count === 1) return false;
    return true;
  });

  visibleRecords = PAGE_SIZE;
  renderGrid();
}

function renderGrid() {
  const records = filteredRecords.slice(0, visibleRecords);
  datasetUI.grid.replaceChildren(
    ...records.map((record) => createCaseCard(record)),
  );

  datasetUI.count.textContent = `${filteredRecords.length} of ${datasetRecords.length} records`;
  datasetUI.loadMore.hidden =
    filteredRecords.length === 0 || records.length >= filteredRecords.length;

  if (filteredRecords.length === 0) {
    datasetUI.grid.append(
      element(
        "p",
        "dataset-empty",
        "No records match these filters. Try clearing one or more fields.",
      ),
    );
  }
}

function populateCategories() {
  const categories = [...new Set(datasetRecords.map((record) => record.category))]
    .sort((a, b) => a.localeCompare(b))
    .map((category) => {
      const option = document.createElement("option");
      option.value = category;
      option.textContent = titleCase(category);
      return option;
    });
  datasetUI.category.append(...categories);
}

function bindDatasetEvents() {
  datasetUI.search.addEventListener("input", applyFilters);
  datasetUI.difficulty.addEventListener("change", applyFilters);
  datasetUI.category.addEventListener("change", applyFilters);
  datasetUI.reasoning.addEventListener("change", applyFilters);

  datasetUI.reset.addEventListener("click", () => {
    datasetUI.search.value = "";
    datasetUI.difficulty.value = "";
    datasetUI.category.value = "";
    datasetUI.reasoning.value = "";
    applyFilters();
    datasetUI.search.focus();
  });

  datasetUI.loadMore.addEventListener("click", () => {
    visibleRecords += PAGE_SIZE;
    renderGrid();
  });

  datasetUI.dialogClose?.addEventListener("click", () =>
    datasetUI.dialog.close(),
  );
  datasetUI.dialog?.addEventListener("click", (event) => {
    if (event.target === datasetUI.dialog) datasetUI.dialog.close();
  });
}

async function initializeDataset() {
  if (!datasetUI.grid || !datasetUI.featured) return;

  try {
    const response = await fetch(`${DATASET_BASE}tasks.json`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    datasetRecords = await response.json();
    filteredRecords = datasetRecords;
    populateCategories();
    renderFeatured();
    renderGrid();
    bindDatasetEvents();
  } catch (error) {
    const message =
      window.location.protocol === "file:"
        ? "Run this page through a local web server to load the dataset explorer."
        : "The dataset explorer could not be loaded. The JSONL download remains available.";
    datasetUI.featured.replaceChildren(
      element("p", "dataset-error", `${message} (${error.message})`),
    );
    datasetUI.grid.replaceChildren(
      element("p", "dataset-error", `${message} (${error.message})`),
    );
    datasetUI.count.textContent = "Dataset unavailable";
    datasetUI.loadMore.hidden = true;
  }
}

initializeDataset();

function initializeVisitorStatistics() {
  const counters = [
    document.getElementById("busuanzi_site_uv"),
    document.getElementById("busuanzi_site_pv"),
    document.getElementById("busuanzi_page_pv"),
  ].filter(Boolean);
  const note = document.querySelector(".visitor-statistics-note");
  if (counters.length === 0) return;

  const isLocalPreview =
    window.location.protocol === "file:" ||
    ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);

  if (isLocalPreview) {
    counters.forEach((counter) => {
      counter.textContent = "—";
    });
    if (note) {
      note.textContent =
        "Counters are enabled automatically on the published project domain.";
    }
    return;
  }

  const script = document.createElement("script");
  script.src = "https://cdn.busuanzi.cc/busuanzi/3.6.9/busuanzi.min.js";
  script.defer = true;
  script.addEventListener("error", () => {
    counters.forEach((counter) => {
      counter.textContent = "—";
    });
    if (note) {
      note.textContent = "Visitor counters are temporarily unavailable.";
    }
  });
  document.body.append(script);
}

initializeVisitorStatistics();
