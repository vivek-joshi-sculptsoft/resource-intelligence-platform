# Design Tokens

Complete design system for mockup generation. Apply these consistently across all mockups.

---

## CSS Variables

```css
:root {
  /* Colors */
  --c-primary: #1B3A5C;
  --c-primary-light: #163a5c;
  --c-primary-hover: #0f2b45;
  --c-accent: #0d9488;
  --c-accent-light: #e6f7f5;
  --c-accent-hover: #0a7a70;

  --c-blue: #2c7be5;
  --c-blue-light: #e8f1fc;

  --c-success: #22c55e;
  --c-success-bg: #f0fdf4;
  --c-warning: #f59e0b;
  --c-warning-bg: #fffbeb;
  --c-danger: #ef4444;
  --c-danger-bg: #fef2f2;

  --c-text: #334155;
  --c-text-secondary: #64748b;
  --c-text-muted: #94a3b8;
  --c-text-inverse: #ffffff;

  --c-bg: #f8fafc;
  --c-bg-card: #ffffff;
  --c-bg-hover: #f1f5f9;
  --c-bg-stripe: #f8fafc;

  --c-border: #e2e8f0;
  --c-border-light: #f1f5f9;
  --c-border-focus: #0d9488;

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', 'Consolas', monospace;

  --fs-xs: 11px;
  --fs-sm: 12px;
  --fs-base: 14px;
  --fs-md: 16px;
  --fs-lg: 18px;
  --fs-xl: 24px;
  --fs-2xl: 32px;

  --fw-regular: 400;
  --fw-medium: 500;
  --fw-semibold: 600;
  --fw-bold: 700;

  --lh-tight: 1.3;
  --lh-base: 1.5;
  --lh-relaxed: 1.7;

  /* Spacing (8px grid) */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 20px;
  --sp-6: 24px;
  --sp-8: 32px;
  --sp-10: 40px;
  --sp-12: 48px;
  --sp-16: 64px;

  /* Borders & Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);

  /* Transitions */
  --transition: 150ms ease;
}
```

---

## Page Layout

```css
body {
  background: var(--c-bg);
  color: var(--c-text);
  font-family: var(--font-family);
  font-size: var(--fs-base);
  line-height: var(--lh-base);
  margin: 0;
  padding: 0;
}

/* Role Switcher Bar — fixed at top */
.role-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--c-primary);
  padding: 8px 24px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-bar label {
  color: #8da4bc;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-right: 8px;
}

.role-btn {
  padding: 5px 14px;
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: var(--radius-full);
  background: transparent;
  color: #8da4bc;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.role-btn:hover { border-color: rgba(255,255,255,0.3); color: #fff; }
.role-btn.active { background: var(--c-accent); border-color: var(--c-accent); color: #fff; }

/* Page container */
.page { max-width: 1200px; margin: 0 auto; padding: 24px 32px; }

/* Page header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title { font-size: var(--fs-xl); font-weight: var(--fw-bold); color: var(--c-primary); }
.breadcrumb { font-size: var(--fs-sm); color: var(--c-text-muted); margin-bottom: 4px; }
.breadcrumb a { color: var(--c-accent); text-decoration: none; }
```

---

## Component Styles

### Cards
```css
.card {
  background: var(--c-bg-card);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--c-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: var(--fs-md);
  font-weight: var(--fw-semibold);
  color: var(--c-primary);
}

.card-body { padding: 20px; }
```

### Tables
```css
.table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-lg);
  border: 1px solid var(--c-border);
}

table { width: 100%; border-collapse: collapse; }

thead th {
  background: var(--c-primary);
  color: var(--c-text-inverse);
  font-size: var(--fs-sm);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 10px 16px;
  text-align: left;
  white-space: nowrap;
}

tbody td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--c-border-light);
  font-size: 13px;
  vertical-align: middle;
}

tbody tr:hover { background: var(--c-bg-hover); }
tbody tr:nth-child(even) { background: var(--c-bg-stripe); }
```

### Buttons
```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--fs-base);
  font-weight: var(--fw-medium);
  cursor: pointer;
  transition: var(--transition);
}

.btn-primary { background: var(--c-accent); color: #fff; }
.btn-primary:hover { background: var(--c-accent-hover); }
.btn-secondary { background: var(--c-bg-hover); color: var(--c-text); border: 1px solid var(--c-border); }
.btn-danger { background: var(--c-danger); color: #fff; }
.btn-sm { padding: 5px 10px; font-size: var(--fs-sm); }
```

### Badges & Status
```css
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--radius-full);
  font-size: var(--fs-xs);
  font-weight: var(--fw-semibold);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge-active { background: #d1fae5; color: #065f46; }
.badge-completed { background: #dbeafe; color: #1e40af; }
.badge-onhold { background: #fef3c7; color: #92400e; }
.badge-cancelled { background: #fee2e2; color: #991b1b; }
.badge-shadow { background: #f3e8ff; color: #6b21a8; }
.badge-overallocated { background: #fee2e2; color: #991b1b; }
```

### Forms
```css
.form-group { margin-bottom: 16px; }

.form-label {
  display: block;
  font-size: var(--fs-sm);
  font-weight: var(--fw-semibold);
  color: var(--c-text-secondary);
  margin-bottom: 4px;
}

.form-label.required::after { content: ' *'; color: var(--c-danger); }

.form-input, .form-select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-md);
  font-size: var(--fs-base);
  transition: var(--transition);
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: var(--c-border-focus);
  box-shadow: 0 0 0 3px rgba(13,148,136,0.1);
}

.form-error { border-color: var(--c-danger) !important; }
.form-error-msg { color: var(--c-danger); font-size: var(--fs-sm); margin-top: 4px; }
```

### KPI Widgets
```css
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }

.kpi-card {
  background: var(--c-bg-card);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.kpi-label { font-size: var(--fs-sm); color: var(--c-text-muted); font-weight: var(--fw-medium); }
.kpi-value { font-size: 28px; font-weight: var(--fw-bold); color: var(--c-primary); margin: 4px 0; }
.kpi-trend { font-size: var(--fs-sm); }
.kpi-trend.up { color: var(--c-success); }
.kpi-trend.down { color: var(--c-danger); }
```

### Tabs
```css
.tabs { display: flex; gap: 0; border-bottom: 2px solid var(--c-border); margin-bottom: 20px; }

.tab {
  padding: 10px 20px;
  font-size: var(--fs-base);
  font-weight: var(--fw-medium);
  color: var(--c-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: var(--transition);
}

.tab:hover { color: var(--c-text); }
.tab.active { color: var(--c-accent); border-bottom-color: var(--c-accent); font-weight: var(--fw-semibold); }
.tab-panel { display: none; }
.tab-panel.active { display: block; }
```

### Pagination
```css
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-top: 1px solid var(--c-border);
  font-size: var(--fs-sm);
  color: var(--c-text-muted);
}
```

### Restricted Field Indicator
```css
.restricted {
  color: var(--c-text-muted);
  font-size: var(--fs-sm);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.restricted::before { content: '🔒'; font-size: 11px; }
```

### Empty State
```css
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--c-text-muted);
}
.empty-state-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.4; }
.empty-state-title { font-size: var(--fs-md); font-weight: var(--fw-semibold); color: var(--c-text-secondary); margin-bottom: 4px; }
.empty-state-desc { font-size: var(--fs-base); margin-bottom: 16px; }
```
