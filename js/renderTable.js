fetch("../data/darvas_breakouts.json")
    .then((res) => res.json())
    .then((data) => {
        // Filter out rows where Signal is "No" or empty
        const filtered = data.filter(row => 
            row.Signal && row.Signal.toLowerCase() !== "no"
        );
        renderTable(filtered);
    });

function renderTable(data) {
    const container = document.getElementById("tableContainer");
    container.innerHTML = "";

    if (!data.length) {
        container.innerHTML =
            "<p class='text-muted'>No breakout/breakdown data available.</p>";
        return;
    }

    const table = document.createElement("table");
    table.className = "table table-bordered table-striped table-responsive";

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
        let pctChange = "";
        if (close && target) {
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
            <td data-label="Close">${close.toFixed(2)}</td>
            <td data-label="Box High">${boxHigh.toFixed(2)}</td>
            <td data-label="Box Low">${boxLow.toFixed(2)}</td>
            <td data-label="Target">${target.toFixed(2)}</td>
            <td data-label="% Change">${pctChange}</td>
            <td data-label="Signal">${signal}</td>
        `;
        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}
