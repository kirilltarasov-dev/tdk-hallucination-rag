/** Build the unlabeled EXP-031 reviewer workbook from blinded JSONL pairs. */

import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const source = "results/annotation/exp031_blinded_pairs.jsonl";
const outputPath = "deliverables/EXP031_Blinded_Annotation_Template.xlsx";
const text = await fs.readFile(source, "utf8");
const pairs = text.trim().split("\n").map((line) => JSON.parse(line));
if (pairs.length !== 100 || new Set(pairs.map((p) => p.case_id)).size !== 100) {
  throw new Error("Expected 100 unique blinded question pairs");
}
try {
  await fs.access(outputPath);
  throw new Error(`Refusing to overwrite ${outputPath}`);
} catch (error) {
  if (error.code !== "ENOENT") throw error;
}

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Responses");
sheet.getRange("A1").values = [["EXP-031 | Blinded semantic annotation"]];
sheet.getRange("A2").values = [[
  "Label all 200 responses independently. Read full context and response in the formula bar; use the codebook in docs/exp031_semantic_annotation_protocol.md."
]];
sheet.getRange("A3").values = [[
  "Source: frozen EXP-029 raw outputs; RGB benchmark answer is a reference, not independent ground truth. Do not open the blind key before labels are locked."
]];
const headers = [
  "Case ID", "Blind arm", "Question", "RGB reference answer",
  "Delivered context", "Model response", "False assertion",
  "Answer status", "Evidence status", "Context answerable",
  "Conflict acknowledged", "Rationale / decisive spans",
  "External fact-check source", "Reviewer ID", "Review date",
];
sheet.getRange("A5:O5").values = [headers];
const data = pairs.flatMap((pair) => ["A", "B"].map((arm) => [
  pair.case_id, arm, pair.question,
  typeof pair.benchmark_reference_answer === "string"
    ? pair.benchmark_reference_answer
    : JSON.stringify(pair.benchmark_reference_answer),
  pair[`context_${arm}`], pair[`response_${arm}`],
  "", "", "", "", "", "", "", "", "",
]));
sheet.getRange("A6:O205").values = data;

sheet.getRange("A1:O205").format.font = { name: "Arial", size: 10, color: "#1F2937" };
sheet.getRange("A1").format.font = { name: "Arial", size: 16, bold: true, color: "#123B5D" };
sheet.getRange("A2:O3").format.rowHeight = 27;
sheet.getRange("A5:O5").format = {
  fill: "#123B5D",
  font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
  rowHeight: 34,
  wrapText: true,
};
sheet.getRange("A6:O205").format.rowHeight = 60;
sheet.getRange("A6:O205").format.verticalAlignment = "top";
sheet.getRange("C6:F205").format.wrapText = true;
sheet.getRange("L6:M205").format.wrapText = true;
sheet.getRange("G6:O205").format.fill = "#FFF6D5";
sheet.getRange("A:A").format.columnWidth = 15;
sheet.getRange("B:B").format.columnWidth = 10;
sheet.getRange("C:C").format.columnWidth = 37;
sheet.getRange("D:D").format.columnWidth = 23;
sheet.getRange("E:E").format.columnWidth = 68;
sheet.getRange("F:F").format.columnWidth = 58;
sheet.getRange("G:K").format.columnWidth = 19;
sheet.getRange("L:L").format.columnWidth = 42;
sheet.getRange("M:M").format.columnWidth = 36;
sheet.getRange("N:O").format.columnWidth = 18;
sheet.getRange("G6:G205").dataValidation = {
  rule: { type: "list", values: ["YES", "NO", "UNCLEAR"] },
};
sheet.getRange("H6:H205").dataValidation = {
  rule: { type: "list", values: ["CORRECT", "INCORRECT", "ABSTAINS", "MIXED", "UNCLEAR"] },
};
sheet.getRange("I6:I205").dataValidation = {
  rule: { type: "list", values: ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED", "MIXED", "NO_CLAIM", "UNCLEAR"] },
};
sheet.getRange("J6:J205").dataValidation = {
  rule: { type: "list", values: ["YES", "NO", "UNCLEAR"] },
};
sheet.getRange("K6:K205").dataValidation = {
  rule: { type: "list", values: ["YES", "NO", "NOT_APPLICABLE", "UNCLEAR"] },
};
sheet.freezePanes.freezeRows(5);
sheet.freezePanes.freezeColumns(2);

workbook.recalculate();
const checked = await workbook.inspect({
  kind: "region", sheetId: "Responses", range: "A5:D8", maxChars: 1200,
});
console.log(checked.ndjson);
const preview = await workbook.render({ sheetName: "Responses", range: "A1:D8", scale: 1.5, format: "png" });
await fs.writeFile("/private/tmp/exp031_annotation_preview.png", new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Wrote ${data.length} unlabeled responses to ${outputPath}`);
