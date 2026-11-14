# Demo Folder

## Purpose
This folder contains a **static HTML/CSS mockup** of the gallery interface. It was created during the design phase to test the card-based gallery layout and UI styling before implementing it in the Flask application.

## Contents
- `index.html` - Static demo page showing the gallery UI design
- `demo.css` - Stylesheet for the demo (separate from main app CSS)

## Status
⚠️ **Not integrated with the Flask application**

This is purely a **design reference**. The actual gallery is implemented in:
- `templates/gallery.html` (server-rendered Jinja2 template)
- `static/css/drive.css` (production stylesheet)
- `routes/gallery.py` (backend routes)

## Usage
To view the demo:
```bash
# Option 1: Open directly in browser
open demo/index.html

# Option 2: Serve with Python
cd demo && python3 -m http.server 8080
```

## Should you delete this?
**Keep it** if you want a quick visual reference of the original design mockup.

**Delete it** if you want to reduce repo clutter - the live app in `templates/` already implements everything.

---
*This folder has no dependencies on the main application and can be safely removed without affecting functionality.*
