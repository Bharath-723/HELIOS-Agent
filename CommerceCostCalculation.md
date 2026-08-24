# HELIOS — Cost Calculation Subsystem

## Financial Breakdown Formula

`CommerceCalculator` calculates the financial total:

$$\text{Total INR} = \text{Item Price} + \text{Shipping Fee} + \text{Tax}$$
$$\text{Total Paise} = \text{Total INR} \times 100$$

## Exact vs Estimated Totals

The system explicitly labels whether taxes and shipping fees are exact or estimated before transaction preparation.
