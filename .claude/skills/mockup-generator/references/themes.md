# Theme Definitions

Three distinct visual themes. Each includes full CSS variables, component overrides, and preview HTML structure. When generating theme previews, use the same content (login + dashboard + form) styled with each theme's CSS.

---

## Theme A: Clean Minimal

**Vibe:** Calm, spacious, understated. Think Notion or Linear. Heavy use of whitespace. Single accent color does all the heavy lifting. Borders are thin and subtle. Nothing screams for attention.

**Best for:** Tools that prioritize readability, content-first design, teams that find busy UIs overwhelming.

```css
:root {
  /* Surfaces */
  --bg-page: #fafafa;
  --bg-card: #ffffff;
  --bg-sidebar: #ffffff;
  --bg-header: #ffffff;
  --bg-hover: #f5f5f5;
  --bg-stripe: #fafafa;
  --bg-input: #ffffff;

  /* Primary / Accent */
  --c-primary: #0f172a;
  --c-accent: #0d9488;
  --c-accent-soft: #f0fdfa;
  --c-accent-hover: #0a7a70;

  /* Text */
  --c-text: #1e293b;
  --c-text-secondary: #64748b;
  --c-text-muted: #a1a1aa;

  /* Borders */
  --c-border: #e5e5e5;
  --c-border-light: #f0f0f0;
  --c-border-focus: #0d9488;
  --border-width: 1px;

  /* Shadows */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.04);
  --shadow-dropdown: 0 4px 12px rgba(0,0,0,0.08);

  /* Radius */
  --radius-card: 8px;
  --radius-input: 6px;
  --radius-badge: 9999px;
  --radius-btn: 6px;

  /* Specific Components */
  --header-bg: #ffffff;
  --header-border: 1px solid #e5e5e5;
  --header-text: #0f172a;

  --sidebar-bg: #ffffff;
  --sidebar-border: 1px solid #e5e5e5;
  --sidebar-text: #64748b;
  --sidebar-active-bg: #f0fdfa;
  --sidebar-active-text: #0d9488;

  --table-header-bg: #fafafa;
  --table-header-text: #64748b;
  --table-header-weight: 600;
  --table-header-transform: uppercase;
  --table-header-size: 11px;
  --table-header-letter-spacing: 0.5px;

  --btn-primary-bg: #0d9488;
  --btn-primary-text: #ffffff;
  --btn-primary-hover: #0a7a70;
  --btn-secondary-bg: #ffffff;
  --btn-secondary-text: #334155;
  --btn-secondary-border: 1px solid #e5e5e5;

  --badge-active-bg: #ecfdf5;
  --badge-active-text: #065f46;

  --kpi-value-color: #0f172a;
  --kpi-label-color: #a1a1aa;

  --role-bar-bg: #0f172a;
  --role-bar-active: #0d9488;

  --login-bg: #fafafa;
  --login-card-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
```

**Preview signature elements:**
- Login: centered card on clean white/gray page, minimal, no gradients
- Dashboard: KPI cards with very thin borders, no colored backgrounds on cards
- Tables: light gray header row (not dark navy), subtle row hovers
- Forms: clean inputs with thin borders, accent color only on focus ring
- Sidebar: white with thin right border, teal text for active item

---

## Theme B: Professional Corporate

**Vibe:** Structured, authoritative, data-confident. Think Jira or Salesforce. Dark header/sidebar anchors the layout. Navy communicates trust. Tables are the star — dense, scannable, efficient. This is the "serious tools for serious work" option.

**Best for:** Data-heavy dashboards, finance-facing tools, organizations that want the tool to feel enterprise-grade.

```css
:root {
  /* Surfaces */
  --bg-page: #f1f5f9;
  --bg-card: #ffffff;
  --bg-sidebar: #0f2b45;
  --bg-header: #0f2b45;
  --bg-hover: #e8f1fc;
  --bg-stripe: #f8fafc;
  --bg-input: #ffffff;

  /* Primary / Accent */
  --c-primary: #1B3A5C;
  --c-accent: #2c7be5;
  --c-accent-soft: #e8f1fc;
  --c-accent-hover: #1a68cc;

  /* Text */
  --c-text: #334155;
  --c-text-secondary: #64748b;
  --c-text-muted: #94a3b8;

  /* Borders */
  --c-border: #e2e8f0;
  --c-border-light: #f1f5f9;
  --c-border-focus: #2c7be5;
  --border-width: 1px;

  /* Shadows */
  --shadow-card: 0 1px 4px rgba(15,43,69,0.06);
  --shadow-dropdown: 0 4px 16px rgba(15,43,69,0.12);

  /* Radius */
  --radius-card: 8px;
  --radius-input: 6px;
  --radius-badge: 9999px;
  --radius-btn: 6px;

  /* Specific Components */
  --header-bg: #0f2b45;
  --header-border: none;
  --header-text: #ffffff;

  --sidebar-bg: #0f2b45;
  --sidebar-border: none;
  --sidebar-text: #8da4bc;
  --sidebar-active-bg: rgba(44,123,229,0.15);
  --sidebar-active-text: #ffffff;

  --table-header-bg: #1B3A5C;
  --table-header-text: #ffffff;
  --table-header-weight: 600;
  --table-header-transform: uppercase;
  --table-header-size: 12px;
  --table-header-letter-spacing: 0.8px;

  --btn-primary-bg: #2c7be5;
  --btn-primary-text: #ffffff;
  --btn-primary-hover: #1a68cc;
  --btn-secondary-bg: #ffffff;
  --btn-secondary-text: #334155;
  --btn-secondary-border: 1px solid #e2e8f0;

  --badge-active-bg: #d1fae5;
  --badge-active-text: #065f46;

  --kpi-value-color: #1B3A5C;
  --kpi-label-color: #94a3b8;

  --role-bar-bg: #0a1f33;
  --role-bar-active: #2c7be5;

  --login-bg: linear-gradient(135deg, #0f2b45, #1B3A5C);
  --login-card-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
```

