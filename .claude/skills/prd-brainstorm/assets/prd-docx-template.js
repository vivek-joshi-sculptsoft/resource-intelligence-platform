/**
 * PRD Word Document Template
 * 
 * This is a REFERENCE template — not meant to be run directly.
 * When generating a PRD as a .docx, adapt this structure:
 * 1. Keep the styling, helpers, and color palette as-is
 * 2. Replace the CONTENT SECTIONS with sections relevant to the specific PRD
 * 3. Module names, section headers, and content are all dynamic
 * 
 * Install: npm install -g docx
 * Run: node your-prd-script.js
 */

const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak, TabStopType, TabStopPosition
} = require("docx");

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// COLOR PALETTE — Consistent across all PRDs
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const C = {
  primary: "1B3A5C",     // Navy — headings, table headers
  accent: "2E75B6",      // Blue — sub-headings, accents
  light: "E8F0F8",       // Light blue — info callout background
  mid: "D0E2F0",         // Mid blue — accents
  dark: "0D2137",        // Dark navy — emphasis
  gray: "666666",        // Gray — meta text
  lightGray: "F5F5F5",   // Alternating row bg
  border: "BDD0E5",      // Table borders
  white: "FFFFFF",
  black: "000000",
  green: "E8F5E9",       // Success callout bg
  yellow: "FFF8E1",      // Warning callout bg
  red: "FFEBEE",         // Error callout bg
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// REUSABLE HELPERS — Use these to build any section
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const border = { style: BorderStyle.SINGLE, size: 1, color: C.border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: C.white };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const cellMargins = { top: 60, bottom: 60, left: 120, right: 120 };
const TABLE_WIDTH = 9360; // US Letter with 1" margins

function spacer(size = 120) {
  return new Paragraph({ spacing: { after: size } });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun(text)],
    spacing: { before: 360, after: 200 },
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun(text)],
    spacing: { before: 280, after: 160 },
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [new TextRun(text)],
    spacing: { before: 200, after: 120 },
  });
}

// Standard paragraph
function para(text, opts = {}) {
  const runs = [];
  if (typeof text === "string") {
    runs.push(new TextRun({ text, size: 22, font: "Arial", color: opts.color || "333333", ...opts }));
  } else {
    // Array of TextRun configs: [{ text: "bold part", bold: true }, { text: " normal part" }]
    text.forEach(t => runs.push(new TextRun({ size: 22, font: "Arial", color: "333333", ...t })));
  }
  return new Paragraph({
    children: runs,
    spacing: { after: opts.after || 120, before: opts.before || 0, line: 276 },
    alignment: opts.alignment || AlignmentType.LEFT,
  });
}

// Table header cell (dark navy background, white text)
function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: C.primary, type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, size: 20, font: "Arial", color: C.white })],
      spacing: { after: 0 },
    })],
  });
}

// Table data cell
function dataCell(content, width, opts = {}) {
  const children = typeof content === "string"
    ? [new Paragraph({
        children: [new TextRun({ text: content, size: 20, font: "Arial", color: "333333", ...opts.runOpts })],
        spacing: { after: 0 },
        alignment: opts.alignment || AlignmentType.LEFT,
      })]
    : Array.isArray(content) ? content : [content];
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: opts.fill || C.white, type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children,
  });
}

/**
 * Create a table with headers and rows
 * @param {string[]} headers - Column header texts
 * @param {string[][]} rows - Array of row data (each row is array of cell texts)
 * @param {number[]} colWidths - Column widths in DXA (must sum to TABLE_WIDTH or desired width)
 */
function simpleTable(headers, rows, colWidths) {
  const totalW = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) }),
      ...rows.map((row, ri) =>
        new TableRow({
          children: row.map((cell, ci) =>
            dataCell(cell, colWidths[ci], { fill: ri % 2 === 0 ? C.white : C.lightGray })
          ),
        })
      ),
    ],
  });
}

/**
 * Callout box — left-border accent with colored background
 * @param {string} label - Bold label (e.g., "Key Distinction", "Warning")
 * @param {string} text - Body text
 * @param {string} fillColor - Background color from C palette (C.light, C.yellow, C.green)
 */
function calloutBox(label, text, fillColor) {
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: [TABLE_WIDTH],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            borders: { top: border, bottom: border, right: border, left: { style: BorderStyle.SINGLE, size: 12, color: C.accent } },
            width: { size: TABLE_WIDTH, type: WidthType.DXA },
            shading: { fill: fillColor, type: ShadingType.CLEAR },
            margins: { top: 100, bottom: 100, left: 200, right: 200 },
            children: [
              new Paragraph({
                children: [new TextRun({ text: label, bold: true, size: 20, font: "Arial", color: C.primary })],
                spacing: { after: 60 },
              }),
              new Paragraph({
                children: [new TextRun({ text, size: 20, font: "Arial", color: "444444" })],
                spacing: { after: 0 },
              }),
            ],
          }),
        ],
      }),
    ],
  });
}

// Bullet list item
function bulletItem(text, bulletRef = "bullets") {
  return new Paragraph({
    numbering: { reference: bulletRef, level: 0 },
    children: [new TextRun({ text, size: 22, font: "Arial", color: "333333" })],
    spacing: { after: 80 },
  });
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// DOCUMENT STYLES — Don't change these
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const docStyles = {
  default: { document: { run: { font: "Arial", size: 22 } } },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 36, bold: true, font: "Arial", color: C.primary },
      paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
    },
    {
      id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, bold: true, font: "Arial", color: C.accent },
      paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 },
    },
    {
      id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 24, bold: true, font: "Arial", color: C.dark },
      paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 },
    },
  ],
};

