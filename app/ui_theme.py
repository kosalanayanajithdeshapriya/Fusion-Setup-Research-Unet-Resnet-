"""Theme constants, an inline SVG icon set, and small HTML-snippet builders
for the Streamlit demo.

Warm, organic "plant nursery" visual language per a supplied design mockup:
cream/tan page backdrop, cream cards (a shade lighter than the page), a
terracotta/burnt-orange primary accent (headline highlight word, solid CTA
pills), a real-photo hero collage (one dataset sample per growth stage),
pale pastel-tinted filter chips, and a two-column "final prediction" card
(badge+confidence on the left, probability breakdown on the right).

No emoji anywhere — icons are hand-embedded SVG path data (Feather-style
line icons for UI chrome, custom filled glyphs for the four growth stages)
rendered inline so they inherit color via `currentColor`.

Palette validated with the dataviz skill's validate_palette.js (categorical,
all-pairs CVD check) against the cream card surface (#f5eee0): growth-stage
colors (violet/teal-green/terracotta/tomato-red) and model/branch colors
(blue/green/berry) both pass clean. See scripts/model_common.py MODEL_CONFIGS
for the underlying model names this maps to.

Responsive tiers: 768px (tablet — hero stacks, insight panel stacks) and
480px (phone — tighter type/padding, hero photo grid becomes a horizontal
scroll strip). Interactive touch targets (upload button) are >=44px tall
per mobile accessibility guidance.
"""

ICONS = {
    # UI chrome (Feather-style line icons, 24x24, stroke-based)
    "image": '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "bar-chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "git-merge": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 21V9a9 9 0 0 0 9 9"/>',
    "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 9.01"/>',
    "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "droplet": '<path d="M12 2.69s-6 7.44-6 11.31a6 6 0 0 0 12 0c0-3.87-6-11.31-6-11.31z"/>',
    "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "external-link": '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
    # growth stages (custom filled glyphs)
    "seed": '<ellipse cx="12" cy="14" rx="4" ry="6" transform="rotate(15 12 14)" fill="currentColor" stroke="none"/><path d="M12 8c0-3 2-5 4-5" fill="none"/>',
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
    "flower": '<circle cx="12" cy="12" r="2.1" fill="currentColor" stroke="none"/><circle cx="12" cy="5.5" r="2.5" fill="currentColor" stroke="none"/><circle cx="12" cy="18.5" r="2.5" fill="currentColor" stroke="none"/><circle cx="5.5" cy="12" r="2.5" fill="currentColor" stroke="none"/><circle cx="18.5" cy="12" r="2.5" fill="currentColor" stroke="none"/>',
    "fruit": '<circle cx="12" cy="13" r="7" fill="currentColor" stroke="none"/><path d="M9 6.3c1-1.4 4-1.4 5 0" fill="none"/><line x1="12" y1="4" x2="12" y2="6.3"/>',
}


