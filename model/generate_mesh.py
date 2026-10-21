#!/usr/bin/env python3
"""
Generate a realistic 3D Multi-Room Building blockMeshDict for OpenFOAM.
Layout:
  - 2 Windward Offices (Room 1 & Room 2) with exterior windows
  - Central Corridor / Hallway connected via interior doorways
  - Leeward Meeting / Common Hall (Room 3) with 2 high exhaust windows
  - Real wall thickness (0.2 m) on all exterior and interior partition walls
"""

import os

# Coordinates definition
X = [0.0, 0.2, 4.0, 4.2, 5.4, 5.6, 9.4, 9.6]
Y = [0.0, 0.2, 0.8, 2.2, 2.8, 3.4, 4.0, 5.4, 6.0, 6.2]
Z = [0.0, 0.9, 2.1, 2.4, 3.0]

# Cell counts per interval
NX = [2, 18, 2, 8, 2, 18, 2]
NY = [2, 4, 10, 4, 4, 4, 10, 4, 2]
NZ = [6, 8, 2, 4]

Nx, Ny, Nz = len(X) - 1, len(Y) - 1, len(Z) - 1

# Helper to identify fluid blocks (i, j, k)
def is_fluid(i, j, k):
    # i=0: West exterior wall window openings
    if i == 0:
        if j == 2 and k == 1: # Window 1
            return True
        if j == 6 and k == 1: # Window 2
            return True
        return False

    # i=1: Rooms 1 and 2
    if i == 1:
        if j in [1, 2, 3]: # Room 1 (South)
            return True
        if j in [5, 6, 7]: # Room 2 (North)
            return True
        return False # j=4 is solid partition wall

    # i=2: Partition wall between Rooms 1/2 and Corridor (contains Door 1 & Door 2)
    if i == 2:
        if j == 2 and k in [0, 1]: # Door 1 (height up to 2.1m)
            return True
        if j == 6 and k in [0, 1]: # Door 2 (height up to 2.1m)
            return True
        return False

    # i=3: Central Corridor
    if i == 3:
        if j in [1, 2, 3, 4, 5, 6, 7]:
            return True
        return False

    # i=4: Corridor to Room 3 wall (contains central double archway)
    if i == 4:
        if j in [3, 4, 5] and k in [0, 1, 2]: # Archway (Y: 2.2 to 4.0m, Z up to 2.4m)
            return True
        return False

    # i=5: Room 3 (East Leeward Space)
    if i == 5:
        if j in [1, 2, 3, 4, 5, 6, 7]:
            return True
        return False

    # i=6: East exterior wall exhaust windows
    if i == 6:
        if j == 2 and k in [1, 2]: # Exhaust Window 1 (Z: 0.9 to 2.4m)
            return True
        if j == 6 and k in [1, 2]: # Exhaust Window 2 (Z: 0.9 to 2.4m)
            return True
        return False

    return False

# Vertex index map: (ix, iy, iz) -> vertex_id
vertex_map = {}
vertices = []
vid = 0
for iz in range(len(Z)):
    for iy in range(len(Y)):
        for ix in range(len(X)):
            vertex_map[(ix, iy, iz)] = vid
            vertices.append((X[ix], Y[iy], Z[iz]))
            vid += 1

# Generate fluid blocks
blocks = []
fluid_cells = set()
for k in range(Nz):
    for j in range(Ny):
        for i in range(Nx):
            if is_fluid(i, j, k):
                fluid_cells.add((i, j, k))

# Block vertices mapping for OpenFOAM hex:
# v0=(i, j, k), v1=(i+1, j, k), v2=(i+1, j+1, k), v3=(i, j+1, k)
# v4=(i, j, k+1), v5=(i+1, j, k+1), v6=(i+1, j+1, k+1), v7=(i, j+1, k+1)
for (i, j, k) in fluid_cells:
    v0 = vertex_map[(i, j, k)]
    v1 = vertex_map[(i+1, j, k)]
    v2 = vertex_map[(i+1, j+1, k)]
    v3 = vertex_map[(i, j+1, k)]
    v4 = vertex_map[(i, j, k+1)]
    v5 = vertex_map[(i+1, j, k+1)]
    v6 = vertex_map[(i+1, j+1, k+1)]
    v7 = vertex_map[(i, j+1, k+1)]
    blocks.append(((v0, v1, v2, v3, v4, v5, v6, v7), (NX[i], NY[j], NZ[k])))

# Boundary faces
patches = {
    'inlet_window1': [],
    'inlet_window2': [],
    'outlet_window1': [],
    'outlet_window2': [],
    'floor': [],
    'ceiling': [],
    'walls': []
}