const numberingConfig = {
  config: [
    {
      reference: "bullets",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    },
    {
      reference: "numbers",
      levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } },
      }],
    },
  ],
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// COVER PAGE — Adapt title and subtitle per project
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function buildCoverPage(title, subtitle, tagline, meta) {
  // meta is array of [key, value] pairs: [["Version", "1.0"], ["Date", "June 2026"], ...]
  return {
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    children: [
      spacer(2000),
      new Paragraph({
        children: [new TextRun({ text: "Product Requirements Document", size: 52, bold: true, font: "Arial", color: C.primary })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
      }),
      new Paragraph({
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent, space: 1 } },
        spacing: { after: 400 },
      }),
      new Paragraph({
        children: [new TextRun({ text: subtitle, size: 36, font: "Arial", color: C.accent })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 120 },
      }),
      new Paragraph({
        children: [new TextRun({ text: tagline, size: 22, font: "Arial", color: C.gray, italics: true })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 600 },
      }),
      new Table({
        width: { size: 5000, type: WidthType.DXA },
        columnWidths: [2000, 3000],
        rows: meta.map(([k, v]) =>
          new TableRow({
            children: [
              new TableCell({
                borders: noBorders, width: { size: 2000, type: WidthType.DXA }, margins: cellMargins,
                children: [new Paragraph({ children: [new TextRun({ text: k, bold: true, size: 20, font: "Arial", color: C.primary })], spacing: { after: 40 } })],
              }),
              new TableCell({
                borders: noBorders, width: { size: 3000, type: WidthType.DXA }, margins: cellMargins,
                children: [new Paragraph({ children: [new TextRun({ text: v, size: 20, font: "Arial", color: "444444" })], spacing: { after: 40 } })],
              }),
            ],
          })
        ),
      }),
      new Paragraph({ children: [new PageBreak()] }),
    ],
  };
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// HEADER & FOOTER — Adapt title per project
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function buildHeaderFooter(shortTitle) {
  return {
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            children: [
              new TextRun({ text: `PRD \u2014 ${shortTitle}`, size: 16, font: "Arial", color: C.gray, italics: true }),
              new TextRun({ text: "\tv1.0", size: 16, font: "Arial", color: C.gray, italics: true }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: C.border, space: 4 } },
          }),
        ],
      }),
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            children: [
              new TextRun({ text: "Confidential \u2014 Internal Use Only", size: 16, font: "Arial", color: C.gray }),
              new TextRun({ text: "\tPage ", size: 16, font: "Arial", color: C.gray }),
              new TextRun({ children: [PageNumber.CURRENT], size: 16, font: "Arial", color: C.gray }),
            ],
            tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            border: { top: { style: BorderStyle.SINGLE, size: 2, color: C.border, space: 4 } },
          }),
        ],
      }),
    },
  };
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// SIGN-OFF — Adapt roles per project
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function buildSignOff(roles) {
  // roles is array of strings: ["CEO", "CTO", "Finance Lead", ...]
  return simpleTable(
    ["Role", "Name", "Signature", "Date"],
    roles.map(r => [r, "", "", ""]),
    [2000, 2500, 3000, 1860]
  );
}


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// EXAMPLE USAGE — Replace this with actual PRD content
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/*
const doc = new Document({
  styles: docStyles,
  numbering: numberingConfig,
  sections: [
    // Cover page
    buildCoverPage(
      "Product Requirements Document",
      "Your Product Name Here",
      "One-line description of what this product does.",
      [
        ["Version", "1.0"],
        ["Date", "June 2026"],
        ["Status", "Draft — Pending Sign-off"],
        ["Confidentiality", "Internal Use Only"],
      ]
    ),

    // Main content
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1200, left: 1440 },
        },
      },
      ...buildHeaderFooter("Your Product Name"),
      children: [

        // ── Section: Executive Summary ──
        heading1("Executive Summary"),
        para("Your executive summary here..."),
        calloutBox("Core Problem", "The crisp problem statement.", C.light),
        spacer(200),

        // ── Section: Objectives ──
        heading1("Goals & Success Metrics"),
        simpleTable(
          ["Goal", "Success Metric"],
          [
            ["Goal 1", "Metric 1"],
            ["Goal 2", "Metric 2"],
          ],
          [4680, 4680]
        ),
        spacer(200),

        // ── Section: Feature Module (dynamic name) ──
        heading1("Seller Onboarding & Storefront"),
        para("Description of this module..."),
        simpleTable(
          ["Capability", "Details"],
          [
            ["Capability 1", "Details here"],
            ["Capability 2", "Details here"],
          ],
          [2400, 6960]
        ),

        // ── More sections as needed... ──

        // ── Sign-Off ──
        new Paragraph({ children: [new PageBreak()] }),
        heading1("Sign-Off"),
        para("By signing below, stakeholders confirm this PRD represents the agreed requirements."),
        spacer(200),
        buildSignOff(["CEO", "CTO", "Product Lead", "Engineering Lead"]),
      ],
    },
  ],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("output-prd.docx", buffer);
  console.log("Done");
});
*/

// Export helpers for use in scripts
module.exports = {
  C, spacer, heading1, heading2, heading3, para,
  headerCell, dataCell, simpleTable, calloutBox, bulletItem,
  docStyles, numberingConfig, buildCoverPage, buildHeaderFooter, buildSignOff,
  TABLE_WIDTH
};
