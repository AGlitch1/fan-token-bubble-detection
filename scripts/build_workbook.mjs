import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(scriptDir, "..");
const finalDir = path.join(rootDir, "outputs");
const previewDir = path.join(finalDir, "previews");
const outputPath = path.join(finalDir, "FRAM_PHASE2_DATA_ANALYSIS.xlsx");

const COLORS = {
  navy: "#17365D",
  blue: "#2F75B5",
  paleBlue: "#D9EAF7",
  paleGreen: "#E2F0D9",
  green: "#548235",
  paleAmber: "#FFF2CC",
  amber: "#BF8F00",
  paleRed: "#FCE4D6",
  red: "#C00000",
  ink: "#1F2937",
  muted: "#5B6573",
  border: "#D9E1F2",
  white: "#FFFFFF",
};
const FONT = "Arial";

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.endsWith("\r") ? field.slice(0, -1) : field);
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows.filter((candidate) => candidate.some((value) => value !== ""));
}

const dateColumns = new Set([
  "date_utc",
  "first_valid_date",
  "last_expected_date",
  "snapshot_last_updated",
  "timestamp_utc",
]);

function coerceValue(header, value) {
  if (value === "") return null;
  if (value === "True" || value === "true") return true;
  if (value === "False" || value === "false") return false;
  if (dateColumns.has(header)) {
    const parsed = new Date(value.length === 10 ? `${value}T00:00:00Z` : value);
    return Number.isNaN(parsed.getTime()) ? value : parsed;
  }
  if (/^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(value)) return Number(value);
  return value;
}

async function readCsv(relativePath, selectedColumns = null) {
  const text = await fs.readFile(path.join(rootDir, relativePath), "utf8");
  const parsed = parseCsv(text);
  const allHeaders = parsed[0];
  const headers = selectedColumns ?? allHeaders;
  const indexes = headers.map((header) => {
    const index = allHeaders.indexOf(header);
    if (index < 0) throw new Error(`Missing column ${header} in ${relativePath}`);
    return index;
  });
  const rows = parsed.slice(1).map((sourceRow) =>
    indexes.map((index, columnIndex) => coerceValue(headers[columnIndex], sourceRow[index] ?? "")),
  );
  return { headers, rows };
}

function rangeAddress(rowCount, colCount, startRow = 0, startCol = 0) {
  function letters(column) {
    let result = "";
    let current = column + 1;
    while (current > 0) {
      const remainder = (current - 1) % 26;
      result = String.fromCharCode(65 + remainder) + result;
      current = Math.floor((current - 1) / 26);
    }
    return result;
  }
  return `${letters(startCol)}${startRow + 1}:${letters(startCol + colCount - 1)}${startRow + rowCount}`;
}

function writeRows(sheet, startRow, startCol, rows, chunkSize = 2000) {
  for (let offset = 0; offset < rows.length; offset += chunkSize) {
    const chunk = rows.slice(offset, offset + chunkSize);
    sheet.getRangeByIndexes(startRow + offset, startCol, chunk.length, chunk[0].length).values = chunk;
  }
}

function styleHeader(range) {
  range.format = {
    fill: COLORS.navy,
    font: { name: FONT, size: 10, bold: true, color: COLORS.white },
    wrapText: true,
    verticalAlignment: "center",
    horizontalAlignment: "center",
    borders: { preset: "all", style: "thin", color: COLORS.border },
  };
  range.format.rowHeight = 32;
}

function styleBody(range) {
  range.format.font = { name: FONT, size: 9, color: COLORS.ink };
  range.format.verticalAlignment = "center";
}

function setColumnWidth(sheet, columnIndex, width, rowCount) {
  sheet.getRangeByIndexes(0, columnIndex, Math.max(rowCount, 1), 1).format.columnWidth = width;
}

