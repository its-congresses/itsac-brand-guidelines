from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import base64
from itertools import permutations
import json
import shutil
import string


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'row-1-colorway-system'
OUT.mkdir(parents=True, exist_ok=True)

CREAM = '#F2EBDA'
INK = '#1A1A1A'
BLUE = '#1E4C9A'
GREEN = '#2E7D4F'
TERRACOTTA = '#BE4A2F'
YELLOW = '#E8B93B'

# Neutral colors remain fixed. Chromatic colors are reassigned by structural role.
# A-D are the approved starting families and retain their original identities.
COLOR_NAMES = {
    TERRACOTTA: 'terracotta',
    YELLOW: 'yellow',
    BLUE: 'blue',
    GREEN: 'green',
}
COLOR_CODES = {TERRACOTTA: 'T', YELLOW: 'Y', BLUE: 'B', GREEN: 'G'}
ROLE_ORDER = ['lead', 'diamond-accent', 'interlock-a', 'interlock-b']
CHROMATIC_COLORS = [TERRACOTTA, YELLOW, BLUE, GREEN]

COLORWAYS = {
    'a-original': {
        'label': 'A · Original / terracotta-led',
        TERRACOTTA: TERRACOTTA, YELLOW: YELLOW, BLUE: BLUE, GREEN: GREEN,
    },
    'b-green-led': {
        'label': 'B · Green-led',
        TERRACOTTA: GREEN, YELLOW: YELLOW, BLUE: BLUE, GREEN: TERRACOTTA,
    },
    'c-blue-led': {
        'label': 'C · Blue-led',
        TERRACOTTA: BLUE, YELLOW: YELLOW, BLUE: GREEN, GREEN: TERRACOTTA,
    },
    'd-yellow-led': {
        'label': 'D · Yellow-led',
        TERRACOTTA: YELLOW, YELLOW: BLUE, BLUE: TERRACOTTA, GREEN: GREEN,
    },
}

# Complete the exhaustive 4! set while preserving A-D above.
used_assignments = {
    tuple(data[color] for color in CHROMATIC_COLORS)
    for data in COLORWAYS.values()
}
remaining_assignments = [
    assignment for assignment in permutations(CHROMATIC_COLORS)
    if assignment not in used_assignments
]
for letter, assignment in zip(string.ascii_uppercase[4:24], remaining_assignments):
    code = '/'.join(COLOR_CODES[color] for color in assignment)
    slug_colors = '-'.join(COLOR_NAMES[color] for color in assignment)
    COLORWAYS[f'{letter.lower()}-{slug_colors}'] = {
        'label': f'{letter} · {code}',
        **dict(zip(CHROMATIC_COLORS, assignment)),
    }

assert len(COLORWAYS) == 24
assert len({tuple(data[color] for color in CHROMATIC_COLORS) for data in COLORWAYS.values()}) == 24

PATHS = [
    ('M0 0H240L360 120 240 240H0L120 120Z', TERRACOTTA),
    ('M240 0H360L480 120 360 240H240L360 120Z', INK),
    ('M360 0H480L600 120 480 240H360L480 120Z', CREAM),
    ('M480 0H720L600 120 720 240H480L600 120Z', BLUE),
    ('M720 0H840L960 120 840 240H720L840 120Z', INK),
    ('M840 0H960L1080 120 960 240H840L960 120Z', CREAM),
    ('M960 0H1200L1080 120 1200 240H960L1080 120Z', GREEN),
    ('M120 40L200 120 120 200 40 120Z', YELLOW),
    ('M600 40L680 120 600 200 520 120Z', CREAM),
    ('M1080 40L1160 120 1080 200 1000 120Z', CREAM),
]

POLYGONS = [
    ([(0, 0), (240, 0), (360, 120), (240, 240), (0, 240), (120, 120)], TERRACOTTA),
    ([(240, 0), (360, 0), (480, 120), (360, 240), (240, 240), (360, 120)], INK),
    ([(360, 0), (480, 0), (600, 120), (480, 240), (360, 240), (480, 120)], CREAM),
    ([(480, 0), (720, 0), (600, 120), (720, 240), (480, 240), (600, 120)], BLUE),
    ([(720, 0), (840, 0), (960, 120), (840, 240), (720, 240), (840, 120)], INK),
    ([(840, 0), (960, 0), (1080, 120), (960, 240), (840, 240), (960, 120)], CREAM),
    ([(960, 0), (1200, 0), (1080, 120), (1200, 240), (960, 240), (1080, 120)], GREEN),
    ([(120, 40), (200, 120), (120, 200), (40, 120)], YELLOW),
    ([(600, 40), (680, 120), (600, 200), (520, 120)], CREAM),
    ([(1080, 40), (1160, 120), (1080, 200), (1000, 120)], CREAM),
]


