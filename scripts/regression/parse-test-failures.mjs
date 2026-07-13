#!/usr/bin/env node
/**
 * Parses a Playwright JSON reporter output file and extracts failing tests
 * into a structured summary — used by the regression-autofix pipeline to
 * build a Jira bug description and a Claude Code fix prompt.
 *
 * Usage: node parse-test-failures.mjs <path-to-results.json> <output-dir>
 */
import { readFileSync, writeFileSync, appendFileSync } from "node:fs";
import { resolve } from "node:path";

const [, , reportPath, outDir = "."] = process.argv;

if (!reportPath) {
  console.error("Usage: node parse-test-failures.mjs <results.json> [outDir]");
  process.exit(2);
}

let report;
try {
  report = JSON.parse(readFileSync(reportPath, "utf8"));
} catch (err) {
  console.error(`Failed to read/parse report at ${reportPath}: ${err.message}`);
  process.exit(2);
}

const failures = [];

function walk(suite, titlePath) {
  for (const child of suite.suites ?? []) {
    walk(child, [...titlePath, child.title].filter(Boolean));
  }
  for (const spec of suite.specs ?? []) {
    for (const test of spec.tests ?? []) {
      // Use the last (most recent) result — retries mean earlier attempts may
      // have failed transiently before eventually passing.
      const results = test.results ?? [];
      const last = results[results.length - 1];
      if (!last) continue;
      if (last.status === "passed" || last.status === "skipped") continue;

      const errors = (last.errors ?? []).map((e) => ({
        message: (e.message ?? "").replace(/\[[0-9;]*m/g, ""), // strip ANSI
        stack: (e.stack ?? "").replace(/\[[0-9;]*m/g, ""),
      }));

      failures.push({
        title: spec.title,
        describe: titlePath.join(" > "),
        fullTitle: [...titlePath, spec.title].join(" > "),
        file: spec.file,
        line: spec.line,
        project: test.projectName,
        status: last.status,
        durationMs: last.duration,
        retries: results.length - 1,
        errors,
      });
    }
  }
}

for (const suite of report.suites ?? []) {
  walk(suite, []);
}

const summary = {
  hasFailures: failures.length > 0,
  failureCount: failures.length,
  generatedAt: new Date().toISOString(),
  failures,
};

writeFileSync(
  resolve(outDir, "regression-failures.json"),
  JSON.stringify(summary, null, 2)
);

const md = [];
md.push(`# Regression Test Failures`);
md.push("");
md.push(`**${failures.length} test(s) failed** — generated ${summary.generatedAt}`);
md.push("");

for (const f of failures) {
  md.push(`## ${f.fullTitle}`);
  md.push("");
  md.push(`- **File:** \`${f.file}:${f.line}\``);
  md.push(`- **Project:** ${f.project}`);
  md.push(`- **Status:** ${f.status}${f.retries ? ` (after ${f.retries} retr${f.retries === 1 ? "y" : "ies"})` : ""}`);
  md.push("");
  for (const e of f.errors) {
    md.push("```");
    md.push(e.message || "(no error message captured)");
    md.push("```");
    if (e.stack && e.stack !== e.message) {
      md.push("<details><summary>Stack trace</summary>");
      md.push("");
      md.push("```");
      md.push(e.stack.slice(0, 4000));
      md.push("```");
      md.push("</details>");
    }
    md.push("");
  }
}

writeFileSync(resolve(outDir, "regression-failures.md"), md.join("\n"));

// GitHub Actions outputs
const githubOutput = process.env.GITHUB_OUTPUT;
if (githubOutput) {
  appendFileSync(githubOutput, `has_failures=${summary.hasFailures}\n`);
  appendFileSync(githubOutput, `failure_count=${summary.failureCount}\n`);
}

console.log(
  `Parsed ${failures.length} failing test(s) from ${reportPath} → ${outDir}/regression-failures.{json,md}`
);
