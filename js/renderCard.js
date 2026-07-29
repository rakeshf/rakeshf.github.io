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
  if (signal.includes("Long Build")) return "bg-success";
  if (signal.includes("Short Build")) return "bg-danger";
  return "bg-light text-dark";
};

let currentStockData = [];
let selectedQuickFilter = "All";

window.buildDataUrl = (path) => {
  const url = new URL(path, window.location.href);
  url.searchParams.set("t", Date.now());
  return url.toString();
};

const toNumberOrNull = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const formatCurrency = (value) => {
  const number = toNumberOrNull(value);
  return number !== null ? `₹${number.toFixed(2)}` : "N/A";
};

const formatPercent = (value) => {
  const number = toNumberOrNull(value);
  return number !== null ? `${number.toFixed(2)}%` : "N/A";
};

const formatCompact = (value) => {
  const number = toNumberOrNull(value);
  return number !== null && number > 0 ? number.toLocaleString("en-IN") : "N/A";
};

const getDirectionClass = (value) => {
  const number = toNumberOrNull(value);
  if (number === null || number === 0) return "text-secondary";
  return number > 0 ? "text-success" : "text-danger";
};

const setText = (id, value) => {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
};

const renderSummary = (data) => {
  setText("summaryTotal", data.length);
  setText("summaryBullish", data.filter((stock) => stock.sentiment === "Bullish").length);
  setText("summaryBearish", data.filter((stock) => stock.sentiment === "Bearish").length);
  setText("summaryConflicts", data.filter((stock) => stock.conflict).length);
};

const sortData = (data, sortValue) => {
  const sorted = [...data];
  const numberSortDesc = (field) =>
    sorted.sort((a, b) => (toNumberOrNull(b[field]) ?? -Infinity) - (toNumberOrNull(a[field]) ?? -Infinity));

  if (sortValue === "priceChangeDesc") return numberSortDesc("price_change_pct");
  if (sortValue === "pcrDesc") return numberSortDesc("pcr");
  if (sortValue === "oiChangeDesc") return numberSortDesc("oi_change_pct");
  if (sortValue === "scoreDesc") return numberSortDesc("master_score");

  return sorted.sort((a, b) => String(a.symbol || "").localeCompare(String(b.symbol || "")));
};

const getFilteredData = () => {
  const sentimentFilter = document.getElementById("sentimentFilter")?.value || "All";
  const signalFilter = document.getElementById("signalFilter")?.value || "All";
  const searchValue = (document.getElementById("symbolSearch")?.value || "").trim().toUpperCase();
  const sortValue = document.getElementById("sortSelector")?.value || "symbol";

  const filtered = currentStockData.filter((stock) => {
    const symbolMatch = !searchValue || String(stock.symbol || "").toUpperCase().includes(searchValue);
    const sentimentMatch = sentimentFilter === "All" || stock.sentiment === sentimentFilter;
    const quickMatch =
      selectedQuickFilter === "All" ||
      stock.sentiment === selectedQuickFilter ||
      (selectedQuickFilter === "Conflicts" && stock.conflict);
    const signalMatch =
      signalFilter === "All" ||
      (signalFilter === "Conflicts" && stock.conflict) ||
      String(stock.signal || "").includes(signalFilter);

    return symbolMatch && sentimentMatch && quickMatch && signalMatch;
  });

  return sortData(filtered, sortValue);
};

const updateResults = () => {
  renderCards(getFilteredData());
};

const renderCards = (data) => {
  const container = document.getElementById("cardContainer");
  if (!container) return;
  container.innerHTML = "";

  setText("resultCount", `${data.length} result${data.length === 1 ? "" : "s"}`);

  if (!data.length) {
    container.innerHTML = `
      <div class="empty-state">
        <span class="material-icons-outlined">search_off</span>
        <strong>No stocks match this view</strong>
        <span>Try changing the search, sentiment, signal, or selected data file.</span>
      </div>
    `;
    return;
  }

  data.forEach((stock) => {
    const price = toNumberOrNull(stock.price);
    const priceChangePct = toNumberOrNull(stock.price_change_pct);
    const priceDirectionClass = getDirectionClass(priceChangePct);

    const card = document.createElement("div");
    card.className = "stock-card";

    const priceIcon =
      priceChangePct !== null && priceChangePct >= 0
        ? `<span class="material-icons-outlined text-success">trending_up</span>`
        : `<span class="material-icons-outlined text-danger">trending_down</span>`;

    const signalBadge = `
  <span class="badge ${getSignalColor(stock.signal)}">
    ${stock.signal || "Signal N/A"}
  </span>`;
    const sentimentBadge = `<span class="badge ${getSentimentColor(
      stock.sentiment
    )} text-white">${stock.sentiment || "N/A"}</span>`;
    const rsi = stock.technicals ? toNumberOrNull(stock.technicals.rsi) : null;

    card.innerHTML = `
      <div class="card h-100 stock-card-inner">
        <div class="card-body">
          <div class="stock-card-top">
            <div>
              <h3 class="stock-symbol">${stock.symbol || "UNKNOWN"}</h3>
              <span class="stock-subtle">Score ${toNumberOrNull(stock.master_score) ?? "N/A"}</span>
            </div>
            ${sentimentBadge}
          </div>

          <div class="price-row">
            <div>
              <span class="stock-subtle">Last Price</span>
              <strong>${price !== null ? formatCurrency(price) : "N/A"}</strong>
            </div>
            <span class="price-change ${priceDirectionClass}">
              ${priceIcon}
              ${formatPercent(priceChangePct)}
            </span>
          </div>

          <div class="metric-grid">
            <div class="metric-cell">
              <span>PCR</span>
              <strong>${toNumberOrNull(stock.pcr) !== null ? toNumberOrNull(stock.pcr).toFixed(2) : "N/A"}</strong>
            </div>
            <div class="metric-cell">
              <span>CE OI</span>
              <strong>${formatCompact(stock.total_ce_oi)}</strong>
            </div>
            <div class="metric-cell">
              <span>PE OI</span>
              <strong>${formatCompact(stock.total_pe_oi)}</strong>
            </div>
            <div class="metric-cell">
              <span>OI Chg</span>
              <strong class="${getDirectionClass(stock.oi_change_pct)}">${formatPercent(stock.oi_change_pct)}</strong>
            </div>
            <div class="metric-cell">
              <span>Build</span>
              <strong>${stock.build_side || "N/A"}</strong>
            </div>
            <div class="metric-cell">
              <span>RSI</span>
              <strong>${rsi !== null ? rsi.toFixed(1) : "N/A"}</strong>
            </div>
          </div>

          <div class="stock-card-footer">
            ${signalBadge}
            <span class="stock-subtle">${getSignalTooltip(stock.signal)}</span>
          </div>
          ${
            stock.conflict
              ? `<div class="conflict-strip" data-bs-toggle="tooltip" title="Conflicting data between price and OI movement. Use caution.">
                  <span class="material-icons-outlined">warning</span>
                  Conflicting Signal
                </div>`
              : ""
          }
        </div>
      </div>
    `;
    container.appendChild(card);
  });

  if (window.bootstrap?.Tooltip) {
    const tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach((el) => new bootstrap.Tooltip(el));
  }
};

