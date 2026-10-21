# 3D Digital Twin Viewer (Frontend)

Lightweight, self-contained 3D WebGL digital twin for real-time multi-axis cutting plane visualization and spatial probing of the OpenFOAM CFD solution.

---

## 1. Requirements

* Any modern WebGL-compatible browser (Google Chrome, Firefox, Safari, Edge).
* Local offline dependencies (`lib/three.min.js`, `lib/OrbitControls.js`) are already included. Zero external CDN calls.

---

## 2. How to Run

### Direct Launch
Open `index.html` directly in your browser:
```bash
xdg-open index.html   # Linux
open index.html       # macOS
```

### Local Web Server
```bash
python3 -m http.server 8080
# Open http://localhost:8080 in your browser
```

---

## 3. Data Pipeline Script

To regenerate `data.js` from the OpenFOAM simulation:
```bash
python3 process_slices.py
```
This parses the 100 native VTK cut planes from `../model/postProcessing/` and serializes the triangulated mesh into `data.js`.
