# SLaMA_school

A comprehensive Python framework for **S**eismic **La**teral **M**echanism **A**nalysis (SLaMA) of reinforced concrete building frames. This repository implements the SLaMA methodology for rapid seismic assessment of existing buildings through capacity analysis and performance evaluation.

## Overview

SLaMA_school provides a complete toolkit for:
- **Structural modeling** of 2D reinforced concrete frames
- **Capacity curve computation** using multiple failure mechanisms (beam sway, column sway, mixed sway)
- **Seismic hazard analysis** based on Italian Building Code (NTC2018)
- **Performance assessment** including damage states and expected annual loss
- **Visualization tools** for capacity curves and ADRS plots

## Key Features

### 🏗️ Structural Analysis
- **Frame modeling**: Regular 2D frame geometries with customizable sections
- **Material modeling**: Concrete and steel with nonlinear properties
- **Section analysis**: Moment-curvature relationships, shear capacity, MN domains
- **Element modeling**: Beams and columns with plastic hinge formulations

### 📊 Capacity Analysis
- **Multiple failure mechanisms**:
  - Beam sidesway mechanism
  - Column sidesway mechanism  
  - Mixed sidesway mechanism (classic and improved formulations)
- **Damage modeling**: Post-earthquake capacity reduction with ductility-based factors
- **Subassembly approach**: Joint-level capacity evaluation with hierarchy analysis

### 🌍 Seismic Hazard
- **NTC2018 compliance**: Italian building code seismic spectra
- **Multi-level analysis**: SLD, SLV limit states
- **Soil categories**: A through E soil classifications
- **Importance factors**: Building classification (I-IV)

### 📈 Performance Assessment
- **Intensity measures**: ISV, ISD computation
- **Fragility analysis**: Capacity-demand relationships
- **Loss estimation**: Expected Annual Loss (EAL) calculation
- **ADRS visualization**: Acceleration-displacement response spectra

## Project Structure

```
SLaMA_school/
├── src/                          # Core source code
│   ├── capacity/                 # Capacity analysis algorithms
│   │   ├── beam_sway.py         # Beam sidesway mechanism
│   │   ├── column_sway.py       # Column sidesway mechanism
│   │   ├── mixed_sway.py        # Mixed sidesway (classic)
│   │   ├── mixed_sidesway_correctted.py  # Improved mixed sway
│   │   └── damaged_slama.py     # Post-earthquake analysis
│   ├── concrete/                 # Concrete material models
│   ├── steel/                    # Steel material models
│   ├── sections/                 # Cross-section analysis
│   │   └── basic_section.py     # RC section implementation
│   ├── elements/                 # Structural elements
│   ├── frame/                    # Frame modeling
│   │   ├── regular_frame.py     # 2D frame geometry
│   │   └── graph.py            # Topological representation
│   ├── subassembly.py           # Joint subassembly analysis
│   ├── hazard/                   # Seismic hazard models
│   │   ├── hazard_spectra.py    # Abstract hazard interface
│   │   └── code_NTC2018_spectra.py  # NTC2018 implementation
│   ├── performance/              # Performance assessment
│   │   ├── capacity_demand.py   # ISV/ISD calculations
│   │   └── expected_annual_loss.py  # EAL computation
│   ├── plotting/                 # Visualization tools
│   └── conf/config.yaml         # Configuration settings
├── model/                        # Data models and validation
│   ├── validation/              # Input validation schemas
│   ├── data_models/             # Output data structures
│   └── enums.py                 # Type definitions
├── inputs/                       # Sample input files
├── outputs/                      # Analysis results
├── main.py                      # Main analysis script
├── main_multiframe.py           # Batch processing
└── *.ipynb                      # Jupyter notebooks for analysis
```

## Installation

### Requirements
- Python 3.8+
- Required packages (see `requirements.txt`):
  ```
  pydantic >= 1.9.1
  numpy >= 1.22.4
  pandas >= 1.4.2
  matplotlib >= 3.5.2
  scipy >= 1.8.1
  pyyaml >= 6.0.1
  ```

### Setup
```bash
git clone <repository-url>
cd SLaMA_school
pip install -r requirements.txt
```

## Usage

### Basic Analysis
```python
from pathlib import Path
from main import main

# Run analysis with default inputs
main()
```

### Custom Analysis
```python
from src.frame import RegularFrameBuilder
from src.capacity import mixed_sidesway
from src.hazard import NTC2018SeismicHazard

# Build frame model
frame_builder = RegularFrameBuilder(frame_data, sections, BasicElement)
frame_builder.build_frame()
frame = frame_builder.get_frame()

# Compute capacity
capacity = mixed_sidesway(subassembly_factory, frame)

# Analyze performance
hazard = NTC2018SeismicHazard(...)
performance = compute_ISV(capacity, hazard)
```

