"""Render hybrid_chip_fab.gds to an interactive HTML viewer."""
import gdstk
import json

lib = gdstk.read_gds("hybrid_chip_fab.gds")
top = lib.top_level()[0]

# Layer key: (layer, datatype)
LAYER_COLORS = {
    "1_0": ("#2196F3", "Waveguide Ridge"),
    "1_1": ("#90CAF9", "Waveguide Slab"),
    "2_0": ("#FF5722", "PPLN Poling"),
    "3_0": ("#FFD700", "Metal Electrodes"),
    "3_1": ("#FFA000", "Bond Pads"),
    "4_0": ("#9C27B0", "Detector Active"),
    "4_1": ("#CE93D8", "Detector Contact"),
    "5_0": ("#4CAF50", "Cladding Opening"),
    "6_0": ("#78909C", "Deep Etch (Chip Edge)"),
    "10_0": ("#607D8B", "Labels"),
    "11_0": ("#37474F", "Floorplan"),
}

shapes = []

def layer_key(layer, datatype):
    return f"{layer}_{datatype}"

def collect_polygons(cell, dx=0, dy=0):
    for poly in cell.polygons:
        lk = layer_key(poly.layer, poly.datatype)
        pts = poly.points.tolist()
        pts = [[p[0] + dx, p[1] + dy] for p in pts]
        info = LAYER_COLORS.get(lk, ("#999", "Unknown"))
        shapes.append({"type": "polygon", "points": pts, "color": info[0],
                       "layer": lk, "name": info[1]})

    for path in cell.paths:
        lk = layer_key(path.layers[0], path.datatypes[0]) if path.layers else "1_0"
        polys = path.to_polygons()
        for poly in polys:
            pts = poly.tolist()
            pts = [[p[0] + dx, p[1] + dy] for p in pts]
            info = LAYER_COLORS.get(lk, ("#999", "Unknown"))
            shapes.append({"type": "polygon", "points": pts, "color": info[0],
                           "layer": lk, "name": info[1]})

    for label in cell.labels:
        lk = layer_key(label.layer, label.texttype)
        x, y = label.origin
        shapes.append({
            "type": "label", "text": label.text,
            "x": x + dx, "y": y + dy, "layer": lk
        })

    for ref in cell.references:
        ref_cell = ref.cell
        ox, oy = ref.origin if hasattr(ref, 'origin') else (0, 0)
        collect_polygons(ref_cell, dx + ox, dy + oy)

collect_polygons(top)

