---
name: Clinical & Logistics Chain Visibility
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0d1c2e'
  on-tertiary-container: '#77859a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#d5e3fc'
  tertiary-fixed-dim: '#b9c7df'
  on-tertiary-fixed: '#0d1c2e'
  on-tertiary-fixed-variant: '#3a485b'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display:
    fontFamily: Inter
    fontSize: 1.875rem
    fontWeight: '700'
    lineHeight: 2.25rem
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: '600'
    lineHeight: 2rem
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.015em
  headline-sm:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.25rem
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1rem
  label-code:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: '500'
    lineHeight: 1rem
    letterSpacing: 0.025em
  metric-tabular:
    fontFamily: JetBrains Mono
    fontSize: 1.125rem
    fontWeight: '600'
    lineHeight: 1.5rem
    letterSpacing: -0.02em
  table-header:
    fontFamily: Inter
    fontSize: 0.6875rem
    fontWeight: '600'
    lineHeight: 1rem
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-lg: 1.5rem
  margin: 1rem
  margin-lg: 1.5rem
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
  space-2xl: 2rem
---

## Brand & Style

This design system governs mission-critical enterprise workflows across clinical logistics, drug distribution, cold-chain monitoring, and regulatory compliance (FDA/EMA). It prioritizes immediate cognitive clarity, low visual fatigue over extended shifts, and precise spatial density.

The aesthetic follows an **Authentic Enterprise** philosophy:
- **Precision over Decoration:** Eliminates gratuitous gradients, synthetic glows, and heavy glassmorphism in favor of structured data cells, crisp structural lines, and distinct information hierarchy.
- **Clinical Sobriety:** Uses restrained semantic alerting. Red is reserved strictly for supply stockouts, critical cold-chain excursions, and regulatory failures; amber marks telemetry drift and customs holding patterns; emerald indicates validated operational health.
- **Operational Ergonomics:** Visual anchor points are defined by high-contrast primary text against calibrated warm slate-tinted canvas backdrops, keeping operator focus centered on exception management and batch resolution.

## Colors

The palette establishes an enterprise light framework engineered for sustained operational use under high ambient office or distribution center lighting.

### Canvas & Surface Hierarchy
- **Canvas / Root Background:** `#F8FAFC` (Slate 50) delivers an eye-friendly, anti-glare foundation.
- **Card & Data Surfaces:** `#FFFFFF` (Pure White) ensures high local contrast against the tinted canvas.
- **Surface Inset / Well:** `#F1F5F9` (Slate 100) provides distinct containment for table headers, filter strips, and nested metric groupings.
- **Structural Borders:** `#E2E8F0` (Slate 200) for container edges; `#CBD5E1` (Slate 300) for active inputs and dividers.

### Typography & Content
- **Text Primary:** `#0F172A` (Slate 900) for metric readouts, data headers, and critical labels.
- **Text Secondary:** `#475569` (Slate 600) for attribute values, axis legends, and column descriptions.
- **Text Muted / Placeholder:** `#64748B` (Slate 500) for secondary metadata and disabled cues.

### Operational State Matrix
- **Critical / Shortage / Excursion:**
  - Ink: `#DC2626`
  - Background Tint: `#FEF2F2`
  - Structural Border: `#FECACA`
- **Warning / Pipeline Risk / Review:**
  - Ink: `#D97706`
  - Background Tint: `#FFFBEB`
  - Structural Border: `#FDE68A`
- **Nominal / Cleared / In-Transit:**
  - Ink: `#059669`
  - Background Tint: `#ECFDF5`
  - Structural Border: `#A7F3D0`
- **Network / Telemetry / Focus:**
  - Ink: `#2563EB`
  - Background Tint: `#EFF6FF`
  - Structural Border: `#BFDBFE`

## Typography

The typographic hierarchy implements a high-density, dual-engine structure:
1. **Primary Interface (`Inter`):** Drives conversational context, standard table cells, structural headers, and command actions. Letter spacing is slightly tightened on larger display tiers for compact enterprise headers.
2. **Telemetry & Identifiers (`JetBrains Mono`):** Applied systematically to machine data, including:
   - FDA NDC (National Drug Code) numbers and FEI facility IDs
   - Batch numbers, LOT codes, and RFID tracking strings
   - UTC/Zulu timestamps and real-time transit telemetry
   - Numeric quantities within tabular comparison matrices to ensure vertical alignment of digits

All table headers leverage uppercase styling with explicit letter tracking (`0.05em`) to clearly delineate metadata columns from row contents.

## Layout & Spacing

This design system uses a 12-column fluid grid system pinned to a maximum content width of 1680px for desktop consoles, scaling fluidly down to single-column card stacks for field tablets.

### Responsive Breakpoints
- **Desktop Console (>=1440px):** 12 columns, 24px (`space-xl`) outer margins, 16px (`gutter`) internal gutters. Left utility rail docked at 64px collapsed / 240px expanded.
- **Workstation / Laptop (1024px - 1439px):** 12 columns, 16px (`margin`) outer margins, 16px (`gutter`) gutters. Telemetry inspection panels convert from docked sidebars to overlay sheets.
- **Tablet / Operational Terminal (<1023px):** Multi-column metrics wrap to 2-column or 1-column cards. Data grids gain horizontal container scroll with frozen left identification columns.

