# Quick Reference: Modular RpiPrint

## 🎯 Where to Find Things

### Need to change...

| What                      | Where                                   |
| ------------------------- | --------------------------------------- |
| **Environment variables** | `config.py` → `Config` class            |
| **Database schema**       | `models/database.py` → `init_db()`      |
| **File upload logic**     | `routes/user_routes.py` → `upload()`    |
| **Admin approval**        | `routes/admin_routes.py` → `approve()`  |
| **Cart operations**       | `services/cart_service.py`              |
| **Printing logic**        | `utils/print_utils.py` → `print_file()` |
| **Push notifications**    | `utils/notification_utils.py`           |
| **WebSocket events**      | `websocket/events.py`                   |
| **API endpoints**         | `routes/api_routes.py`                  |
| **CUPS monitoring**       | `services/cups_monitor.py`              |

## 📝 Common Tasks

### Add a New Config Setting

```python
# config.py
class Config:
    NEW_SETTING = os.getenv('NEW_SETTING', 'default_value')
```

### Add a Database Column

```python
# models/database.py - in init_db()
cur.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        ...existing columns...,
        new_column TEXT  -- Add here
    )
''')
```

### Add a User Route

```python
# routes/user_routes.py
@user_bp.route('/my-route')
def my_route():
    return render_template('my_template.html')
```

### Add an API Endpoint

```python
# routes/api_routes.py
@api_bp.route('/my-endpoint', methods=['POST'])
def my_endpoint():
    data = request.json
    return jsonify({'success': True})
```

### Add a Utility Function

```python
# utils/file_utils.py (or create new util file)
def my_utility():
    """Description"""
    pass

# Don't forget to export in utils/__init__.py
```

### Modify Cart Logic

```python
# services/cart_service.py
def my_cart_function():
    cart = session.get('cart', [])
    # Do something with cart
    session['cart'] = cart
```

## 🔄 Import Examples

### Import config settings

```python
from config import Config
printer = Config.PRINTER_NAME
```

### Import database functions

```python
from models.database import get_job, save_job, update_job_status
```

### Import utilities

```python
from utils import print_file, send_push_notification, count_pdf_pages
# Or specific imports:
from utils.print_utils import print_file
```

### Import cart service

```python
from services.cart_service import get_cart_summary, add_to_cart
```

### Broadcast WebSocket update

```python
from websocket.events import broadcast_job_update
from flask import current_app

socketio = current_app.extensions.get('socketio')
broadcast_job_update(socketio, job_id, status, 'action')
```

## 🚨 Important Notes

### Flask Application Context

When working with database or WebSocket in background threads:

```python
with app.app_context():
    # Your code here
    update_job_status(job_id, 'completed')
    broadcast_job_update(socketio, job_id, 'completed', 'updated')
```

### Blueprint URL Generation

Use blueprint name in `url_for()`:

```python
# Old way:
redirect(url_for('index'))

# New way:
redirect(url_for('user.index'))  # user_bp routes
redirect(url_for('admin.dashboard'))  # admin_bp routes
redirect(url_for('api.cart_summary'))  # api_bp routes
```

### Circular Import Prevention

Import inside functions if needed:

```python
def my_function():
    # Import here instead of top of file
    from websocket.events import broadcast_job_update
    broadcast_job_update(...)
```

## 🧪 Testing

### Test a specific module

```python
# test_cart.py
from services.cart_service import add_to_cart, get_cart_summary

def test_add_to_cart():
    # Test logic
    pass
```

### Run the app

```bash
# Activate virtual environment
source venv/bin/activate

# Run new modular version
python3 app.py

# Or replace old app.py first:
cp app.py app_old.py
python3 app.py
```

## 📦 File Organization

```
config.py               - Settings, environment variables
├── models/            - Database layer
│   └── database.py    - DB operations
├── utils/             - Helper functions
│   ├── file_utils.py  - File operations
│   ├── print_utils.py - CUPS printing
│   └── notification_utils.py - Push notifications
├── services/          - Business logic
│   ├── cart_service.py - Cart management
│   └── cups_monitor.py - Background monitoring
├── websocket/         - Real-time features
│   └── events.py      - Socket handlers
└── routes/            - HTTP endpoints
    ├── user_routes.py - User pages
    ├── admin_routes.py - Admin pages
    ├── api_routes.py  - REST API
    └── test_routes.py - Testing
```

## 🎓 Best Practices

1. **Keep modules focused** - One responsibility per file
2. **Use type hints** - Add types for better IDE support
3. **Document functions** - Clear docstrings
4. **Import at top** - Except for circular dependencies
5. **Use Config class** - Don't hardcode values
6. **Test independently** - Each module should work alone
7. **Use blueprints** - For logical route grouping

---

**Quick Start**: `source venv/bin/activate && python3 app.py`
