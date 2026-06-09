# Component Library

Reusable HTML patterns for common UI components. Copy and adapt these when building mockups.

---

## Role Switcher Bar

Include at the top of every mockup. Default to the screen's primary audience role.

```html
<div class="role-bar">
  <label>Viewing as:</label>
  <button class="role-btn active" onclick="switchRole('CEO')">CEO</button>
  <button class="role-btn" onclick="switchRole('CTO')">CTO</button>
  <button class="role-btn" onclick="switchRole('DM')">DM</button>
  <button class="role-btn" onclick="switchRole('PM')">PM</button>
  <button class="role-btn" onclick="switchRole('Finance')">Finance</button>
  <button class="role-btn" onclick="switchRole('HR')">HR</button>
  <button class="role-btn" onclick="switchRole('Engineer')">Engineer</button>
  <span style="margin-left:auto;color:#64748b;font-size:12px;">🔒 = restricted for this role</span>
</div>
```

```javascript
function switchRole(role) {
  document.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');

  // Show/hide elements based on role
  document.querySelectorAll('[data-roles]').forEach(el => {
    const roles = el.dataset.roles.split(',');
    el.style.display = roles.includes(role) ? '' : 'none';
  });

  // Restrict fields — show lock icon
  document.querySelectorAll('[data-restrict]').forEach(el => {
    const restricted = el.dataset.restrict.split(',');
    if (restricted.includes(role)) {
      el.dataset.origHtml = el.dataset.origHtml || el.innerHTML;
      el.innerHTML = '<span class="restricted">Restricted</span>';
    } else if (el.dataset.origHtml) {
      el.innerHTML = el.dataset.origHtml;
    }
  });
}
```

Usage on elements:
```html
<!-- Only visible to these roles -->
<div data-roles="CEO,CTO,Finance">Margin: ₹4,50,000</div>

<!-- Content replaced with 🔒 for restricted roles -->
<td data-restrict="HR,Engineer">₹2,00,000/month</td>
```

---

## Data Table with Actions

```html
<div class="card">
  <div class="card-header">
    <span class="card-title">Resource Assignments</span>
    <button class="btn btn-primary btn-sm" data-roles="PM,DM,CTO,CEO">+ Add Assignment</button>
  </div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Resource</th>
          <th>Designation</th>
          <th>Allocation</th>
          <th>Billability</th>
          <th data-roles="CEO,CTO,DM,PM">Shadow</th>
          <th data-roles="CEO,CTO,Finance">Rate</th>
          <th>End Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Vivek Sharma</strong></td>
          <td>Tech Lead</td>
          <td>60%</td>
          <td data-restrict="HR,Engineer">50%</td>
          <td data-roles="CEO,CTO,DM,PM">No</td>
          <td data-restrict="PM,HR,Engineer">$45/hr</td>
          <td>31 Aug 2026</td>
          <td>
            <button class="btn btn-sm btn-secondary" data-roles="PM,DM,CTO,CEO">Edit</button>
            <button class="btn btn-sm btn-danger" data-roles="PM,DM,CTO,CEO">Release</button>
          </td>
        </tr>
        <!-- more rows -->
      </tbody>
    </table>
  </div>
  <div class="pagination">
    <span>Showing 1-10 of 24 assignments</span>
    <div>
      <button class="btn btn-sm btn-secondary">← Prev</button>
      <button class="btn btn-sm btn-secondary">Next →</button>
    </div>
  </div>
</div>
```

---

## KPI Dashboard Row

```html
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Billable Utilization</div>
    <div class="kpi-value">74%</div>
    <div class="kpi-trend up">↑ 3% from last month</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">On Bench</div>
    <div class="kpi-value">4</div>
    <div class="kpi-trend down">↑ 2 from last week</div>
  </div>
  <div class="kpi-card" data-roles="CEO,CTO,Finance">
    <div class="kpi-label">Company Margin</div>
    <div class="kpi-value">₹18.4L</div>
    <div class="kpi-trend up">↑ 5% from last month</div>
  </div>
</div>
```

