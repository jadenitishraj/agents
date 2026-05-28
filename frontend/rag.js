/**
 * RAG Search Frontend — upload a file, search with pure retrieval.
 */

const API = "";
let corpusId = "";

// ─── Upload ────────────────────────────────────────────────

const zone = document.getElementById("upload-zone");
const fileInput = document.getElementById("file-input");

zone.addEventListener("click", () => fileInput.click());
zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("dragover"); });
zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
zone.addEventListener("drop", (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
    clearError();
    zone.querySelector(".label").innerHTML = `<strong>Uploading & indexing...</strong> ${escapeHtml(file.name)}`;

    const form = new FormData();
    form.append("file", file);

    try {
        const res = await fetch(`${API}/rag/upload`, { method: "POST", body: form });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Upload failed: ${res.status}`);
        }
        const data = await res.json();
        corpusId = data.corpus_id;

        // Show status
        document.getElementById("status-filename").textContent = data.filename;
        const pills = [...data.categories.map(c => `<span class="pill">${escapeHtml(c)}</span>`),
                        ...data.strategies.map(s => `<span class="pill">${escapeHtml(s)}</span>`)].join("");
        document.getElementById("status-meta").innerHTML =
            `${data.chunks} chunks indexed · corpus ${data.corpus_id} ${pills}`;
        document.getElementById("status-bar").classList.add("visible");

        // Enable search
        document.getElementById("search-input").disabled = false;
        document.getElementById("search-btn").disabled = false;
        document.getElementById("search-input").focus();

        zone.querySelector(".label").innerHTML =
            `<strong>✓ Indexed!</strong> Drop another file to replace, or start searching below.`;
    } catch (err) {
        showError(err.message);
        zone.querySelector(".label").innerHTML =
            `Drop a <strong>PDF</strong>, <strong>TXT</strong>, or <strong>MD</strong> file here — or click to browse`;
    }
}

// ─── Search ────────────────────────────────────────────────

const searchBtn = document.getElementById("search-btn");
const searchInput = document.getElementById("search-input");

searchBtn.addEventListener("click", runSearch);
searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSearch();
});

async function runSearch() {
    const query = searchInput.value.trim();
    if (!query || !corpusId) return;

    clearError();
    setSearchLoading(true);
    document.getElementById("results-container").innerHTML = "";
    document.getElementById("results-header").classList.remove("visible");

    try {
        const res = await fetch(`${API}/rag/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query, corpus_id: corpusId, top_k: 5 }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Search failed: ${res.status}`);
        }
        const data = await res.json();
        renderResults(data);
    } catch (err) {
        showError(err.message);
    } finally {
        setSearchLoading(false);
    }
}

// ─── Render ────────────────────────────────────────────────

function renderResults(data) {
    const header = document.getElementById("results-header");
    const container = document.getElementById("results-container");
    const elapsed = document.getElementById("elapsed");

    header.classList.add("visible");
    elapsed.textContent = `${data.results.length} results · ${data.elapsed_seconds}s`;

    container.innerHTML = data.results.map((r, i) => {
        const pills = [
            r.category ? `<span class="pill">${escapeHtml(r.category)}</span>` : "",
            r.chunk_strategy ? `<span class="pill">${escapeHtml(r.chunk_strategy)}</span>` : "",
        ].filter(Boolean).join("");

        return `
        <div class="result-card" style="animation-delay:${i * 0.08}s">
            <div class="result-top">
                <span class="result-title">📄 ${escapeHtml(r.title)}</span>
                <span class="score-badge">${r.score.toFixed(2)}</span>
            </div>
            <div class="result-text" id="text-${i}">${escapeHtml(r.text)}</div>
            <button class="expand-btn" onclick="toggleExpand(${i})">Show more ▾</button>
            <div class="result-pills">${pills}</div>
        </div>`;
    }).join("");
}

function toggleExpand(i) {
    const el = document.getElementById(`text-${i}`);
    const btn = el.nextElementSibling;
    el.classList.toggle("expanded");
    btn.textContent = el.classList.contains("expanded") ? "Show less ▴" : "Show more ▾";
}

// ─── Helpers ───────────────────────────────────────────────

function setSearchLoading(on) {
    searchBtn.disabled = on;
    searchBtn.querySelector(".btn-text").textContent = on ? "Searching..." : "Search";
    document.getElementById("search-spinner").style.display = on ? "inline-block" : "none";
}

function showError(msg) {
    const el = document.getElementById("error-card");
    el.textContent = msg;
    el.classList.add("visible");
}

function clearError() {
    const el = document.getElementById("error-card");
    el.textContent = "";
    el.classList.remove("visible");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