def icon_svg(name, size=18, stroke_width=1.8, css_class="icon"):
    body = ICONS[name]
    return (
        f'<svg class="{css_class}" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


STAGE_META = {
    "seeding":    {"icon": "seed", "var": "--stage-seeding", "label": "Seeding"},
    "developing": {"icon": "leaf", "var": "--stage-developing", "label": "Developing"},
    "flowering":  {"icon": "flower", "var": "--stage-flowering", "label": "Flowering"},
    "fruiting":   {"icon": "fruit", "var": "--stage-fruiting", "label": "Fruiting"},
}

MODEL_META = {
    "A_resnet_only": {
        "var": "--model-a", "short": "A", "label": "ResNet-only",
        "eyebrow": "MODEL A · BRANCH 02 · CNN", "subtitle": "2048-dim visual features",
    },
    "B_lpf_only": {
        "var": "--model-b", "short": "B", "label": "LPF-only",
        "eyebrow": "MODEL B · BRANCH 01 · U-NET", "subtitle": "1-dim leaf pixel fraction",
    },
    "C_fused": {
        "var": "--model-c", "short": "C", "label": "Fused",
        "eyebrow": "MODEL C · FUSION", "subtitle": "ResNet50 + U-Net combined",
    },
}

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

/* ============================== design tokens ============================== */
:root {
  --page-bg: #ECE1CC;
  --surface-card: #F6EFE2;
  --border: rgba(43, 33, 20, 0.08);
  --shadow: 0 10px 26px rgba(43, 33, 20, 0.10);
  --text-primary: #241C12;
  --text-secondary: #6B6152;
  --text-muted: #948A76;

  --brand-terracotta: #C1622E;
  --brand-green: #2F6B3F;
  --brand-green-soft: #DCEBD2;

  --stage-seeding: #6E4FA6;
  --stage-developing: #1F8A5F;
  --stage-flowering: #C1622E;
  --stage-fruiting: #B03A2E;

  --model-a: #1D4ED8;
  --model-b: #3D7A3D;
  --model-c: #A3195B;
}

/* ============================== page chrome ============================== */
html, body, [class*="css"] { font-family: 'Inter', system-ui, -apple-system, "Segoe UI", sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: var(--page-bg); }
section[data-testid="stSidebar"] { background: #F6EFE2; }

.icon { vertical-align: -0.22em; flex-shrink: 0; }

.icon-chip {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.9rem; height: 1.9rem; border-radius: 9px; flex-shrink: 0;
  background: color-mix(in srgb, var(--chip-color, var(--model-a)) 14%, white);
  color: var(--chip-color, var(--model-a));
}

.eyebrow {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.3rem 0.85rem; border-radius: 999px;
  background: var(--brand-green-soft);
  color: var(--brand-green);
  font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 700;
  letter-spacing: 0.06em; text-transform: uppercase;
  margin-bottom: 0.8rem;
}

/* ============================== hero ============================== */
.hero-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 2rem; padding: 0.4rem 0.1rem 0; }
.hero-text { flex: 1 1 480px; min-width: 0; }
.hero-text h1 {
  margin: 0; font-family: 'Outfit', sans-serif; font-size: clamp(1.7rem, 4.2vw, 2.4rem); font-weight: 800;
  color: var(--text-primary); letter-spacing: -0.01em; line-height: 1.14;
}
.hero-text h1 .accent { color: var(--brand-terracotta); }
.hero-text p { margin: 0.7rem 0 0; color: var(--text-secondary); font-size: 0.98rem; max-width: 560px; }

.chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1.1rem 0 0; }
.chip {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.4rem 0.9rem; border-radius: 999px;
  background: color-mix(in srgb, var(--chip-color, var(--text-primary)) 14%, white);
  color: var(--chip-color, var(--text-primary));
  font-weight: 600; font-size: 0.83rem;
}

/* real-photo growth-stage collage, right of the hero text on desktop */
.hero-photo-grid {
  flex: 0 0 auto; width: 264px;
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.65rem;
}
.hero-photo-card {
  position: relative; border-radius: 14px; overflow: hidden; aspect-ratio: 1 / 1;
  box-shadow: 0 8px 20px rgba(43,33,20,0.16); border: 1px solid var(--border);
}
.hero-photo-card img { width: 100%; height: 100%; object-fit: cover; display: block; }
.hero-photo-label {
  position: absolute; left: 0; right: 0; bottom: 0;
  background: linear-gradient(to top, rgba(20,14,6,0.68), transparent);
  color: #fff; font-size: 0.66rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;
  padding: 0.45rem 0.5rem 0.3rem;
}

/* ============================== cards ============================== */
.card {
  background: var(--surface-card);
  border-radius: 20px;
  padding: 1.1rem 1.25rem;
  box-shadow: var(--shadow);
  margin-bottom: 0.9rem;
}
.model-card { box-shadow: 0 10px 24px color-mix(in srgb, var(--card-accent, var(--model-a)) 16%, transparent); border: 1px solid color-mix(in srgb, var(--card-accent, var(--model-a)) 30%, transparent); }
.card h3 {
  font-family: 'Outfit', sans-serif; font-size: 1rem; font-weight: 700; margin: 0 0 0.6rem;
  color: var(--text-primary); display: flex; align-items: center; gap: 0.55rem;
}
.card .subtitle { color: var(--text-muted); font-size: 0.78rem; margin: -0.35rem 0 0.7rem; }

