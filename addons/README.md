# Custom Odoo Modules

Place your custom Odoo modules in this directory. Each module should be in its own subdirectory.

## Module Structure

A typical Odoo module structure:
```
module_name/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── model_file.py
├── views/
│   └── view_file.xml
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── data/
│   └── data_file.xml
├── static/
│   └── description/
│       └── icon.png
└── controllers/
    ├── __init__.py
    └── controller_file.py
```

## Adding a New Module

1. Create your module directory in this folder
2. Restart the Odoo container
3. Go to Apps menu in Odoo
4. Click "Update Apps List"
5. Search for your module and install it