### Batch Processing
```bash
# Process multiple buildings
python main_multiframe.py

# Or use shell script
./run_batch.sh
```

## Configuration

The framework uses YAML configuration (`src/conf/config.yaml`) for:

```yaml
nodes:
  tension_kj_values:        # Joint tension factors
  compression_kj_value: 0.6
  external_node_rotation:   # Rotation limits
  internal_node_rotation:
  cracking_rotation: 0.0002

element_settings:
  moment_curvature: 'stress_block'    # Analysis method
  shear_formulation: 'NZSEE2017'      # Shear capacity model
  domain_mn: 'four_points'            # MN domain points

subassembly_settings:
  sub_hierarchy: 'avg'      # Capacity combination method
  sub_stiffness: 'avg'      # Stiffness calculation
```

## Input Format

### Frame Geometry (`Frame.json`)
```json
{
  "L": [0.0, 6.0, 12.0],           # Column positions [m]
  "H": [3.5, 7.0, 10.5],          # Floor heights [m]  
  "m": [180000, 180000, 90000],    # Floor masses [kg]
  "loads": [...],                   # Nodal loads [N]
  "columns": [[...], [...]],        # Column section IDs
  "beams": [[...], [...]]          # Beam section IDs
}
```

### Materials (`Materials.json`)
```json
{
  "steel": {
    "id": "B450C",
    "fy": 450e6,
    "fu": 540e6,
    "E": 200e9,
    "epsilon_u": 0.075
  },
  "concrete": {
    "id": "C25/30",
    "fc": 25e6,
    "E": 31000e6,
    "epsilon_0": 0.002,
    "epsilon_u": 0.0035
  }
}
```

### Sections (`Sections.json`)
```json
{
  "beams": [{
    "id": 1,
    "b": 0.30,
    "h": 0.50,
    "As": 0.001256,
    "As1": 0.000628,
    "cover": 0.04,
    "s": 0.15,
    "Ast": 0.000157
  }],
  "columns": [...]
}
```

## Methodological Background

### SLaMA Methodology
The **S**eismic **La**teral **M**echanism **A**nalysis (SLaMA) method provides rapid assessment of RC buildings through:

1. **Hierarchy identification**: Determine critical failure mechanisms
2. **Capacity evaluation**: Compute force-displacement relationships  
3. **Demand assessment**: Apply seismic hazard spectra
4. **Performance quantification**: Evaluate limit state exceedance

### Failure Mechanisms
- **Beam sway**: Plastic hinges form in beams
- **Column sway**: Plastic hinges form in columns  
- **Mixed sway**: Combined beam-column yielding
- **Joint failure**: Beam-column connection failure

### Analysis Features
- **Nonlinear section analysis**: Stress-block method for moment-curvature
- **Shear capacity**: NZSEE2017 formulation with size effects
- **Damage modeling**: Stiffness/strength degradation with ductility
- **Multi-level assessment**: Damage limitation (SLD) and life safety (SLV)

## Scientific Background

This implementation is based on established research in seismic assessment:

- **SLaMA methodology**: Rossetto & Elnashai (2003), Kappos et al. (2013)
- **RC modeling**: NZSEE guidelines (2017), Eurocode 8
- **Damage models**: Di Ludovico et al. (2013)
- **Italian seismic code**: NTC2018, Circolare 2019

## Project Team

| Role          	    | Team Member 	        |
|---------------------|----------------------|
| Development Lead 	  | Livio Pedone 	      |
| Developer  	        | Simone D'Amore       |
| Developer 	          | Michele Matteoni     |
| Developer      	    | Giada Formichetti    |
| Technical Lead 	    | Simona Bianchi       |
| Infrastructure Lead | Jonathan Ciurlanti   |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the terms specified in the LICENSE file.

## Citation

If you use this software in your research, please cite:

```bibtex
@software{slama_school,
  title={SLaMA_school: A Python Framework for Seismic Assessment of RC Buildings},
  author={Pedone, Livio and D'Amore, Simone and Matteoni, Michele and Formichetti, Giada and Bianchi, Simona and Ciurlanti, Jonathan},
  year={2024},
  url={https://github.com/...}
}
```

## Core Modules and Algorithms

### Materials and Sections

#### Material Models
- **Concrete** (`src/concrete/`):
  - Stress-strain relationships with compressive strength `fc`
  - Elastic modulus `E` and ultimate strain `epsilon_u`
  - Support for different concrete grades (C25/30, etc.)

- **Steel** (`src/steel/`):
  - Yield strength `fy` and ultimate strength `fu`
  - Elastic modulus and ultimate elongation
  - B450C standard reinforcement properties