.photo-frame { position: relative; border-radius: 16px; overflow: hidden; line-height: 0; }
.floating-pill {
  position: absolute; bottom: 10px; right: 10px; z-index: 2;
  display: inline-flex; align-items: center; gap: 0.35rem;
  background: rgba(255,255,255,0.94); backdrop-filter: blur(6px);
  padding: 0.35rem 0.75rem; border-radius: 999px;
  font-size: 0.76rem; font-weight: 700; color: var(--text-primary);
  box-shadow: 0 4px 14px rgba(43,33,20,0.2);
}
.floating-pill .icon { color: var(--pill-color, var(--brand-green)); }

/* ============================== badges & bars ============================== */
.stage-badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.28rem 0.8rem; border-radius: 999px;
  background: color-mix(in srgb, var(--badge-color) 13%, white);
  color: var(--badge-color);
  font-weight: 600; font-size: 0.88rem;
}
.stage-badge-lg {
  display: inline-flex; align-items: center; gap: 0.45rem;
  padding: 0.6rem 1.35rem; border-radius: 999px;
  background: var(--badge-color); color: #ffffff;
  font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.35rem;
  box-shadow: 0 10px 22px color-mix(in srgb, var(--badge-color) 45%, transparent);
}
.stage-badge-lg .icon { width: 22px; height: 22px; }

.confidence-tag {
  display: inline-block; padding: 0.22rem 0.65rem;
  border-radius: 999px; background: color-mix(in srgb, var(--text-primary) 7%, white);
  color: var(--text-secondary);
  font-size: 0.8rem; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap;
}

.result-row { display: flex; align-items: center; flex-wrap: wrap; gap: 0.55rem; }

.result-split { display: flex; align-items: center; gap: 1.6rem; flex-wrap: wrap; }
.result-split .result-left { flex: 0 0 auto; display: flex; flex-direction: column; align-items: flex-start; gap: 0.7rem; }
.result-split .result-right { flex: 1 1 260px; min-width: 220px; }

.prob-row { display: flex; align-items: center; gap: 0.6rem; margin: 0.35rem 0; }
.prob-row.predicted .prob-label { color: var(--text-primary); font-weight: 700; }
.prob-label { flex: 0 0 100px; font-size: 0.8rem; color: var(--text-secondary); display: flex; align-items: center; gap: 0.3rem; }
.prob-track { flex: 1; height: 8px; background: color-mix(in srgb, var(--text-primary) 7%, white); border-radius: 999px; overflow: hidden; }
.prob-fill { height: 100%; border-radius: 999px; }
.prob-value { flex: 0 0 40px; text-align: right; font-size: 0.78rem; font-variant-numeric: tabular-nums; color: var(--text-secondary); }
.prob-row.predicted .prob-value { color: var(--text-primary); font-weight: 700; }

.agree-banner {
  border-radius: 16px; padding: 0.75rem 1.1rem; margin-bottom: 1.1rem;
  background: var(--brand-green-soft);
  font-weight: 600; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;
}
.agree-banner.ok { color: var(--brand-green); }
.agree-banner.warn { background: color-mix(in srgb, var(--stage-flowering) 16%, white); color: var(--stage-flowering); }

/* ============================== model-insight panel ============================== */
.insight-panel { display: flex; align-items: stretch; gap: 0.9rem; }
.insight-card {
  flex: 1 1 0; background: var(--surface-card); border-radius: 18px;
  padding: 1.1rem 1.3rem; box-shadow: var(--shadow);
  border-top: 3px solid var(--insight-color, var(--brand-terracotta));
}
.insight-label {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--text-muted); margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem;
}
.insight-value { font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.3rem; color: var(--text-primary); }
.insight-sub { font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem; }
.insight-connector {
  flex: 0 0 auto; display: flex; align-items: center; justify-content: center;
  width: 2.1rem; height: 2.1rem; border-radius: 50%; align-self: center;
  background: var(--brand-green-soft); color: var(--brand-green);
}

