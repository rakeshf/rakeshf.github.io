fetch("data/darvas_breakouts.json")
    .then((res) => {
        if (!res.ok) {
            throw new Error(`Failed to load Darvas data (${res.status})`);
        }
        return res.json();
    })
    .then((data) => {
        // Filter out rows where Signal is "No" or empty
        const filtered = data.filter(row => 
            row.Signal && row.Signal.toLowerCase() !== "no"
        );
        renderTable(filtered);
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
            "<div class='alert alert-secondary'>No breakout/breakdown data available.</div>";
        if (summary) {
            summary.textContent = "No active signals found.";
        }
        return;
    }

    if (summary) {
        const upCount = data.filter(row => (row.Direction ?? "").toLowerCase() === "up").length;
        const downCount = data.filter(row => (row.Direction ?? "").toLowerCase() === "down").length;
        summary.textContent = `${data.length} active signals: ${upCount} upside, ${downCount} downside.`;
    }

    const table = document.createElement("table");
    table.className = "table table-bordered table-striped table-hover";

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
        const close = parseFloat(row.Close);
        const boxHigh = parseFloat(row["Box High"]);
        const boxLow = parseFloat(row["Box Low"]);
        const signal = row.Signal ?? "-";
        const direction = (row.Direction ?? "").toLowerCase();

        // Use target from backend if available, else fallback
        let target = row.Target !== undefined ? parseFloat(row.Target) : null;

        // Fallback logic
        if (target === null || isNaN(target)) {
            if (direction === "up") {
                target = 2 * boxHigh - boxLow; // breakout formula
            } else if (direction === "down") {
                target = boxLow; // simple breakdown fallback
            }
        }

        // Calculate % change
        let pctChange = "N/A";
        if (Number.isFinite(close) && Number.isFinite(target) && close !== 0) {
            const change = ((target - close) / close) * 100;
            pctChange = change.toFixed(2) + "%";
        }

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
