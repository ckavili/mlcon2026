# Recorded local rehearsals

These are actual generated responses, not templates. They are examples, not live results or a reliability benchmark. All data is synthetic.

## products

Recorded: 2026-11-15T20:54:43.236217+00:00; duration: 6.9 seconds.

Prompt:

What mortgage products does Fedaura offer? Look up the product catalog and summarize three options briefly.

Observed tools: product_info

Response:

```text
Fedaura offers several mortgage products, including:

1. 30-Year Fixed Conventional: A standard fixed-rate option with a minimum 3% down payment and a typical rate of 6.5%. Ideal for long-term homeownership.
2. 15-Year Fixed Conventional: Offers a shorter term with higher monthly payments but less total interest, requiring at least 3% down and typically carrying a 5.75% rate.
3. FHA Loan: A government-backed loan allowing lower credit scores and a minimum 3.5% down payment, though it includes mortgage insurance premiums.

Other options include VA Loans (0% down for eligible veterans), Jumbo Loans (for high-value properties), USDA Loans (zero down for rural areas), and 5/1 Adjustable Rate Mortgages.
```

## affordability

Recorded: 2026-11-15T20:48:44.366825+00:00; duration: 11.1 seconds.

Prompt:

Use the affordability calculator for this synthetic example: gross annual income $102,000, monthly debt payments $2,400, down payment $80,000, interest rate 6.5%, and a 30-year loan. Give the estimated maximum loan, purchase price and monthly payment. Keep it brief.

Observed tools: affordability_calc

Response:

```text
Based on your inputs, the estimated maximum loan amount is $198,554.58. With an $80,000 down payment, the estimated purchase price is $278,554.58. The estimated monthly payment for this loan is $1,255.00, resulting in a debt-to-income (DTI) ratio of 43.0%.
```

## risk

Recorded: 2026-11-15T20:50:24.371111+00:00; duration: 8.0 seconds.

Prompt:

For a standalone synthetic example, use your external risk tools to calculate DTI and LTV and evaluate credit risk: monthly income $8,500, monthly debts $2,400, loan amount $320,000, property value $400,000, and self-reported credit score 742. Give the three values and their risk ratings. Do not make a lending decision or look up an application.

Observed tools: calculate_dti, calculate_ltv, evaluate_credit_risk

Response:

```text
Here are the standalone risk calculations:

- DTI: 28.2% (Low) – Well within conventional guidelines.
- LTV: 80.0% (Medium) – At the upper boundary of acceptable levels.
- Credit Risk: 742 (Low) – Based on self-reported score, indicating strong creditworthiness.

All three factors are calculated independently without a full underwriting recommendation or application lookup.
```

## queue

Recorded: 2026-11-15T20:54:47.653960+00:00; duration: 4.1 seconds.

Prompt:

Show my underwriting queue. List only the application count and each application's actual ID and borrower name. Do not inspect individual details, calculate ratios, assign risk ratings, or change anything.

Observed tools: uw_queue_view

Response:

```text
Your underwriting queue contains 3 applications:

- App #120: Lisa Washington
- App #119: Robert Kim
- App #121: Daniel Ramirez
```
