# Quick Start Guide

## Start Odoo in 3 Steps

1. **Start Docker containers:**
   ```powershell
   docker-compose up -d
   ```

2. **Open browser to:** `http://localhost:8069`

3. **Create database:**
   - Master password: `admin`
   - Database name: `odoo_dev`
   - Load demo data: ✓ (recommended)

## Install Example Module

1. Apps → Update Apps List
2. Remove "Apps" filter
3. Search "Library Management"
4. Click Install

## Key Commands

```powershell
# View logs
docker-compose logs -f web

# Restart Odoo
docker-compose restart web

# Stop everything
docker-compose down

# Upgrade module after changes
docker-compose run --rm web odoo -d odoo_dev -u library_management --stop-after-init
```

## File Structure

- `addons/` - Your custom modules go here
- `config/odoo.conf` - Odoo configuration
- `docker-compose.yml` - Docker setup


