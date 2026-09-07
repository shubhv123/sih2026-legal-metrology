# Statutory Rules Reference Manual

**Document Version:** 1.1  
**Lead Author:** Parul (Legal Content & Statutory Documentation)  
**Applicable Authority:** The Legal Metrology Act, 2009 & The Legal Metrology (Packaged Commodities) Rules, 2011  
**Machine-Readable Mapping:** [`backend/app/data/rules/lmpc_rules_v1.json`](file:///Users/shubhverma/vscode/sih2026-legal-metrology/backend/app/data/rules/lmpc_rules_v1.json)

---

## 1. Statutory Foundations & Regulatory Hierarchy

This reference manual documents the primary statutory rules and technical thresholds governing pre-packaged commodities in India under **SIH Problem Statement SIH26034**.

```
                           THE LEGAL METROLOGY ACT, 2009
                                (Act No. 1 of 2010)
                                         │
                                         ▼
                 THE LEGAL METROLOGY (PACKAGED COMMODITIES) RULES, 2011
                               (Notification G.S.R. 202(E))
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
     RULE 6                           RULE 7                           RULE 8 & 9
Mandatory Package                Minimum Numeral &              Placement, Legibility,
   Declarations                    Letter Heights                Grouping, & Contrast
```

### 1.1 Enabling Statutes
1. **The Legal Metrology Act, 2009 (Act No. 1 of 2010):**
   - Enacted to establish and enforce standards of weights and measures, regulate trade and commerce in weights, measures, and other goods which are sold or distributed by weight, measure, or number.
   - **Section 18:** Mandates that no person shall manufacture, pack, sell, distribute, deliver, offer, expose for sale or have in possession for sale any pre-packaged commodity unless it conforms to standard quantities and declarations.
2. **The Legal Metrology (Packaged Commodities) Rules, 2011:**
   - Published via Notification G.S.R. 202(E) dated 7th March, 2011; in force from 1st April, 2011.
   - Superseded the Standards of Weights and Measures (Packaged Commodities) Rules, 1977.
3. **Key Subsequent Amendments Incorporated:**
   - **2017 Amendments (G.S.R. 629(E)):** Enhanced consumer care declarations, medical device labeling alignments, and font size table harmonizations.
   - **2021 & 2022 Amendments (G.S.R. 779(E) & G.S.R. 226(E)):** Introduced mandatory Unit Sale Price (USP) under Rule 6(11), effective 1st October, 2022.
   - **2025 Amendment:** Explicit exemption for medical device packaging harmonized under Medical Devices Rules, 2017.

---

## 2. Core Statutory Definitions

### 2.1 Principal Display Panel (PDP) — Rule 2(h)
> **Rule 2(h):** *"principal display panel", in relation to a package, means the total surface area of the package which is available for providing the information required under these rules, namely:—*
> - *(i) in the case of a rectangular package, where one entire side can properly be considered to be the principal display panel, the product of the height to the width of that side;*
> - *(ii) in the case of a cylindrical or nearly cylindrical package, forty per cent of the product of the height to the circumference of the package;*
> - *(iii) in the case of any other shaped package, forty per cent of the total surface of the package, or an area considered by the manufacturer, packer or importer to be the principal display panel;*
> 
> *provided that where all information could be grouped together and given at one place, the area surrounding that information shall be treated as the principal display panel.*

**Automated Detection Implication:** The vision pipeline detects the bounding rectangle of the primary declaration cluster or front face as the designated PDP bbox.

### 2.2 Pre-Packed Commodity — Rule 2(l) / Act Section 2(l)
A commodity which, without the purchaser being present, is placed in a package of whatever nature, whether sealed or not, so that the product contained therein has a predetermined quantity.

### 2.3 Retail Sale Price Rounding — Rule 2(m)
When calculating or declaring retail sale prices:
- Any fraction of a rupee below 50 paise shall be rounded down to the preceding rupee.
- Any fraction of 50 paise up to 95 paise shall be rounded to fifty paise.

---

## 3. Rule 6: Mandatory Package Declarations

Every retail package must bear the statutory declarations detailed below on its Principal Display Panel or prominent face.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRINCIPAL DISPLAY PANEL                         │
│                                                                        │
│  [Commodity Generic Name] — Rule 6(1)(b)                               │
│                                                                        │
│  Net Quantity: 500 g — Rule 6(1)(c) & Rule 13                          │
│                                                                        │
│  MRP Rs. 149.00 (incl. of all taxes) — Rule 6(1)(e)                    │
│  Unit Sale Price: Rs. 0.30 / g — Rule 6(11)                            │
│                                                                        │
│  Mfg Date: 08/2026 — Rule 6(1)(d)                                      │
│  Best Before: 24 months from packaging (perishable articles)           │
│                                                                        │
│  Manufactured & Packed By: ABC Foods Pvt Ltd, [Address] — Rule 6(1)(a) │
│  Consumer Care: Toll-free 1800-XXX-XXXX / care@abcfoods.com — Rule 6(2)│
│  Country of Origin: India (imported packages) — Rule 6(1)(a) proviso  │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Rule 6(1)(a) & Rule 10: Manufacturer / Packer / Importer
- **Statutory Requirement:** Name and complete physical address of the manufacturer, or where manufacturer is not packer, both manufacturer and packer. For imported goods, name and address of the importer.
- **Rule 10 Declaration Standard:** Complete postal address must include the city, state, and postal index number (PIN code). Mentioning merely a corporate website or PO box without physical address is non-compliant.
- **Rule Engine ID:** `RULE_6_1_A_MANUFACTURER`
- **Failure Classification:** `FAIL` if manufacturer name/address is omitted.

### 3.2 Rule 6(1)(b): Generic or Common Name of Commodity
- **Statutory Requirement:** Common or generic name of the commodity contained in the package. For combination packages, the name and quantity of each distinct item.
- **Rule Engine ID:** `RULE_6_1_B_GENERIC_NAME`
- **Failure Classification:** `FAIL` if commodity identity is omitted.

### 3.3 Rule 6(1)(c) & Rule 13: Net Quantity Declaration
- **Statutory Requirement:** Net quantity declared in terms of the standard SI metric unit of weight (g, kg), volume (ml, l), length (m, cm), or numerical count (u, number).
- **Rule 13 Measurement Conventions:**
  - Solid commodities: Weight (grams for $< 1\text{ kg}$, kilograms for $\ge 1\text{ kg}$).
  - Liquid commodities: Volume (milliliters for $< 1\text{ L}$, liters for $\ge 1\text{ L}$).
  - Semi-solid/viscous: Weight or volume as per customary trade practice.
- **Rule Engine ID:** `RULE_6_1_C_NET_QTY`
- **Failure Classification:** `FAIL` if missing or if non-standard/imperial units (lbs, oz) are declared.

### 3.4 Rule 6(1)(d): Month and Year of Manufacture / Packing
- **Statutory Requirement:** Month and year in which commodity is manufactured, pre-packed, or imported.
- **Accepted Formats:** `MM/YYYY`, `MM-YYYY`, or textual month name (`August 2026`). Full dates (`DD/MM/YYYY`) are normalized by dropping the day, as a day declaration is over-compliant.
- **Food / Perishable Proviso:** Proviso to Rule 6(1)(d) defers date declarations on perishable food items to applicable food safety legislation (the Food Safety and Standards Act, 2006 / FSSAI), requiring "Best before" or "Use by" dates.
- **Rule Engine ID:** `RULE_6_1_D_MFG_DATE` (and `RULE_6_1_D_FOOD_EXPIRY` for perishable articles).

### 3.5 Rule 6(1)(e): Maximum Retail Price (MRP)
- **Statutory Requirement:** Retail sale price in the format:
  $$\text{MRP Rs. } X \text{ (incl. of all taxes)} \quad\text{or}\quad \text{MRP ₹ } X \text{ inclusive of all taxes}$$
- **Essential Components:**
  1. Price digits rounded per Rule 2(m).
  2. Mandatory currency prefix (`Rs.` or `₹`).
  3. Mandatory tax qualifier (*"inclusive of all taxes"* or *"incl. of all taxes"*).
- **Rule Engine ID:** `RULE_6_1_E_MRP`
- **Failure Classification:** `FAIL` if price or tax inclusivity stipulation is omitted.

### 3.6 Rule 6(11): Unit Sale Price (USP)
- **Statutory Requirement:** Inserted by 2021/2022 amendments, packages containing net weight/volume must state price per standard unit:
  - Per gram (if net quantity $< 1\text{ kg}$) or per kilogram (if net quantity $\ge 1\text{ kg}$).
  - Per milliliter (if net quantity $< 1\text{ L}$) or per liter (if net quantity $\ge 1\text{ L}$).
  - Per number/unit (if sold by count).
- **Rounding:** Rounded to nearest two decimal places.
- **Exemptions:** Not required where retail sale price equals unit sale price (e.g. 1 unit = ₹10), or for combination multi-packs under 2023 clarifications.
- **Rule Engine ID:** `RULE_6_11_UNIT_SALE_PRICE`

### 3.7 Rule 6(2): Consumer Care Details
- **Statutory Requirement:** Name, address, telephone number, and email address of the person or office that can be contacted in case of consumer complaints.
- **Rule Engine ID:** `RULE_6_2_CONSUMER_CARE`
- **Failure Classification:** `FAIL` if consumer grievance mechanism is completely absent.

### 3.8 Country of Origin (Imported Commodities)
- **Statutory Requirement:** For imported packages, the country of origin, manufacture, or assembly must be declared alongside the importer details.
- **Verification Note:** *(Note: Traced from secondary legal commentary as amended into Rule 6(1)(a) proviso for imported packages; exact Gazette amending instrument pending primary Gazette confirmation — verify against primary Gazette before citing in formal judicial proceedings)*.
- **Rule Engine ID:** `RULE_6_1_A_ORIGIN`

---

## 4. Rule 7: Font-Height & Typography Thresholds

Rule 7 specifies mandatory minimum character heights for numerals and letters to guarantee readability.

### 4.1 Rule 7(2)(i) Table-I: Numeral Height by Net Quantity
Applicable when net quantity is declared in terms of weight or volume:

| Bracket ID | Net Quantity Range | Normal Packaging ($H_{\text{min}}$) | Blown, Formed, Molded, or Embossed ($H_{\text{min}}$) |
|---|---|---|---|
| `upto_200g_ml` | $\le 200\text{ g / mL}$ | **$1.0\text{ mm}$** | **$2.0\text{ mm}$** |
| `200g_to_500g_ml` | $> 200\text{ g / mL} \le 500\text{ g / mL}$ | **$2.0\text{ mm}$** | **$4.0\text{ mm}$** |
| `above_500g_ml` | $> 500\text{ g / mL}$ | **$4.0\text{ mm}$** | **$6.0\text{ mm}$** |

### 4.2 Rule 7(2)(ii) Table-II: Numeral Height by PDP Area
Applicable based on total Principal Display Panel surface area:

| Bracket ID | PDP Area Range | Normal Packaging ($H_{\text{min}}$) | Blown, Formed, Molded, or Embossed ($H_{\text{min}}$) |
|---|---|---|---|
| `upto_100cm2` | $\le 100\text{ cm}^2$ | **$1.0\text{ mm}$** | **$2.0\text{ mm}$** |
| `100_to_500cm2` | $> 100\text{ cm}^2 \le 500\text{ cm}^2$ | **$2.0\text{ mm}$** | **$4.0\text{ mm}$** |
| `500_to_2500cm2` | $> 500\text{ cm}^2 \le 2500\text{ cm}^2$ | **$4.0\text{ mm}$** | **$6.0\text{ mm}$** |
| `above_2500cm2` | $> 2500\text{ cm}^2$ | **$6.0\text{ mm}$** | **$6.0\text{ mm}$** |

### 4.3 Rule 7(3): Letter Heights & Proportion Rules
- **Minimum Letter Height:** The height of any letter in declarations shall not be less than **$1.0\text{ mm}$** for standard packaging, and not less than **$2.0\text{ mm}$** for blown, molded, or embossed packaging.
- **Width-to-Height Ratio:** The width of any numeral or letter shall not be less than **one-third of its height**, except for numeral `1` and letter `I`.

---

## 5. Placement, Grouping, & Legibility Rules

### 5.1 Principal Display Panel Grouping — Rule 2(h) & Rule 8
- **Rule 2(h) Grouping Mandate:** Declarations are expected to be consolidated in one designated area where consumer access is immediate.
- **Rule 8 Display Requirements:** All statutory declarations must appear on the Principal Display Panel and shall be printed in clear, conspicuous type with sufficient clear space surrounding them to ensure legibility.
- **Rule Engine ID:** `RULE_6_PLACEMENT_OUTSIDE_PDP`

### 5.2 Manner of Declaration — Rule 9
- **Color Contrast (Rule 9(1)):** Every declaration specified in Rule 6 shall be legible and prominent. The numerals and letters of the declaration shall be printed in a color that provides distinct contrast with the background of the label or container.
- **Language Requirements (Rule 9(1)):** Declarations must be made either in **Hindi in Devanagari script** or in **English**.
- **Outer Wrapper Duplication (Rule 9(2)):** Where a retail package is provided with an outside wrapper or container, all statutory declarations shall also appear on such outer wrapper, unless the inner package's declarations are clearly transparent and legible through the wrapper.

---

## 6. The Three Statutory Category Exceptions

To ensure engineering feasibility during the prototype evaluation, the rule engine implements exactly three statutory category exceptions:

```
                              CATEGORY EXCEPTIONS
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
  medical_device                  bulk_exempt                    food_expiry
2025 Amendment Exemption       Rule 3 Wholesale Exemption     Rule 6(1)(d) Food Safety
 (Medical Devices Rules)           (> 25 kg or Bulk)             (FSSAI Expiry Date)
```

### 6.1 Exception 1: `medical_device`
- **Statutory Source:** Legal Metrology (Packaged Commodities) Amendment Rules, 2025.
- **Condition:** Package contains a declared medical device.
- **Exemption Effect:** Fully exempt from LMPC Rules 6 & 7 retail declarations; governed exclusively by the Medical Devices Rules, 2017.
- **Rule Engine ID:** `RULE_2_H_MEDICAL_DEVICE_EXEMPT` $\to$ Evaluated as `PASS` (Exempt).

### 6.2 Exception 2: `bulk_exempt`
- **Statutory Source:** Legal Metrology (Packaged Commodities) Rules, 2011, Rule 3.
- **Condition:** 
  1. Package contains quantity exceeding $25\text{ kg}$ or $25\text{ L}$ (excluding cement and fertilizer sold in bags up to $50\text{ kg}$).
  2. Commodity packaged exclusively for industrial or institutional consumers.
- **Exemption Effect:** Fully exempt from Chapter II Retail Package declaration requirements.
- **Rule Engine ID:** `RULE_3_BULK_PACKAGE_EXEMPT` $\to$ Evaluated as `PASS` (Exempt).

### 6.3 Exception 3: `food_expiry`
- **Statutory Source:** Rule 6(1)(d) proviso read with the Food Safety and Standards Act, 2006.
- **Condition:** Food or perishable articles.
- **Exemption Effect:** Defers date declaration to food safety law, triggering an additional mandatory requirement for `expiry_date` / `best_before_date`.
- **Rule Engine ID:** `RULE_6_1_D_FOOD_EXPIRY`.

---

## 7. Penalties & Enforcement Disclaimers

### 7.1 Statutory Penalties
- **General Penalty Clause — Rule 32(2):** Whoever contravenes any provision of these rules for which no punishment is provided either in the Act or the rules shall be punishable with fine which may extend to **two thousand rupees (₹2,000)**.
- **Section 36(1) of the Act:** 
  *(Note: Traced from secondary drafting notes; verify against the primary text of Act No. 1 of 2010 before relying in formal judicial or enforcement proceedings)*.
  Provides statutory penalties for manufacturing, packing, or selling non-standard pre-packaged commodities.

### 7.2 Decision Support & Three-State Evidentiary Rule
This system is engineered as an **objective decision-support and screening platform** for field inspectors, not an autonomous judicial adjudicator.

Every check evaluates to one of three distinct states:
1. **`PASS`:** Affirmative visual evidence of statutory conformity.
2. **`FAIL`:** Clear evidence of omission or statutory non-compliance.
3. **`REVIEW_REQUIRED` (Confidence $< 0.75$):** Visual ambiguity, glare, faint dot-matrix printing, or uncalibrated scale. Directs the human inspector to conduct manual verification before initiating statutory notices.