---

## Tab Navigation

```html
<div class="tabs">
  <div class="tab active" onclick="showTab('overview')">Overview</div>
  <div class="tab" onclick="showTab('assignments')">Assignments (12)</div>
  <div class="tab" onclick="showTab('milestones')" data-roles="CEO,CTO,DM,PM">Milestones</div>
  <div class="tab" onclick="showTab('invoices')" data-roles="CEO,CTO,Finance">Invoices</div>
  <div class="tab" onclick="showTab('costs')" data-roles="CEO,CTO,DM,PM,Finance">Costs</div>
  <div class="tab" onclick="showTab('worklogs')">Worklogs</div>
</div>

<div id="tab-overview" class="tab-panel active"><!-- content --></div>
<div id="tab-assignments" class="tab-panel"><!-- content --></div>
```

```javascript
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}
```

---

## Form with Validation

```html
<div class="card" style="max-width:600px;">
  <div class="card-header">
    <span class="card-title">Add Assignment</span>
  </div>
  <div class="card-body">
    <div class="form-group">
      <label class="form-label required">Resource</label>
      <select class="form-select">
        <option value="">Select resource...</option>
        <option>Vivek Sharma — Tech Lead</option>
        <option>Priya Patel — Senior Developer</option>
      </select>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div class="form-group">
        <label class="form-label required">Allocation %</label>
        <input type="number" class="form-input" value="60" min="1" max="100">
      </div>
      <div class="form-group">
        <label class="form-label required">Billability %</label>
        <input type="number" class="form-input form-error" value="70">
        <div class="form-error-msg">Billability cannot exceed allocation percentage</div>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Project Designation (override)</label>
      <input type="text" class="form-input" placeholder="Leave blank to use default">
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
      <div class="form-group">
        <label class="form-label required">Start Date</label>
        <input type="date" class="form-input" value="2026-07-01">
      </div>
      <div class="form-group">
        <label class="form-label">End Date</label>
        <input type="date" class="form-input" value="2027-03-31">
      </div>
    </div>
    <div class="form-group">
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
        <input type="checkbox"> Shadow resource (not billed to client)
      </label>
    </div>
    <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:24px;">
      <button class="btn btn-secondary">Cancel</button>
      <button class="btn btn-primary">Save Assignment</button>
    </div>
  </div>
</div>
```

---

## Multi-Currency Input

```html
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">
  <div class="form-group">
    <label class="form-label required">Amount</label>
    <input type="number" class="form-input" value="4500">
  </div>
  <div class="form-group">
    <label class="form-label required">Currency</label>
    <select class="form-select" onchange="updateRate(this)">
      <option value="USD">USD</option>
      <option value="EUR">EUR</option>
      <option value="GBP">GBP</option>
      <option value="INR">INR</option>
    </select>
  </div>
  <div class="form-group">
    <label class="form-label required">Exchange Rate</label>
    <input type="number" class="form-input" value="83.50" step="0.0001" id="rateInput">
  </div>
</div>
<div style="background:#e6f7f5;padding:12px 16px;border-radius:6px;margin-top:8px;">
  <strong>INR Equivalent:</strong> ₹3,75,750.00
</div>
```

---

## Empty State

```html
<div class="empty-state">
  <div class="empty-state-icon">📋</div>
  <div class="empty-state-title">No assignments yet</div>
  <div class="empty-state-desc">This project doesn't have any resource assignments. Add your first assignment to start tracking allocations.</div>
  <button class="btn btn-primary">+ Add Assignment</button>
</div>
```

---

## Index Page