function applyNumberFormats(sheet, headers, rowCount) {
  if (!rowCount) return;
  const formats = {
    date_utc: "yyyy-mm-dd",
    first_valid_date: "yyyy-mm-dd",
    last_expected_date: "yyyy-mm-dd",
    timestamp_utc: "yyyy-mm-dd hh:mm",
    coverage_ratio: "0.0%",
    price_correlation: "0.000",
    return_correlation: "0.000",
    median_abs_relative_difference: "0.0%",
    p95_abs_relative_difference: "0.0%",
    open_usd: "0.000000",
    high_usd: "0.000000",
    low_usd: "0.000000",
    close_usd: "0.000000",
    adj_close_usd: "0.000000",
    volume_reported: "#,##0",
    snapshot_market_cap_usd: "$#,##0",
    snapshot_volume_usd: "$#,##0",
    log_price: "0.000000",
    log_volume: "0.000000",
    indexed_price_100: "0.00",
    return_pct: "0.00",
    rolling_volatility_30d_pct_annualized: "0.00",
  };
  headers.forEach((header, index) => {
    let format = formats[header];
    if (!format && (header.includes("return") || header.includes("volatility"))) format = "0.00";
    if (!format && header.includes("correlation")) format = "0.000";
    if (format) sheet.getRangeByIndexes(1, index, rowCount, 1).format.numberFormat = format;
  });
}

function addTableSheet(workbook, name, data, options = {}) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.tabColor = options.tabColor ?? COLORS.blue;
  sheet.getRangeByIndexes(0, 0, 1, data.headers.length).values = [data.headers];
  if (data.rows.length) writeRows(sheet, 1, 0, data.rows, options.chunkSize ?? 2000);
  const usedRows = data.rows.length + 1;
  const used = sheet.getRangeByIndexes(0, 0, usedRows, data.headers.length);
  styleBody(used);
  styleHeader(sheet.getRangeByIndexes(0, 0, 1, data.headers.length));
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(options.freezeColumns ?? 1);
  applyNumberFormats(sheet, data.headers, data.rows.length);
  data.headers.forEach((header, index) => {
    let width = 14;
    if (["asset_id", "coingecko_id"].includes(header)) width = 32;
    if (["asset_name", "screening_note", "quality_issues", "definition", "rule", "url", "use"].includes(header)) width = 34;
    if (["date_utc", "first_valid_date", "last_expected_date"].includes(header)) width = 13;
    if (header.includes("return") || header.includes("volatility") || header.includes("difference")) width = 22;
    if (header.includes("correlation") || header.endsWith("status")) width = 18;
    setColumnWidth(sheet, index, width, usedRows);
  });
  if (options.table !== false && data.rows.length <= 5000) {
    const table = sheet.tables.add(rangeAddress(usedRows, data.headers.length), true, options.tableName);
    table.style = "TableStyleMedium2";
    table.showBandedRows = true;
  }
  return sheet;
}

function applyStatusFormatting(sheet, headers, rowCount) {
  const statusIndex = headers.findIndex((header) => header.endsWith("status"));
  if (statusIndex < 0 || !rowCount) return;
  const status = sheet.getRangeByIndexes(1, statusIndex, rowCount, 1);
  status.conditionalFormats.add("containsText", {
    text: "PASS",
    format: { fill: COLORS.paleGreen, font: { color: COLORS.green, bold: true } },
  });
  status.conditionalFormats.add("containsText", {
    text: "REVIEW",
    format: { fill: COLORS.paleRed, font: { color: COLORS.red, bold: true } },
  });
}

