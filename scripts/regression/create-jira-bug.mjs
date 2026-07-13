#!/usr/bin/env node
/**
 * Creates a Jira Bug ticket from a regression-failures.json summary
 * (produced by parse-test-failures.mjs), assigns it, and prints the
 * ticket key + URL as GitHub Actions outputs.
 *
 * Required env vars:
 *   JIRA_SITE            e.g. sspl-organisation.atlassian.net
 *   JIRA_PROJECT_KEY      e.g. VRIP
 *   JIRA_USER_EMAIL       account used for API auth (needs create-issue perms)
 *   JIRA_API_TOKEN        API token for JIRA_USER_EMAIL
 *   JIRA_ASSIGNEE_EMAIL   who the bug gets assigned to (defaults to JIRA_USER_EMAIL)
 *
 * Usage: node create-jira-bug.mjs <regression-failures.json> <github-run-url>
 */
import { readFileSync, appendFileSync } from "node:fs";

const [, , summaryPath, runUrl] = process.argv;

function requireEnv(name) {
  const val = process.env[name];
  if (!val) {
    console.error(`Missing required env var: ${name}`);
    process.exit(2);
  }
  return val;
}

const site = requireEnv("JIRA_SITE");
const projectKey = requireEnv("JIRA_PROJECT_KEY");
const userEmail = requireEnv("JIRA_USER_EMAIL");
const apiToken = requireEnv("JIRA_API_TOKEN");
const assigneeEmail = process.env.JIRA_ASSIGNEE_EMAIL || userEmail;

if (!summaryPath) {
  console.error("Usage: node create-jira-bug.mjs <regression-failures.json> [runUrl]");
  process.exit(2);
}

const summary = JSON.parse(readFileSync(summaryPath, "utf8"));

const authHeader =
  "Basic " + Buffer.from(`${userEmail}:${apiToken}`).toString("base64");

async function jiraFetch(path, options = {}) {
  const resp = await fetch(`https://${site}${path}`, {
    ...options,
    headers: {
      Authorization: authHeader,
      "Content-Type": "application/json",
      Accept: "application/json",
      ...options.headers,
    },
  });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`Jira API ${path} failed: ${resp.status} ${body}`);
  }
  return resp.status === 204 ? null : resp.json();
}

async function findAccountId(email) {
  const users = await jiraFetch(
    `/rest/api/3/user/search?query=${encodeURIComponent(email)}`
  );
  const match = users.find((u) => u.emailAddress?.toLowerCase() === email.toLowerCase());
  if (!match) {
    throw new Error(`No Jira user found for email ${email}`);
  }
  return match.accountId;
}

function toAdf(summaryObj, runUrl) {
  const content = [];
  content.push({
    type: "paragraph",
    content: [
      {
        type: "text",
        text: `${summaryObj.failureCount} regression test(s) failed on push to main. Auto-created by the regression-autofix pipeline.`,
      },
    ],
  });

  if (runUrl) {
    content.push({
      type: "paragraph",
      content: [
        { type: "text", text: "CI run: " },
        {
          type: "text",
          text: runUrl,
          marks: [{ type: "link", attrs: { href: runUrl } }],
        },
      ],
    });
  }

  for (const f of summaryObj.failures) {
    content.push({
      type: "heading",
      attrs: { level: 3 },
      content: [{ type: "text", text: f.fullTitle }],
    });
    content.push({
      type: "paragraph",
      content: [
        {
          type: "text",
          text: `${f.file}:${f.line} — project: ${f.project} — status: ${f.status}`,
        },
      ],
    });
    const errorText = f.errors
      .map((e) => e.message)
      .filter(Boolean)
      .join("\n\n")
      .slice(0, 3000);
    if (errorText) {
      content.push({
        type: "codeBlock",
        content: [{ type: "text", text: errorText }],
      });
    }
  }

  return { type: "doc", version: 1, content };
}

async function main() {
  const assigneeAccountId = await findAccountId(assigneeEmail);

  const failureTitles = summary.failures.map((f) => f.title).slice(0, 3);
  const summaryLine =
    summary.failureCount === 1
      ? `Regression test failure: ${failureTitles[0]}`
      : `${summary.failureCount} regression tests failed on main (${failureTitles.join(", ")}${
          summary.failureCount > 3 ? ", …" : ""
        })`;

  const created = await jiraFetch(`/rest/api/3/issue`, {
    method: "POST",
    body: JSON.stringify({
      fields: {
        project: { key: projectKey },
        summary: summaryLine.slice(0, 250),
        issuetype: { name: "Bug" },
        description: toAdf(summary, runUrl),
        assignee: { accountId: assigneeAccountId },
        labels: ["auto-regression", "auto-fix-pipeline"],
      },
    }),
  });

  const ticketUrl = `https://${site}/browse/${created.key}`;
  console.log(`Created Jira ticket ${created.key}: ${ticketUrl}`);

  const githubOutput = process.env.GITHUB_OUTPUT;
  if (githubOutput) {
    appendFileSync(githubOutput, `ticket_key=${created.key}\n`);
    appendFileSync(githubOutput, `ticket_url=${ticketUrl}\n`);
  }
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
