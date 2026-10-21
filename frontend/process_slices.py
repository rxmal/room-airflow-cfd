#!/usr/bin/env python3
import json
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "../model/postProcessing"))
DATA_JS = os.path.join(SCRIPT_DIR, "data.js")

def parse_cutplane(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()
    pts, polys, fields = [], [], {}
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("POINTS"):
            n_pts = int(line.split()[1])
            i += 1
            while len(pts) < n_pts * 3 and i < len(lines):
                parts = lines[i].strip().split()
                if parts:
                    pts.extend([float(x) for x in parts])
                i += 1
            continue
        elif line.startswith("POLYGONS"):
            parts = line.split()
            total_ints = int(parts[2])
            i += 1
            poly_ints = []
            while len(poly_ints) < total_ints and i < len(lines):
                parts = lines[i].strip().split()
                if parts:
                    poly_ints.extend([int(x) for x in parts])
                i += 1
            idx = 0
            while idx < len(poly_ints):
                nv = poly_ints[idx]
                idx += 1
                v = poly_ints[idx:idx+nv]
                idx += nv
                if nv == 3:
                    polys.extend(v)
                elif nv == 4:
                    polys.extend([v[0], v[1], v[2], v[0], v[2], v[3]])
                elif nv > 4:
                    for k in range(1, nv-1):
                        polys.extend([v[0], v[k], v[k+1]])
            continue
        elif line.startswith("POINT_DATA"):
            i += 1
            while i < len(lines) and not lines[i].startswith("FIELD attributes"):
                i += 1
            if i < len(lines):
                nfields = int(lines[i].strip().split()[2])
                i += 1
                for _ in range(nfields):
                    while i < len(lines) and not lines[i].strip():
                        i += 1
                    if i >= len(lines):
                        break
                    hdr = lines[i].strip().split()
                    fname = hdr[0]
                    ncomp = int(hdr[1])
                    ntup = int(hdr[2])
                    i += 1
                    vals = []
                    while len(vals) < ncomp * ntup and i < len(lines):
                        parts = lines[i].strip().split()
                        if parts:
                            vals.extend([float(x) for x in parts])
                        i += 1
                    fields[fname] = vals
            break
        i += 1

    U_data = fields.get("U", [])
    U_mag = []
    for k in range(0, len(U_data), 3):
        ux, uy, uz = U_data[k], U_data[k+1], U_data[k+2]
        U_mag.append(math.sqrt(ux*ux + uy*uy + uz*uz))

    return {
        "points": [round(p, 3) for p in pts],
        "indices": polys,
        "U_mag": [round(v, 3) for v in U_mag],
        "age": [round(v, 2) for v in fields.get("age", [])],
        "p": [round(v, 3) for v in fields.get("p", [])],
        "k": [round(v, 4) for v in fields.get("k", [])]
    }

def main():
    print("Parsing all native OpenFOAM cutting planes...")

    # 1. Z Slices: 0.20 to 2.80m, step 0.10m
    z_dict = {}
    for iz in range(2, 29):
        z = iz / 10.0
        fpath = os.path.join(BASE_DIR, f"allCutPlanes/2000/z_{z:.2f}.vtk".replace(".", "_").replace("_vtk", ".vtk"))
        if os.path.exists(fpath):
            z_dict[f"{z:.2f}"] = parse_cutplane(fpath)
    print(f"Loaded {len(z_dict)} Z-slices (Elevation)")

    # 2. X Slices: 0.40 to 9.20m, step 0.20m
    x_dict = {}
    for ix in range(4, 93, 2):
        x = ix / 10.0
        fpath = os.path.join(BASE_DIR, f"multiAxisPlanes/2000/x_{x:.2f}.vtk".replace(".", "_").replace("_vtk", ".vtk"))
        if os.path.exists(fpath):
            x_dict[f"{x:.2f}"] = parse_cutplane(fpath)
    print(f"Loaded {len(x_dict)} X-slices (Longitudinal)")

    # 3. Y Slices: 0.40 to 5.80m, step 0.20m
    y_dict = {}
    for iy in range(4, 59, 2):
        y = iy / 10.0
        fpath = os.path.join(BASE_DIR, f"multiAxisPlanes/2000/y_{y:.2f}.vtk".replace(".", "_").replace("_vtk", ".vtk"))
        if os.path.exists(fpath):
            y_dict[f"{y:.2f}"] = parse_cutplane(fpath)
    print(f"Loaded {len(y_dict)} Y-slices (Transverse)")

    # Load existing data.js
    with open(DATA_JS, "r") as f:
        text = f.read()

    prefix = "window.BUILDING_CFD_DATA = "
    json_str = text[text.find("{"):text.rfind("}")+1]
    dataset = json.loads(json_str)

    # Attach all multi-axis slices
    dataset["native_slices"] = z_dict
    dataset["native_slices_z"] = z_dict
    dataset["native_slices_x"] = x_dict
    dataset["native_slices_y"] = y_dict
    dataset["paraview_slice"] = z_dict.get("1.50", list(z_dict.values())[0])

    with open(DATA_JS, "w") as f:
        f.write(prefix + json.dumps(dataset) + ";\n")

    final_size_kb = os.path.getsize(DATA_JS) // 1024
    print(f"Successfully updated {DATA_JS} with 3-axis native cut planes! File size: {final_size_kb} KB ({final_size_kb/1024:.2f} MB)")

if __name__ == "__main__":
    main()
