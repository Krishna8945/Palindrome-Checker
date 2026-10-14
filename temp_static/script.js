/**
 * Palindrome Checker Web App Client Script
 * Handles real-time verification via Fetch API & Interactive UI state
 */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("palindromeForm");
    const input = document.getElementById("inputText");
    const clearBtn = document.getElementById("clearBtn");
    const resetBtn = document.getElementById("resetBtn");
    const sampleChips = document.querySelectorAll(".sample-chip");

    const resultCard = document.getElementById("resultCard");
    const resultBadgeType = document.getElementById("resultBadgeType");
    const resultContent = document.getElementById("resultContent");

    // Clear textarea button
    if (clearBtn && input) {
        clearBtn.addEventListener("click", () => {
            input.value = "";
            input.focus();
        });
    }

    // Reset button
    if (resetBtn) {
        resetBtn.addEventListener("click", () => {
            setTimeout(() => {
                if (resultCard) {
                    resultCard.style.display = "none";
                }
            }, 50);
        });
    }

    // Quick sample pill clicks
    sampleChips.forEach((chip) => {
        chip.addEventListener("click", () => {
            const sampleText = chip.getAttribute("data-sample");
            if (sampleText) {
                input.value = sampleText;
                submitPalindromeCheck();
            }
        });
    });

    // Asynchronous check function
    async function submitPalindromeCheck() {
        const text = input.value.trim();
        if (!text) {
            input.focus();
            return;
        }

        const optCase = document.getElementById("optCase")?.checked ?? true;
        const optSpaces = document.getElementById("optSpaces")?.checked ?? true;
        const optPunct = document.getElementById("optPunct")?.checked ?? true;

        const checkBtn = document.getElementById("checkBtn");
        if (checkBtn) {
            checkBtn.disabled = true;
            checkBtn.innerHTML = '<span class="btn-icon">⏳</span> Checking...';
        }

        try {
            const response = await fetch("/api/check", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    text: text,
                    ignore_case: optCase,
                    ignore_spaces: optSpaces,
                    ignore_punctuation: optPunct
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            const data = await response.json();
            renderResults(data);
        } catch (err) {
            console.error("Palindrome check error:", err);
            // Fallback: standard form submit if fetch fails
            form.submit();
        } finally {
            if (checkBtn) {
                checkBtn.disabled = false;
                checkBtn.innerHTML = '<span class="btn-icon">⚡</span> Check Palindrome';
            }
        }
    }

    // Form submit interception
    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            submitPalindromeCheck();
        });
    }

    // Render DOM elements dynamically based on JSON response
    function renderResults(data) {
        if (!resultCard || !resultContent) return;

        resultCard.style.display = "block";

        const isPal = data.is_palindrome;

        // Badge update
        if (resultBadgeType) {
            resultBadgeType.className = `status-pill ${isPal ? "pill-success" : "pill-danger"}`;
            resultBadgeType.textContent = isPal ? "PALINDROME" : "NOT PALINDROME";
        }

        // Build HTML
        let html = `
            <!-- Banner -->
            <div class="result-banner ${isPal ? "banner-success" : "banner-danger"}">
                <div class="banner-icon">${isPal ? "🎉" : "❌"}</div>
                <div class="banner-text">
                    <h3>${isPal ? "Yes! This is a valid palindrome." : "No, this is not a palindrome."}</h3>
                    <p>${escapeHtml(data.message)}</p>
                </div>
            </div>

            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-box">
                    <span class="stat-label">Raw Length</span>
                    <span class="stat-value">${data.raw_text ? data.raw_text.length : 0}</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">Cleaned Deque Size</span>
                    <span class="stat-value">${data.total_chars}</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">Deque Comparisons</span>
                    <span class="stat-value">${data.steps.length}</span>
                </div>
                <div class="stat-box">
                    <span class="stat-label">Center Pivot</span>
                    <span class="stat-value pivot">${data.middle_char !== null && data.middle_char !== undefined ? `'${escapeHtml(data.middle_char)}'` : "None"}</span>
                </div>
            </div>
        `;

        // Initial Deque Cells
        if (data.cleaned_text && data.cleaned_text.length > 0) {
            const cellsHtml = data.cleaned_text
                .split("")
                .map((ch) => `<div class="deque-cell">${escapeHtml(ch)}</div>`)
                .join("");

            html += `
                <div class="deque-initial-box">
                    <div class="section-subheading">
                        <span>Initial Deque Representation</span>
                        <span class="subheading-tag">Front &larr; &bull; &rarr; Rear</span>
                    </div>
                    <div class="deque-container">
                        <div class="deque-end-label front-label">&larr; Front (popleft)</div>
                        <div class="deque-cells">${cellsHtml}</div>
                        <div class="deque-end-label rear-label">Rear (pop) &rarr;</div>
                    </div>
                </div>
            `;
        }

        // Step-by-Step Trace
        html += `
            <div class="trace-section">
                <div class="section-subheading">
                    <span>Step-by-Step Deque Comparison Trace</span>
                    <span class="subheading-tag">popleft() vs pop()</span>
                </div>
        `;

        if (data.steps && data.steps.length > 0) {
            const rowsHtml = data.steps
                .map((s) => {
                    const rowClass = s.matched ? "row-match" : "row-mismatch";
                    const matchBadge = s.matched
                        ? `<span class="match-tag match-yes">&check; Match ('${escapeHtml(s.front)}' == '${escapeHtml(s.rear)}')</span>`
                        : `<span class="match-tag match-no">&#10006; Mismatch ('${escapeHtml(s.front)}' &ne; '${escapeHtml(s.rear)}')</span>`;
                    const remaining = s.remaining_str
                        ? `<code>${escapeHtml(s.remaining_str)}</code>`
                        : `<em>(empty deque)</em>`;

                    return `
                        <tr class="${rowClass}">
                            <td><span class="step-badge">#${s.step}</span></td>
                            <td><code class="char-chip">${escapeHtml(s.front)}</code></td>
                            <td><code class="char-chip">${escapeHtml(s.rear)}</code></td>
                            <td>${matchBadge}</td>
                            <td><span class="remaining-str">${remaining}</span></td>
                        </tr>
                    `;
                })
                .join("");

            html += `
                <div class="table-responsive">
                    <table class="trace-table">
                        <thead>
                            <tr>
                                <th>Step</th>
                                <th>popleft() (Front)</th>
                                <th>pop() (Rear)</th>
                                <th>Comparison</th>
                                <th>Remaining Deque</th>
                            </tr>
                        </thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                </div>
            `;
        } else if (data.total_chars <= 1) {
            html += `
                <p class="empty-trace-note">
                    A string with ${data.total_chars} character is trivially a palindrome without needing two-ended comparisons.
                </p>
            `;
        }

        html += `</div>`;

        resultContent.innerHTML = html;

        // Smooth scroll to result if on mobile
        if (window.innerWidth < 900) {
            resultCard.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
