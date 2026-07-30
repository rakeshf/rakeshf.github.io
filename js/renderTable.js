let darvasRows = [];

const setDarvasText = (id, value) => {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
};

const toFiniteNumber = (value) => {
    const number = parseFloat(value);
    return Number.isFinite(number) ? number : null;
};

const getDarvasTarget = (row) => {
    const direction = (row.Direction ?? "").toLowerCase();
    const boxHigh = toFiniteNumber(row["Box High"]);
    const boxLow = toFiniteNumber(row["Box Low"]);
    let target = row.Target !== undefined ? toFiniteNumber(row.Target) : null;

    if (target === null) {
        if (direction === "up" && boxHigh !== null && boxLow !== null) {
            target = 2 * boxHigh - boxLow;
        } else if (direction === "down" && boxLow !== null) {
            target = boxLow;
        }
    }

    return target;
};

const getDarvasPctChange = (row) => {
    const close = toFiniteNumber(row.Close);
    const target = getDarvasTarget(row);
    if (close === null || target === null || close === 0) return null;
    return ((target - close) / close) * 100;
};

const updateDarvasSummary = (data) => {
    const upCount = data.filter(row => (row.Direction ?? "").toLowerCase() === "up").length;
    const downCount = data.filter(row => (row.Direction ?? "").toLowerCase() === "down").length;
    const confirmedCount = data.filter(row => String(row.Signal ?? "").toLowerCase().includes("confirmed")).length;

    setDarvasText("darvasTotal", data.length);
    setDarvasText("darvasUpside", upCount);
    setDarvasText("darvasDownside", downCount);
    setDarvasText("darvasConfirmed", confirmedCount);
};

const getFilteredDarvasRows = () => {
    const query = (document.getElementById("darvasSearch")?.value || "").trim().toUpperCase();
    const direction = document.getElementById("darvasDirectionFilter")?.value || "All";
    const signal = document.getElementById("darvasSignalFilter")?.value || "All";
    const sort = document.getElementById("darvasSort")?.value || "symbol";

    const filtered = darvasRows.filter((row) => {
        const symbol = String(row.Symbol ?? "").toUpperCase();
        const rowDirection = String(row.Direction ?? "").toLowerCase();
        const rowSignal = String(row.Signal ?? "").toLowerCase();

        const matchesQuery = !query || symbol.includes(query);
        const matchesDirection = direction === "All" || rowDirection === direction;
        const matchesSignal =
            signal === "All" ||
            (signal === "confirmed" && rowSignal.includes("confirmed")) ||
            (signal === "pre" && rowSignal.includes("pre"));

        return matchesQuery && matchesDirection && matchesSignal;
    });

    return filtered.sort((a, b) => {
        if (sort === "pctDesc") return (getDarvasPctChange(b) ?? -Infinity) - (getDarvasPctChange(a) ?? -Infinity);
        if (sort === "closeDesc") return (toFiniteNumber(b.Close) ?? -Infinity) - (toFiniteNumber(a.Close) ?? -Infinity);
        if (sort === "targetDesc") return (getDarvasTarget(b) ?? -Infinity) - (getDarvasTarget(a) ?? -Infinity);
        return String(a.Symbol ?? "").localeCompare(String(b.Symbol ?? ""));
    });
};

const updateDarvasTable = () => {
    renderTable(getFilteredDarvasRows());
};

fetch("data/darvas_breakouts.json")
    .then((res) => {
        if (!res.ok) {
            throw new Error(`Failed to load Darvas data (${res.status})`);
        }
        return res.json();
    })
    .then((data) => {
        // Filter out rows where Signal is "No" or empty
        darvasRows = data.filter(row => 
            row.Signal && row.Signal.toLowerCase() !== "no"
        );
        updateDarvasSummary(darvasRows);
        updateDarvasTable();
    })
    .catch((err) => {
        const container = document.getElementById("tableContainer");
        if (container) {
            container.innerHTML = `<div class="alert alert-danger">Error loading Darvas Box data: ${err.message}</div>`;
        }
    });

function renderTable(data) {
    const container = document.getElementById("tableContainer");
    const summary = document.getElementById("tableSummary");
    container.innerHTML = "";

    if (!data.length) {
        container.innerHTML =
            "<div class='empty-state'><span class='material-icons-outlined'>search_off</span><strong>No Darvas signals match this view.</strong><span>Try changing search, direction, or signal filter.</span></div>";
        if (summary) {
            summary.textContent = "0 results";
        }
        return;
    }

    if (summary) {
        const upCount = data.filter(row => (row.Direction ?? "").toLowerCase() === "up").length;
        const downCount = data.filter(row => (row.Direction ?? "").toLowerCase() === "down").length;
        summary.textContent = `${data.length} result${data.length === 1 ? "" : "s"}: ${upCount} upside, ${downCount} downside.`;
    }

    const table = document.createElement("table");
    table.className = "table table-bordered table-striped table-hover screener-table";

    const thead = document.createElement("thead");
    thead.innerHTML = `
        <tr>
            <th>Symbol</th>
            <th>Close</th>
            <th>Box High</th>
            <th>Box Low</th>
            <th>Target</th>
            <th>% Change</th>
            <th>Signal</th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    const formatNumber = (value) => Number.isFinite(value) ? value.toFixed(2) : "N/A";

    data.forEach((row) => {
        const symbol = row.Symbol ?? "-";
        const close = toFiniteNumber(row.Close);
        const boxHigh = toFiniteNumber(row["Box High"]);
        const boxLow = toFiniteNumber(row["Box Low"]);
        const signal = row.Signal ?? "-";
        const direction = (row.Direction ?? "").toLowerCase();
        const target = getDarvasTarget(row);
        const pctChangeValue = getDarvasPctChange(row);
        const pctChange = pctChangeValue !== null ? pctChangeValue.toFixed(2) + "%" : "N/A";

        const tr = document.createElement("tr");

        // Color breakout/breakdown
        if (direction === "up") {
            tr.classList.add("table-success");
        } else if (direction === "down") {
            tr.classList.add("table-danger");
        }

        tr.innerHTML = `
            <td data-label="Symbol">${symbol}</td>
            <td data-label="Close">${formatNumber(close)}</td>
            <td data-label="Box High">${formatNumber(boxHigh)}</td>
            <td data-label="Box Low">${formatNumber(boxLow)}</td>
            <td data-label="Target">${formatNumber(target)}</td>
            <td data-label="% Change">${pctChange}</td>
            <td data-label="Signal">${signal}</td>
        `;
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

["darvasSearch", "darvasDirectionFilter", "darvasSignalFilter", "darvasSort"].forEach((id) => {
    const element = document.getElementById(id);
    if (element) {
        element.addEventListener("input", updateDarvasTable);
        element.addEventListener("change", updateDarvasTable);
    }
});