The central hub at `mockups/index.html` for reviewing all module mockups. Self-contained, no external deps. Embed all module/screen data in the JS object at top of script.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{Project Name} — Mockup Review</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; color: #334155; display: flex; flex-direction: column; height: 100vh; }

    /* Top bar */
    .topbar {
      background: #0f2b45;
      color: #fff;
      padding: 0 24px;
      height: 52px;
      display: flex;
      align-items: center;
      gap: 16px;
      flex-shrink: 0;
    }
    .topbar-title { font-size: 15px; font-weight: 700; }
    .topbar-badge {
      padding: 3px 10px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .badge-html { background: #0d9488; color: #fff; }
    .badge-figma { background: #7c3aed; color: #fff; }
    .topbar-meta { margin-left: auto; font-size: 12px; color: #8da4bc; }

    /* Layout */
    .layout { display: flex; flex: 1; overflow: hidden; }

    /* Sidebar */
    .sidebar {
      width: 260px;
      background: #fff;
      border-right: 1px solid #e2e8f0;
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      overflow-y: auto;
    }
    .sidebar-header {
      padding: 16px 20px 12px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #94a3b8;
      border-bottom: 1px solid #f1f5f9;
    }
    .module-item {
      padding: 12px 20px;
      cursor: pointer;
      border-left: 3px solid transparent;
      transition: background 150ms;
    }
    .module-item:hover { background: #f8fafc; }
    .module-item.active { background: #f0fdfa; border-left-color: #0d9488; }
    .module-item-name { font-size: 13px; font-weight: 600; color: #1e293b; }
    .module-item-meta { font-size: 11px; color: #94a3b8; margin-top: 2px; }
    .module-item.active .module-item-name { color: #0d9488; }

    /* Main */
    .main { flex: 1; overflow-y: auto; padding: 24px 28px; }
    .main-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    .main-title { font-size: 20px; font-weight: 700; color: #0f2b45; }
    .btn-open-all {
      padding: 7px 16px;
      background: #0d9488;
      color: #fff;
      border: none;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-open-all:hover { background: #0a7a70; }

    /* Screen grid */
    .screen-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      gap: 16px;
    }
    .screen-card {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 18px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      transition: box-shadow 150ms, border-color 150ms;
    }
    .screen-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); border-color: #0d9488; }
    .screen-icon { font-size: 24px; margin-bottom: 10px; }
    .screen-name { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
    .screen-desc { font-size: 12px; color: #64748b; line-height: 1.5; margin-bottom: 14px; min-height: 36px; }
    .btn-open {
      display: inline-block;
      padding: 6px 14px;
      background: #f0fdfa;
      color: #0d9488;
      border: 1px solid #0d9488;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      text-decoration: none;
    }
    .btn-open:hover { background: #0d9488; color: #fff; }

    /* Empty state */
    .no-module {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 300px;
      color: #94a3b8;
      font-size: 14px;
    }
    .no-module-icon { font-size: 48px; opacity: 0.3; margin-bottom: 12px; }
  </style>
</head>
<body>

<div class="topbar">
  <div class="topbar-title" id="projectTitle">Project Mockups</div>
  <span class="topbar-badge badge-html" id="modeBadge">HTML</span>
  <span class="topbar-badge" id="themeBadge" style="background:#1B3A5C;color:#fff;display:none;"></span>
  <div class="topbar-meta" id="topbarMeta"></div>
</div>

<div class="layout">
  <div class="sidebar">
    <div class="sidebar-header">Modules</div>
    <div id="moduleList"></div>
  </div>
  <div class="main" id="mainPanel">
    <div class="no-module">
      <div class="no-module-icon">📐</div>
      <div>Select a module to view its screens</div>
    </div>
  </div>
</div>

<script>
// ── EDIT THIS DATA BLOCK ──────────────────────────────────────────
const MOCKUP_DATA = {
  project: "Resource Management System",
  theme: "Professional Corporate",    // set to "" for Figma mode
  mode: "html",                        // "html" or "figma"
  modules: [
    {
      id: "05-allocation-tracking",
      name: "Allocation Tracking",
      screens: [
        {
          name: "Allocation List",
          type: "list",
          description: "Table of all resource allocations with filters and bulk actions",
          file: "../modules/05-allocation-tracking/mockups/allocation-list.html"
        },
        {
          name: "Add Assignment",
          type: "form",
          description: "Form to create a new resource-project assignment",
          file: "../modules/05-allocation-tracking/mockups/add-assignment.html"
        }
      ]
    }
    // Add more modules here as they are generated
  ]
};
// ─────────────────────────────────────────────────────────────────

const ICONS = { list: "📋", form: "📝", dashboard: "📊", calendar: "🗓", settings: "⚙️", detail: "🔍", report: "📈" };

function init() {
  document.getElementById("projectTitle").textContent = MOCKUP_DATA.project + " — Mockup Review";
  document.title = MOCKUP_DATA.project + " — Mockup Review";

  const modeBadge = document.getElementById("modeBadge");
  modeBadge.textContent = MOCKUP_DATA.mode.toUpperCase();
  modeBadge.className = "topbar-badge " + (MOCKUP_DATA.mode === "figma" ? "badge-figma" : "badge-html");

  if (MOCKUP_DATA.theme) {
    const tb = document.getElementById("themeBadge");
    tb.textContent = MOCKUP_DATA.theme;
    tb.style.display = "";
  }

  const totalScreens = MOCKUP_DATA.modules.reduce((s, m) => s + m.screens.length, 0);
  document.getElementById("topbarMeta").textContent =
    `${MOCKUP_DATA.modules.length} modules · ${totalScreens} screens`;

  const list = document.getElementById("moduleList");
  MOCKUP_DATA.modules.forEach((mod, i) => {
    const el = document.createElement("div");
    el.className = "module-item" + (i === 0 ? " active" : "");
    el.innerHTML = `<div class="module-item-name">${mod.name}</div>
      <div class="module-item-meta">${mod.screens.length} screen${mod.screens.length !== 1 ? "s" : ""}</div>`;
    el.onclick = () => selectModule(mod, el);
    list.appendChild(el);
  });

  if (MOCKUP_DATA.modules.length > 0) selectModule(MOCKUP_DATA.modules[0], list.firstChild);
}

function selectModule(mod, itemEl) {
  document.querySelectorAll(".module-item").forEach(el => el.classList.remove("active"));
  itemEl.classList.add("active");

  const panel = document.getElementById("mainPanel");
  panel.innerHTML = `
    <div class="main-header">
      <div class="main-title">${mod.name}</div>
      <button class="btn-open-all" onclick="openAll('${mod.id}')">Open All Screens ↗</button>
    </div>
    <div class="screen-grid" id="grid-${mod.id}"></div>`;

  const grid = document.getElementById("grid-" + mod.id);
  mod.screens.forEach(screen => {
    const icon = ICONS[screen.type] || "📄";
    const card = document.createElement("div");
    card.className = "screen-card";
    card.innerHTML = `
      <div class="screen-icon">${icon}</div>
      <div class="screen-name">${screen.name}</div>
      <div class="screen-desc">${screen.description}</div>
      <a class="btn-open" href="${screen.file}" target="_blank">Open →</a>`;
    grid.appendChild(card);
  });
}

function openAll(modId) {
  const mod = MOCKUP_DATA.modules.find(m => m.id === modId);
  if (mod) mod.screens.forEach(s => window.open(s.file, "_blank"));
}

init();
</script>
</body>
</html>
```

**When generating this file:**
- Replace `MOCKUP_DATA` with the actual project name, selected theme, mode, and all generated modules/screens
- Use relative paths from `mockups/` to `modules/{module}/mockups/*.html` (e.g., `../modules/05-allocation-tracking/mockups/screen.html`)
- Update the file every time a new module batch is generated — add the new module's entry to the `modules` array
- Apply the selected theme's colors to the sidebar active state and button colors (override the CSS variables at the top of `<style>`)

---

## Over-Allocation Warning

```html
<tr style="background:#fff5f5;">
  <td><strong>Arjun Mehta</strong> <span class="badge badge-overallocated">120%</span></td>
  <td>Senior Developer</td>
  <td style="color:#ef4444;font-weight:600;">40% <small>(total: 120%)</small></td>
  <!-- ... -->
</tr>
```
