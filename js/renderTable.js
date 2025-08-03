async function renderTable() {
  const data = await fetchData();
  const tableContainer = document.getElementById('tableContainer');

  const rows = renderTableRows(data);
  const table = `
    <table class="table table-bordered table-striped">
      <thead>
        <tr>
          <th>Symbol</th>
          <th>Close</th>
          <th>Box High</th>
          <th>Signal</th>
        </tr>
      </thead>
      <tbody>${rows || '<tr><td colspan="4">No breakout</td></tr>'}</tbody>
    </table>
  `;

  tableContainer.innerHTML = table;
}
