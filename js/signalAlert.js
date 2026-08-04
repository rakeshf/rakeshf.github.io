const signalAlertsUrl = typeof window.buildDataUrl === "function"
  ? window.buildDataUrl("data/signal_alerts.json")
  : new URL("data/signal_alerts.json", window.location.href).toString();

fetch(signalAlertsUrl)
  .then((res) => {
    if (res.status === 404) {
      return [];
    }
    if (!res.ok) throw new Error(`Failed to load signal alerts (${res.status} ${res.statusText})`);
    return res.json();
  })
  .then((data) => {
    const alerts = Array.isArray(data) ? data : [];
    const container = document.getElementById("signalAlertContainer");
    const count = document.getElementById("signalAlertCount");
    if (count) count.textContent = alerts.length;
    if (!container) return;
    if (!alerts.length) {
      container.innerHTML =
        "<div class='signal-empty'>No signal changes detected.</div>";
      return;
    }

    alerts.forEach((item) => {
      const card = document.createElement("div");
      card.className = "signal-change-item";

      card.innerHTML = `
  <div class="signal-symbol">${item.symbol}</div>
  <div class="signal-flow">
    <span class="old-signal">${item.old_signal}</span>
    <span class="material-icons-outlined">arrow_forward</span>
    <span class="new-signal">${item.new_signal}</span>
  </div>
`;

      container.appendChild(card);
    });
  })
  .catch((err) => {
    console.error("Error loading signal alerts:", err);
    const container = document.getElementById("signalAlertContainer");
    if (container) {
      container.innerHTML =
        "<div class='signal-empty text-warning'>Failed to load signal alert data.</div>";
    }
  });
