# CTT Logistics — Enterprise Design System (`DESIGN.md`)

## 1. Visual Theme & Atmosphere
- **Direction:** Industrial Precision & Operational Clarity (inspired by Linear, Vercel, and SAP enterprise logistics).
- **Mood:** Calm, high-contrast, functional, and zero-decoration. Every border, badge, and spacing value serves data scannability.
- **Anti-Patterns (Strictly Forbidden):**
  - No emojis anywhere in UI labels, buttons, headings, or table cells (use 1.5px stroke SVG icons only).
  - No linear/radial gradients, glassmorphism (`backdrop-blur`), or neon glow shadows.
  - No generic 3-equal-card hero rows or nested cards inside cards.
  - No browser `alert()` dialogs (use non-blocking bottom-right toast notifications).

## 2. Color Palette & Temperature (Warm Industrial Neutral + Single Brand Accent)
- **Light Surface (Operations & Customer Tracking):**
  - Canvas Background: `#F7F6F2` (Warm Stone)
  - Elevated Surface / Table: `#FFFFFF` (Pure Crisp White)
  - Subtle Surface / Header Tint: `#F0EEE9` (Warm Sand)
  - Hairline Border: `#E2DFD7`
  - Primary Text: `#181715` (Warm Charcoal)
  - Secondary Text: `#57534E` (Stone 600)
- **Dark Surface (Fleet Map Telemetry):**
  - Canvas Background: `#121110` (Warm Near-Black)
  - Elevated Panel: `#1A1917`
  - Hairline Border: `#2C2A26`
  - Primary Text: `#F5F5F4`
  - Secondary Text: `#A8A29E`
- **Brand & Semantic Tokens:**
  - Primary Brand Accent: `#D97706` (CTT Industrial Amber) / Hover: `#B45309`
  - Status — Pending (`รับเข้าระบบ`): `#0369A1` text on `#F0F9FF` surface (`#BAE6FD` border)
  - Status — In Transit (`กำลังจัดส่ง`): `#B45309` text on `#FFFBEB` surface (`#FDE68A` border)
  - Status — Delivered (`จัดส่งสำเร็จ`): `#15803D` text on `#F0FDF4` surface (`#BBF7D0` border)

## 3. Typography Rules
- **Primary UI & Thai Sans:** `'IBM Plex Sans Thai', sans-serif` (weights: 400, 500, 600, 700). Never use Inter, Roboto, or Prompt.
- **Monospace (Tracking IDs, Timestamps, Coordinates):** `'Geist Mono', monospace` with `font-variant-numeric: tabular-nums`.
- **Wrapping:** `h1, h2, h3 { text-wrap: balance; }` and `p { text-wrap: pretty; }`.

## 4. Concentric Radius & Spacing
- Outer Containers / Modals: `12px` (`rounded-xl`)
- Inner Inputs / Buttons (with `4px`–`8px` gap): `8px` (`rounded-lg`)
- Status Pills & Badges: `6px` (`rounded-md`)
