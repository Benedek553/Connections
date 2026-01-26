from pathlib import Path
import csv
import hashlib
import mimetypes
import sqlite3
import sys
import os
from urllib.parse import urlparse
from urllib.request import Request, urlopen

if sys.platform == "win32":
    base = Path.home() / "AppData" / "Local"
else:
    base = Path.home() / ".local" / "share"

app_dir = base / "connections-app"
app_dir.mkdir(parents=True, exist_ok=True)
photos_dir = app_dir / "photos"
photos_dir.mkdir(parents=True, exist_ok=True)

# Define the database file path
#db_file_path = os.path.join(os.path.dirname(__file__), 'table.db')

# Connect to the SQLite database file
def connect_to_database():
    try:
        conn = sqlite3.connect(app_dir / "table.db")
        print('Connected to the SQLite database.')
        return conn
    except sqlite3.Error as e:
        print(f'Error opening database: {e}')
        return None

# Create a table to store metadata about other tables if it doesn't exist
def create_tables_metadata_table(conn):
    try:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print('Tables metadata table created or already exists.')
    except sqlite3.Error as e:
        print(f'Error creating tables metadata table: {e}')

# Validate table names
def is_valid_table_name(name):
    reserved_keywords = {
        'SELECT', 'FROM', 'WHERE', 'INSERT', 'DELETE', 'UPDATE', 'CREATE', 'DROP',
        'ALTER', 'TABLE', 'INDEX', 'VIEW', 'TRIGGER', 'AS', 'AND', 'OR', 'NOT',
        'NULL', 'JOIN', 'ON', 'IN', 'IS', 'LIKE', 'BETWEEN', 'EXISTS', 'UNION',
        'ALL', 'ANY', 'DISTINCT', 'GROUP', 'BY', 'HAVING', 'ORDER', 'LIMIT',
        'OFFSET', 'ASC', 'DESC', 'INTO', 'VALUES', 'SET', 'INNER', 'LEFT', 'RIGHT',
        'FULL', 'OUTER', 'CROSS', 'NATURAL', 'USING', 'CASE', 'WHEN', 'THEN', 'ELSE',
        'END', 'CAST', 'CONVERT', 'EXCEPT', 'INTERSECT'
    }
    return name.isidentifier() and name.upper() not in reserved_keywords

# Add a new table metadata entry
def add_table_metadata(conn, table_name):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return False
    try:
        with conn:
            conn.execute('INSERT INTO tables (name) VALUES (?)', (table_name,))
            print(f'Table metadata for "{table_name}" added.')
            return True
    except sqlite3.Error as e:
        print(f'Error adding table metadata: {e}')
        return False

