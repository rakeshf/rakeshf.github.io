let goldenRows = [];

const buildGoldenDataUrl = (path) => {
  const url = new URL(path, window.location.href);
  url.searchParams.set("t", Date.now());
  return url.toString();
};

const setGoldenText = (id, value) => {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
};

const toGoldenNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
};

const getGoldenValue = (id, fallback) => {
  const element = document.getElementById(id);
  return element ? element.value : fallback;
};

const goldenFallback = (value, fallback) => value === null ? fallback : value;

const formatGoldenPrice = (value) => {
  const number = toGoldenNumber(value);
  return number !== null ? `₹${number.toFixed(2)}` : "N/A";
};

const updateGoldenSummary = (data) => {
  const dates = data.map((row) => row["Golden Cross Date"]).filter(Boolean).sort();
  const prices = data.map((row) => toGoldenNumber(row["Last Price"])).filter((value) => value !== null);

  setGoldenText("goldenTotal", data.length);
  setGoldenText("goldenLatestDate", dates.length ? dates[dates.length - 1] : "N/A");
  setGoldenText("goldenHighestPrice", prices.length ? formatGoldenPrice(Math.max(...prices)) : "N/A");
};

const getFilteredGoldenRows = () => {
  const query = (getGoldenValue("goldenSearch", "") || "").trim().toUpperCase();
  const sort = getGoldenValue("goldenSort", "dateDesc") || "dateDesc";
  const filtered = goldenRows.filter((row) =>
    !query || String(row.Symbol || "").toUpperCase().includes(query)
  );

  return filtered.sort((a, b) => {
    if (sort === "symbol") return String(a.Symbol || "").localeCompare(String(b.Symbol || ""));
    if (sort === "priceDesc") return goldenFallback(toGoldenNumber(b["Last Price"]), -Infinity) - goldenFallback(toGoldenNumber(a["Last Price"]), -Infinity);
    if (sort === "priceAsc") return goldenFallback(toGoldenNumber(a["Last Price"]), Infinity) - goldenFallback(toGoldenNumber(b["Last Price"]), Infinity);
    return String(b["Golden Cross Date"] || "").localeCompare(String(a["Golden Cross Date"] || ""));
  });
};

const renderGoldenRows = (data) => {
  const tbody = document.getElementById("results");
  if (!tbody) return;

  setGoldenText("goldenResultCount", `${data.length} result${data.length === 1 ? "" : "s"}`);

  if (!Array.isArray(data) || data.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3">No Golden Cross signals match this view.</td></tr>';
    return;
  }

  tbody.innerHTML = "";
  data.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td data-label="Symbol"><strong>${row.Symbol || "N/A"}</strong></td>
      <td data-label="Golden Cross Date" class="golden-cross-date">${row["Golden Cross Date"] || "N/A"}</td>
      <td data-label="Last Price">${formatGoldenPrice(row["Last Price"])}</td>
    `;
    tbody.appendChild(tr);
  });
};

const updateGoldenTable = () => renderGoldenRows(getFilteredGoldenRows());

["goldenSearch", "goldenSort"].forEach((id) => {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener("input", updateGoldenTable);
    element.addEventListener("change", updateGoldenTable);
  }
});

fetch(buildGoldenDataUrl("data/golden_cross.json"))
  .then((res) => {
    if (!res.ok) throw new Error(`Failed to load Golden Cross data (${res.status})`);
    return res.json();
  })
  .then((data) => {
    goldenRows = Array.isArray(data) ? data : [];
    updateGoldenSummary(goldenRows);
    updateGoldenTable();
  })
  .catch((err) => {
    const tbody = document.getElementById("results");
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="3">Failed to load data: ${err.message}</td></tr>`;
    }
    console.error(err);
  });