html = f"""<!DOCTYPE html>
<html>
<head>
<title>Wavelength-Ternary Hybrid SFG Chip — Fab Level</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #0d1117; font-family: 'Courier New', monospace; color: #e0e0e0; overflow: hidden; }}
canvas {{ display: block; cursor: grab; }}
canvas:active {{ cursor: grabbing; }}
#hud {{ position: fixed; top: 15px; left: 15px; background: rgba(0,0,0,0.85); padding: 12px 16px; border-radius: 8px; border: 1px solid #333; font-size: 12px; z-index: 10; max-width: 320px; }}
#hud h2 {{ color: #4CAF50; margin-bottom: 8px; font-size: 13px; }}
#hud div {{ margin: 2px 0; color: #aaa; }}
#legend {{ position: fixed; top: 15px; right: 15px; background: rgba(0,0,0,0.85); padding: 12px 16px; border-radius: 8px; border: 1px solid #333; font-size: 11px; z-index: 10; max-height: 90vh; overflow-y: auto; }}
#legend h3 {{ color: #aaa; margin-bottom: 6px; font-size: 12px; }}
.legend-item {{ display: flex; align-items: center; gap: 8px; margin: 3px 0; cursor: pointer; }}
.legend-item:hover {{ opacity: 0.8; }}
.legend-swatch {{ width: 12px; height: 12px; border-radius: 2px; border: 1px solid #555; flex-shrink: 0; }}
#controls {{ position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.75); padding: 8px 16px; border-radius: 8px; border: 1px solid #333; font-size: 11px; color: #666; z-index: 10; }}
#coords {{ position: fixed; bottom: 15px; right: 15px; background: rgba(0,0,0,0.75); padding: 6px 12px; border-radius: 6px; border: 1px solid #333; font-size: 11px; color: #888; z-index: 10; }}
</style>
</head>
<body>
<div id="hud">
  <h2>WAVELENGTH-TERNARY HYBRID SFG CHIP</h2>
  <div>Fabrication-level GDS &bull; LNOI platform</div>
  <div>3.2 &times; 2.7 mm chip</div>
  <div>5 edge couplers &bull; 27 MZI gates</div>
  <div>54 PPLN SFG elements &bull; 54 detectors</div>
  <div style="margin-top:6px; color:#666;">Waveguide: 800 nm &bull; Bend: 50 &mu;m min</div>
  <div style="color:#666;">Poling: 12.6-13.5 &mu;m periods</div>
</div>
<div id="legend">
  <h3>FAB LAYERS</h3>
</div>
<div id="controls">Scroll: zoom &bull; Drag: pan &bull; Click legend: toggle</div>
<div id="coords">-</div>
<canvas id="c"></canvas>
<script>
const DATA = {json.dumps(shapes)};
const COLORS = {json.dumps(LAYER_COLORS)};

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
const coordsDiv = document.getElementById('coords');
let W, H;
let panX = 0, panY = 0, zoom = 1;
let dragging = false, dragX = 0, dragY = 0;
let hiddenLayers = new Set();

function resize() {{
  W = canvas.width = window.innerWidth;
  H = canvas.height = window.innerHeight;
  draw();
}}

function fitView() {{
  let minX=Infinity, minY=Infinity, maxX=-Infinity, maxY=-Infinity;
  DATA.forEach(s => {{
    if (s.type === 'polygon') {{
      s.points.forEach(p => {{ minX=Math.min(minX,p[0]); minY=Math.min(minY,p[1]); maxX=Math.max(maxX,p[0]); maxY=Math.max(maxY,p[1]); }});
    }}
  }});
  const dw = maxX - minX, dh = maxY - minY;
  const pad = 100;
  zoom = Math.min((W - pad*2) / dw, (H - pad*2) / dh);
  panX = W/2 - (minX + dw/2) * zoom;
  panY = H/2 + (minY + dh/2) * zoom;
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(panX, panY);
  ctx.scale(zoom, -zoom);

  // Draw order: back to front
  const order = ['6_0', '11_0', '5_0', '1_1', '1_0', '2_0', '3_0', '3_1', '4_0', '4_1'];
  order.forEach(lk => {{
    if (hiddenLayers.has(lk)) return;
    DATA.forEach(s => {{
      if (s.type !== 'polygon' || s.layer !== lk) return;
      ctx.beginPath();
      s.points.forEach((p, i) => i === 0 ? ctx.moveTo(p[0], p[1]) : ctx.lineTo(p[0], p[1]));
      ctx.closePath();
      if (lk === '6_0' || lk === '11_0') {{
        ctx.strokeStyle = s.color;
        ctx.lineWidth = Math.max(1, 2 / zoom);
        ctx.stroke();
      }} else {{
        const alpha = lk === '2_0' ? 'bb' : lk === '5_0' ? '44' : '99';
        ctx.fillStyle = s.color + alpha;
        ctx.fill();
        ctx.strokeStyle = s.color;
        ctx.lineWidth = Math.max(0.2, 0.5 / zoom);
        ctx.stroke();
      }}
    }});
  }});

  // Labels (only show when zoomed in enough)
  if (!hiddenLayers.has('10_0') && zoom > 0.15) {{
    ctx.save();
    ctx.scale(1, -1);
    const fontSize = Math.max(4, Math.min(12, 8 / zoom));
    DATA.forEach(s => {{
      if (s.type !== 'label') return;
      ctx.fillStyle = '#aaa';
      ctx.font = `${{fontSize}}px Courier New`;
      ctx.textAlign = 'center';
      ctx.fillText(s.text, s.x, -s.y);
    }});
    ctx.restore();
  }}

  ctx.restore();
}}

// Legend
const legendDiv = document.getElementById('legend');
Object.entries(COLORS).forEach(([lk, [color, name]]) => {{
  const item = document.createElement('div');
  item.className = 'legend-item';
  item.innerHTML = `<div class="legend-swatch" style="background:${{color}}"></div><span>${{name}}</span>`;
  item.onclick = () => {{
    if (hiddenLayers.has(lk)) {{ hiddenLayers.delete(lk); item.style.opacity = '1'; }}
    else {{ hiddenLayers.add(lk); item.style.opacity = '0.3'; }}
    draw();
  }};
  legendDiv.appendChild(item);
}});

// Pan
canvas.addEventListener('mousedown', e => {{ dragging = true; dragX = e.clientX; dragY = e.clientY; }});
canvas.addEventListener('mousemove', e => {{
  // Coordinates display
  const mx = (e.clientX - panX) / zoom;
  const my = -(e.clientY - panY) / zoom;
  coordsDiv.textContent = `${{mx.toFixed(1)}} × ${{my.toFixed(1)}} μm`;

  if (!dragging) return;
  panX += e.clientX - dragX;
  panY += e.clientY - dragY;
  dragX = e.clientX;
  dragY = e.clientY;
  draw();
}});
canvas.addEventListener('mouseup', () => dragging = false);
canvas.addEventListener('mouseleave', () => dragging = false);

// Zoom
canvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const mx = e.clientX, my = e.clientY;
  const factor = e.deltaY < 0 ? 1.2 : 1/1.2;
  panX = mx - (mx - panX) * factor;
  panY = my - (my - panY) * factor;
  zoom *= factor;
  draw();
}}, {{ passive: false }});

window.addEventListener('resize', resize);
resize();
fitView();
draw();
</script>
</body>
</html>
"""

with open("viewer_fab.html", "w") as f:
    f.write(html)
print("viewer_fab.html written")
