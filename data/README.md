# Sample Data

This folder holds sample documents used for local development and testing of the ingestion pipeline.

## Included

- **`sample_report.pdf`** — a synthetic, generated test document (a fictitious "Northwind Logistics" quarterly operations report, produced with the open-source ReportLab PDF library). It contains no real organization's data and is safe to include and redistribute. It exists purely to exercise PDF loading and parsing without depending on real HR policy content.

## Not Included

An `IIA_HR_Policy.pdf` file was present locally during early development but is **excluded from version control** (see `.gitignore`). It is a real, identifiable organization's internal HR policy document, and this project has no confirmed rights to redistribute it. Committing it to a public repository would not be appropriate.

## Providing Your Own Test Documents

To exercise the ingestion pipeline with realistic HR policy content, place your own HR policy PDF(s) in this folder. Use documents you have the rights to use — either your own organization's policies (with appropriate authorization) or publicly licensed sample policy documents. Do not commit real, confidential, or third-party-owned policy documents to this repository.