# Create a new table
def create_table(conn, table_name):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return False

    create_table_sql = f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone_contact TEXT,
        email TEXT,
        whatsapp_phone TEXT,
        signal_phone TEXT,
        telegram_handle TEXT,
        facebook TEXT,  -- New column
        linkedin TEXT,  -- New column
        photo TEXT,
        relationship TEXT,
        other_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    '''
    try:
        with conn:
            conn.execute(create_table_sql)
        print(f'Table "{table_name}" created.')
        return True
    except sqlite3.Error as e:
        print(f'Error creating table: {e}')
        return False


# Fetch all tables
def fetch_all_tables(conn):
    try:
        cursor = conn.execute('SELECT * FROM tables')
        tables = cursor.fetchall()
        return tables
    except sqlite3.Error as e:
        print(f'Error fetching tables: {e}')
        return []

# Add an entry to a specific table
def add_entry(conn, table_name, entry_data):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return False
    if not ensure_table_schema(conn, table_name):
        return False

    entry_data = normalize_entry_photo(entry_data)

    insert_sql = f'''
    INSERT INTO {table_name} (name, phone_contact, email, whatsapp_phone, signal_phone, telegram_handle, facebook, linkedin, photo, relationship, other_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    try:
        with conn:
            conn.execute(insert_sql, entry_data)
        print(f'Entry added to table "{table_name}".')
        return True
    except sqlite3.Error as e:
        print(f'Error inserting entry: {e}')
        return False


def ensure_table_schema(conn, table_name):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return False
    try:
        cursor = conn.execute(f'PRAGMA table_info({table_name})')
        columns = {row[1] for row in cursor.fetchall()}
    except sqlite3.Error as e:
        print(f'Error reading table schema: {e}')
        return False

    missing = []
    if "photo" not in columns:
        missing.append("photo")

    if not missing:
        return True

    try:
        with conn:
            for column in missing:
                conn.execute(f'ALTER TABLE {table_name} ADD COLUMN {column} TEXT')
        return True
    except sqlite3.Error as e:
        print(f'Error updating table schema: {e}')
        return False


def is_remote_url(value):
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def guess_photo_extension(url, content_type):
    if content_type:
        extension = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if extension:
            return extension
    _, ext = os.path.splitext(url)
    if ext:
        return ext
    return ".jpg"


def fetch_remote_photo(url):
    try:
        request = Request(url, headers={"User-Agent": "Connections/1.0"})
        with urlopen(request, timeout=10) as response:
            content = response.read()
            content_type = response.headers.get("Content-Type", "")
    except Exception as e:
        print(f'Error fetching photo from "{url}": {e}')
        return ""

    extension = guess_photo_extension(url, content_type)
    name = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    file_path = photos_dir / f"{name}{extension}"

    try:
        with open(file_path, "wb") as file_handle:
            file_handle.write(content)
    except OSError as e:
        print(f'Error saving photo "{file_path}": {e}')
        return ""

    return str(file_path)


def normalize_photo_value(value):
    value = (value or "").strip()
    if not value:
        return ""
    if is_remote_url(value):
        return fetch_remote_photo(value)
    return value


def normalize_entry_photo(entry_data):
    if len(entry_data) < 9:
        return entry_data
    entry_list = list(entry_data)
    entry_list[8] = normalize_photo_value(entry_list[8])
    return tuple(entry_list)


def parse_google_contacts_csv(file_path, mapping):
    entries = []
    skipped = 0

    with open(file_path, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            name_column = mapping.get("name", "")
            name_column_2 = mapping.get("name_2", "")
            phone_column = mapping.get("phone_contact", "")
            email_column = mapping.get("email", "")
            whatsapp_column = mapping.get("whatsapp_phone", "")
            signal_column = mapping.get("signal_phone", "")
            telegram_column = mapping.get("telegram_handle", "")
            facebook_column = mapping.get("facebook", "")
            linkedin_column = mapping.get("linkedin", "")
            photo_column = mapping.get("photo", "")
            relationship_column = mapping.get("relationship", "")
            notes_column = mapping.get("other_notes", "")

            name_primary = row.get(name_column, "").strip() if name_column else ""
            name_secondary = row.get(name_column_2, "").strip() if name_column_2 else ""
            name = " ".join(part for part in [name_primary, name_secondary] if part)
            phone = row.get(phone_column, "").strip() if phone_column else ""
            email = row.get(email_column, "").strip() if email_column else ""
            whatsapp = row.get(whatsapp_column, "").strip() if whatsapp_column else ""
            signal = row.get(signal_column, "").strip() if signal_column else ""
            telegram = row.get(telegram_column, "").strip() if telegram_column else ""
            facebook = row.get(facebook_column, "").strip() if facebook_column else ""
            linkedin = row.get(linkedin_column, "").strip() if linkedin_column else ""
            photo_raw = row.get(photo_column, "").strip() if photo_column else ""
            photo = normalize_photo_value(photo_raw)
            relationship = row.get(relationship_column, "").strip() if relationship_column else ""
            notes = row.get(notes_column, "").strip() if notes_column else ""

            if not name:
                skipped += 1
                continue

            entry_data = (
                name,
                phone,
                email,
                whatsapp,
                signal,
                telegram,
                facebook,
                linkedin,
                photo,
                relationship,
                notes,
            )
            entries.append(entry_data)

    return entries, skipped


def import_google_contacts(conn, table_name, file_path, mapping):
    if not is_valid_table_name(table_name):
        return None, None, "Invalid table name."
    if not ensure_table_schema(conn, table_name):
        return None, None, "Could not update table schema."

    try:
        entries, skipped = parse_google_contacts_csv(file_path, mapping)
    except OSError as e:
        return None, None, f"Could not read CSV: {e}"
    except csv.Error as e:
        return None, None, f"Invalid CSV format: {e}"

    if not entries:
        return 0, skipped, None

    insert_sql = f'''
    INSERT INTO {table_name} (name, phone_contact, email, whatsapp_phone, signal_phone, telegram_handle, facebook, linkedin, photo, relationship, other_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    try:
        with conn:
            conn.executemany(insert_sql, entries)
        return len(entries), skipped, None
    except sqlite3.Error as e:
        return None, None, f"Error importing contacts: {e}"

# Fetch entries from a specific table
def fetch_entries(conn, table_name):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return []
    ensure_table_schema(conn, table_name)
    try:
        cursor = conn.execute(f'SELECT * FROM {table_name}')
        entries = cursor.fetchall()
        return entries
    except sqlite3.Error as e:
        print(f'Error querying table: {e}')
        return []

# Edit an entry in a specific table
def edit_entry(conn, table_name, entry_id, entry_data):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return False
    if not ensure_table_schema(conn, table_name):
        return False

    entry_data = normalize_entry_photo(entry_data)

    update_sql = f'''
    UPDATE {table_name}
    SET name = ?, phone_contact = ?, email = ?, whatsapp_phone = ?, signal_phone = ?, telegram_handle = ?, facebook = ?, linkedin = ?, photo = ?, relationship = ?, other_notes = ?, last_modified = CURRENT_TIMESTAMP
    WHERE id = ?
    '''
    try:
        with conn:
            conn.execute(update_sql, (*entry_data, entry_id))
        print(f'Entry {entry_id} updated in table "{table_name}".')
        return True
    except sqlite3.Error as e:
        print(f'Error updating entry: {e}')
        return False



# Delete an entry from a specific table
def delete_entry(conn, table_name, entry_id):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return False
    delete_sql = f'DELETE FROM {table_name} WHERE id = ?'
    try:
        with conn:
            conn.execute(delete_sql, (entry_id,))
            print(f'Entry {entry_id} deleted from table "{table_name}".')
            return True
    except sqlite3.Error as e:
        print(f'Error deleting entry: {e}')
        return False

# Delete a table
def delete_table(conn, table_name):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return False
    drop_table_sql = f'DROP TABLE IF EXISTS {table_name}'
    try:
        with conn:
            conn.execute(drop_table_sql)
            conn.execute('DELETE FROM tables WHERE name = ?', (table_name,))
            print(f'Table "{table_name}" and its metadata deleted.')
            return True
    except sqlite3.Error as e:
        print(f'Error deleting table: {e}')
        return False

# Combine tables
def combine_tables(conn, table_names):
    if len(table_names) < 2:
        print('Select at least two tables to combine.')
        return []
    valid_tables = [name for name in table_names if is_valid_table_name(name)]
    if len(valid_tables) < 2:
        print('Invalid table names selected.')
        return []
    
    for table_name in valid_tables:
        if not ensure_table_schema(conn, table_name):
            return []

    # Create a query for each table that includes the source table name
    queries = [f"SELECT *, '{name}' AS source_table FROM {name}" for name in valid_tables]
    combined_query = ' UNION ALL '.join(queries)
    
    try:
        cursor = conn.execute(combined_query)
        combined_data = cursor.fetchall()
        combined_data.sort(key=lambda x: x[1])  # Assuming the second column is 'name'
        # Output the result to the console


        return combined_data
    except sqlite3.Error as e:
        print(f'Error combining tables: {e}')
        return []




# Search tables
def search_tables(conn, search_term, table_names, search_type='name'):
    if not table_names:
        print('No tables selected for search.')
        return []

    valid_tables = [name for name in table_names if is_valid_table_name(name)]
    combined_results = []

    for table_name in valid_tables:
        if not ensure_table_schema(conn, table_name):
            return []
        if search_type == 'name':
            query = f"SELECT *, '{table_name}' AS source_table FROM {table_name} WHERE name LIKE ?"
        elif search_type == 'relationship':
            query = f"SELECT *, '{table_name}' AS source_table FROM {table_name} WHERE relationship LIKE ?"
        else:
            continue

        try:
            cursor = conn.execute(query, (f'%{search_term}%',))
            combined_results.extend(cursor.fetchall())
        except sqlite3.Error as e:
            print(f'Error searching table {table_name}: {e}')


    return combined_results



def get_table_creation_date(conn, table_name):
    try:
        cursor = conn.execute('SELECT created_at FROM tables WHERE name = ?', (table_name,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f'Error fetching creation date for table {table_name}: {e}')
        return None
