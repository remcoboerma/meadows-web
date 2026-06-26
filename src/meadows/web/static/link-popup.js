/**
 * Link Tracking Popup System
 *
 * REQUIREMENT: Intercept clicks on mediamatch search result links
 * BUSINESS RULE: Track user engagement with search results
 * UX RULE: Show popup with options to open, provide feedback, add comments
 *
 * Features:
 * - Intercepts clicks on links with data-link-id attribute
 * - Shows modal popup with link metadata
 * - "Open in New Tab" button → resolves link ID via API → opens original URL
 * - Thumbs up/down buttons → submit feedback to API
 * - Optional comment field → additional user feedback
 * - Records: shown_timestamp, clicked_timestamp, feedback_timestamp
 *
 * Integration:
 * - Called from index.html WebChat class
 * - Uses /link/{id} endpoint to resolve tracking IDs
 * - Uses /link/{id}/feedback endpoint to submit feedback
 */

class LinkPopup {
  constructor(apiBaseUrl = "") {
    this.apiBaseUrl = apiBaseUrl;
    this.currentLinkId = null;
    this.initializePopup();
  }

  /**
   * Initialize popup modal and event listeners
   */
  initializePopup() {
    // Create modal HTML if it doesn't exist
    if (!document.getElementById("link-popup-modal")) {
      this.createPopupModal();
    }

    // REQUIREMENT: Listen for hash-based link URLs (#/link/XXXXX)
    // TECHNICAL: Frontend intercepts hash changes and shows popup
    // This allows proper markdown link rendering with frontend routing
    window.addEventListener("hashchange", () => this.handleHashChange());
    
    // Also handle initial hash on page load
    this.handleHashChange();
  }
  
