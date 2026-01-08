# gamspy-data-driven-dynamic-humanitarian-allocation-ngo-telegram-analytics
Data driven humanitarian resource allocation for NGOs using Telegram DAta and optimization models built with GAMSPy.

## Setup

```bash
pip install -r requirements.txt
```

## Input Data

Create these CSV files in `Input_Data/`:

### demand(i,k,r,t).csv
Columns: `t,Location,month,service_medical_L,service_medical_M,service_medical_H,service_info_legal_L,service_info_legal_M,service_info_legal_H,product_food_clothing_L,product_food_clothing_M,product_food_clothing_H,product_nonfood_items_clothing_L,product_nonfood_items_clothing_M,product_nonfood_items_clothing_H,product_housing_L,product_housing_M,product_housing_H`

- `t`: time period (0, 1, 2, ...)
- `Location`: location name
- `month`: date (YYYY-MM-DD)
- Other columns: demand values for each item-risk combination

### procurement_allowance.csv
Columns: `Location,Allowed`

- `Location`: location name
- `Allowed`: 1 if can procure, 0 otherwise

## Config

Edit `model_config.yaml`:
- `costs`: shipment, procurement, holding, wage, relocation
- `capacity`: staff capacity, total staff available
- `budget.per_period`: budget per time period
- `penalties`: backlog penalties by item/risk/age
- `policy.procurement_origin`: which location procures

## Run

```bash
python main.py
```

Results in `output/`:
- `csvs/`: decision variables
- `reports/`: summary, Excel report
- `visualizations/`: map visualization (open HTML file)

## License

MIT