for (i, j, k) in fluid_cells:
    # x_min (i, j, k) to (i, j+1, k+1)
    if (i-1, j, k) not in fluid_cells:
        face = (vertex_map[(i, j, k)], vertex_map[(i, j, k+1)], vertex_map[(i, j+1, k+1)], vertex_map[(i, j+1, k)])
        if i == 0 and j == 2 and k == 1:
            patches['inlet_window1'].append(face)
        elif i == 0 and j == 6 and k == 1:
            patches['inlet_window2'].append(face)
        else:
            patches['walls'].append(face)

    # x_max (i+1, j, k) to (i+1, j+1, k+1)
    if (i+1, j, k) not in fluid_cells:
        face = (vertex_map[(i+1, j, k)], vertex_map[(i+1, j+1, k)], vertex_map[(i+1, j+1, k+1)], vertex_map[(i+1, j, k+1)])
        if i == 6 and j == 2 and k in [1, 2]:
            patches['outlet_window1'].append(face)
        elif i == 6 and j == 6 and k in [1, 2]:
            patches['outlet_window2'].append(face)
        else:
            patches['walls'].append(face)

    # y_min (i, j, k) to (i+1, j, k+1)
    if (i, j-1, k) not in fluid_cells:
        face = (vertex_map[(i, j, k)], vertex_map[(i+1, j, k)], vertex_map[(i+1, j, k+1)], vertex_map[(i, j, k+1)])
        patches['walls'].append(face)

    # y_max (i, j+1, k) to (i+1, j+1, k+1)
    if (i, j+1, k) not in fluid_cells:
        face = (vertex_map[(i, j+1, k)], vertex_map[(i, j+1, k+1)], vertex_map[(i+1, j+1, k+1)], vertex_map[(i+1, j+1, k)])
        patches['walls'].append(face)

    # z_min (i, j, k) to (i+1, j+1, k)
    if (i, j, k-1) not in fluid_cells:
        face = (vertex_map[(i, j, k)], vertex_map[(i, j+1, k)], vertex_map[(i+1, j+1, k)], vertex_map[(i+1, j, k)])
        if k == 0:
            patches['floor'].append(face)
        else:
            patches['walls'].append(face)

    # z_max (i, j, k+1) to (i+1, j+1, k+1)
    if (i, j, k+1) not in fluid_cells:
        face = (vertex_map[(i, j, k+1)], vertex_map[(i+1, j, k+1)], vertex_map[(i+1, j+1, k+1)], vertex_map[(i, j+1, k+1)])
        if k == Nz - 1:
            patches['ceiling'].append(face)
        else:
            patches['walls'].append(face)

# Write blockMeshDict
script_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(script_dir, 'system/blockMeshDict')
with open(out_path, 'w') as f:
    f.write("""/*--------------------------------*- C++ -*----------------------------------*\\
  =========                 |
  \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\\\    /   O peration     | Website:  https://openfoam.org
    \\\\  /    A nd           | Version:  14
     \\\\/     M anipulation  |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    format      ascii;
    class       dictionary;
    location    "system";
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

scale   1;

vertices
(
""")
    for v in vertices:
        f.write(f"    ({v[0]:.4f} {v[1]:.4f} {v[2]:.4f})\n")
    f.write(");\n\nblocks\n(\n")
    for b in blocks:
        pts = " ".join(str(idx) for idx in b[0])
        cells = f"({b[1][0]} {b[1][1]} {b[1][2]})"
        f.write(f"    hex ({pts}) {cells} simpleGrading (1 1 1)\n")
    f.write(");\n\nedges\n(\n);\n\nboundary\n(\n")

    # Inlets
    for name in ['inlet_window1', 'inlet_window2']:
        f.write(f"    {name}\n    {{\n        type patch;\n        faces\n        (\n")
        for face in patches[name]:
            f.write(f"            ({' '.join(str(x) for x in face)})\n")
        f.write("        );\n    }\n\n")

    # Outlets
    for name in ['outlet_window1', 'outlet_window2']:
        f.write(f"    {name}\n    {{\n        type patch;\n        faces\n        (\n")
        for face in patches[name]:
            f.write(f"            ({' '.join(str(x) for x in face)})\n")
        f.write("        );\n    }\n\n")

    # Floor, Ceiling, Walls
    for name in ['floor', 'ceiling', 'walls']:
        f.write(f"    {name}\n    {{\n        type wall;\n        faces\n        (\n")
        for face in patches[name]:
            f.write(f"            ({' '.join(str(x) for x in face)})\n")
        f.write("        );\n    }\n\n")

    f.write(");\n\n// ************************************************************************* //\n")

print(f"Generated {len(blocks)} fluid blocks and {len(vertices)} vertices.")
for k, v in patches.items():
    print(f"Patch {k}: {len(v)} faces")