def svg_strip(mapping, title, view_width=1200):
    paths = '\n'.join(
        f'  <path d="{d}" fill="{mapping.get(color, color)}"/>' for d, color in PATHS
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{view_width}" height="240" viewBox="0 0 {view_width} 240" role="img" aria-label="{title}">
  <title>{title}</title>
  <rect width="1200" height="240" fill="{CREAM}"/>
{paths}
</svg>
'''


def render_strip(mapping, scale=4):
    """Rasterize the same master geometry from clean vector coordinates."""
    canvas = Image.new('RGB', (1200 * scale, 240 * scale), CREAM)
    draw = ImageDraw.Draw(canvas)
    for points, color in POLYGONS:
        scaled = [(x * scale, y * scale) for x, y in points]
        draw.polygon(scaled, fill=mapping.get(color, color))
    return canvas.resize((1200, 240), Image.Resampling.LANCZOS)

comparison_rows = []
manifest = {
    'system': 'row-1-colorway-system',
    'colorway_count': 24,
    'module_count': 120,
    'module_size': 240,
    'sequence': [1, 2, 3, 4, 5],
    'fixed_neutrals': {'cream': CREAM, 'ink': INK},
    'role_order': ROLE_ORDER,
    'colorways': {},
}

for slug, mapping_data in COLORWAYS.items():
    folder = OUT / slug
    module_folder = folder / 'modules'
    module_folder.mkdir(parents=True, exist_ok=True)
    mapping = {k: v for k, v in mapping_data.items() if k.startswith('#')}
    label = mapping_data['label']

    strip = render_strip(mapping)
    strip.save(folder / f'{slug}-master-strip.png', optimize=True)
    strip_svg = svg_strip(mapping, f'{label} continuous five-module master strip')
    (folder / f'{slug}-master-strip.svg').write_text(strip_svg)

    module_files = []
    for i in range(5):
        number = i + 1
        module = strip.crop((i * 240, 0, (i + 1) * 240, 240))
        module.save(module_folder / f'module-{number}{slug[0]}.png', optimize=True)
        module_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240" viewBox="0 0 240 240" role="img" aria-label="Module {number}{slug[0]} · {label}">
  <defs><clipPath id="tile"><rect width="240" height="240"/></clipPath></defs>
  <g clip-path="url(#tile)" transform="translate({-i * 240} 0)">
    <svg width="1200" height="240" viewBox="0 0 1200 240">
{svg_strip(mapping, label).split('>', 1)[1].rsplit('</svg>', 1)[0]}
    </svg>
  </g>
</svg>
'''
        (module_folder / f'module-{number}{slug[0]}.svg').write_text(module_svg)
        module_files.append(f'module-{number}{slug[0]}')

    # Full-screen proof uses the already-approved paired phase offsets.
    layout = [0, 0, 2, 2, 4, 4, 1, 1, 3]
    fullscreen = Image.new('RGB', (3840, 2160), CREAM)
    for row, offset in enumerate(layout):
        for col in range(16):
            idx = (col + offset) % 5
            tile = strip.crop((idx * 240, 0, (idx + 1) * 240, 240))
            fullscreen.paste(tile, (col * 240, row * 240))
    fullscreen.save(folder / f'{slug}-fullscreen-4k.png', optimize=True)

    # Self-contained vector full-screen using repeated master strips.
    strip_b64 = base64.b64encode(strip_svg.encode()).decode()
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="3840" height="2160" viewBox="0 0 3840 2160" role="img" aria-label="{label} 4K full-screen pattern">']
    for row, offset in enumerate(layout):
        start = -offset * 240
        for x in range(start - 1200, 3840 + 1200, 1200):
            svg.append(f'  <image x="{x}" y="{row * 240}" width="1200" height="240" href="data:image/svg+xml;base64,{strip_b64}"/>')
    svg.append('</svg>')
    (folder / f'{slug}-fullscreen-4k.svg').write_text('\n'.join(svg) + '\n')

    comparison_rows.append((label, strip))
    manifest['colorways'][slug] = {
        'label': label,
        'role_map': mapping,
        'role_assignments': {
            role: {'name': COLOR_NAMES[color], 'hex': color}
            for role, color in zip(ROLE_ORDER, [mapping[source] for source in CHROMATIC_COLORS])
        },
        'modules': module_files,
        'valid_sequence': [f'{i}{slug[0]}' for i in range(1, 6)],
        'wraps_to': f'1{slug[0]}',
    }

# Full-resolution strip stack for detailed visual inspection.
full_stack = Image.new('RGB', (1200, 240 * len(comparison_rows)), CREAM)
for row, (_, strip) in enumerate(comparison_rows):
    full_stack.paste(strip, (0, row * 240))
full_stack.save(OUT / 'row-1-all-24-master-strips-full-resolution.png', optimize=True)

# Compact labeled comparison board: two columns by twelve rows.
thumb_w, thumb_h = 600, 120
cell_w, cell_h = 620, 155
margin_x, margin_y = 30, 20
columns = 2
rows = (len(comparison_rows) + columns - 1) // columns
board = Image.new('RGB', (margin_x * 2 + cell_w * columns, margin_y * 2 + cell_h * rows), INK)
draw = ImageDraw.Draw(board)
font = ImageFont.load_default(size=18)
for index, (label, strip) in enumerate(comparison_rows):
    column = index % columns
    row = index // columns
    left = margin_x + column * cell_w
    top = margin_y + row * cell_h
    draw.text((left, top), label, fill=CREAM, font=font)
    board.paste(strip.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (left, top + 25))
board.save(OUT / 'row-1-colorways-comparison.png', optimize=True)

# Grid proof: every scaled module boundary is explicit.
grid_board = board.copy()
grid = ImageDraw.Draw(grid_board)
for index in range(len(comparison_rows)):
    column = index % columns
    row = index // columns
    x0 = margin_x + column * cell_w
    y0 = margin_y + row * cell_h + 25
    x1, y1 = x0 + thumb_w, y0 + thumb_h
    for x in range(x0, x1 + 1, thumb_w // 5):
        grid.line((x, y0, x, y1), fill='#FF2A00', width=2)
    grid.rectangle((x0, y0, x1, y1), outline='#FF2A00', width=2)
grid_board.save(OUT / 'row-1-colorways-comparison-with-grid.png', optimize=True)

(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
family_lines = '\n'.join(
    f"- **{data['label']}** — " + ', '.join(
        f"{role}: {COLOR_NAMES[data[source]]}"
        for role, source in zip(ROLE_ORDER, CHROMATIC_COLORS)
    )
    for data in COLORWAYS.values()
)
(OUT / 'README.md').write_text(f'''# Row 1 colorway system — complete 24-family edition

## Locked construction

- Geometry, anchors, module size and sequence are immutable.
- The canonical repeating sequence is `1–2–3–4–5`.
- Each colorway is generated from one continuous 1200 × 240 master strip and sliced only after recoloring.
- Cream (`#F2EBDA`) and ink (`#1A1A1A`) remain fixed.
- Terracotta, yellow, blue and green are reassigned as coordinated structural roles.
- Every chromatic color is used exactly once per family.

## Families

The role order is: lead, diamond accent, interlock A, interlock B.

{family_lines}

## Compatibility

Use complete same-suffix sequences: `1a–2a–3a–4a–5a`, `1b–2b–3b–4b–5b`, and so on. The fifth module wraps back to the first module of the same family. Cross-family adjacency is not guaranteed unless the two boundary signatures are explicitly matched.

Every family folder contains the editable master strip, five individual SVG/PNG modules and a 4K full-screen proof. The complete system contains 24 families and 120 distinct modules.
''')

archive_base = ROOT / 'outputs' / 'row-1-colorway-system'
zip_path = ROOT / 'outputs' / 'row-1-colorway-system.zip'
if zip_path.exists():
    zip_path.unlink()
shutil.make_archive(str(archive_base), 'zip', root_dir=OUT.parent, base_dir=OUT.name)
