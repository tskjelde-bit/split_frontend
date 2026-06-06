export const ADMIN_HTML = `<!DOCTYPE html>
<html lang="no">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex">
  <title>Boligvelger — Admin</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Georgia, 'Times New Roman', serif;
      background: #FBFAF6;
      color: #1E3D2B;
      padding: 2rem;
      max-width: 860px;
      margin: 0 auto;
    }
    h1 { font-size: 1.5rem; margin-bottom: 1rem; }
    .password-row {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      margin-bottom: 1.5rem;
    }
    .password-row label { font-size: 0.9rem; }
    .password-row input {
      font-family: inherit;
      border: 1px solid #1E3D2B;
      background: #FBFAF6;
      color: #1E3D2B;
      padding: 0.3rem 0.6rem;
      font-size: 0.9rem;
      width: 220px;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      font-size: 0.9rem;
    }
    th {
      text-align: left;
      border-bottom: 2px solid #1E3D2B;
      padding: 0.4rem 0.6rem;
      font-weight: bold;
    }
    td {
      border-bottom: 1px solid #c8d5cc;
      padding: 0.4rem 0.6rem;
    }
    .btn-group { display: flex; gap: 0.4rem; }
    button {
      font-family: Georgia, serif;
      font-size: 0.8rem;
      padding: 0.25rem 0.7rem;
      border: 1px solid #1E3D2B;
      background: #FBFAF6;
      color: #1E3D2B;
      cursor: pointer;
    }
    button.active { background: #1E3D2B; color: #FBFAF6; }
    button:hover:not(.active) { background: #e8ece7; }
    #error {
      margin-top: 1rem;
      color: #c0392b;
      font-size: 0.9rem;
      min-height: 1.2em;
    }
    .floor-heading td {
      background: #edf2ee;
      font-weight: bold;
      padding-top: 0.6rem;
    }
  </style>
</head>
<body>
  <h1>Boligvelger — Statusadmin</h1>
  <div class="password-row">
    <label for="pw">Passord:</label>
    <input type="password" id="pw" autocomplete="current-password">
  </div>
  <table id="tbl">
    <thead>
      <tr>
        <th>Enhet</th>
        <th>Status</th>
        <th>Endre</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="error"></div>

  <script>
    const UNITS = [
      'H0101','H0102','H0103','H0104','H0105',
      'H0201','H0202','H0203','H0204','H0205',
      'H0301','H0302','H0303','H0304','H0305','H0306',
    ];
    const STATUSES = ['ledig', 'reservert', 'solgt'];
    const FLOOR_LABELS = { H0101: '1. etasje', H0201: '2. etasje', H0301: '3. etasje' };

    const pwEl = document.getElementById('pw');
    const tbodyEl = document.getElementById('tbody');
    const errorEl = document.getElementById('error');

    // Persist password across page reload within session
    const saved = sessionStorage.getItem('admin-pw');
    if (saved) pwEl.value = saved;
    pwEl.addEventListener('input', () => sessionStorage.setItem('admin-pw', pwEl.value));

    let currentStatus = {};

    function render() {
      tbodyEl.innerHTML = '';
      UNITS.forEach(unit => {
        if (FLOOR_LABELS[unit]) {
          const hr = document.createElement('tr');
          hr.className = 'floor-heading';
          hr.innerHTML = \`<td colspan="3">\${FLOOR_LABELS[unit]}</td>\`;
          tbodyEl.appendChild(hr);
        }
        const status = currentStatus[unit] || 'ledig';
        const tr = document.createElement('tr');
        const btnCells = STATUSES.map(s => {
          const active = s === status ? ' class="active"' : '';
          return \`<button\${active} data-unit="\${unit}" data-status="\${s}">\${s}</button>\`;
        }).join('');
        tr.innerHTML = \`
          <td>\${unit}</td>
          <td>\${status}</td>
          <td><div class="btn-group">\${btnCells}</div></td>
        \`;
        tbodyEl.appendChild(tr);
      });
    }

    async function load() {
      try {
        const res = await fetch('/api/status');
        currentStatus = await res.json();
        render();
      } catch (e) {
        errorEl.textContent = 'Kunne ikke laste status: ' + e.message;
      }
    }

    tbodyEl.addEventListener('click', async (e) => {
      const btn = e.target.closest('button[data-unit]');
      if (!btn) return;
      const unit = btn.dataset.unit;
      const status = btn.dataset.status;
      const pw = pwEl.value;
      errorEl.textContent = '';
      try {
        const res = await fetch('/api/status', {
          method: 'POST',
          headers: {
            'content-type': 'application/json',
            'x-admin-password': pw,
          },
          body: JSON.stringify({ unit, status }),
        });
        if (res.status === 401) {
          errorEl.textContent = 'Feil passord (401).';
          return;
        }
        if (!res.ok) {
          const t = await res.text();
          errorEl.textContent = 'Feil: ' + t;
          return;
        }
        currentStatus = await res.json();
        render();
      } catch (e) {
        errorEl.textContent = 'Nettverksfeil: ' + e.message;
      }
    });

    load();
  </script>
</body>
</html>`;
