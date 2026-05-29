/**
 * Frontend JS — simple fetch to the FastAPI backend.
 *
 * Flow:
 *  1. User types a question, clicks Research.
 *  2. POST /research with the question.
 *  3. Wait for response (show spinner).
 *  4. Display the final answer.
 */

const API_BASE = "";  // Same origin — served by FastAPI.

// ─── Tabs ───────────────────────────────────────────────────

function switchTab(tab) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    event.target.classList.add("active");

    if (tab === "research") {
        document.getElementById("research-tab").style.display = "block";
        document.getElementById("upload-tab").style.display = "none";
    } else {
        document.getElementById("research-tab").style.display = "none";
        document.getElementById("upload-tab").style.display = "block";
    }
}

// ─── Upload ─────────────────────────────────────────────────

async function uploadFile() {
    const fileInput = document.getElementById("file-input");
    const statusEl = document.getElementById("upload-status");
    const btn = document.getElementById("upload-btn");
    const text = btn.querySelector(".btn-text");
    const loader = btn.querySelector(".btn-loader");
    
    if (!fileInput.files.length) {
        statusEl.textContent = "Please select a file first.";
        statusEl.style.color = "#ff6b6b";
        return;
    }

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append("file", file);

    btn.disabled = true;
    text.textContent = "Uploading...";
    loader.style.display = "inline-block";
    statusEl.textContent = "";

    try {
        const res = await fetch(`${API_BASE}/rag/upload`, {
            method: "POST",
            body: formData,
        });
        
        const data = await res.json();
        
        if (!res.ok) {
            throw new Error(data.error || "Upload failed");
        }
        
        statusEl.textContent = `Success! Indexed ${data.chunks} chunks from ${data.filename}.`;
        statusEl.style.color = "#4ade80";
        fileInput.value = ""; // Clear input
        
    } catch (err) {
        statusEl.textContent = `Error: ${err.message}`;
        statusEl.style.color = "#ff6b6b";
    } finally {
        btn.disabled = false;
        text.textContent = "Upload to RAG";
        loader.style.display = "none";
    }
}

// ─── Submit ─────────────────────────────────────────────────

async function submitQuestion() {
    const input = document.getElementById("question-input");
    const question = input.value.trim();
    if (!question) return;

    // Reset UI.
    resetUI();
    setLoading(true);

    try {
        const res = await fetch(`${API_BASE}/research`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });

        if (!res.ok) {
            let message = `Server error: ${res.status}`;
            try {
                const errorData = await res.json();
                message = errorData.message || message;
            } catch {
                // Keep the default message when the response is not JSON.
            }
            throw new Error(message);
        }
        const data = await res.json();

        // Show team badges.
        showTeam(data.team);

        // Show final answer.
        showAnswer(data);

    } catch (err) {
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

// ─── UI Helpers ─────────────────────────────────────────────

function resetUI() {
    document.getElementById("team-section").style.display = "none";
    document.getElementById("answer-section").style.display = "none";
    document.getElementById("error-section").style.display = "none";
    document.getElementById("team-badges").innerHTML = "";
    document.getElementById("final-answer").textContent = "";
    document.getElementById("rag-metrics").innerHTML = "";
    document.getElementById("rag-metrics").style.display = "none";
    document.getElementById("run-summary").textContent = "";
}

function setLoading(loading) {
    const btn = document.getElementById("submit-btn");
    const text = btn.querySelector(".btn-text");
    const loader = btn.querySelector(".btn-loader");
    btn.disabled = loading;
    text.textContent = loading ? "Researching..." : "Research";
    loader.style.display = loading ? "inline-block" : "none";
}

function showTeam(team) {
    const section = document.getElementById("team-section");
    const badges = document.getElementById("team-badges");
    badges.innerHTML = team
        .map((name) => `<span class="team-badge">${escapeHtml(name)}</span>`)
        .join("");
    section.style.display = "block";
}

function showAnswer(data) {
    const section = document.getElementById("answer-section");
    const answer = document.getElementById("final-answer");
    const metrics = document.getElementById("rag-metrics");
    const summary = document.getElementById("run-summary");
    const chunksBtn = document.getElementById("view-chunks-btn");

    answer.textContent = data.final_answer;
    showMetrics(metrics, data.rag_metrics || {}, data.rag_parser_summary || {});
    summary.textContent =
        `${data.iterations} iteration(s) · ${data.llm_calls} LLM calls · ` +
        `${data.sources_count} sources · ${data.duration_seconds.toFixed(1)}s`;

    // Save contexts for modal
    window.currentChunks = data.retrieved_contexts || [];
    if (window.currentChunks.length > 0) {
        chunksBtn.style.display = "inline-block";
    } else {
        chunksBtn.style.display = "none";
    }

    section.style.display = "block";
    section.scrollIntoView({ behavior: "smooth" });
}

// ─── Modal ──────────────────────────────────────────────────

function openChunksModal() {
    const container = document.getElementById("chunks-container");
    const chunks = window.currentChunks || [];
    
    if (chunks.length === 0) {
        container.innerHTML = "<p>No chunks retrieved for this question.</p>";
    } else {
        container.innerHTML = chunks.map(chunk => 
            `<div class="chunk-card">${escapeHtml(chunk)}</div>`
        ).join("");
    }
    
    document.getElementById("chunks-modal").style.display = "flex";
}

function closeChunksModal() {
    document.getElementById("chunks-modal").style.display = "none";
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById("chunks-modal");
    if (event.target === modal) {
        closeChunksModal();
    }
}

function showError(message) {
    const section = document.getElementById("error-section");
    const el = document.getElementById("error-message");
    el.textContent = message;
    section.style.display = "block";
}

function showMetrics(container, metrics, parserSummary) {
    const cards = Object.entries(metrics)
        .filter(([key]) => key !== "note")
        .map(([key, value]) => {
            const label = key.replace(/_/g, " ");
            return `
                <div class="metric-card">
                    <span class="metric-label">${escapeHtml(label)}</span>
                    <span class="metric-value">${Number(value).toFixed(2)}</span>
                </div>
            `;
        });

    const parserText = Object.entries(parserSummary)
        .map(([name, count]) => `${name}: ${count}`)
        .join(" · ");

    const note = metrics.note || "";
    const detail = [parserText, note].filter(Boolean).join(" | ");

    if (!cards.length && !detail) return;

    container.innerHTML = `${cards.join("")}${detail ? `<div class="metric-note">${escapeHtml(detail)}</div>` : ""}`;
    container.style.display = "grid";
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ─── Enter key to submit ────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("question-input").addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submitQuestion();
        }
    });
});
