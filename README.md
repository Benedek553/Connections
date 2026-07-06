# Connections

A desktop contact management application written in Python using **PyQt5** and **SQLite**.

Connections allows you to organize contacts into multiple independent tables (groups), search across them, combine multiple datasets, and import contacts directly from Google Contacts CSV exports.

---

## Features

- Multiple contact tables
- SQLite database backend
- Contact photos
  - Local image support
  - Automatic download and caching of remote image URLs
- Google Contacts CSV import
- Custom CSV field mapping
- Search contacts by
  - Name
  - Relationship
- Combine multiple tables into a single view
- Contact metadata
  - Creation timestamp
  - Last modified timestamp
- Responsive PyQt5 GUI
- Cross-platform database storage

---

## Contact Fields

Each contact can store:

- Name
- Phone number
- Email
- WhatsApp
- Signal
- Telegram
- Facebook
- LinkedIn
- Photo
- Relationship
- Notes

---

## Screens

The application contains several windows:

### Main Window

- Create new tables
- View existing tables
- Delete tables
- Open tables
- Search across tables
- Combine tables

### Table Window

- View contacts
- Add contacts
- Edit contacts
- Delete contacts
- Import Google Contacts

### Search

Search across one or more tables by:

- Name
- Relationship

### Combine Tables

Merge multiple tables into a single read-only result list while preserving the original source table.

---

## Google Contacts Import

Connections can import CSV files exported from Google Contacts.

Features:

- Automatic field mapping suggestions
- Manual field mapping
- Skips empty contacts
- Downloads remote profile pictures automatically
- Stores photos locally

Supported fields include:

- Given Name
- Family Name
- Phone
- Email
- Notes
- Group Membership
- Photo URL

---

## Database

SQLite is used as the local database.

The application automatically creates:

- metadata table
- contact tables
- missing columns during upgrades

Each contact stores:

- created_at
- last_modified

---

## Project Structure

```
project/
│
├── frontend.py
├── backend.py
├── global-network.ico
└── global-network.icns
```

The application stores its data inside the user's application data directory.

### Windows

```
%LOCALAPPDATA%/connections-app/
```

### Linux

```
~/.local/share/connections-app/
```

Stored data includes:

- SQLite database
- downloaded profile photos

---

## Requirements

- Python 3.10+
- PyQt5

Install dependencies:

```bash
pip install PyQt5
```

---

## Running

```bash
python frontend.py
```

---

## Architecture

```
PyQt5 GUI
      │
      ▼
backend.py
      │
      ▼
SQLite Database
      │
      ├── Tables metadata
      ├── Contact tables
      └── Cached photos
```

---

## Search

The application supports searching across multiple selected tables.

Current search modes:

- Name
- Relationship

---

## Security

Table names are validated before use.

The backend prevents invalid SQL table names by:

- validating identifiers
- rejecting SQL keywords
- using parameterized queries wherever applicable

---

## Future Ideas

- Tags
- Birthday support
- vCard import/export
- Duplicate detection
- Full-text search
- Dark mode
- Automatic backups
- Encrypted database
- Google Contacts API synchronization
