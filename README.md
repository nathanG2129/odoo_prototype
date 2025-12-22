# Odoo 14 Development Environment

This is a complete Odoo 14 development environment setup using Docker Desktop with Python 3.7.7.

## 📋 Prerequisites

- Docker Desktop installed and running
- Basic understanding of Python
- Text editor or IDE (VS Code recommended)

## 🚀 Getting Started

### 1. Start the Environment

Open PowerShell in this directory and run:

```powershell
docker-compose up -d
```

This will:
- Pull the Odoo 14 image (includes Python 3.7.7)
- Start PostgreSQL database
- Mount your custom addons directory
- Start Odoo in development mode (`--dev=all`)

### 2. Access Odoo

1. Open your browser and go to: `http://localhost:8069`
2. Create a new database:
   - Master password: `admin`
   - Database name: `odoo_dev`
   - Email: your email
   - Password: your password
   - Check "Load demonstration data" (recommended for learning)
3. Click "Create database"

### 3. Install the Example Module

1. After login, go to **Apps** menu
2. Click **Update Apps List** (remove the "Apps" filter first)
3. Search for "Library Management"
4. Click **Install**

## 📚 Understanding the Example Module

The `library_management` module demonstrates core Odoo development concepts:

### Module Structure

```
library_management/
├── __init__.py              # Python package initialization
├── __manifest__.py          # Module metadata and dependencies
├── models/                  # Business logic layer
│   ├── __init__.py
│   ├── library_book.py      # Book model with states, constraints
│   ├── library_member.py    # Member model with computed fields
│   └── library_book_category.py
├── views/                   # User interface (XML)
│   ├── library_book_views.xml
│   ├── library_member_views.xml
│   └── library_menus.xml
├── security/                # Access control
│   ├── library_security.xml # Groups and record rules
│   └── ir.model.access.csv  # Model access rights
├── data/                    # Initial data
│   └── library_category_data.xml
└── demo/                    # Demo data for testing
    └── library_demo.xml
```

### Key Concepts Demonstrated

#### 1. **Models** (`models/library_book.py`)
- `_name`: Internal model identifier
- `_inherit`: Inherit from mail.thread for messaging
- Field types: Char, Date, Integer, Float, Many2one, One2many, Selection
- Computed fields: `@api.depends` decorator
- Constraints: `@api.constrains` for validation
- Business methods: Custom actions like borrow/return
- CRUD overrides: Custom create() and write() methods

#### 2. **Views** (`views/library_book_views.xml`)
- Tree view: List display with decorations
- Form view: Detailed form with notebooks, buttons
- Search view: Filters and group by options
- Actions: Window actions to open views
- Domains: Filter records dynamically

#### 3. **Security** (`security/`)
- Groups: User vs Manager permissions
- Access rights: CRUD permissions per model
- Record rules: Row-level security

#### 4. **Data Files**
- Master data: Categories loaded on install
- Demo data: Sample records for testing

## 🛠️ Development Workflow

### Making Changes to Your Module

1. **Edit your code** in the `addons/library_management/` directory

2. **Restart Odoo** to load changes:
   ```powershell
   docker-compose restart web
   ```

3. **Upgrade the module** in Odoo:
   - Go to Apps menu
   - Search for your module
   - Click "Upgrade" button
   
   Or use the command line:
   ```powershell
   docker-compose run --rm web odoo -d odoo_dev -u library_management --stop-after-init
   ```

### Development Tips

- **Enable Developer Mode**: Settings → Activate Developer Mode
  - Shows technical names
  - Enables debugging tools
  - Access to security settings

- **Use `--dev=all` flag** (already enabled in docker-compose):
  - Auto-reload Python code
  - Reload XML/CSV files without restart
  - Enhanced logging

- **Check logs**:
  ```powershell
  docker-compose logs -f web
  ```

- **Access database directly**:
  ```powershell
  docker-compose exec db psql -U odoo -d odoo_dev
  ```

## 📖 Learning Path

### 1. Start with Models
- Create a simple model with basic fields
- Add computed fields with `@api.depends`
- Implement constraints with `@api.constrains`
- Practice Many2one and One2many relationships

