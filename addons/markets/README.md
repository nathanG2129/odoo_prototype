# KST Markets Module

## Overview

The KST Markets module manages market rentals, stall listings, and rent/utility collections for KST Statistics. This module is part of the larger KST system that includes Markets, Units, and Disbursements.

## Features

### Masterfiles
- **Markets**: Manage market locations (e.g., BBH, KTC)
- **Stalls**: Individual rental spaces within markets
- **Tenants**: Lessees who rent stalls
- **Stall Groups**: Groupings for collective utility billing
- **Pay Types**: Payment frequency configurations for utilities

### Transactions
- **Rent Collections**: Track and process market rent payments
- **Utility Collections**: Track and process electricity and water billing
  - Individual billing with meter readings
  - Group billing for stall groups

## Installation

1. **Start Odoo** (if not already running):
   ```powershell
   cd C:\Projects\KST_Statistics\odoo_prototype
   docker-compose up -d
   ```

2. **Access Odoo**: Open browser to `http://localhost:8069`

3. **Update Apps List**:
   - Go to Apps menu
   - Click "Update Apps List"
   - Confirm the update

4. **Install KST Markets**:
   - Remove the "Apps" filter
   - Search for "KST Markets"
   - Click "Install"

5. **Assign User Groups**:
   - Go to Settings → Users & Companies → Users
   - Edit a user
   - Under "KST Markets", assign either:
     - **User**: Can view masterfiles and create/edit transactions
     - **Manager**: Full access to all data including masterfiles

## Module Structure

```
markets/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── market.py                      # Markets masterfile
│   ├── tenant.py                      # Tenants masterfile
│   ├── market_pay_type.py             # Pay types masterfile
│   ├── stall_group.py                 # Stall groups masterfile
│   ├── stall.py                       # Stalls masterfile
│   ├── market_rent_transaction.py     # Rent transactions
│   └── market_utility_transaction.py  # Utility transactions
├── security/
│   ├── security.xml                   # User groups
│   └── ir.model.access.csv            # Access rights
└── views/
    ├── market_views.xml
    ├── tenant_views.xml
    ├── market_pay_type_views.xml
    ├── stall_group_views.xml
    ├── stall_views.xml
    ├── market_rent_transaction_views.xml
    └── market_utility_transaction_views.xml
```

## Menu Structure

After installation, you'll see the following menu structure:

```
KST Markets
├── Transactions
│   ├── Rent Collections
│   └── Utility Collections
├── Masterfiles
│   ├── Markets
│   ├── Stalls
│   ├── Tenants
│   └── Stall Groups
└── Configuration (Manager only)
    └── Pay Types
```

## Usage Guide

### Setting Up Masterfiles

1. **Create Markets**:
   - Go to Masterfiles → Markets
   - Add markets with codes (e.g., BBH, KTC)

2. **Create Pay Types**:
   - Go to Configuration → Pay Types
   - Add payment types for electricity and water
   - Specify frequency (daily, weekly, monthly)

3. **Create Stall Groups** (if using group billing):
   - Go to Masterfiles → Stall Groups
   - Add groups with codes (e.g., LG, UGP)
   - Assign electric and water pay types

4. **Create Tenants**:
   - Go to Masterfiles → Tenants
   - Add tenant information with start/end dates

5. **Create Stalls**:
   - Go to Masterfiles → Stalls
   - Link to market, tenant, and stall group
   - Set rental and electricity rates
   - Assign pay types for utilities
   - Add meter information if applicable

### Processing Transactions

#### Rent Collections

1. Go to Transactions → Rent Collections
2. Click "Create"
3. Select the stall
4. Enter transaction date and payment details
5. Add COBP (Cash on Billing Period) information if applicable
6. Enter receipt number
7. Save

#### Utility Collections

**For Individual Billing:**
1. Go to Transactions → Utility Collections
2. Click "Create"
3. Select the stall (leave Stall Group empty)
4. Choose utility type (Electricity or Water)
5. Enter previous and current readings
6. Consumption will be calculated automatically
7. Enter amount paid and receipt number
8. Save

**For Group Billing:**
1. Go to Transactions → Utility Collections
2. Click "Create"
3. Select the stall group (leave Stall empty)
4. Choose utility type
5. No meter readings needed
6. Enter amount paid and receipt number
7. Save

## Business Rules

1. **Stall Code Uniqueness**: Stall codes must be unique within each market
2. **XOR Billing**: Utility transactions must have either a stall OR a stall group, not both
3. **Meter Readings**: For individual billing, current reading must be ≥ previous reading
4. **Consumption Calculation**: Automatically computed as current - previous reading
5. **Audit Trail**: All transactions automatically record who created them and when
6. **Tenant Active Status**: Automatically computed based on date_end field

## Data Model

### Key Relationships

- A **Market** contains multiple **Stalls**
- A **Tenant** rents one or more **Stalls**
- A **Stall Group** contains multiple **Stalls** for collective billing
- A **Stall** has electric and water **Pay Types**
- A **Stall** records **Rent Transactions** and **Utility Transactions**
- **Utility Transactions** can reference either a **Stall** (individual) or **Stall Group** (group)

### Computed Fields

- **Market.stall_count**: Number of stalls in the market
- **Tenant.active**: Based on date_end (active if date_end >= today or null)
- **Tenant.stall_count**: Number of stalls rented by tenant
- **Stall.display_name**: Formatted as "[Market Code] Stall Code"
- **MarketUtilityTransaction.consumption**: current_reading - previous_reading
- **MarketUtilityTransaction.billing_type**: "Individual" or "Group"

## Upgrading the Module

After making changes to the module code:

```powershell
cd C:\Projects\KST_Statistics\odoo_prototype
docker-compose restart web
docker-compose run --rm web odoo -d odoo_dev -u markets --stop-after-init
```

## Troubleshooting

### Module not appearing in Apps list
- Make sure you clicked "Update Apps List"
- Remove the "Apps" filter in the search

### Permission errors
- Check that users are assigned to the correct group (User or Manager)
- Managers have full access, Users can only edit transactions

### Cannot create utility transaction with both stall and group
- This is by design (XOR constraint)
- Choose either individual billing (stall) OR group billing (stall group)

## Next Steps

After setting up the Markets module, you can proceed with:
1. **KST Units Module**: For managing rental units and contracts
2. **KST Disbursements Module**: For managing vouchers and payments
3. **KST Base Module**: For shared masterfiles (Users, Banks, KCode)

## Support

For issues or questions, refer to the project documentation or contact the development team.

