    fetch('../data/golden_cross.json')
      .then(res => res.json())
      .then(data => {
        const tbody = document.querySelector('#gc-table tbody');
        const updated = document.getElementById('updated-date');
        data.forEach(row => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${row.Symbol}</td>
            <td>${row["Golden Cross Date"]}</td>
            <td>${row["Last Price"]}</td>
          `;
          tbody.appendChild(tr);
        });

        const today = new Date();
        updated.textContent = `Updated: ${today.toLocaleDateString()} ${today.toLocaleTimeString()}`;
      })
      .catch(err => {
        document.querySelector('#gc-table').innerHTML = '<tr><td colspan="3">Error loading JSON data</td></tr>';
        console.error('Failed to load JSON:', err);
      });