Proposed Rental & Accounting Models
Diagram Link

General
Users (Masterfile)
The list of all users, their details and their access level throughout the system.
User ID (PK)
Username
Full Name
Access Group / Role
Email
isActive
Modified


Banks (Masterfile)
The list of all bank accounts used by the company, including account names and numbers.
Bank ID (PK)
Bank Name
Account Name
Account Number
Created By
Created Date
Modified By
Modified Date

KCode (Masterfile)
The list of codes used throughout the system, mainly used in identifying units and vouchers.
KCode ID (PK)
KCode
Created By
Created Date
Modified By
Modified Date






Market Rentals
Markets (Masterfile)
The list of markets containing leased stalls by the company.
Market ID (PK)
Market Code
Sample: BBH, KTC
Market Name
Address
Created By
Created Date
Modified By
Modified Date

Stalls (Masterfile)
The list of stalls leased by the company to tenants. Includes rates, utility pay types.
Stall ID (PK)
Market ID (FK to Markets)
Tenant ID (FK to Tenants)
Stall Group ID (FK to Stall Groups)
Stall Code
Rental Rate
Electricity Rate
Electric Pay Type ID (FK to Payment Types)
Water Pay Type ID (FK to Payment Types)
Rent Collection Type
Sample: Daily, Weekly, Monthly
isActive
needOR
Meralco Account Number
Electricity Sub-Meter Number
Created By
Created Date
Modified By
Modified Date

Stall Groups (Masterfile)
The list of stall categories used for group utility billing.
Stall Group ID (PK)
Stall Group Code
Electric Pay Type ID
Water Pay Type ID
Created By
Created Date
Modified By
Modified Date


Tenants (Masterfile)
The list of lessees of stalls in markets.
Tenant ID (PK)
Tenant Name
Date Started
Date End
Created By
Created Date
Modified By
Modified Date

Market Pay Types (Masterfile)
The list of paying types of market utilities and can be grouped into different frequencies.
Pay Type ID (PK)
Pay Type Code
Sample: K1-MH, UGS Weekly, NAWASA, Toilet
Pay Type Name
Pay Type Use
Sample: Electricity or Water
Sub-Group 
Sample: Daily, Weekly, Monthly
Created By
Created Date
Modified By
Modified Date

Market Rent Transactions (Transactional)
The listing and tracking of all market rent collections from stalls.
Transaction ID (PK)
Stall ID (FK to Stalls)
Transaction Date
Payment Status
Rent Paid
COPB Due
COPB Paid
Receipt Number
Encoded By
Encoded Date
Modified By
Modified Date

Market Utilities Transactions (Transactional)
The listing and tracking of MERALCO / Water utility usage and dues from stalls.
Transaction ID (PK)
Stall ID (FK to Stalls)
Stall Group ID (FK to Stall Groups)
Transaction Date
Payment Status
Utility Type
Sample: Water, Electricity
Previous Reading
Current Reading 
Consumption (Calculated)
Receipt Number
Amount Paid
Encoded By
Encoded Date
Modified By
Modified Date

Unit Rentals
Location (Masterfile)
The list of locations of units leased by the company.
Location ID (PK)
Location Code
Location Description
Company Name
Company Code
Company Address
Created By
Created Date
Modified By
Modified Date


Unit Category (Masterfile)
The list of possible categories of leased units.
Category ID (PK)
CategoryName
Sample: Residential (Condo), Residential 
Created By
Created Date
Modified By
Modified Date


Units (Masterfile)
The list of units being leased by the company.
Unit ID (PK)
Lessor ID (FK to Lessors)
Category ID (FK to Unit Category)
Location ID (FK to Location)
Bank ID (FK to Banks)
KCode (FK to KCode)
Sample: RET
Unit Specified
Sample: 2
Full Code
Sample: RET-2
Unit Address 
Description 
Note: Type of Use in Legacy
Size
SOA Bank Account Number
Created By
Created Date
Modified By
Modified Date

Lessees (Masterfile)
The list of lessees of units.
Lessee ID (PK)
Lessee Name
Lessee Address
Lessee Contact
Lessee Email
Created By
Created Date
Modified By
Modified Date

Lessors (Masterfile)
The list of lessors of units.
Lessor ID (PK)
Lessor Code
Lessor Name
Created By
Created Date
Modified By
Modified Date

Unit Rent Transactions (Transactional)
The listing and tracking of all rent from units leased.
Transaction ID (PK)
Contract ID (FK to Contracts)
Bank ID (FK to Banks)
Payment Status
Payment Category
Payment Type
Payment Reference 
AmountDeposited
TransactionDate
Notes
isBounced
Encoded By
Encoded Date
Modified By
Modified Date

Contracts (Masterfile / Transactional)
The list of contracts filed to lessees of rental units. Includes rent, taxes and timed escalations.
Contract ID (PK)
Unit ID (Foreign Key to Units)
Lessee ID (Foreign Key to Lessees)
Lessor ID (Foreign Key to Lessors)
Contract Number
Period From and To
Basic Rent
eVAT
Withholding Tax
MPTR
Monthly Rate (Calculated) 
Sample: Basic Rent + eVAT + With. Tax
CUSA Rate
Escalation Percentage
Escalation Date in Months
Notes
Status
Filed By
Filed Date
Modified By
Modified Date

Disbursements
Expense Category (Masterfile)
The list of possible expense categories, such as OPEX (Operational Expenses).
Expense Category ID (PK)
Expense Category Name
Created By
Created Date
Modified By
Modified Date

Expense Masterlist (Masterfile)
The list of common company expenses. Used in categorizing check vouchers.
Expense ID (PK)
Expense Category ID (FK to Expense Category)
Expense Name
Expense Type
Expense General Group
Created By
Created Date
Modified By
Modified Date

Payee / Supplier (Masterfile)
The list of suppliers that need to be paid based on the check voucher transaction entries.
Payee ID (PK)
Payee Name
Payee Address
Payee TIN
Created By
Created Date
Modified By
Modified Date

Voucher Prefix (Masterfile)
The list of voucher prefixes used in voucher identification.
Voucher Prefix ID (PK)
Voucher Prefix Code
Voucher Prefix Name
Voucher Prefix Address
Created By
Created Date
Modified By
Modified Date

Voucher Header (Transactional)
The list of disbursements processed using check vouchers.
Voucher ID (PK)
Voucher Prefix ID
Expense ID (FK to Expense)
Payee ID (FK to Payees)
Bank ID (FK to Banks)
KCode ID (FK to KCode)
Voucher Number
Voucher Code (Calculated, Prefix + Number)
Voucher Date
Check Name
Check Date
Check Number
Check Amount
Particulars
Compute
Remarks
isPosted
Period Covered From
Period Covered To
Created By
Created Date
Modified By
Modified Date


Voucher Details (Transactional)
The list of possible voucher payables in a disbursement process.
Voucher Detail ID (PK)
Voucher ID (FK to Voucher)
Account Number
Account Name
BillDue
PayDue
Consumption
Remarks
Period Covered From
Period Covered To