# GAMSPy Data-Driven Dynamic Humanitarian Allocation

A data-driven optimization framework for dynamic humanitarian resource allocation using **GAMSPy**.  
The model integrates demand signals (e.g., derived from Telegram analytics), operational constraints, and policy parameters to optimize multi-period allocation of staff and products under budget, capacity, and fairness considerations.

---

## Repository Structure

```
.
├── Input_Data/                 # Input CSV files (not tracked in git)
│   ├── demand(i,k,r,t).csv
│   └── procurement_allowance.csv
├── output/                     # Model outputs (auto-generated, not tracked in git)
│   ├── csvs/
│   ├── reports/
│   └── visualizations/
├── src/                        # Model components (sets, parameters, variables, constraints)
├── main.py                     # Main execution entry point
├── model_config.yaml           # Model configuration file
├── requirements.txt            # Python dependencies
├── README.md
└── LICENSE
```

---

## Requirements

- Python 3.9–3.11 (recommended: 3.10)
- GAMS installed and available in system PATH
- pip or conda environment manager

Verify GAMS installation:

```bash
gams
```

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/Amirwpi/gamspy-data-driven-dynamic-humanitarian-allocation-ngo-telegram-analytics.git
cd gamspy-data-driven-dynamic-humanitarian-allocation-ngo-telegram-analytics
```

### Create and Activate a Virtual Environment (Recommended)

**Conda**

```bash
conda create -n gamspy-env python=3.10 -y
conda activate gamspy-env
```

**venv**

```bash
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Input Data

Create the following CSV files inside the `Input_Data/` directory.

---

### 1. `demand(i,k,r,t).csv`

#### Columns

```
t,
Location,
month,
service_medical_L,
service_medical_M,
service_medical_H,
service_info_legal_L,
service_info_legal_M,
service_info_legal_H,
product_food_clothing_L,
product_food_clothing_M,
product_food_clothing_H,
product_nonfood_items_clothing_L,
product_nonfood_items_clothing_M,
product_nonfood_items_clothing_H,
product_housing_L,
product_housing_M,
product_housing_H
```

#### Definitions

- **t**: Time period index (0, 1, 2, ...)
- **Location**: Location / node name
- **month**: Date in format `YYYY-MM-DD`
- **Remaining columns**: Demand values for each service/product and risk class (L / M / H)

#### Minimal Example

```csv
t,Location,month,service_medical_L,service_medical_M,service_medical_H,service_info_legal_L,service_info_legal_M,service_info_legal_H,product_food_clothing_L,product_food_clothing_M,product_food_clothing_H,product_nonfood_items_clothing_L,product_nonfood_items_clothing_M,product_nonfood_items_clothing_H,product_housing_L,product_housing_M,product_housing_H
0,Kyiv,2025-01-01,10,5,2,8,4,1,20,10,5,15,7,3,12,6,2
1,Kyiv,2025-02-01,12,6,3,9,5,2,22,11,6,16,8,4,13,7,3
```

---

### 2. `procurement_allowance.csv`

#### Columns

```
Location,Allowed
```

#### Definitions

- **Location**: Location name
- **Allowed**: `1` if procurement is allowed at this location, `0` otherwise

#### Example

```csv
Location,Allowed
Kyiv,1
Lviv,0
```

---

## Configuration

Edit `model_config.yaml` to specify model parameters.

### Key Sections

```yaml
costs:
  shipment: ...
  procurement: ...
  holding: ...
  wage: ...
  relocation: ...

capacity:
  staff_capacity: ...
  total_staff: ...

budget:
  per_period: ...

penalties:
  backlog: ...

policy:
  procurement_origin: ...
```

### Important Notes

- Budgets and capacities must be strictly positive to avoid infeasibility.
- Penalty values control backlog aging and service prioritization behavior.
- Procurement policy determines which locations can serve as sourcing nodes.

---

## Running the Model

From the repository root:

```bash
python main.py
```

If execution is successful, outputs will be generated in:

```
output/
 ├── csvs/            # Decision variables and raw outputs
 ├── reports/         # Summary tables and Excel reports
 └── visualizations/  # Interactive maps and charts (HTML)
```

Open visualization files directly in a browser.

---

## Reproducibility Notes

- Input data and outputs should NOT be committed to Git.
- Only configuration, code, and documentation should be version-controlled.
- For large-scale experiments, consider batch execution and logging.

---

## Recommended `.gitignore`

Create or update `.gitignore`:

```gitignore
# Data and outputs
Input_Data/
output/

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
*.log

# Virtual environments
venv/
.env/

# IDE
.vscode/
.idea/
```

---

## Troubleshooting

### GAMS Not Found

If `gams` is not recognized:

1. Install GAMS from the official website.
2. Add the GAMS installation directory to your system PATH.

---

### Dependency Issues

Reinstall dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Model Infeasible or Crashes

Check:

- Input CSV formatting and column names.
- Budget and capacity values in `model_config.yaml`.
- All locations in demand data exist in procurement allowance data.

---

## License

MIT License  
Copyright (c) 2026 Amir Jamali
