# Menu Maker

A FastAPI restaurant menu builder with owner signup/login, SQLite storage, image uploads, public menu pages, and QR codes for each menu.

## Run

```powershell
python -m uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`, create a restaurant owner account, then create menus, categories, and items.

## Features

- Restaurant owner signup, login, and logout
- Create multiple menus per restaurant
- Add categories and menu items
- Upload item images
- Publish or hide a menu
- Public guest menu at `/m/{slug}`
- QR code SVG for each public menu

The app uses `menu_maker.db` in the project root. It is created automatically on first run.

## Database and Cloud Deploy

Local development uses SQLite by default:

```powershell
python -m uvicorn main:app --reload
```

For FastAPI Cloud or another hosted environment, set `DATABASE_URL` to your cloud database connection string. The backend initializes tables during FastAPI startup, so database setup stays server-side and does not depend on frontend code.
