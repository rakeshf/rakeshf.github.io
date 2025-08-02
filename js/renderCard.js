const getSentimentColor = (sentiment) => {
  if (sentiment === "Bullish") return "bg-success";
  if (sentiment === "Bearish") return "bg-danger";
  if (sentiment === "Neutral") return "bg-secondary";
  return "bg-dark";
};

const getSignalColor = (signal) => {
  if (signal.includes("Short Covering")) return "bg-warning text-dark";
  if (signal.includes("Long Unwinding")) return "bg-info text-dark";
  return "bg-light text-dark";
};

const renderCards = (data) => {
  const container = document.getElementById("cardContainer");
  container.innerHTML = "";

  data.forEach((stock) => {
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
  <span class="badge ${getSignalColor(stock.signal)}"
        data-bs-toggle="tooltip"
        data-bs-placement="top"
        data-bs-html="true"
        title="${getSignalTooltip(stock.signal)}">
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
            ₹${stock.price.toFixed(2)} (${
      stock.price_direction
    } ${stock.price_change_pct.toFixed(2)}%)
          </p>
          <p class="card-text mb-1">
            Prev Close: ₹${stock.previous_close.toFixed(2)}
          </p>
          <p class="card-text mb-1">
            <span class="material-icons-outlined text-info">equalizer</span>
            CE OI: <strong>${stock.total_ce_oi.toLocaleString()}</strong>,
            PE OI: <strong>${stock.total_pe_oi.toLocaleString()}</strong>
          </p>
          <p class="card-text mb-1">
            ${oiIcon} OI: ${stock.oi_direction} ${stock.oi_change_pct.toFixed(
      2
    )}%
          </p>
          <p class="card-text mb-1">
            CE Δ: ${stock.ce_oi_change_pct.toFixed(2)}% &nbsp;
            PE Δ: ${stock.pe_oi_change_pct.toFixed(2)}%
          </p>
          <p class="card-text mb-1">
            PCR: <strong>${stock.pcr.toFixed(2)}</strong>
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
    fileList.forEach((file) => {
      // const option = document.createElement("option");
      const cleanFilename = file.replace(/^(\.\/|\.\.\/)?data\//, "");
      const option = document.createElement("option");
      option.value = cleanFilename;
      option.textContent = cleanFilename.replace(/\.json$/, "");
      console.log("Adding file option:", file);
      select.appendChild(option);
    });

    // Load the first file initially
    if (fileList.length) {
      loadAndRenderData(fileList[0]);
      loadAndRenderFilename(fileList[0]);
    }

    // Reload dashboard on file change
    select.addEventListener("change", () => {
      loadAndRenderData(select.value);
      loadAndRenderFilename(select.value);
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
  fetch(`data/${filename}`)
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
  if (signal.includes("Short Covering"))
    return "Price ↑, OI ↓ → Short positions are being closed.";
  if (signal.includes("Long Unwinding"))
    return "Price ↓, OI ↓ → Long positions are being closed.";
  if (signal.includes("Long Buildup"))
    return "Price ↑, OI ↑ → New long positions are being added.";
  if (signal.includes("Short Buildup"))
    return "Price ↓, OI ↑ → New short positions are being added.";
  return "Signal based on price and OI movement.";
};
