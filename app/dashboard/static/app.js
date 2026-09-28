// Live dashboard polling and UI state controller
async function fetchState() {
  try {
    const res = await fetch("/api/state");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("badge-mode").innerText = data.mode;
    document.getElementById("badge-status").innerText = data.run_status;
    document.getElementById("action-text").innerText = data.current_action || "Idle";

    // Metrics
    document.getElementById("metric-total").innerText = data.metrics.total;
    document.getElementById("metric-completed").innerText = data.metrics.completed;
    document.getElementById("metric-pending").innerText = data.metrics.pending;
    document.getElementById("metric-failed").innerText = data.metrics.failed;
    document.getElementById("metric-priority").innerText = data.metrics.priority;

    // Progress bar
    document.getElementById("progress-bar").style.width = `${data.progress_percent}%`;

    // Connections
    if (data.connections.gmail) {
      document.getElementById("conn-gmail-badge").innerText = data.connections.gmail.status;
    }
    if (data.connections.whatsapp) {
      document.getElementById("conn-whatsapp-badge").innerText = data.connections.whatsapp.status;
    }
  } catch (err) {
    console.error("State polling error:", err);
  }
}

async function fetchEvents() {
  try {
    const res = await fetch("/api/events?limit=25");
    if (!res.ok) return;
    const data = await res.json();
    const container = document.getElementById("events-stream");
    if (!data.events || data.events.length === 0) return;

    container.innerHTML = data.events.map(e => `
      <div class="event-row">
        <span class="icon">${e.icon || "•"}</span>
        <span class="msg">${e.message}</span>
      </div>
    `).join("");
  } catch (err) {
    console.error("Events fetch error:", err);
  }
}

async function sendControl(action) {
  try {
    const res = await fetch("/api/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action })
    });
    if (res.ok) {
      await fetchState();
      await fetchEvents();
    }
  } catch (err) {
    alert("Control request failed: " + err);
  }
}

function openWhatsAppModal() {
  document.getElementById("wa-modal").classList.add("open");
}

function closeWhatsAppModal() {
  document.getElementById("wa-modal").classList.remove("open");
}

async function saveWhatsApp(event) {
  event.preventDefault();
  const phoneId = document.getElementById("wa-phone-id").value;
  const wabaId = document.getElementById("wa-waba-id").value;
  const token = document.getElementById("wa-token").value;

  try {
    const res = await fetch("/api/connections/whatsapp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phone_number_id: phoneId,
        waba_id: wabaId,
        access_token: token
      })
    });
    if (res.ok) {
      closeWhatsAppModal();
      await fetchState();
    } else {
      alert("Failed to save credentials");
    }
  } catch (err) {
    alert("Error saving: " + err);
  }
}

// Initial fetch and interval poll every 2000ms
fetchState();
fetchEvents();
setInterval(fetchState, 2000);
setInterval(fetchEvents, 3000);

// ---------------------------------------------------------------- Gmail OAuth
async function connectGmail() {
  const btn = document.getElementById("btn-gmail-connect");
  btn.disabled = true;
  btn.innerText = "Opening Google...";
  try {
    const res = await fetch("/api/connections/gmail/connect");
    const data = await res.json();
    if (data.error) {
      alert("Gmail connect failed:\n" + data.error);
    } else {
      // Hand off to Google's consent screen. The browser returns to
      // /oauth2/callback which stores the token and redirects back here.
      window.location.href = data.authorization_url;
    }
  } catch (err) {
    alert("Could not reach the dashboard API: " + err);
  }
  btn.disabled = false;
  btn.innerText = "Connect";
}

async function testGmail() {
  try {
    const res = await fetch("/api/connections/gmail/test", { method: "POST" });
    const data = await res.json();
    if (data.ok) {
      alert("Gmail connected: " + data.account + "\n" + data.detail);
    } else {
      alert("Gmail not connected.\n\n" + data.detail);
    }
    await fetchState();
  } catch (err) {
    alert("Connection test failed: " + err);
  }
}

// Surface the OAuth result the server appended to the redirect URL.
const gmailResult = new URLSearchParams(window.location.search).get("gmail");
if (gmailResult === "connected") {
  alert("Gmail connected successfully.");
  fetchState();
  fetchEvents();
} else if (gmailResult === "denied") {
  alert("Google consent was denied. Gmail is still disconnected.");
} else if (gmailResult === "bad_state") {
  alert("Security check failed (expired request). Please click Connect again.");
} else if (gmailResult === "error") {
  alert("Gmail authorization failed. Check the server log for details.");
}
// ------------------------------------------------------------ WhatsApp connect
function openWhatsAppModal() {
  document.getElementById("wa-modal").classList.add("open");
  document.getElementById("wa-result").classList.add("hidden");
  refreshWhatsAppStatus();
}

function closeWhatsAppModal() {
  document.getElementById("wa-modal").classList.remove("open");
}

function showWaResult(ok, text) {
  const box = document.getElementById("wa-result");
  box.textContent = text;
  box.classList.remove("hidden");
  box.classList.toggle("result-ok", ok);
  box.classList.toggle("result-err", !ok);
}

async function saveWhatsApp(event) {
  event.preventDefault();
  const btn = document.getElementById("wa-submit");
  btn.disabled = true;
  btn.innerText = "Testing connection...";
  try {
    const res = await fetch("/api/connections/whatsapp/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        phone_number_id: document.getElementById("wa-phone-id").value.trim(),
        waba_id: document.getElementById("wa-waba-id").value.trim(),
        access_token: document.getElementById("wa-token").value.trim(),
      }),
    });
    const data = await res.json();
    if (data.error) {
      showWaResult(false, data.error + (data.hint ? "\n" + data.hint : ""));
    } else if (data.connected) {
      showWaResult(true, "Connected. " + data.detail);
      document.getElementById("wa-token").value = "";
      await refreshWhatsAppStatus();
      await fetchEvents();
      setTimeout(closeWhatsAppModal, 2500);
    } else {
      showWaResult(false, "Credentials saved but the test did not confirm the connection.\n\n" + data.detail);
      await refreshWhatsAppStatus();
    }
  } catch (err) {
    showWaResult(false, "Request failed: " + err);
  }
  btn.disabled = false;
  btn.innerText = "Save & Test Connection";
}

async function testWhatsApp() {
  try {
    const res = await fetch("/api/connections/whatsapp/test", { method: "POST" });
    const data = await res.json();
    alert((data.ok ? "WhatsApp connected.\n\n" : "WhatsApp not connected.\n\n") + data.detail);
    await refreshWhatsAppStatus();
  } catch (err) {
    alert("Test failed: " + err);
  }
}

async function refreshWhatsAppStatus() {
  try {
    const res = await fetch("/api/connections/whatsapp");
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById("conn-whatsapp-badge");
    if (data.provider === "stub") {
      badge.innerText = "STUB MODE";
      document.getElementById("conn-whatsapp-desc").innerText = "Offline simulation - no real messages";
    } else if (data.connected) {
      badge.innerText = "CONNECTED";
      badge.classList.add("badge-active");
      document.getElementById("conn-whatsapp-desc").innerText =
        "Meta Cloud API - " + (data.phone_number_id || "configured");
    } else {
      badge.innerText = data.configured ? "NOT VERIFIED" : "NOT CONFIGURED";
      document.getElementById("conn-whatsapp-desc").innerText = data.detail || "";
    }
  } catch (err) { /* status is non-critical */ }
}

// Keep the WhatsApp badge current with the rest of the dashboard.
setInterval(refreshWhatsAppStatus, 5000);
refreshWhatsAppStatus();