#### Section Analysis (`src/sections/basic_section.py`)
- **Moment-Curvature**: Analytical stress-block method
  - Yielding point computation with axial interaction
  - Ultimate capacity considering concrete crushing
  - Bilinear approximation for pushover analysis

- **Shear Capacity**: NZSEE2017 formulation
  - Concrete contribution with size effects
  - Steel stirrup contribution
  - Axial load interaction effects

- **MN Domains**: Four-point interaction diagrams
  - Pure tension, compression, balanced, and limit points
  - Support for biaxial bending analysis

### Frame Modeling (`src/frame/`)

#### Regular Frame Builder
- **Topology**: Graph-based representation of 2D frames
- **Geometry**: Span lengths, story heights, column positioning
- **Mass Distribution**: Floor masses for dynamic analysis
- **Load Assignment**: Tributary area loads and axial forces

#### Node Classification
- **Internal/External**: Different joint behavior models
- **Top/Base**: Boundary condition handling
- **Tension Factors**: `kj` values for joint capacity

### Capacity Analysis (`src/capacity/`)

#### Failure Mechanisms

1. **Beam Sidesway** (`beam_sway.py`)
   - Plastic hinges form in beams first
   - Column moments resist overturning
   - Suitable for strong-column weak-beam design

2. **Column Sidesway** (`column_sway.py`)
   - Plastic hinges form in columns
   - Critical for older buildings
   - Lower displacement capacity

3. **Mixed Sidesway** (`mixed_sway.py`)
   - Combined beam-column yielding
   - Realistic behavior for most structures
   - Two formulations: classic and improved

4. **Improved Mixed Sway** (`mixed_sidesway_correctted.py`)
   - Considers subassembly stiffness distribution
   - Lower yielding criterion
   - More accurate capacity prediction

#### Subassembly Approach (`src/subassembly.py`)
- **Joint Analysis**: Beam-column connection behavior
- **Hierarchy Rules**: Determine critical failure mode
- **Stiffness Combination**: Parallel element interaction
- **Axial Effects**: P-M interaction in columns

### Damage Modeling (`src/capacity/damaged_slama.py`)

#### Post-Earthquake Assessment
- **Ductility-Based Factors**:
  - Stiffness reduction factor `K`
  - Strength reduction factor `Q`
  - Residual drift `res`

- **Element-Specific Models**:
  - Beam/Column: Di Ludovico et al. (2013) formulation
  - Joints: Simplified stiffness degradation
  - Progressive deterioration with ductility

### Seismic Hazard (`src/hazard/`)

#### NTC2018 Compliance (`code_NTC2018_spectra.py`)
- **Soil Categories**: A through E classification
- **Response Spectra**: Elastic acceleration spectra
- **Limit States**: SLD (damage), SLV (life safety)
- **Site Effects**: Topographic and soil amplification

#### Spectral Analysis
- **Periods**: Automatic period array generation
- **Damping**: Variable damping with ductility
- **Displacement**: Conversion to displacement spectra

### Performance Assessment (`src/performance/`)

#### Intensity Measures (`capacity_demand.py`)
- **IS-V**: Intensity measure for ultimate limit state
- **IS-D**: Intensity measure for damage limit state
- **Effective Period**: Based on capacity curve secant
- **Damping**: Ductility-dependent equivalent damping

#### Loss Estimation (`expected_annual_loss.py`)
- **PAM**: Probabilistic Assessment Method per NTC2018
- **Fragility**: Limit state exceedance probabilities
- **Loss Ratios**: Damage-to-replacement cost ratios
- **Annual Frequency**: Seismic hazard integration

### Visualization (`src/plotting/`)

#### Capacity Curves (`capacity_curves.py`)
- **ADRS Plots**: Acceleration-Displacement Response Spectra
- **Multi-Mechanism**: Overlay different failure modes
- **Scaled Spectra**: Intensity measure visualization
- **Performance Points**: Capacity-demand intersections

## Algorithm Details

### Capacity Computation Workflow

1. **Subassembly Creation**
   ```python
   subassembly_factory = SubassemblyFactory(frame=frame)
   ```

2. **Mechanism Analysis**
   ```python
   beam_capacity = beam_sidesway(subassembly_factory, frame)
   column_capacity = column_sidesway(subassembly_factory, frame)
   mixed_capacity = mixed_sidesway(subassembly_factory, frame)
   ```

3. **Performance Evaluation**
   ```python
   hazard = NTC2018SeismicHazard(hazard_input)
   IS_V = compute_ISV(capacity, hazard)
   IS_D = compute_ISD(capacity, hazard)
   ```

### Numerical Methods

- **Root Finding**: `scipy.optimize.fsolve` for equilibrium
- **Integration**: Trapezoidal rule for areas under curves
- **Interpolation**: Linear interpolation for spectra
- **Caching**: `@cache` decorator for computational efficiency
