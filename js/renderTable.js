    fetch("../data/darvas_breakouts.json")
        .then((res) => res.json())
        .then((data) => {
            renderTable(data);
        });

    function renderTable(data) {
        const container = document.getElementById("tableContainer");

        if (!data.length) {
            container.innerHTML =
                "<p class='text-muted'>No breakout data available.</p>";
            return;
        }

        const table = document.createElement("table");
        table.className = "table table-bordered table-striped table-responsive";

        const thead = document.createElement("thead");
        thead.innerHTML = `
            <tr>
                <th>Symbol</th>
                <th>Close Price</th>
                <th>Box High</th>
                <th>Box Low</th>
                <th>Box Target</th>
                <th>Signal</th>
            </tr>
        `;

        const tbody = document.createElement("tbody");
        data.forEach((row) => {
            const boxHigh = parseFloat(row["Box High"]);
            const boxLow = parseFloat(row["Box Low"]);
            const boxTarget = (2 * boxHigh - boxLow).toFixed(2);

            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td data-label="Symbol">${row.Symbol}</td>
                <td data-label="Close Price">${row.Close}</td>
                <td data-label="Box High">${boxHigh}</td>
                <td data-label="Box Low">${boxLow}</td>
                <td data-label="Box Target">${boxTarget}</td>
                <td data-label="Signal" class="breakout">${row.Signal}</td>
            `;
            tbody.appendChild(tr);
        });

        table.appendChild(thead);
        table.appendChild(tbody);
        container.appendChild(table);
    }