function makeOverview(sheet, overview) {
  sheet.showGridLines = false;
  sheet.tabColor = COLORS.navy;
  sheet.getRange("A1:H2").merge();
  sheet.getRange("A1").values = [["FRAM Phase 2 — Data, Cleaning, Validation and Preliminary Analysis"]];
  sheet.getRange("A1:H2").format = {
    fill: COLORS.navy,
    font: { name: FONT, size: 20, bold: true, color: COLORS.white },
    verticalAlignment: "center",
    horizontalAlignment: "left",
  };
  sheet.getRange("A3:H3").merge();
  sheet.getRange("A3").values = [[`Daily UTC panel | ${overview.data_start_date} to ${overview.data_cutoff_date} | generated from reproducible Python outputs`]];
  sheet.getRange("A3:H3").format = { fill: COLORS.paleBlue, font: { name: FONT, size: 10, italic: true, color: COLORS.muted } };

  const cards = [
    ["A5:B5", "A6:B7", "Fan tokens", "=COUNTA(Sample!B2:B21)", "0"],
    ["C5:D5", "C6:D7", "Benchmarks", "=3", "0"],
    ["E5:F5", "E6:F7", "Valid price observations", "=SUM(Sample!I2:I21)", "#,##0"],
    ["G5:H5", "G6:H7", "Return observations", "=SUM(Sample!J2:J21)", "#,##0"],
    ["A9:B9", "A10:B11", "Median coverage", "=MEDIAN(Sample!L2:L21)", "0.0%"],
    ["C9:D9", "C10:D11", "Series passing QC", "=COUNTIF(Sample!T2:T21,\"PASS\")", "0"],
    ["E9:F9", "E10:F11", "Extreme-return flags", "=SUM(Sample!Q2:Q21)", "0"],
    ["G9:H9", "G10:H11", "Cross-source passes", "=COUNTIF(Validation!G2:G20,\"PASS\")", "0"],
  ];
  for (const [labelRange, valueRange, label, formula, numberFormat] of cards) {
    sheet.getRange(labelRange).merge();
    sheet.getRange(valueRange).merge();
    sheet.getRange(labelRange.split(":")[0]).values = [[label]];
    sheet.getRange(valueRange.split(":")[0]).formulas = [[formula]];
    sheet.getRange(labelRange).format = {
      fill: COLORS.blue,
      font: { name: FONT, size: 9, bold: true, color: COLORS.white },
      horizontalAlignment: "center",
      verticalAlignment: "center",
      borders: { preset: "all", style: "thin", color: COLORS.border },
    };
    sheet.getRange(valueRange).format = {
      fill: COLORS.white,
      font: { name: FONT, size: 18, bold: true, color: COLORS.navy },
      horizontalAlignment: "center",
      verticalAlignment: "center",
      numberFormat,
      borders: { preset: "all", style: "thin", color: COLORS.border },
    };
  }

  const sections = [
    ["A13:H13", "A14:H17", "Read this first", "This workbook is the review and reporting layer. The full reproducible inputs are the CSV files under data/. The sample is an unbalanced panel: each token enters on its first valid trading date. Missing values are never forward-filled, and flagged observations remain in the data unless a documented correction is justified."],
    ["A19:H19", "A20:H24", "Recommended sequence", "1. Review Sample and Quality.\n2. Investigate every REVIEW row in Validation and every extreme-return flag in Clean Data.\n3. Use Descriptive, Diagnostics, Correlation, and Charts for the Phase 2 preliminary analysis.\n4. Freeze the sample before running SADF/GSADF, BSADF date-stamping, change-point, and Bayesian models."],
    ["A26:H26", "A27:H30", "Interpretation safeguard", "The tables describe distributional shape, volatility clustering, and co-movement. They do not prove the existence or timing of speculative bubbles. Bubble claims require the formal econometric procedures specified in the methodology."],
  ];
  for (const [headingRange, bodyRange, heading, body] of sections) {
    sheet.getRange(headingRange).merge();
    sheet.getRange(bodyRange).merge();
    sheet.getRange(headingRange.split(":")[0]).values = [[heading]];
    sheet.getRange(bodyRange.split(":")[0]).values = [[body]];
    sheet.getRange(headingRange).format = { fill: COLORS.navy, font: { name: FONT, size: 11, bold: true, color: COLORS.white } };
    sheet.getRange(bodyRange).format = {
      fill: COLORS.white,
      font: { name: FONT, size: 10, color: COLORS.ink },
      wrapText: true,
      verticalAlignment: "top",
      borders: { preset: "all", style: "thin", color: COLORS.border },
    };
  }
  sheet.getRange("A1:H30").format.font.name = FONT;
  sheet.getRange("A1:H30").format.columnWidth = 15;
  sheet.getRange("A1:H30").format.rowHeight = 22;
  sheet.getRange("A1:H2").format.rowHeight = 32;
  sheet.getRange("A14:H17").format.rowHeight = 28;
  sheet.getRange("A20:H24").format.rowHeight = 26;
  sheet.getRange("A27:H30").format.rowHeight = 26;
  return sheet;
}

