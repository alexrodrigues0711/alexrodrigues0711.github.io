/* Market Intel Bancário — frontend vanilla (sem build) */

const charts = {};

const fmt = (value, suffix = '') => (value == null ? '—' : `${value}${suffix}`);

function destroyCharts() {
  Object.values(charts).forEach((c) => c.destroy());
  Object.keys(charts).forEach((k) => delete charts[k]);
}

function kpiCard({ title, value, subtitle, icon, colorClass }) {
  return `
    <div class="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex items-start space-x-4">
      <div class="p-3 rounded-lg ${colorClass} text-white text-xl">${icon}</div>
      <div>
        <p class="text-sm font-medium text-slate-500 mb-1">${title}</p>
        <h3 class="text-2xl font-bold text-slate-800">${value}</h3>
        <p class="text-xs text-slate-400 mt-1">${subtitle}</p>
      </div>
    </div>`;
}

function renderLoading() {
  document.getElementById('app').innerHTML = `
    <div class="min-h-screen flex items-center justify-center">
      <div class="text-center">
        <div class="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
        <p class="text-slate-600">Carregando dados do Banco Central...</p>
        <p class="text-xs text-slate-400 mt-2">Primeira carga pode levar ~30s</p>
      </div>
    </div>`;
}

function renderError(message) {
  document.getElementById('app').innerHTML = `
    <div class="min-h-screen flex items-center justify-center p-6">
      <div class="bg-white border border-red-100 rounded-xl p-8 max-w-lg shadow-sm text-center">
        <h2 class="text-lg font-bold text-red-700 mb-2">Erro ao carregar</h2>
        <p class="text-slate-600 text-sm mb-4">${message}</p>
        <button onclick="loadDashboard()" class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">Tentar novamente</button>
      </div>
    </div>`;
}

function topBy(banks, key) {
  return [...banks].filter((b) => b[key] != null).sort((a, b) => b[key] - a[key])[0];
}

function renderDashboard(meta, banks, history, activeTab = 'geral') {
  const topLucro = topBy(banks, 'lucro');
  const topRoe = topBy(banks, 'roe');
  const topBasileia = topBy(banks, 'basileia');

  const tabClass = (tab) =>
    `px-6 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
      activeTab === tab ? 'tab-active' : 'text-slate-600 hover:text-slate-900'
    }`;

  document.getElementById('app').innerHTML = `
    <div class="min-h-screen p-4 md:p-8">
      <div class="max-w-7xl mx-auto mb-8 flex flex-col md:flex-row justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-slate-900">Market Intel Bancário</h1>
          <p class="text-slate-500 mt-1">Dados públicos do BCB (IF.data) — conglomerado prudencial</p>
        </div>
        <div class="text-right">
          <div class="inline-flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span class="text-sm font-medium">Referência: ${meta.periodLabel}</span>
          </div>
          <p class="text-xs text-slate-400 mt-2">${meta.source}</p>
        </div>
      </div>

      <div class="max-w-7xl mx-auto mb-4">
        <div class="bg-amber-50 border border-amber-100 text-amber-900 text-sm rounded-lg px-4 py-3">
          MVP factual: lucro, ROE (calculado) e Basileia vêm do BCB. Clientes, inadimplência, Reclame Aqui e nota de app não estão nesta versão.
        </div>
      </div>

      <div class="max-w-7xl mx-auto mb-6">
        <div class="flex space-x-1 bg-slate-200/50 p-1 rounded-xl w-fit">
          <button id="tab-geral" class="${tabClass('geral')}">Visão Geral</button>
          <button id="tab-financeiro" class="${tabClass('financeiro')}">Saúde Financeira</button>
        </div>
      </div>

      <div id="tab-content" class="max-w-7xl mx-auto"></div>
    </div>`;

  document.getElementById('tab-geral').onclick = () => renderDashboard(meta, banks, history, 'geral');
  document.getElementById('tab-financeiro').onclick = () => renderDashboard(meta, banks, history, 'financeiro');

  const content = document.getElementById('tab-content');
  destroyCharts();

  if (activeTab === 'geral') {
    content.innerHTML = `
      <div class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          ${kpiCard({ title: 'Maior Lucro (Tri)', value: `R$ ${fmt(topLucro?.lucro)} Bi`, subtitle: `${topLucro?.name || '—'} (${meta.periodLabel})`, icon: '💰', colorClass: 'bg-yellow-500' })}
          ${kpiCard({ title: 'Melhor ROE (anualizado)', value: fmt(topRoe?.roe, '%'), subtitle: `${topRoe?.name || '—'} — lucro/PL × 4`, icon: '📈', colorClass: 'bg-purple-600' })}
          ${kpiCard({ title: 'Maior Índice Basileia', value: fmt(topBasileia?.basileia, '%'), subtitle: topBasileia?.name || '—', icon: '🛡️', colorClass: 'bg-emerald-500' })}
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 class="text-lg font-bold mb-4">Participação no Lucro Trimestral</h3>
            <div class="h-80"><canvas id="pie-chart"></canvas></div>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 class="text-lg font-bold mb-4">Lucro (R$ Bi) vs ROE (%)</h3>
            <div class="h-80"><canvas id="bar-chart"></canvas></div>
          </div>
        </div>
      </div>`;
    renderPieChart(banks);
    renderBarChart(banks);
  } else {
    const basileiaRows = [...banks]
      .sort((a, b) => (b.basileia || 0) - (a.basileia || 0))
      .map(
        (b) => `
        <div>
          <div class="flex justify-between text-sm mb-1">
            <span class="font-medium">${b.name}</span>
            <span class="font-bold">${fmt(b.basileia, '%')}</span>
          </div>
          <div class="w-full bg-slate-100 rounded-full h-2">
            <div class="h-2 rounded-full" style="width:${Math.min(((b.basileia || 0) / 20) * 100, 100)}%;background:${(b.basileia || 0) < 12 ? '#ef4444' : b.color}"></div>
          </div>
        </div>`
      )
      .join('');

    const tableRows = banks
      .map(
        (b) => `
        <tr class="border-b border-slate-50">
          <td class="py-2 font-medium">${b.name}</td>
          <td class="py-2">${fmt(b.lucro)} Bi</td>
          <td class="py-2">${fmt(b.roe, '%')}</td>
          <td class="py-2">${fmt(b.basileia, '%')}</td>
        </tr>`
      )
      .join('');

    content.innerHTML = `
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100 lg:col-span-2">
          <h3 class="text-lg font-bold mb-4">Evolução Histórica — Lucro Líquido (R$ Bi)</h3>
          <div class="h-96"><canvas id="line-chart"></canvas></div>
        </div>
        <div class="space-y-6">
          <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 class="text-lg font-bold mb-1">Índice de Basileia</h3>
            <p class="text-xs text-slate-400 mb-4">Mínimo regulatório: 11%</p>
            <div class="space-y-4">${basileiaRows}</div>
          </div>
          <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 class="text-lg font-bold mb-4">Tabela — ${meta.periodLabel}</h3>
            <table class="w-full text-sm">
              <thead><tr class="text-left text-slate-500 border-b"><th class="pb-2">Banco</th><th>Lucro</th><th>ROE</th><th>Basileia</th></tr></thead>
              <tbody>${tableRows}</tbody>
            </table>
          </div>
        </div>
      </div>`;
    renderLineChart(banks, history);
  }
}

