# 🚚 HUDSON CARGO INVOICING (HCI)

<div align="center">

![Odoo](https://img.shields.io/badge/Odoo-18.0-714B67?style=for-the-badge&logo=odoo&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-Private-red?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

### A Professional Cargo & Freight Forwarding Invoicing Solution for Odoo 18

*Designed specifically for logistics companies requiring intelligent invoicing, ZATCA compliance, Arabic localization, and streamlined shipment management.*

</div>

---

# 📑 Table of Contents

- [📖 Overview](#-overview)
- [✨ Key Features](#-key-features)
  - [📦 Intelligent Contact Management](#-intelligent-contact-management)
  - [💰 Bi-directional Financial Engine](#-bi-directional-financial-engine)
  - [🇸🇦 ZATCA Phase 1 Compliance](#-zatca-phase-1-compliance)
  - [🌍 Full Arabic Localization](#-full-arabic-localization)
  - [📲 Multi-channel Communication](#-multi-channel-communication)
  - [📊 Analytics & Reporting](#-analytics--reporting)
- [🛠️ Technology Stack](#️-technology-stack)
- [📥 Installation](#-installation)
- [🚀 Usage](#-usage)
- [📁 Module Structure](#-module-structure)
- [📸 Screenshots](#-screenshots)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

# 📖 Overview

**Cargo Manual Invoicing** is a custom-built **Odoo 18** module designed specifically for **cargo, courier, freight forwarding, and logistics businesses**.

Unlike generic accounting applications, this module provides a complete invoicing workflow tailored for shipment operations while leveraging Odoo's powerful framework.

It combines intelligent contact management, automated VAT calculations, Arabic localization, ZATCA compliance, communication tools, and reporting into one streamlined solution.

---

# ✨ Key Features

## 📦 Intelligent Contact Management

Built upon Odoo's native **`res.partner`** architecture for maximum compatibility.

### Features

- Uses **Shipper** and **Receiver** partner records
- Automatically retrieves:
  - Phone Number
  - VAT Number
  - Contact Information
- Prevents duplicate customer records
- Automatically links invoices with existing contacts
- Background auto-save when contact details are edited directly from the invoice
- Keeps customer information synchronized throughout the system

---

## 💰 Bi-directional Financial Engine

The financial engine performs mathematical VAT calculations **in both directions**.

### Forward Calculation

Input:

```
Net Amount
```

Automatically calculates:

- VAT (15%)
- Gross Total

Example:

| Field | Value |
|-------|--------|
| Net Amount | 100.00 |
| VAT (15%) | 15.00 |
| Gross Total | 115.00 |

---

### Reverse Calculation

Input:

```
Gross Total
```

Automatically computes:

- Net Amount
- VAT Amount

Example:

| Field | Value |
|-------|--------|
| Gross Total | 115.00 |
| Net Amount | 100.00 |
| VAT | 15.00 |

This allows users to enter whichever amount they already know without performing manual calculations.

---

## 🇸🇦 ZATCA Phase 1 Compliance

The module automatically generates a **ZATCA Phase 1 compliant QR Code** for every invoice.

The QR code encodes:

- Seller Name
- VAT Registration Number
- Invoice Timestamp
- Invoice Total
- VAT Total

using the official:

- TLV Encoding
- Base64 Encoding

The QR Code is printed automatically on the generated PDF invoice.

---

## 🌍 Full Arabic Localization

Designed for bilingual business environments.

The module includes a complete **i18n translation system**.

Changing the Odoo user's language instantly translates:

- Invoice Fields
- Buttons
- Menus
- Labels
- Reports
- Form Views
- Tree Views
- Navigation

between English and Arabic without requiring any additional configuration.

---

## 📲 Multi-channel Communication

### WhatsApp Integration

Generate shipment summaries and open **WhatsApp Web** directly from the invoice for quick customer communication.

Features include:

- One-click WhatsApp launch
- Pre-filled shipment information
- Faster customer updates

---

### Email Integration

Send invoices directly from Odoo.

Features:

- One-click email action
- Automatically attaches the PDF invoice
- Logs the communication in Odoo Chatter
- Maintains complete communication history

---

## 📊 Analytics & Reporting

### Daily Collection Wizard

Generate an End-of-Day revenue report with advanced filtering.

Filter by:

- Cash
- Card
- Company
- Delivery Agent

Outputs a professional PDF report summarizing daily collections.

---

### Interactive Backend Analytics

Includes powerful Odoo reporting views:

- 📈 Graph View
- 📊 Pivot View
- 📋 List View
- 🔍 Search Filters

Helping management analyze revenue and operational performance efficiently.

---

# 🛠️ Technology Stack

| Technology | Purpose |
|------------|----------|
| Odoo 18 | ERP Framework |
| Python 3 | Backend Development |
| PostgreSQL | Database |
| XML | Views & UI |
| QWeb | PDF Reports |
| JavaScript | Client-side Enhancements |
| HTML/CSS | User Interface |
| i18n | Arabic Localization |
| WhatsApp Web | Customer Communication |
| ZATCA TLV Encoding | QR Generation |

---

# 📥 Installation

## 1️⃣ Clone the Repository

Clone this repository into your Odoo custom addons directory.

```bash
cd /path/to/odoo/custom/addons

git clone https://github.com/yourusername/cargo-manual-invoicing.git
```

---

## 2️⃣ Restart Odoo

Restart your Odoo server.

Example:

```bash
./odoo-bin
```

or

```bash
sudo systemctl restart odoo
```

---

## 3️⃣ Enable Developer Mode

Inside Odoo:

1. Open **Settings**
2. Scroll to **Developer Tools**
3. Click **Activate Developer Mode**

---

## 4️⃣ Update Apps List

Navigate to:

```
Apps
```

Click:

```
Update Apps List
```

Confirm the update.

---

## 5️⃣ Install the Module

Search for:

```
Cargo Manual Invoicing
```

Click:

```
Install
```

The module is now ready to use.

---

# 🚀 Usage

After installation:

1. Open the Cargo Manual Invoicing module.
2. Create a new invoice.
3. Select or create the Shipper and Receiver.
4. Enter either the Net Amount or Gross Total.
5. Let the financial engine calculate the remaining values automatically.
6. Generate the invoice PDF with the embedded ZATCA QR code.
7. Share the invoice via WhatsApp or Email directly from Odoo.
8. Monitor collections and revenue using the reporting tools.

---

# 📁 Module Structure

```text
cargo_manual_invoicing/
├── models/
├── views/
├── reports/
├── wizard/
├── security/
├── static/
├── i18n/
├── data/
├── __init__.py
├── __manifest__.py
└── README.md
```

---

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

If you would like to contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Submit a Pull Request

---

# 📄 License

This project is proprietary software developed for logistics and freight forwarding operations.

Please refer to your organization's licensing terms before redistribution or commercial use.

---

<div align="center">

### ⭐ If you find this project useful, consider giving it a star!

**Built with ❤️ HUDSON SOFTWARE SOLUTIONS**

</div>