function makeCharts(sheet, indexed, volatility, descriptive) {
  sheet.showGridLines = false;
  sheet.tabColor = COLORS.green;
  sheet.getRange("A1:P1").merge();
  sheet.getRange("A1").values = [["Preliminary visual analysis"]];
  sheet.getRange("A1:P1").format = { fill: COLORS.navy, font: { name: FONT, size: 16, bold: true, color: COLORS.white } };

  const monthLabel = (value) => value instanceof Date ? value.toISOString().slice(0, 7) : String(value).slice(0, 7);
  const indexedRows = indexed.rows.map((row) => [monthLabel(row[0]), ...row.slice(1)]);
  const volatilityRows = volatility.rows.map((row) => [monthLabel(row[0]), ...row.slice(1)]);
  const medianVolIndex = descriptive.headers.indexOf("median_annualized_30d_volatility_pct");
  const symbolIndex = descriptive.headers.indexOf("symbol");
  const medianRows = descriptive.rows
    .map((row) => [row[symbolIndex], row[medianVolIndex]])
    .sort((a, b) => b[1] - a[1]);

  sheet.getRangeByIndexes(36, 0, 1, indexed.headers.length).values = [["month", ...indexed.headers.slice(1)]];
  writeRows(sheet, 37, 0, indexedRows);
  sheet.getRangeByIndexes(36, 8, 1, volatility.headers.length).values = [["month", ...volatility.headers.slice(1)]];
  writeRows(sheet, 37, 8, volatilityRows);
  sheet.getRange("Q37:R37").values = [["symbol", "median_annualized_30d_volatility_pct"]];
  writeRows(sheet, 37, 16, medianRows);
  styleHeader(sheet.getRangeByIndexes(36, 0, 1, indexed.headers.length));
  styleHeader(sheet.getRangeByIndexes(36, 8, 1, volatility.headers.length));
  styleHeader(sheet.getRange("Q37:R37"));
  sheet.getRangeByIndexes(37, 1, indexedRows.length, indexed.headers.length - 1).format.numberFormat = "0.00";
  sheet.getRangeByIndexes(37, 9, volatilityRows.length, volatility.headers.length - 1).format.numberFormat = "0.00";
  sheet.getRangeByIndexes(37, 17, medianRows.length, 1).format.numberFormat = "0.00";

  const indexedRange = sheet.getRangeByIndexes(36, 0, indexedRows.length + 1, indexed.headers.length);
  const indexedChart = sheet.charts.add("line", indexedRange);
  indexedChart.title = "Indexed fan-token prices (first observation = 100)";
  indexedChart.titleTextStyle.typeface = FONT;
  indexedChart.legend = { position: "top", textStyle: { typeface: FONT } };
  indexedChart.xAxis = { axisType: "textAxis", textStyle: { typeface: FONT, fontSize: 9 } };
  indexedChart.yAxis = { numberFormatCode: "0", numberFormatSourceLinked: false, textStyle: { typeface: FONT } };
  indexedChart.setPosition("A3", "H17");

  const volatilityRange = sheet.getRangeByIndexes(36, 8, volatilityRows.length + 1, volatility.headers.length);
  const volatilityChart = sheet.charts.add("line", volatilityRange);
  volatilityChart.title = "Annualized 30-day volatility — top five tokens";
  volatilityChart.titleTextStyle.typeface = FONT;
  volatilityChart.legend = { position: "top", textStyle: { typeface: FONT } };
  volatilityChart.xAxis = { axisType: "textAxis", textStyle: { typeface: FONT, fontSize: 9 } };
  volatilityChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: FONT } };
  volatilityChart.setPosition("I3", "P17");

  const medianRange = sheet.getRangeByIndexes(36, 16, medianRows.length + 1, 2);
  const medianChart = sheet.charts.add("bar", medianRange);
  medianChart.title = "Median annualized 30-day volatility by token";
  medianChart.titleTextStyle.typeface = FONT;
  medianChart.hasLegend = false;
  medianChart.xAxis = { axisType: "textAxis", textStyle: { typeface: FONT, fontSize: 9 } };
  medianChart.yAxis = { numberFormatCode: "0.0", numberFormatSourceLinked: false, textStyle: { typeface: FONT } };
  medianChart.setPosition("A19", "P34");
  return sheet;
}

