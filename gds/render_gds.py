"""Render hybrid_chip_3x3.gds to an interactive HTML viewer."""
import gdstk
import json

lib = gdstk.read_gds("hybrid_chip_3x3.gds")
top = lib.top_level()[0]

LAYER_COLORS = {
    1:  ("#2196F3", "Input Waveguides"),
    2:  ("#FF5722", "SFG Elements"),
    3:  ("#4CAF50", "Chamber Outline"),
    4:  ("#9C27B0", "Photodetectors"),
    5:  ("#FF9800", "Metal (Column Sum)"),
    6:  ("#607D8B", "Labels"),
    7:  ("#78909C", "Chip Border"),
    8:  ("#8B4513", "Weight Buses (+1/-1)"),
    9:  ("#111111", "Gates (Control)"),
    10: ("#E91E63", "RGB Lasers"),
}

shapes = []

def collect_polygons(cell, dx=0, dy=0):
    for poly in cell.polygons:
        layer = poly.layer
        pts = poly.points.tolist()
        pts = [[p[0] + dx, p[1] + dy] for p in pts]
        color = LAYER_COLORS.get(layer, ("#999", "Unknown"))[0]
        name = LAYER_COLORS.get(layer, ("", "Unknown"))[1]
        shapes.append({"type": "polygon", "points": pts, "color": color, "layer": layer, "name": name})

    for path in cell.paths:
        layer = path.layers[0] if path.layers else 1
        polys = path.to_polygons()
        for poly in polys:
            pts = poly.tolist()
            pts = [[p[0] + dx, p[1] + dy] for p in pts]
            color = LAYER_COLORS.get(layer, ("#999", "Unknown"))[0]
            name = LAYER_COLORS.get(layer, ("", "Unknown"))[1]
            shapes.append({"type": "polygon", "points": pts, "color": color, "layer": layer, "name": name})

    for label in cell.labels:
        layer = label.layer
        x, y = label.origin
        shapes.append({
            "type": "label",
            "text": label.text,
            "x": x + dx,
            "y": y + dy,
            "layer": layer
        })

    for ref in cell.references:
        ref_cell = ref.cell
        ox, oy = ref.origin if hasattr(ref, 'origin') else (0, 0)
        collect_polygons(ref_cell, dx + ox, dy + oy)

collect_polygons(top)

html = f"""<!DOCTYPE html>
<html>
<head>
<title>Wavelength-Ternary Hybrid SFG Chip - GDS Viewer</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ background: #1a1a2e; font-family: 'Courier New', monospace; color: #e0e0e0; overflow: hidden; }}
canvas {{ display: block; cursor: grab; }}
canvas:active {{ cursor: grabbing; }}
#hud {{ position: fixed; top: 15px; left: 15px; background: rgba(0,0,0,0.75); padding: 12px 16px; border-radius: 8px; border: 1px solid #333; font-size: 12px; z-index: 10; }}
#hud h2 {{ color: #4CAF50; margin-bottom: 8px; font-size: 14px; }}
#hud div {{ margin: 2px 0; }}
#legend {{ position: fixed; top: 15px; right: 15px; background: rgba(0,0,0,0.75); padding: 12px 16px; border-radius: 8px; border: 1px solid #333; font-size: 12px; z-index: 10; }}
#legend h3 {{ color: #aaa; margin-bottom: 6px; font-size: 13px; }}
.legend-item {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; cursor: pointer; }}
.legend-item:hover {{ opacity: 0.8; }}
.legend-swatch {{ width: 14px; height: 14px; border-radius: 2px; border: 1px solid #555; }}
#controls {{ position: fixed; bottom: 15px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.75); padding: 8px 16px; border-radius: 8px; border: 1px solid #333; font-size: 11px; color: #888; z-index: 10; }}
</style>
</head>
<body>
<div id="hud">
  <h2>WAVELENGTH-TERNARY HYBRID SFG CHIP</h2>
  <div>3&times;3 SFG chambers &bull; 6 SFG elements each</div>
  <div>54 total SFGs &bull; 27 controllable gates</div>
  <div>3 RGB lasers (always on) &bull; 2 weight buses (+1/-1)</div>
  <div>3 column dot-product summers</div>
</div>
<div id="legend">
  <h3>LAYERS</h3>
</div>
<div id="controls">Scroll: zoom &bull; Drag: pan &bull; Click legend: toggle layers</div>
<canvas id="c"></canvas>
<script>
const DATA = {json.dumps(shapes)};
const COLORS = {json.dumps({str(k): v for k, v in LAYER_COLORS.items()})};

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
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
  const pad = 80;
  zoom = Math.min((W - pad*2) / dw, (H - pad*2) / dh);
  panX = W/2 - (minX + dw/2) * zoom;
  panY = H/2 + (minY + dh/2) * zoom;
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(panX, panY);
  ctx.scale(zoom, -zoom);

  // Draw polygons by layer order (back to front)
  [7, 3, 8, 1, 10, 2, 4, 5, 9].forEach(layer => {{
    if (hiddenLayers.has(layer)) return;
    DATA.forEach(s => {{
      if (s.type !== 'polygon' || s.layer !== layer) return;
      ctx.beginPath();
      s.points.forEach((p, i) => i === 0 ? ctx.moveTo(p[0], p[1]) : ctx.lineTo(p[0], p[1]));
      ctx.closePath();
      if (layer === 7 || layer === 3) {{
        ctx.strokeStyle = s.color;
        ctx.lineWidth = 2 / zoom;
        ctx.stroke();
      }} else if (layer === 9) {{
        // Gates — solid black circles
        ctx.fillStyle = '#222';
        ctx.fill();
        ctx.strokeStyle = '#666';
        ctx.lineWidth = 1 / zoom;
        ctx.stroke();
      }} else {{
        ctx.fillStyle = s.color + (layer === 2 ? 'cc' : 'aa');
        ctx.fill();
        ctx.strokeStyle = s.color;
        ctx.lineWidth = 0.5 / zoom;
        ctx.stroke();
      }}
    }});
  }});

  // Draw labels
  if (!hiddenLayers.has(6)) {{
    ctx.save();
    ctx.scale(1, -1);
    DATA.forEach(s => {{
      if (s.type !== 'label') return;
      ctx.fillStyle = '#ccc';
      ctx.font = `${{Math.max(8, 10/zoom)}}px Courier New`;
      ctx.textAlign = 'center';
      ctx.fillText(s.text, s.x, -s.y);
    }});
    ctx.restore();
  }}

  ctx.restore();
}}

// Legend
const legendDiv = document.getElementById('legend');
Object.entries(COLORS).forEach(([layer, [color, name]]) => {{
  const item = document.createElement('div');
  item.className = 'legend-item';
  const swatchColor = parseInt(layer) === 9 ? '#222' : color;
  item.innerHTML = `<div class="legend-swatch" style="background:${{swatchColor}}"></div><span>${{name}}</span>`;
  item.onclick = () => {{
    const l = parseInt(layer);
    if (hiddenLayers.has(l)) {{ hiddenLayers.delete(l); item.style.opacity = '1'; }}
    else {{ hiddenLayers.add(l); item.style.opacity = '0.3'; }}
    draw();
  }};
  legendDiv.appendChild(item);
}});

// Pan
canvas.addEventListener('mousedown', e => {{ dragging = true; dragX = e.clientX; dragY = e.clientY; }});
canvas.addEventListener('mousemove', e => {{
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
  const factor = e.deltaY < 0 ? 1.15 : 1/1.15;
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

with open("viewer.html", "w") as f:
    f.write(html)
print("viewer.html written")
