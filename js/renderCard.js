const getSentimentColor = (sentiment) => {
  if (sentiment === "Bullish") return "bg-success";
  if (sentiment === "Bearish") return "bg-danger";
  if (sentiment === "Neutral") return "bg-secondary";
  return "bg-dark";
};

const getSignalColor = (signal) => {
  if (!signal) return "bg-light text-dark";
  if (signal.includes("Short Covering")) return "bg-warning text-dark";
  if (signal.includes("Long Unwinding")) return "bg-info text-dark";
  return "bg-light text-dark";
};

const renderCards = (data) => {
  const container = document.getElementById("cardContainer");
  if (!container) return;
  container.innerHTML = "";

  data.forEach((stock) => {
    const price = Number.isFinite(Number(stock.price)) ? Number(stock.price) : null;
    const priceChangePct = Number.isFinite(Number(stock.price_change_pct)) ? Number(stock.price_change_pct) : null;
    const previousClose = Number.isFinite(Number(stock.previous_close)) ? Number(stock.previous_close) : null;
    const totalCeOi = Number.isFinite(Number(stock.total_ce_oi)) ? Number(stock.total_ce_oi) : null;
    const totalPeOi = Number.isFinite(Number(stock.total_pe_oi)) ? Number(stock.total_pe_oi) : null;
    const oiChangePct = Number.isFinite(Number(stock.oi_change_pct)) ? Number(stock.oi_change_pct) : null;
    const ceOiChangePct = Number.isFinite(Number(stock.ce_oi_change_pct)) ? Number(stock.ce_oi_change_pct) : null;
    const peOiChangePct = Number.isFinite(Number(stock.pe_oi_change_pct)) ? Number(stock.pe_oi_change_pct) : null;
    const pcr = Number.isFinite(Number(stock.pcr)) ? Number(stock.pcr) : null;

    const card = document.createElement("div");
    card.className = "col";

    const priceIcon =
      stock.price_direction === "↑"
        ? `<span class="material-icons-outlined text-success">trending_up</span>`
        : `<span class="material-icons-outlined text-danger">trending_down</span>`;

    const oiIcon =
      stock.oi_direction === "↑"
        ? `<span class="material-icons-outlined text-success">north</span>`
        : `<span class="material-icons-outlined text-danger">south</span>`;

    const signalBadge = `
  <span class="badge ${getSignalColor(stock.signal)}">
    ${stock.signal}
  </span>`;
    const sentimentBadge = `<span class="badge ${getSentimentColor(
      stock.sentiment
    )} text-white">${stock.sentiment}</span>`;

    card.innerHTML = `
      <div class="card h-100 shadow">
        <div class="card-body">
          <h5 class="card-title">${stock.symbol}</h5>
          <p class="card-text mb-1">
            ${priceIcon}
            ${price !== null ? `₹${price.toFixed(2)}` : 'Price N/A'} (${
      stock.price_direction || ''
    } ${priceChangePct !== null ? priceChangePct.toFixed(2) + '%' : 'N/A'})
          </p>
          <p class="card-text mb-1">
            Prev Close: ${previousClose !== null ? `₹${previousClose.toFixed(2)}` : 'N/A'}
          </p>
          <p class="card-text mb-1">
            <span class="material-icons-outlined text-info">equalizer</span>
            CE OI: <strong>${totalCeOi !== null && totalCeOi > 0 ? totalCeOi.toLocaleString() : 'N/A'}</strong>,
            PE OI: <strong>${totalPeOi !== null && totalPeOi > 0 ? totalPeOi.toLocaleString() : 'N/A'}</strong>
          </p>
          <p class="card-text mb-1">
            ${oiIcon} OI: ${stock.oi_direction || ''} ${oiChangePct !== null ? oiChangePct.toFixed(2) + '%' : 'N/A'}
          </p>
          <p class="card-text mb-1">
            CE Δ: ${ceOiChangePct !== null ? ceOiChangePct.toFixed(2) + '%' : 'N/A'} &nbsp;
            PE Δ: ${peOiChangePct !== null ? peOiChangePct.toFixed(2) + '%' : 'N/A'}
          </p>
          <p class="card-text mb-1">
            PCR: <strong>${pcr !== null ? pcr.toFixed(2) : 'N/A'}</strong>
          </p>
          <p class="card-text mb-1">
            Build Side: <strong>${stock.build_side}</strong>
          </p>
          <p class="mb-1">
            ${sentimentBadge} ${signalBadge}
          </p>
          ${
            stock.conflict
              ? `<p class="text-danger fw-bold mt-1" data-bs-toggle="tooltip" title="Conflicting data between price and OI movement. Use caution.">⚠️ Conflicting Signal</p>`
              : ""
          }
          <p class="mb-1">
            <small class='text-muted'>${getSignalTooltip(stock.signal)}</small>
          </p>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
};

// Load available files into dropdown (assumes data/index.json contains array of filenames)
fetch("data/index.json")
  .then((res) => res.json())
  .then((fileList) => {
    const select = document.getElementById("fileSelector");
    if (!select) return;
    const cleanFiles = fileList.map((file) =>
      file.replace(/^(\.\/|\.\.\/)?data\//, "")
    );
    cleanFiles.forEach((cleanFilename) => {
      const option = document.createElement("option");
      option.value = cleanFilename;
      option.textContent = cleanFilename.replace(/\.json$/, "");
      select.appendChild(option);
    });

    // Load the first file initially
    if (cleanFiles.length) {
      loadAndRenderData(cleanFiles[0]);
      if (typeof loadAndRenderFilename === "function") {
        loadAndRenderFilename(cleanFiles[0]);
      }
    }

    // Reload dashboard on file change
    select.addEventListener("change", () => {
      loadAndRenderData(select.value);
      if (typeof loadAndRenderFilename === "function") {
        loadAndRenderFilename(select.value);
      }
    });
  })
  .catch((err) => {
    console.error("Error loading file list:", err);
    document.getElementById(
      "cardContainer"
    ).innerHTML = `<p class="text-danger">Error loading file list: ${err.message}</p>`;
  });

// Load + render cards from a file
const loadAndRenderData = (filename) => {
  const cleanFilename = filename.replace(/^(\.\/|\.\.\/)?data\//, "");
  fetch(`data/${cleanFilename}`)
    .then((response) => {
      if (!response.ok) throw new Error("Failed to fetch data");
      return response.json();
    })
    .then((data) => {
      renderCards(data);

      // Filter handler
      const filter = document.getElementById("sentimentFilter");
      if (filter) {
        filter.onchange = () => {
          const selected = filter.value;
          const filtered =
            selected === "All"
              ? data
              : data.filter((item) => item.sentiment === selected);
          renderCards(filtered);
        };
      }
    })
    .catch((error) => {
      document.getElementById(
        "cardContainer"
      ).innerHTML = `<p class="text-danger">Error loading data: ${error.message}</p>`;
      console.error("Fetch error:", error);
    });
};

const getSignalTooltip = (signal) => {
  if (!signal) return "Signal data is unavailable.";
  if (signal.includes("Short Covering"))
    return "Price ↑, OI ↓ → Shorts are being closed.";
  if (signal.includes("Long Unwinding"))
    return "Price ↓, OI ↓ → Longs are being closed.";
  if (signal.includes("Long Build-up") || signal.includes("Long Buildup"))
    return "Price ↑, OI ↑ → New long positions are being added.";
  if (signal.includes("Short Build-up") || signal.includes("Short Buildup"))
    return "Price ↓, OI ↑ → New short positions are being added.";
  return "Signal based on price and OI movement.";
};
