# OpenFOAM Physics Simulation Model

This folder contains the full OpenFOAM CFD case including all converged solution time-steps, raw VTK exports, post-processing planes, and mesh generation scripts.

---

## 1. Requirements

* **OpenFOAM**: OpenFOAM 14 (Foundation) or OpenFOAM-dev / v11 / v12 / v2212+
  ```bash
  source /opt/openfoam14/etc/bashrc
  ```
* **Post-Processing / Visualization**:
  * ParaView (v5.10+)
  * `foamToVTK` (included with OpenFOAM)
* **Python**: Python 3.8+ (for procedural blockMesh generation: `python3 generate_mesh.py`)

---

## 2. Model Specifications

* **Domain Dimensions**: $9.60\,\text{m} \times 6.20\,\text{m} \times 3.00\,\text{m}$ (Volume: $149.8\,\text{m}^3$)
* **Layout**: 2 Windward Offices (Rooms 1 & 2), Central Corridor, Leeward Conference Hall (Room 3) with $0.20\,\text{m}$ solid wall thickness throughout.
* **Mesh**: 35,424 structured hexahedral cells generated via `generate_mesh.py`.
* **Flow Physics**:
  * Incompressible steady-state Reynolds-Averaged Navier–Stokes (RANS) with SIMPLE coupling (`foamRun` / `simpleFoam`).
  * Turbulence Closure: Standard $k$-$\varepsilon$ model with logarithmic wall functions (`nutkWallFunction`, `kqRwallFunction`, `epsilonWallFunction`).
  * Indoor Air Quality: Passive scalar transport equation for Local Mean Age of Air ($\tau$).

### Boundary Conditions

| Patch | Type | Velocity ($\mathbf{U}$) | Gauge Pressure ($p$) | Age of Air ($\tau$) |
| :--- | :--- | :--- | :--- | :--- |
| `inlet_window1` | Inflow Aperture | `fixedValue (1.5 0.1 0) m/s` | `zeroGradient` | `0 s` |
| `inlet_window2` | Inflow Aperture | `fixedValue (1.2 -0.1 0) m/s` | `zeroGradient` | `0 s` |
| `outlet_window1`| Leeward Exhaust | `pressureInletOutletVelocity` | `fixedValue 0 m²/s²` | `zeroGradient` |
| `outlet_window2`| Leeward Exhaust | `pressureInletOutletVelocity` | `fixedValue 0 m²/s²` | `zeroGradient` |
| `walls` / `floor` / `ceiling` | Solid Boundaries | `noSlip` | `zeroGradient` | `zeroGradient` |

* **Total Airflow Intake**: $Q = 4.536\,\text{m}^3/\text{s} = 16,330\,\text{m}^3/\text{h}$
* **Ventilation Rate**: $109\,\text{ACH}$ (Air Changes per Hour)

---

## 3. Contents & Generated Data

* `0/`: Initial boundary conditions.
* `2000/`: Converged solution fields (`U`, `p`, `phi`, `k`, `epsilon`, `nut`, `age`).
* `constant/`: Physical properties, turbulence selection, and generated `polyMesh/`.
* `system/`: Solver controls, schemes (`fvSchemes`, `fvSolution`), and cut plane sampling dictionaries (`multiAxisPlanes`, `allCutPlanes`).
* `VTK/`: Volumetric VTK export (`multiRoomBuilding_2000.vtk`) and boundary patches.
* `postProcessing/`: 100 native cutting planes (VTK format across $Z$, $X$, $Y$) and probe point histories.
* `multiRoomBuilding.foam`: Dummy file to load the entire simulation directly in ParaView.

---

## 4. How to Run / Inspect

### Inspect in ParaView
```bash
paraview multiRoomBuilding.foam
# or open VTK/multiRoomBuilding_2000.vtk
```

### Re-run Simulation from Scratch
```bash
# Clean previous run
./Allclean

# Execute meshing, solver, age post-processing, and VTK export
./Allrun
```
