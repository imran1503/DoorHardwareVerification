# Door Hardware Checker — Pro Security Controls Inc.

For Prosecurity Controls Inc. and the Egress Systems website: [egress-systems.com](https://egress-systems.com/).

A React interface and local SQLite database for checking and maintaining door hardware compatibility records. The app deliberately reports an unrecorded combination as **unverified**; it does not infer that untested hardware will work.

## Run locally

Requirements: Python 3.10+ and Node.js 18+.

1. Install the frontend packages once with `npm install`.
2. In one terminal, run `python server.py` from this folder. It creates `doorhardware.db` beside the server and starts the API at `http://127.0.0.1:8000`.
3. In a second terminal, run `npm run dev` and open the local URL printed by Vite (usually `http://localhost:5173`).

The SQLite file is the source of truth and is easy to back up or inspect with any SQLite editor. Add hardware in **Hardware library** and confirmed combinations in **Compatibility rules**. The database starts with the project's original lookup values and four example records from `SQL/populateTables.sql`.

For a production deployment, put the API and built frontend behind an authenticated company service and add a review / approval process for rule changes. The current local build is intended for development and does not include user accounts or access control.

## API

The Python API uses only the standard library. `GET /api/bootstrap` returns the editable catalog and rules. `POST /api/check` evaluates a selection. `POST /api/items` and `POST /api/rules` add records; rules can also be edited or removed through the app.