  /**
   * Handle hash change to detect link tracking URLs
   * Format: #/link/XXXXX where XXXXX is the tracking ID
   */
  handleHashChange() {
    const hash = window.location.hash;
    const linkMatch = hash.match(/^#\/link\/([a-zA-Z0-9_-]+)$/);
    
    if (linkMatch) {
      const linkId = linkMatch[1];
      // Clear hash to prevent navigation
      window.history.replaceState(null, "", window.location.pathname);
      // Show popup for this link ID
      this.showPopup(linkId);
    }
  }

  /**
   * Create the popup modal HTML structure
   */
  createPopupModal() {
    const modal = document.createElement("div");
    modal.id = "link-popup-modal";
    modal.className = "link-popup-modal";
    modal.innerHTML = `
      <div class="link-popup-content">
        <div class="link-popup-header">
          <h3 id="link-popup-title">Link</h3>
          <button class="link-popup-close" aria-label="Close popup">&times;</button>
        </div>

        <div class="link-popup-body">
          <div id="link-popup-info" class="link-info">
            <!-- Dynamically populated -->
          </div>

          <div class="link-popup-actions">
            <button id="link-open-btn" class="link-btn link-btn-primary">
              🔗 Open in New Tab
            </button>
          </div>

          <div class="link-popup-feedback">
            <label>Was this result helpful?</label>
            <div class="feedback-buttons">
              <button id="link-feedback-up" class="feedback-btn feedback-up" title="Thumbs up - helpful">
                👍 Yes
              </button>
              <button id="link-feedback-down" class="feedback-btn feedback-down" title="Thumbs down - not helpful">
                👎 No
              </button>
            </div>

            <div id="link-comment-section" class="comment-section" style="display: none;">
              <textarea
                id="link-comment-input"
                class="link-comment-input"
                placeholder="What did you think of this result? (optional)"
                rows="3"
              ></textarea>
              <button id="link-submit-feedback-btn" class="link-btn link-btn-secondary">
                Submit Feedback
              </button>
            </div>
          </div>

          <div id="link-feedback-status" class="feedback-status"></div>
        </div>
      </div>
    </div>
    `;

    // Inject styles
    this.injectStyles();

    // Add modal to page
    document.body.appendChild(modal);

    // Set up event listeners
    modal
      .querySelector(".link-popup-close")
      .addEventListener("click", () => this.closePopup());

    document.getElementById("link-open-btn").addEventListener("click", () =>
      this.openLink()
    );

    document.getElementById("link-feedback-up").addEventListener("click", () =>
      this.showCommentSection("up")
    );

    document.getElementById("link-feedback-down").addEventListener("click", () =>
      this.showCommentSection("down")
    );

    document
      .getElementById("link-submit-feedback-btn")
      .addEventListener("click", () => this.submitFeedback());

    // Close popup when clicking outside
    modal.addEventListener("click", (e) => {
      if (e.target === modal) {
        this.closePopup();
      }
    });

    // Close popup on Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && modal.classList.contains("active")) {
        this.closePopup();
      }
    });
  }

  /**
   * Inject CSS styles for popup
   */
  injectStyles() {
    const styleId = "link-popup-styles";
    if (document.getElementById(styleId)) return;

    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
      /* Link Popup Modal */
      .link-popup-modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10000;
        align-items: center;
        justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      }

      .link-popup-modal.active {
        display: flex;
      }

      .link-popup-content {
        background: var(--bg-primary, #ffffff);
        color: var(--text-primary, #000000);
        border-radius: 8px;
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
      }

      .link-popup-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        border-bottom: 1px solid var(--border-color, #ddd);
      }

      .link-popup-header h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
      }

      .link-popup-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: var(--text-secondary, #666);
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .link-popup-close:hover {
        color: var(--text-primary, #000);
      }

      .link-popup-body {
        padding: 16px;
      }

      .link-info {
        margin-bottom: 16px;
        padding: 12px;
        background: var(--bg-secondary, #f5f5f5);
        border-radius: 4px;
      }

      .link-info-row {
        margin-bottom: 8px;
        font-size: 14px;
      }

      .link-info-label {
        font-weight: 600;
        color: var(--text-secondary, #666);
      }

      .link-info-value {
        color: var(--text-primary, #000);
        word-break: break-all;
        margin-top: 4px;
      }

      /* Action Buttons */
      .link-popup-actions {
        margin-bottom: 16px;
      }

      .link-btn {
        width: 100%;
        padding: 12px 16px;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .link-btn-primary {
        background: #1976d2;
        color: white;
      }

      .link-btn-primary:hover {
        background: #1565c0;
      }

      .link-btn-secondary {
        background: var(--bg-secondary, #f5f5f5);
        color: var(--text-primary, #000);
        border: 1px solid var(--border-color, #ddd);
      }

      .link-btn-secondary:hover {
        background: var(--border-color, #ddd);
      }

      /* Feedback Section */
      .link-popup-feedback {
        border-top: 1px solid var(--border-color, #ddd);
        padding-top: 16px;
      }

      .link-popup-feedback > label {
        display: block;
        margin-bottom: 12px;
        font-weight: 600;
        font-size: 14px;
      }

      .feedback-buttons {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
      }

      .feedback-btn {
        flex: 1;
        padding: 10px 16px;
        border: 2px solid var(--border-color, #ddd);
        background: var(--bg-primary, #ffffff);
        color: var(--text-primary, #000);
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .feedback-btn:hover {
        border-color: #1976d2;
      }

      .feedback-btn.selected {
        background: #1976d2;
        color: white;
        border-color: #1976d2;
      }

      .comment-section {
        margin-top: 12px;
      }

      .link-comment-input {
        width: 100%;
        padding: 12px;
        border: 1px solid var(--border-color, #ddd);
        border-radius: 4px;
        background: var(--bg-primary, #ffffff);
        color: var(--text-primary, #000);
        font-family: inherit;
        font-size: 14px;
        resize: vertical;
        margin-bottom: 12px;
      }

      .link-comment-input:focus {
        outline: none;
        border-color: #1976d2;
        box-shadow: 0 0 0 3px rgba(25, 118, 210, 0.1);
      }

      .feedback-status {
        margin-top: 12px;
        padding: 12px;
        border-radius: 4px;
        font-size: 14px;
        display: none;
      }

      .feedback-status.success {
        display: block;
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
      }

      .feedback-status.error {
        display: block;
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
      }

      /* Dark mode support */
      body.dark-mode .link-popup-content {
        background: var(--bg-secondary, #1e1e1e);
        color: var(--text-primary, #ffffff);
      }

      body.dark-mode .link-info {
        background: var(--bg-primary, #2d2d2d);
      }

      body.dark-mode .feedback-btn {
        border-color: var(--border-color, #444);
      }

      body.dark-mode .link-comment-input {
        background: var(--bg-secondary, #2d2d2d);
        color: var(--text-primary, #ffffff);
        border-color: var(--border-color, #444);
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * Handle click on links with tracking IDs
   * TECHNICAL: Uses link-id: prefix in markdown links to identify tracked links
   */
  /**
   * Show popup with link information
   */
  async showPopup(linkId) {
    this.currentLinkId = linkId;

    try {
      // Fetch link information from API
      const response = await fetch(
        `${this.apiBaseUrl}/link/${encodeURIComponent(linkId)}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch link: ${response.status}`);
      }

      const linkData = await response.json();

      // Display link information
      this.displayLinkInfo(linkData);

      // Show modal
      const modal = document.getElementById("link-popup-modal");
      modal.classList.add("active");

      // Reset feedback UI
      this.resetFeedbackUI();
    } catch (error) {
      console.error("[LinkPopup] Error fetching link:", error);
      this.showError("Failed to load link information");
    }
  }

  /**
   * Display link information in popup
   */
  displayLinkInfo(linkData) {
    const infoDiv = document.getElementById("link-popup-info");
    const titleEl = document.getElementById("link-popup-title");

    titleEl.textContent = linkData.title || "Link";

    let html = "";

    if (linkData.search_query) {
      html += `
        <div class="link-info-row">
          <div class="link-info-label">Search Query</div>
          <div class="link-info-value">"${linkData.search_query}"</div>
        </div>
      `;
    }

    if (linkData.type) {
      const typeLabel = linkData.type === "chunk" ? "Transcript" : "Full Document";
      html += `
        <div class="link-info-row">
          <div class="link-info-label">Type</div>
          <div class="link-info-value">${typeLabel}</div>
        </div>
      `;
    }

    if (linkData.resource_id) {
      html += `
        <div class="link-info-row">
          <div class="link-info-label">Resource ID</div>
          <div class="link-info-value"><code style="font-size: 12px;">${linkData.resource_id}</code></div>
        </div>
      `;
    }

    infoDiv.innerHTML = html;
  }

  /**
   * Show comment section after feedback selection
   */
  showCommentSection(feedback) {
    // Mark button as selected
    document
      .querySelectorAll(".feedback-btn")
      .forEach((btn) => btn.classList.remove("selected"));

    const btn =
      feedback === "up"
        ? document.getElementById("link-feedback-up")
        : document.getElementById("link-feedback-down");
    btn.classList.add("selected");

    // Show comment section
    document.getElementById("link-comment-section").style.display = "block";
  }

  /**
   * Submit feedback to API
   */
  async submitFeedback() {
    if (!this.currentLinkId) return;

    const feedback = document.querySelector(
      ".feedback-btn.selected"
    )?.textContent;
    if (!feedback) {
      this.showError("Please select thumbs up or down");
      return;
    }

    const feedbackValue = feedback.includes("👍") ? "up" : "down";
    const comment =
      document.getElementById("link-comment-input")?.value || null;

    try {
      const response = await fetch(
        `${this.apiBaseUrl}/link/${encodeURIComponent(this.currentLinkId)}/feedback`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            feedback: feedbackValue,
            comment: comment,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to submit feedback: ${response.status}`);
      }

      this.showSuccess("Thank you for your feedback!");

      // Clear feedback buttons and comment
      setTimeout(() => {
        this.closePopup();
      }, 1500);
    } catch (error) {
      console.error("[LinkPopup] Error submitting feedback:", error);
      this.showError("Failed to submit feedback");
    }
  }

  /**
   * Open the link in a new tab
   */
  async openLink() {
    if (!this.currentLinkId) return;

    try {
      const response = await fetch(
        `${this.apiBaseUrl}/link/${encodeURIComponent(this.currentLinkId)}`
      );

      if (!response.ok) {
        throw new Error(`Failed to resolve link: ${response.status}`);
      }

      const linkData = await response.json();
      const url = linkData.full_url;

      if (url) {
        window.open(url, "_blank");
      } else {
        throw new Error("No URL returned from server");
      }
    } catch (error) {
      console.error("[LinkPopup] Error opening link:", error);
      this.showError("Failed to open link");
    }
  }

  /**
   * Close the popup
   */
  closePopup() {
    const modal = document.getElementById("link-popup-modal");
    modal.classList.remove("active");
    this.currentLinkId = null;
    this.resetFeedbackUI();
  }

  /**
   * Reset feedback UI for next use
   */
  resetFeedbackUI() {
    document
      .querySelectorAll(".feedback-btn")
      .forEach((btn) => btn.classList.remove("selected"));
    document.getElementById("link-comment-input").value = "";
    document.getElementById("link-comment-section").style.display = "none";
    document.getElementById("link-feedback-status").innerHTML = "";
  }

  /**
   * Show error message
   */
  showError(message) {
    const statusEl = document.getElementById("link-feedback-status");
    statusEl.textContent = "❌ " + message;
    statusEl.className = "feedback-status error";
  }

  /**
   * Show success message
   */
  showSuccess(message) {
    const statusEl = document.getElementById("link-feedback-status");
    statusEl.textContent = "✓ " + message;
    statusEl.className = "feedback-status success";
  }
}

// Auto-initialize on DOM ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    window.linkPopup = new LinkPopup("");
  });
} else {
  window.linkPopup = new LinkPopup("");
}