await fs.mkdir(previewDir, { recursive: true });

const [
  sample,
  descriptive,
  benchmarkCorr,
  diagnostics,
  correlation,
  quality,
  validation,
  dictionary,
  cleaningLog,
  sources,
  extremeReturns,
  indexed,
  volatility,
  cleanData,
] = await Promise.all([
  readCsv("data/analysis/sample_overview.csv"),
  readCsv("data/analysis/descriptive_statistics.csv"),
  readCsv("data/analysis/benchmark_correlations.csv"),
  readCsv("data/analysis/autocorrelation_diagnostics.csv"),
  readCsv("data/analysis/return_correlation_matrix.csv"),
  readCsv("data/quality/data_quality_report.csv"),
  readCsv("data/quality/cross_source_validation.csv"),
  readCsv("data/quality/data_dictionary.csv"),
  readCsv("data/quality/cleaning_log.csv"),
  readCsv("data/quality/source_manifest.csv"),
  readCsv("data/quality/extreme_return_review.csv"),
  readCsv("data/analysis/monthly_indexed_price_top5.csv"),
  readCsv("data/analysis/monthly_volatility_top5.csv"),
  readCsv("data/clean/clean_observed_panel.csv", [
    "date_utc",
    "asset_id",
    "symbol",
    "asset_name",
    "asset_type",
    "sample_rank",
    "close_usd",
    "volume_reported",
    "log_price",
    "return_pct",
    "indexed_price_100",
    "rolling_volatility_30d_pct_annualized",
    "extreme_return_flag",
    "gap_days_since_prior_valid",
  ]),
]);
const overview = JSON.parse(await fs.readFile(path.join(rootDir, "data/analysis/analysis_overview.json"), "utf8"));

const workbook = Workbook.create();
const overviewSheet = workbook.worksheets.add("Overview");
const chartsSheet = workbook.worksheets.add("Charts");

const sampleSheet = addTableSheet(workbook, "Sample", sample, { tableName: "SampleTable", tabColor: COLORS.blue });
applyStatusFormatting(sampleSheet, sample.headers, sample.rows.length);
const coverageIndex = sample.headers.indexOf("coverage_ratio");
if (coverageIndex >= 0) {
  sampleSheet.getRangeByIndexes(1, coverageIndex, sample.rows.length, 1).conditionalFormats.add("colorScale", {
    colors: [COLORS.paleRed, COLORS.paleAmber, COLORS.paleGreen],
    thresholds: ["min", { type: "percentile", value: 50 }, "max"],
  });
}

const descriptiveSheet = addTableSheet(workbook, "Descriptive", descriptive, { tableName: "DescriptiveTable", tabColor: COLORS.green });
for (const header of ["median_annualized_30d_volatility_pct", "return_excess_kurtosis"]) {
  const index = descriptive.headers.indexOf(header);
  if (index >= 0) descriptiveSheet.getRangeByIndexes(1, index, descriptive.rows.length, 1).conditionalFormats.add("colorScale", {
    colors: [COLORS.paleGreen, COLORS.paleAmber, COLORS.paleRed],
    thresholds: ["min", { type: "percentile", value: 50 }, "max"],
  });
}

