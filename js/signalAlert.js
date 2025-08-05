fetch("data/signal_alerts.json")
  .then((res) => res.json())
  .then((data) => {
    const container = document.getElementById("signalAlertContainer");
    if (!data.length) {
      container.innerHTML =
        "<div class='col'><div class='alert alert-info'>No signal changes detected.</div></div>";
      return;
    }

    data.forEach((item) => {
      const card = document.createElement("div");
      card.className = "col";

      card.innerHTML = `
<div class="card h-100 shadow my-3">
  <div class="card-body">
    <h5 class="card-title">${item.symbol}</h5>
    <p class="card-text mb-1">
      <span class="badge bg-danger text-white">Old:</span>
      <span class="text-danger">${item.old_signal}</span>
    </p>
    <p class="card-text mb-1">
      <span class="badge bg-success text-white">New:</span>
      <span class="text-success">${item.new_signal}</span>
    </p>
  </div>
</div>
`;

      container.appendChild(card);
    });
  })
  .catch((err) => {
    console.error("Error loading signal alerts:", err);
    const container = document.getElementById("cardContainer");
    container.innerHTML =
      "<div class='col'><div class='alert alert-warning'>Failed to load signal alert data.</div></div>";
  });