**Preview signature elements:**
- Login: dark navy gradient background, white card floating with strong shadow
- Dashboard: dark navy header/sidebar, white content cards, blue accents
- Tables: navy header row with white text, alternating gray stripes, blue hover
- Forms: clean but with blue focus rings, navy section headers
- Sidebar: dark navy with light blue active states, white text

---

## Theme C: Modern Vibrant

**Vibe:** Fresh, friendly, energetic. Think Vercel or Stripe dashboard. Subtle gradients, rounded generous shapes, colorful but not childish. Purple/indigo primary with teal secondary. Cards feel elevated. The tool has personality without sacrificing professionalism.

**Best for:** Teams that want something that feels modern and pleasant to use daily, startups, design-conscious organizations.

```css
:root {
  /* Surfaces */
  --bg-page: #f5f3ff;
  --bg-card: #ffffff;
  --bg-sidebar: #faf5ff;
  --bg-header: #ffffff;
  --bg-hover: #f5f3ff;
  --bg-stripe: #faf5ff;
  --bg-input: #ffffff;

  /* Primary / Accent */
  --c-primary: #6d28d9;
  --c-accent: #0d9488;
  --c-accent-soft: #f0fdfa;
  --c-accent-hover: #0a7a70;

  /* Text */
  --c-text: #1e1b4b;
  --c-text-secondary: #6b7280;
  --c-text-muted: #a78bfa;

  /* Borders */
  --c-border: #e9d5ff;
  --c-border-light: #f3e8ff;
  --c-border-focus: #6d28d9;
  --border-width: 1px;

  /* Shadows */
  --shadow-card: 0 2px 8px rgba(109,40,217,0.06), 0 1px 3px rgba(0,0,0,0.04);
  --shadow-dropdown: 0 8px 24px rgba(109,40,217,0.12);

  /* Radius */
  --radius-card: 12px;
  --radius-input: 8px;
  --radius-badge: 9999px;
  --radius-btn: 8px;

  /* Specific Components */
  --header-bg: #ffffff;
  --header-border: 1px solid #f3e8ff;
  --header-text: #6d28d9;

  --sidebar-bg: #faf5ff;
  --sidebar-border: 1px solid #f3e8ff;
  --sidebar-text: #6b7280;
  --sidebar-active-bg: #ede9fe;
  --sidebar-active-text: #6d28d9;

  --table-header-bg: linear-gradient(135deg, #6d28d9, #7c3aed);
  --table-header-text: #ffffff;
  --table-header-weight: 600;
  --table-header-transform: none;
  --table-header-size: 13px;
  --table-header-letter-spacing: 0;

  --btn-primary-bg: linear-gradient(135deg, #6d28d9, #7c3aed);
  --btn-primary-text: #ffffff;
  --btn-primary-hover: #5b21b6;
  --btn-secondary-bg: #ffffff;
  --btn-secondary-text: #6d28d9;
  --btn-secondary-border: 1px solid #e9d5ff;

  --badge-active-bg: #d1fae5;
  --badge-active-text: #065f46;

  --kpi-value-color: #6d28d9;
  --kpi-label-color: #a78bfa;

  --role-bar-bg: #1e1b4b;
  --role-bar-active: #7c3aed;

  --login-bg: linear-gradient(135deg, #4c1d95, #6d28d9, #7c3aed);
  --login-card-shadow: 0 8px 32px rgba(109,40,217,0.15);
}
```

**Preview signature elements:**
- Login: purple gradient background, white card with generous radius and soft purple shadow
- Dashboard: light purple tints, gradient table headers, purple KPI values
- Tables: gradient purple header, lavender hover, more rounded corners
- Forms: purple focus rings, rounded inputs, gradient submit button
- Sidebar: light lavender background, purple active highlights

---

## Preview HTML Structure

All 3 preview files use this same HTML structure. Only the CSS variables change.

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Theme Preview: {Theme Name}</title>
  <style>
    /* Paste the theme's CSS variables here */
    /* Then paste shared component styles from design-tokens.md */
    /* Component styles reference var(--xxx) so they adapt per theme */
  </style>
</head>
<body>

  <!-- Section 1: Login Preview -->
  <div class="preview-section">
    <h2 class="preview-label">Login</h2>
    <!-- Login card with app name, email, password, button -->
  </div>

  <!-- Section 2: Dashboard Preview -->
  <div class="preview-section">
    <h2 class="preview-label">Dashboard</h2>
    <!-- Sidebar + header + 4 KPI cards + mini table -->
  </div>

  <!-- Section 3: Form Preview -->
  <div class="preview-section">
    <h2 class="preview-label">Data Entry Form</h2>
    <!-- Form with inputs, dropdowns, date pickers, error state, buttons -->
  </div>

</body>
</html>
```

Each preview file is self-contained. The user opens all 3 in browser tabs and compares side by side.

---

## After Selection

Once the user picks a theme:
1. Store the selected theme's CSS variables
2. Use them in all subsequent mockup generation
3. The design-tokens.md base styles (typography, spacing, component structure) stay the same
4. Only the visual properties (colors, shadows, radii, backgrounds) come from the chosen theme
5. If the user wants to tweak specific values ("make the accent orange instead of teal"), apply the override on top of the selected theme