/* ============================== sidebar & misc ============================== */
.stat-pill {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.45rem 0.1rem; border-bottom: 1px solid var(--border); font-size: 0.83rem;
  color: var(--text-secondary);
}
.stat-pill:last-child { border-bottom: none; }
.stat-pill b { color: var(--text-primary); font-variant-numeric: tabular-nums; }

.section-title {
  font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.05rem;
  color: var(--text-primary); margin: 1.3rem 0 0.6rem;
  display: flex; align-items: center; gap: 0.5rem;
}

.sidebar-title { display: flex; align-items: center; gap: 0.5rem; font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.05rem; color: var(--text-primary); margin-bottom: 0.3rem; }

/* ============================== footer ============================== */
.app-footer {
  margin-top: 2.5rem; padding: 1.3rem 1rem 2rem; text-align: center;
  border-top: 1px solid var(--border);
}
.app-footer p {
  font-size: 0.82rem; color: var(--text-muted); max-width: 580px;
  margin: 0 auto 0.6rem; line-height: 1.55;
}
.app-footer a {
  display: inline-flex; align-items: center; gap: 0.3rem;
  font-size: 0.82rem; color: var(--brand-terracotta); font-weight: 700; text-decoration: none;
}
.app-footer a:hover { text-decoration: underline; }

/* ============================== uploader & spinner ============================== */
div[data-testid="stFileUploaderDropzone"] {
  background: var(--surface-card); border-radius: 18px;
  border: 1.5px dashed color-mix(in srgb, var(--brand-terracotta) 45%, var(--border));
}
div[data-testid="stFileUploaderDropzone"] button {
  background: var(--brand-terracotta) !important; color: #ffffff !important;
  border-radius: 999px !important; border: none !important; font-weight: 600 !important;
  min-height: 44px !important; padding: 0.5rem 1.3rem !important;
}
div[data-testid="stSpinner"] { color: var(--brand-terracotta); font-weight: 600; }
div[data-testid="stSpinner"] svg { color: var(--brand-terracotta) !important; }

/* ============================== tablet tier (<=768px) ============================== */
@media (max-width: 768px) {
  /* .hero-text's flex-basis (480px) sizes the row layout's WIDTH on desktop;
     once .hero-row switches to a column, that same basis would size HEIGHT
     instead and force a large empty gap, so it must be reset here. */
  .hero-row { flex-direction: column; gap: 1.2rem; }
  .hero-text { flex: 1 1 auto; }
  .hero-photo-grid { width: 100%; flex: 1 1 auto; display: flex; grid-template-columns: unset; overflow-x: auto; padding-bottom: 0.35rem; scroll-snap-type: x mandatory; }
  .hero-photo-card { flex: 0 0 108px; scroll-snap-align: start; }
  .insight-panel { flex-direction: column; }
  .insight-connector { align-self: center; transform: rotate(90deg); }
}

