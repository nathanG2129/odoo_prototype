
Proposed Modules
Markets Module
This module is for managing markets, stall listings, tracking and processing collections of rent, electricity and water utilities. 
( Diagram Link )

Makes use of the following masterfiles:
Markets 
Stall location identifier (e.g. BBH, KTC)	
Stalls
Individual units of space being leased 
Stall Groups
Groupings of stalls for collective utility billing (e.g., LG, UGP, K1-MH)
Tenants 
Lessees of stalls
Market Pay Type
Determines the frequency or interval of required payments

Makes of the following transactionals:
Market Rent Transactions
Tracks and processes all rent collections from stalls
Market Utility Transactions
Tracks and processes all utility collections (electricity and water)

Relationships
A market contains multiple stalls 
A tenant rents one or more stalls
A stall group categorizes and contains multiple stalls for collective billing	
A stall can have an electric and/or water pay type
Stalls can be billed individually or as part of a stall group
Users encode market rent and market utility transactions

Business Rules
For individual billing, a utility transaction references a specific stall with meter readings
For group billing, a utility transaction references a stall group with no readings
For rent collections, billed individually per stall



Units Module
This module is for managing rental units, lease contracts, and tracking rent collections.
( Diagram Link )

Makes use of the following masterfiles:
Locations
Property location identifiers with company information (e.g., Retiro)
Unit Categories
Classification of unit types (e.g., Residential Condo, Commercial)
Units
Individual rental spaces being leased by the company
Lessees
Tenants who lease units
Lessors
Property owners who lease out units
Contracts
Rental agreements between lessees and lessors, including rent rates, taxes, and escalation terms

Makes use of the following transactionals:
Unit Rent Transactions
Tracks and processes all rent payments from unit lessees

Relationships:
A location contains multiple units
A unit category classifies units
A lessor owns one or more units
A unit has one active contract at a time
A lessee signs one or more contracts
A lessor leases units through contracts
A contract generates unit rent transactions
A bank receives rent deposits
Users file contracts and encode unit rent transactions

Business Rules:
Each unit is linked to a calculated Full Code for identification
Contracts define the monthly rate (calculated: Basic Rent + eVAT + Withholding Tax)
Contracts include escalation terms (percentage and interval in months)
Rent transactions track payment status, category, type, and reference
Bounced payments are flagged with isBounced for follow-up
Disbursements Module
This module is for managing company expenses, supplier payments, and processing check voucher disbursements.
( Diagram Link )
Makes use of the following masterfiles:
Expense Categories
Classification of expense types (e.g., OPEX - Operational Expenses)
Expenses
Specific expense definitions used in categorizing vouchers
Payees / Suppliers
Vendors and suppliers who receive payments from the company
Voucher Prefixes
Voucher ID prefixes for different entities (e.g., BBHCV, KSTCV)

Makes use of the following transactionals:
Voucher Header
Tracks and processes all disbursements using check vouchers
Voucher Details
Line items for each voucher, specifying individual payables and amounts


Relationships:
An expense category contains multiple expenses
A voucher prefix identifies vouchers by company/entity
An expense category and expense classify each voucher
A payee receives payment through vouchers
A voucher header has one or more voucher details
A bank processes the check payment
Users encode and post vouchers

Business Rules:
Voucher Code is computed from Prefix + Voucher Number (e.g., BBHCV-006350)
Vouchers track check information (name, date, number, amount)
isPosted flag controls workflow (draft vs posted vouchers)
Period Covered tracks the billing period for recurring expenses
Each voucher detail includes an Account Number and Account Name