### Density Tiers
- **Comfortable (Master Dashboards):** Container padding at `space-lg` (16px), cell padding at `space-md` (12px).
- **Compact (Inspection Tables & Telemetry Feeds):** Table row height fixed at 36px, cell padding at `space-sm` horizontal (8px) and `space-xs` vertical (4px).

## Elevation & Depth

To avoid visual confusion in data-heavy enterprise screens, depth is established using **structured containment lines and low-diffusion ambient shadows** instead of exaggerated elevation steps.

- **Level 0 (Canvas):** Flat base `#F8FAFC`.
- **Level 1 (Cards, Metric Tiles, Table Wrappers):** `#FFFFFF` fill with a 1px solid border `#E2E8F0` and an ambient boundary shadow: `0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.02)`.
- **Level 2 (Dropdowns, Popovers, Filter Menus):** `#FFFFFF` fill, 1px solid border `#CBD5E1`, with shadow: `0 4px 6px -1px rgba(15, 23, 42, 0.07), 0 2px 4px -2px rgba(15, 23, 42, 0.05)`.
- **Level 3 (Modal Dialogs, Urgent Audit Overlays):** `#FFFFFF` fill, 1px solid border `#CBD5E1`, layered above an overlay backdrop of `rgba(15, 23, 42, 0.45)`, using deep structural projection: `0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.06)`.

## Shapes

The design system uses a strict **Level 1 (Soft / 0.25rem - 0.375rem)** geometry. Rounded corners are intentionally constrained to 6px (`0.375rem`) for cards and inputs, preserving vertical and horizontal grid alignment across complex data tables.

- **Containers, Panels & Cards:** Fixed at `6px` radius.
- **Buttons, Text Inputs & Dropdown Triggers:** Fixed at `6px` radius.
- **Badges, Lozenge Status Indicators & Facility Tags:** `4px` radius for small technical tags, or fully pill-shaped (`9999px`) exclusively for high-level summary counts and breadcrumb state chips.
- **Table Outlines:** Outer wrapper curved at `6px`; internal cells maintain square geometry (`0px`) with clean hairline grid dividers.

## Components

### Global Header
- **Background:** Deep navy/slate `#0F172A` with contrasting white/slate-200 text, or clean white `#FFFFFF` with a bottom border `#E2E8F0`.
- **Elements:** Operational environment selector (e.g., `PROD-US-EAST`), UTC clock in `label-code`, tenant switcher, and system status indicator with a 6px status dot.

### Buttons & Interactive Controls
- **Primary:** Background `#0F172A`, text `#FFFFFF`, hover `#1E293B`. For focused action pathways (e.g., "Authorize Release", "Reroute Shipment"), background is `#2563EB`, hover `#1D4ED8`.
- **Secondary / Outline:** Background `#FFFFFF`, border 1px solid `#CBD5E1`, text `#0F172A`, hover `#F8FAFC`.
- **Destructive:** Background `#FEF2F2`, border 1px solid `#FECACA`, text `#DC2626`, hover `#FEE2E2`.
- **Touch Target & Height:** 32px height for compact data-dense toolbars; 38px height for standard interface actions.

### Data Tables & Grid Lists
- **Header:** Background `#F1F5F9`, border-bottom 1px solid `#CBD5E1`, typography `table-header` in `#475569`.
- **Row Styling:** Background alternates `#FFFFFF` on hover to `#F8FAFC`. Bottom row border is 1px solid `#F1F5F9`.
- **Numeric Cells:** Right-aligned, formatted with `JetBrains Mono` for rapid visual column scanning.

### Status Badges & Operational Lozenges
- Constructed with a 1px border, 15% tint background, and solid ink label:
  - **Stockout / Critical:** `#FEF2F2` bg, `#FECACA` border, `#DC2626` text, leading 6px circle dot.
  - **At Risk / Delayed:** `#FFFBEB` bg, `#FDE68A` border, `#D97706` text.
  - **Nominal / Cleared:** `#ECFDF5` bg, `#A7F3D0` border, `#059669` text.
  - **Cold Chain Tracked:** `#EFF6FF` bg, `#BFDBFE` border, `#2563EB` text.

### Form Inputs & Filters
- **Input Field:** Height 36px, background `#FFFFFF`, border 1px solid `#CBD5E1`, font size `0.875rem`. Focus ring uses an explicit 2px offset ring in `#2563EB` at 20% opacity with a `#2563EB` border.
- **Search with Monospace Filtering:** Embedded trailing shortcut chip (e.g., `⌘K`) using `#F1F5F9` background and `#64748B` label.

### Supply Chain Topology & Telemetry Visualizations
- **Node Representation:** Multi-tier hubs rendered as 28px slate/white roundels with 2px borders indicating facility tier (e.g., Primary API Synthesis, Formulation Plant, Central Hub, Clinical Site).
- **Route Connectors:** 1.5px paths using `#94A3B8` for nominal transit; dynamic dashed routes for customs delays; solid `#DC2626` routes for cold-chain excursions.
- **Distribution Metric Bars:** Micro horizontal progress tracks (6px height) with light gray base tracks (`#E2E8F0`) and solid fills corresponding to stock levels against safety stock thresholds.