CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    birth DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_DATE,
    updated_at DATETIME DEFAULT CURRENT_DATE
);
