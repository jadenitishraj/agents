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

        if (!res.ok) throw new Error(`Server error: ${res.status}`);
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
    const summary = document.getElementById("run-summary");

    answer.textContent = data.final_answer;
    summary.textContent =
        `${data.iterations} iteration(s) · ${data.llm_calls} LLM calls · ` +
        `${data.sources_count} sources · ${data.duration_seconds.toFixed(1)}s`;

    section.style.display = "block";
    section.scrollIntoView({ behavior: "smooth" });
}

function showError(message) {
    const section = document.getElementById("error-section");
    const el = document.getElementById("error-message");
    el.textContent = message;
    section.style.display = "block";
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
