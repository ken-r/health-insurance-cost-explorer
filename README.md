# Health Insurance Cost Explorer
Health insurance premiums make up a significant portion of many people’s expenses. Every year, these premiums are adjusted, and switching insurance providers or plans can lead to considerable savings.
However, comparing premiums across different providers together with varying deductible (franchise) levels is often complex and confusing.

This tool (developed with Shiny and Python) simplifies this by enabling you to:

- Compare premium prices from multiple insurance providers side-by-side (similar to the official website [Priminfo](https://www.priminfo.admin.ch/de/praemien))
- Visualize how different deductible levels affect your total out-of-pocket costs (including premiums, deductibles, and the additional expenses that you need to cover).

When it comes to choosing a deductible level as an adult, the rule of thumb that you often hear is as follows:

*If your healthcare costs exceed 2000 CHF, the lowest deductible level (300 CHF) will result in the lowest total costs for you.
Otherwise, the highest deductible level (2500 CHF) is the best option.*

With this visualization tool, you will see that this is (approximately) true for all insurance providers and plans. For some plans, the critical point is slightly below 2000 CHF, for others it is slightly above.

## Data Information

The application uses official Swiss health insurance data for 2027, published by the Federal Office of Public Health (FOPH).

| | |
|---|---|
| **Source** | Federal Office of Public Health ([FOPH](https://www.bag.admin.ch)) |
| **Data year** | 2027 |
| **Downloaded** | 2026-10-24 |
| **Updates** | Data is stored locally in `/data` and updated manually if necessary. |

### Datasets

| File | Description | Source page | Direct download |
|---|---|---|---|
| `premiums.csv` | Health insurance premiums by insurer, region, and insurance model. | [opendata.swiss](https://opendata.swiss/en/dataset/health-insurance-premiums) | [Prämien_CH.csv](https://opendata.bagnet.ch/?r=/download&path=L1ByYWVtaWVuL1Byw6RtaWVuX0NILmNzdg%3D%3D)
| `premium_regions.xlsx` | Mapping of postal codes and municipalities to premium regions. | [Priminfo](https://www.priminfo.admin.ch/de/downloads/aktuell) | [praemienregionen-2027.xlsx](https://www.priminfo.admin.ch/downloads/praemienregionen-2027.xlsx)
| `insurance_model_restrictions.csv` | Regional availability restrictions for insurance models. | [opendata.swiss](https://opendata.swiss/en/dataset/health-insurance-premiums) | [Eingeschr.-Tät.gebiete.csv](https://opendata.bagnet.ch/?r=/download&path=L1ByYWVtaWVuL0Vpbmdlc2Noci4tVMOkdC5nZWJpZXRlLmNzdg%3D%**3D)
| `insurance_providers.xlsx` | Mapping of insurer IDs to insurer names. | [Priminfo](https://www.priminfo.admin.ch/de/downloads/aktuell) | [zugelassene-krankenversicherer-2026-10.xlsx](https://www.priminfo.admin.ch/downloads/zugelassene-krankenversicherer-2026-10.xlsx)

The datasets were downloaded with the direct download link and renamed for consistency.

### Data License

The datasets originate from the Swiss Federal Office of Public Health (FOPH) and are subject to their original terms of use. They are not covered by this project's software license.