/* ============================== phone tier (<=480px) ============================== */
@media (max-width: 480px) {
  .card { padding: 0.9rem 1rem; border-radius: 16px; }
  .stage-badge-lg { font-size: 1.1rem; padding: 0.5rem 1.1rem; }
  .stage-badge-lg .icon { width: 19px; height: 19px; }
  .prob-label { flex-basis: 84px; font-size: 0.75rem; }
  .prob-value { flex-basis: 36px; font-size: 0.74rem; }
  .section-title { font-size: 0.95rem; }
  .chip { padding: 0.4rem 0.8rem; font-size: 0.8rem; }
  .result-split { gap: 1rem; }
  .hero-photo-card { flex-basis: 92px; }
  .insight-value { font-size: 1.15rem; }
}
</style>
"""


def stage_badge_html(stage, large=False):
    meta = STAGE_META[stage]
    cls = "stage-badge-lg" if large else "stage-badge"
    return (
        f'<span class="{cls}" style="--badge-color: var({meta["var"]})">'
        f'{icon_svg(meta["icon"], size=15)} {meta["label"]}</span>'
    )


def probability_bars_html(class_names, probabilities, predicted_class=None):
    """Bars sorted by probability descending; the predicted class's row (if
    given) gets a bold-text highlight so it stands out from the ranking."""
    ordered = sorted(class_names, key=lambda c: probabilities[c], reverse=True)
    rows = []
    for c in ordered:
        meta = STAGE_META[c]
        pct = probabilities[c] * 100
        row_cls = "prob-row predicted" if c == predicted_class else "prob-row"
        rows.append(f'''<div class="{row_cls}">
          <span class="prob-label">{icon_svg(meta["icon"], size=13)} {meta["label"]}</span>
          <div class="prob-track"><div class="prob-fill" style="width:{pct:.1f}%; background: var({meta["var"]})"></div></div>
          <span class="prob-value">{pct:.1f}%</span>
        </div>''')
    return "".join(rows)


def card_title_html(icon_name, title, chip_color_var):
    return (
        f'<h3><span class="icon-chip" style="--chip-color: var({chip_color_var})">'
        f'{icon_svg(icon_name, size=16)}</span>{title}</h3>'
    )


def eyebrow_html(text):
    return f'<div class="eyebrow">{text}</div>'


def floating_pill_html(icon_name, text, color_var="--brand-green"):
    return (
        f'<div class="floating-pill" style="--pill-color: var({color_var})">'
        f'{icon_svg(icon_name, size=14)} {text}</div>'
    )


def chip_html(stage):
    meta = STAGE_META[stage]
    return (
        f'<span class="chip" style="--chip-color: var({meta["var"]})">'
        f'{icon_svg(meta["icon"], size=15)} {meta["label"]}</span>'
    )


def hero_photo_grid_html(stage_data_uris):
    """stage_data_uris: dict of stage -> image data URI, in STAGE_META order."""
    cards = []
    for stage, meta in STAGE_META.items():
        uri = stage_data_uris.get(stage)
        if not uri:
            continue
        cards.append(
            f'<div class="hero-photo-card">'
            f'<img src="{uri}" alt="{meta["label"]} stage sample"/>'
            f'<div class="hero-photo-label">{meta["label"]}</div>'
            f'</div>'
        )
    return f'<div class="hero-photo-grid">{"".join(cards)}</div>'


def insight_panel_html(resnet_class, resnet_confidence, lpf_value, color_a="--model-a", color_b="--model-b"):
    resnet_label = STAGE_META[resnet_class]["label"]
    return f'''<div class="insight-panel">
      <div class="insight-card" style="--insight-color: var({color_a})">
        <div class="insight-label">{icon_svg("image", size=13)} Visual signal &middot; ResNet50</div>
        <div class="insight-value">{resnet_label}</div>
        <div class="insight-sub">{resnet_confidence:.1%} confidence &middot; 2048-dim feature vector</div>
      </div>
      <div class="insight-connector">{icon_svg("plus", size=16)}</div>
      <div class="insight-card" style="--insight-color: var({color_b})">
        <div class="insight-label">{icon_svg("droplet", size=13)} Structural signal &middot; U-Net LPF</div>
        <div class="insight-value">LPF {lpf_value:.4f}</div>
        <div class="insight-sub">Leaf pixel fraction &middot; segmentation-derived</div>
      </div>
    </div>'''


def footer_html():
    return f'''<div class="app-footer">
      <p>This demo is part of an undergraduate research project on tomato growth-stage
      classification, fusing a U-Net leaf-segmentation branch with a ResNet50 visual
      classification branch, trained on a self-collected greenhouse dataset.</p>
      <a href="https://tomatoresearch.vercel.app" target="_blank" rel="noopener">
        {icon_svg("external-link", size=13)} tomatoresearch.vercel.app</a>
    </div>'''