### 2. Build Views
- Create tree and form views
- Add search filters and grouping
- Use domains to filter records
- Implement smart buttons

### 3. Add Security
- Define security groups
- Set up access rights (CRUD)
- Create record rules for row-level security

### 4. Advanced Topics
- Wizards (transient models)
- Reports (QWeb)
- Controllers (web endpoints)
- Scheduled actions (cron jobs)
- JavaScript/OWL widgets

## 🎓 Learning Resources

### Official Documentation
- [Odoo 14 Developer Documentation](https://www.odoo.com/documentation/14.0/developer.html)
- [Odoo 14 API Reference](https://www.odoo.com/documentation/14.0/reference.html)

### Key Topics to Study
1. **ORM Methods**: create(), write(), unlink(), search(), browse()
2. **Decorators**: @api.depends, @api.constrains, @api.onchange, @api.model
3. **View Inheritance**: Extending existing views
4. **QWeb**: Odoo's templating engine
5. **OWL Framework**: Odoo Web Library for JavaScript

### Practice Projects
1. **Todo App**: Simple task management
2. **Expense Tracker**: Track expenses with categories
3. **Inventory System**: Products, stock moves
4. **CRM Extension**: Add custom fields to leads/opportunities
5. **Report Generator**: Custom PDF reports

## 🔧 Useful Commands

### Docker Commands

```powershell
# Start Odoo
docker-compose up -d

# Stop Odoo
docker-compose down

# Restart Odoo
docker-compose restart web

# View logs
docker-compose logs -f web

# Access Odoo shell
docker-compose run --rm web odoo shell -d odoo_dev

# Update module
docker-compose run --rm web odoo -d odoo_dev -u library_management --stop-after-init

# Install module from command line
docker-compose run --rm web odoo -d odoo_dev -i library_management --stop-after-init
```

### Odoo Scaffold (Create New Module)

```powershell
# Create a new module structure
docker-compose run --rm web odoo scaffold module_name /mnt/extra-addons
```

## 🐛 Troubleshooting

### Module Not Appearing
- Click "Update Apps List" in Apps menu
- Check that `__manifest__.py` is correct
- Ensure `installable: True` in manifest

### Changes Not Loading
- Restart the container: `docker-compose restart web`
- Upgrade the module in Apps menu
- Check logs for errors: `docker-compose logs -f web`

### Database Issues
```powershell
# Reset everything
docker-compose down -v
docker-compose up -d
# Create new database via browser
```

### Import Errors
- The import errors in VS Code are normal - Odoo is running in Docker
- To fix: Install `odoo` Python package locally for IDE autocomplete (optional)

## 📝 Next Steps

1. **Explore the example module**: Click through the Library app in Odoo
2. **Modify existing code**: Add a new field to the Book model
3. **Create a new module**: Use `odoo scaffold` to start fresh
4. **Extend core modules**: Practice view inheritance
5. **Build your own app**: Create something useful for your company!

## 🤝 Module Development Checklist

When creating a new module:

- [ ] Create directory in `addons/`
- [ ] Add `__init__.py` files
- [ ] Create `__manifest__.py` with proper metadata
- [ ] Define models in `models/` directory
- [ ] Create views in `views/` directory
- [ ] Set up security (groups, access rights)
- [ ] Add menu items
- [ ] Test CRUD operations
- [ ] Test security permissions
- [ ] Add demo data for testing
- [ ] Document your module

## 💡 Best Practices

1. **Use meaningful names**: Follow Odoo naming conventions
2. **Add help text**: Document fields with `help` parameter
3. **Validate data**: Use constraints to ensure data integrity
4. **Log activities**: Use message_post() for tracking
5. **Test thoroughly**: Test all user roles and scenarios
6. **Version control**: Use git for your custom modules
7. **Backup data**: Regular PostgreSQL backups

---

Happy Odoo Development! 🎉

For questions or issues, refer to:
- [Odoo Community Forum](https://www.odoo.com/forum)
- [Odoo GitHub Repository](https://github.com/odoo/odoo)
