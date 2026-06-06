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

## Over-Allocation Warning

```html
<tr style="background:#fff5f5;">
  <td><strong>Arjun Mehta</strong> <span class="badge badge-overallocated">120%</span></td>
  <td>Senior Developer</td>
  <td style="color:#ef4444;font-weight:600;">40% <small>(total: 120%)</small></td>
  <!-- ... -->
</tr>
```