function renderPieChart(banks) {
  const data = banks.filter((b) => b.lucro != null);
  const ctx = document.getElementById('pie-chart');
  if (!ctx) return;
  charts.pie = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map((b) => b.name),
      datasets: [{ data: data.map((b) => b.lucro), backgroundColor: data.map((b) => b.color) }],
    },
    options: { maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } },
  });
}

function renderBarChart(banks) {
  const ctx = document.getElementById('bar-chart');
  if (!ctx) return;
  charts.bar = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: banks.map((b) => b.name),
      datasets: [
        {
          label: 'Lucro (R$ Bi)',
          data: banks.map((b) => b.lucro),
          backgroundColor: banks.map((b) => b.color),
          yAxisID: 'y',
        },
        {
          label: 'ROE (%)',
          data: banks.map((b) => b.roe),
          backgroundColor: 'rgba(14, 165, 233, 0.35)',
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      scales: {
        y: { type: 'linear', position: 'left', title: { display: true, text: 'R$ Bi' } },
        y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'ROE %' } },
      },
    },
  });
}

function renderLineChart(banks, history) {
  const ctx = document.getElementById('line-chart');
  if (!ctx) return;
  charts.line = new Chart(ctx, {
    type: 'line',
    data: {
      labels: history.map((h) => h.period),
      datasets: banks.map((b) => ({
        label: b.name,
        data: history.map((h) => h[b.name] ?? null),
        borderColor: b.color,
        backgroundColor: b.color,
        tension: 0.3,
        spanGaps: true,
      })),
    },
    options: { maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } },
  });
}

async function loadDashboard() {
  renderLoading();
  const meta = {
    period: 202603,
    periodLabel: '1T26',
    source: 'Banco Central do Brasil \u2014 IF.data (OData)',
  };
  const banks = [
    { id: 'itau', name: 'Ita\u00fa', color: '#EC7000', lucro: 12.15, roe: 20.91, basileia: 14.77 },
    { id: 'bradesco', name: 'Bradesco', color: '#CC092F', lucro: 5.04, roe: 11.38, basileia: 14.9 },
    { id: 'bb', name: 'BB', color: '#F8D117', lucro: 3.21, roe: 6.87, basileia: 14.23 },
    { id: 'santander', name: 'Santander', color: '#EC0000', lucro: 4.08, roe: 15.25, basileia: 15.15 },
    { id: 'nubank', name: 'Nubank', color: '#8A05BE', lucro: 1.42, roe: 26.88, basileia: 15.1 },
  ];
  const history = [
    ['1T23', 8.35, 4.29, 8.34, 2.28, 0.8], ['2T23', 8.71, 4.53, 8.51, 2.27, 0.9],
    ['3T23', 8.04, 4.63, 8.61, 2.83, 1.39], ['4T23', 9.37, 1.71, 9.27, 2.28, 1.64],
    ['1T24', 9.82, 4.22, 9.03, 3.07, 1.77], ['2T24', 10.14, 4.72, 9.14, 3.29, 2.3],
    ['3T24', 10.45, 5.23, 9.08, 3.42, 2.5], ['4T24', 10.52, 4.94, 8.86, 3.67, 2.94],
    ['1T25', 11.13, 5.83, 6.81, 3.96, 2.87], ['2T25', 11.5, 6.05, 3.23, 3.86, 3.1],
    ['3T25', 11.77, 6.18, 3.11, 4.33, 2.89], ['4T25', 12.32, 6.53, 5.08, 4.25, 3.84],
    ['1T26', 12.15, 5.04, 3.21, 4.08, 1.42],
  ].map(([period, itau, bradesco, bb, santander, nubank]) => ({
    period, 'Ita\u00fa': itau, Bradesco: bradesco, BB: bb, Santander: santander, Nubank: nubank,
  }));
  renderDashboard(meta, banks, history, 'geral');
}

loadDashboard();
