import sqlite3
import os
from datetime import datetime

# Define the database file path
#db_file_path = os.path.join(os.path.dirname(__file__), 'table.db')
db_file_path = os.path.join(os.path.expanduser('~'), '.local', 'share', 'connections-app', 'table.db')

# Connect to the SQLite database file
def connect_to_database():
    try:
        conn = sqlite3.connect(db_file_path)
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

    insert_sql = f'''
    INSERT INTO {table_name} (name, phone_contact, email, whatsapp_phone, signal_phone, telegram_handle, facebook, linkedin, relationship, other_notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    try:
        with conn:
            conn.execute(insert_sql, entry_data)
        print(f'Entry added to table "{table_name}".')
        return True
    except sqlite3.Error as e:
        print(f'Error inserting entry: {e}')
        return False


# Fetch entries from a specific table
def fetch_entries(conn, table_name):
    if not is_valid_table_name(table_name):
        print('Invalid table name.')
        return []
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

    update_sql = f'''
    UPDATE {table_name}
    SET name = ?, phone_contact = ?, email = ?, whatsapp_phone = ?, signal_phone = ?, telegram_handle = ?, facebook = ?, linkedin = ?, relationship = ?, other_notes = ?, last_modified = CURRENT_TIMESTAMP
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