addTableSheet(workbook, "Benchmark Corr", benchmarkCorr, { tableName: "BenchmarkCorrelationTable" });
addTableSheet(workbook, "Diagnostics", diagnostics, { tableName: "DiagnosticsTable" });
const corrSheet = addTableSheet(workbook, "Correlation", correlation, { table: false, freezeColumns: 1 });
if (correlation.rows.length && correlation.headers.length > 1) {
  corrSheet.getRangeByIndexes(1, 1, correlation.rows.length, correlation.headers.length - 1).conditionalFormats.add("colorScale", {
    colors: ["#5B9BD5", COLORS.white, "#ED7D31"],
    thresholds: ["min", { type: "number", value: 0 }, "max"],
  });
  corrSheet.getRangeByIndexes(1, 1, correlation.rows.length, correlation.headers.length - 1).format.numberFormat = "0.00";
}

const qualitySheet = addTableSheet(workbook, "Quality", quality, { tableName: "QualityTable", tabColor: COLORS.amber });
applyStatusFormatting(qualitySheet, quality.headers, quality.rows.length);
const validationSheet = addTableSheet(workbook, "Validation", validation, { tableName: "ValidationTable", tabColor: COLORS.amber });
applyStatusFormatting(validationSheet, validation.headers, validation.rows.length);
addTableSheet(workbook, "Data Dictionary", dictionary, { tableName: "DictionaryTable" });
addTableSheet(workbook, "Cleaning Log", cleaningLog, { tableName: "CleaningLogTable" });
addTableSheet(workbook, "Sources", sources, { tableName: "SourcesTable" });
const extremeSheet = addTableSheet(workbook, "Extreme Returns", extremeReturns, { tableName: "ExtremeReturnReviewTable", tabColor: COLORS.red });
const reviewStatusIndex = extremeReturns.headers.indexOf("review_status");
if (reviewStatusIndex >= 0) {
  extremeSheet.getRangeByIndexes(1, reviewStatusIndex, extremeReturns.rows.length, 1).conditionalFormats.add("containsText", {
    text: "PENDING",
    format: { fill: COLORS.paleAmber, font: { color: COLORS.amber, bold: true } },
  });
}

const cleanSheet = addTableSheet(workbook, "Clean Data", cleanData, {
  table: false,
  tabColor: COLORS.green,
  freezeColumns: 3,
  chunkSize: 1500,
});
const extremeIndex = cleanData.headers.indexOf("extreme_return_flag");
if (extremeIndex >= 0) {
  cleanSheet.getRangeByIndexes(1, extremeIndex, cleanData.rows.length, 1).conditionalFormats.add("containsText", {
    text: "TRUE",
    format: { fill: COLORS.paleRed, font: { color: COLORS.red, bold: true } },
  });
}

// Populate the two leading sheets only after every cross-sheet formula target exists.
makeOverview(overviewSheet, overview);
makeCharts(chartsSheet, indexed, volatility, descriptive);

workbook.recalculate();

const inspection = await workbook.inspect({
  kind: "workbook,sheet,table,drawing",
  maxChars: 12000,
  tableMaxRows: 4,
  tableMaxCols: 6,
});
await fs.writeFile(path.join(finalDir, "workbook_inspection.txt"), inspection.ndjson ?? String(inspection));

const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 200 },
  maxChars: 12000,
});
await fs.writeFile(path.join(finalDir, "formula_error_scan.txt"), formulaErrors.ndjson ?? String(formulaErrors));

const previewSpecs = [
  ["Overview", "A1:H30"],
  ["Charts", "A1:P34"],
  ["Sample", "A1:Z21"],
  ["Descriptive", "A1:R21"],
  ["Benchmark Corr", "A1:E25"],
  ["Diagnostics", "A1:J21"],
  ["Correlation", "A1:X24"],
  ["Quality", "A1:U24"],
  ["Validation", "A1:G8"],
  ["Data Dictionary", "A1:D24"],
  ["Cleaning Log", "A1:B12"],
  ["Sources", "A1:C6"],
  ["Extreme Returns", "A1:J8"],
  ["Clean Data", "A1:N35"],
];
for (const [sheetName, range] of previewSpecs) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  const safeName = sheetName.toLowerCase().replaceAll(" ", "_");
  await fs.writeFile(path.join(previewDir, `${safeName}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
console.log(`Created ${outputPath}`);
