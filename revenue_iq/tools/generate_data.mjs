import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Workbook } from "@oai/artifact-tool";

const currentDir = path.dirname(fileURLToPath(import.meta.url));
const outputPath = path.resolve(currentDir, "../data/revenue_data.csv");

function mulberry32(seed) {
  return function random() {
    let value = seed += 0x6D2B79F5;
    value = Math.imul(value ^ value >>> 15, value | 1);
    value ^= value + Math.imul(value ^ value >>> 7, value | 61);
    return ((value ^ value >>> 14) >>> 0) / 4294967296;
  };
}

const random = mulberry32(20260622);
const regions = [
  { name: "Sudeste", weight: 0.42 },
  { name: "Sul", weight: 0.29 },
  { name: "Nordeste", weight: 0.18 },
  { name: "Centro-Oeste", weight: 0.11 },
];
const channels = [
  { name: "Venda direta", weight: 0.43 },
  { name: "Parceiros", weight: 0.29 },
  { name: "Digital", weight: 0.18 },
  { name: "Outros", weight: 0.10 },
];
const segments = [
  { name: "Enterprise", weight: 0.47 },
  { name: "Mid-market", weight: 0.31 },
  { name: "SMB", weight: 0.22 },
];
const products = [
  { name: "Enterprise Pro", price: 62000, margin: 0.41, weight: 0.25 },
  { name: "Data Cloud", price: 48000, margin: 0.36, weight: 0.21 },
  { name: "Enterprise Plus", price: 71000, margin: 0.29, weight: 0.19 },
  { name: "Analytics Core", price: 35000, margin: 0.31, weight: 0.18 },
  { name: "Revenue Starter", price: 18000, margin: 0.44, weight: 0.17 },
];
const customers = [
  "Atlas Group", "Aurora Foods", "Nexo Energia", "Vértice Logística",
  "Lumina Saúde", "Orbe Retail", "Pulsar Tech", "Cobalto Indústria",
  "Prisma Serviços", "Horizonte Telecom", "Via Norte", "Mosaico Labs",
];
const seasonality = [0.90, 0.84, 0.73, 0.93, 0.96, 1.00, 0.98, 1.05, 1.11, 1.08, 1.14, 1.22];

function weightedPick(items) {
  const draw = random();
  let cumulative = 0;
  for (const item of items) {
    cumulative += item.weight;
    if (draw <= cumulative) return item;
  }
  return items.at(-1);
}

function csvEscape(value) {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const header = [
  "date", "order_id", "region", "channel", "segment", "product", "customer",
  "units", "unit_price", "discount_rate", "revenue", "cost", "gross_profit",
  "margin", "target_revenue",
];
const rows = [];
let orderNumber = 1;

for (let year = 2024; year <= 2025; year += 1) {
  for (let month = 0; month < 12; month += 1) {
    const annualGrowth = year === 2025 ? 1.124 : 1;
    const transactionCount = 92 + Math.round(random() * 20);

    for (let index = 0; index < transactionCount; index += 1) {
      const region = weightedPick(regions);
      const channel = weightedPick(channels);
      const segment = weightedPick(segments);
      const product = weightedPick(products);
      const customer = customers[Math.floor(random() * customers.length)];
      const day = 1 + Math.floor(random() * 27);
      const baseUnits = segment.name === "Enterprise" ? 1 : segment.name === "Mid-market" ? 2 : 3;
      let units = Math.max(1, Math.round(baseUnits * seasonality[month] * (0.7 + random() * 1.1)));
      let demandFactor = annualGrowth * (0.97 + random() * 0.08);

      if (year === 2025 && month === 2 && region.name === "Sul" && product.name === "Enterprise Plus") {
        demandFactor *= 0.58;
        units = Math.max(1, Math.round(units * 0.62));
      }

      const discountBase = channel.name === "Parceiros" ? 0.09 : channel.name === "Digital" ? 0.05 : 0.035;
      const discountRate = Math.min(0.18, discountBase + random() * 0.035);
      const unitPrice = product.price * (0.96 + random() * 0.08);
      const revenue = units * unitPrice * (1 - discountRate) * demandFactor;
      const marginPressure = channel.name === "Parceiros" ? 0.025 : 0;
      const margin = Math.max(0.18, product.margin - marginPressure + (random() - 0.5) * 0.025);
      const grossProfit = revenue * margin;
      const cost = revenue - grossProfit;
      const targetRevenue = revenue * (1.025 + random() * 0.035);
      const date = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

      rows.push([
        date,
        `ORD-${String(orderNumber).padStart(5, "0")}`,
        region.name,
        channel.name,
        segment.name,
        product.name,
        customer,
        units,
        unitPrice.toFixed(2),
        discountRate.toFixed(4),
        revenue.toFixed(2),
        cost.toFixed(2),
        grossProfit.toFixed(2),
        margin.toFixed(4),
        targetRevenue.toFixed(2),
      ]);
      orderNumber += 1;
    }
  }
}

const csv = [header, ...rows].map(row => row.map(csvEscape).join(",")).join("\n") + "\n";
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.writeFile(outputPath, csv, "utf8");

const workbook = await Workbook.fromCSV(csv, { sheetName: "RevenueData" });
const inspection = await workbook.inspect({
  kind: "table",
  range: "RevenueData!A1:O8",
  include: "values",
  tableMaxRows: 8,
  tableMaxCols: 15,
  maxChars: 4000,
});

console.log(JSON.stringify({ outputPath, rowCount: rows.length, inspection: inspection.ndjson }));