// Load available files into dropdown (assumes data/index.json contains array of filenames)
const normalizeFileList = (fileList) => {
  if (Array.isArray(fileList)) return fileList;
  if (fileList && Array.isArray(fileList.files)) return fileList.files;
  return [];
};

const getFileOptions = (fileList) =>
  normalizeFileList(fileList)
    .filter((file) => typeof file === "string")
    .map((file) => String(file).trim())
    .map((file) => file.replace(/^(\.\/|\.\.\/)?data\//, ""))
    .filter(Boolean);

fetch(buildDataUrl("data/index.json"))
  .then((res) => {
    if (!res.ok) throw new Error(`Failed to load index.json (${res.status} ${res.statusText})`);
    return res.json();
  })
  .then((fileList) => {
    const select = document.getElementById("fileSelector");
    if (!select) return;
    select.innerHTML = "";

    const cleanFiles = getFileOptions(fileList);
    cleanFiles.forEach((cleanFilename) => {
      const option = document.createElement("option");
      option.value = cleanFilename;
      option.textContent = cleanFilename.replace(/\.json$/, "");
      select.appendChild(option);
    });

    if (cleanFiles.length) {
      loadAndRenderData(cleanFiles[0]);
      if (typeof loadAndRenderFilename === "function") {
        loadAndRenderFilename(cleanFiles[0]);
      }
    } else {
      const container = document.getElementById("cardContainer");
      if (container) {
        container.innerHTML = `<div class="empty-state text-warning"><strong>No data files found.</strong><span>Check the data/index.json file and refresh the page.</span></div>`;
      }
    }

    select.addEventListener("change", () => {
      loadAndRenderData(select.value);
      if (typeof loadAndRenderFilename === "function") {
        loadAndRenderFilename(select.value);
      }
    });
  })
  .catch((err) => {
    console.error("Error loading file list:", err);
    const container = document.getElementById("cardContainer");
    if (container) {
      container.innerHTML = `<p class="text-danger">Error loading file list: ${err.message}</p>`;
    }
  });

// Load + render cards from a file
const loadAndRenderData = (filename) => {
  const cleanFilename = String(filename || "").replace(/^(\.\/|\.\.\/)?data\//, "");
  const container = document.getElementById("cardContainer");
  if (container) {
    container.innerHTML = `
      <div class="empty-state">
        <span class="material-icons-outlined">hourglass_top</span>
        <strong>Loading F&O data...</strong>
      </div>
    `;
  }

  const dataUrl = buildDataUrl(cleanFilename.startsWith("data/") ? cleanFilename : `data/${cleanFilename}`);

  fetch(dataUrl)
    .then((response) => {
      if (!response.ok) throw new Error(`Failed to fetch data (${response.status} ${response.statusText})`);
      return response.text();
    })
    .then((text) => {
      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch (error) {
        throw new Error(`Invalid JSON payload for ${cleanFilename}`);
      }

      currentStockData = Array.isArray(parsed) ? parsed : [];
      renderSummary(currentStockData);
      updateResults();
    })
    .catch((error) => {
      const message = error?.message || String(error);
      document.getElementById("cardContainer").innerHTML = `<div class="empty-state text-danger"><strong>Error loading data:</strong><span>${message}</span></div>`;
      console.error("Fetch error:", error);
    });
};

["sentimentFilter", "signalFilter", "sortSelector", "symbolSearch"].forEach((id) => {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener("input", updateResults);
    element.addEventListener("change", updateResults);
  }
});

document.querySelectorAll(".quick-filter").forEach((button) => {
  button.addEventListener("click", () => {
    selectedQuickFilter = button.dataset.filter || "All";
    document.querySelectorAll(".quick-filter").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    updateResults();
  });
});

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
