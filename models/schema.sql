-- Health Tracker Database Schema

-- Schema Version Table
-- Tracks database migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Habits Table
-- Stores user's habits with visibility and ordering preferences
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    is_public BOOLEAN DEFAULT 1 NOT NULL,
    order_index INTEGER DEFAULT 0 NOT NULL,
    tracks_value BOOLEAN DEFAULT 0 NOT NULL,
    value_unit TEXT,
    value_aggregation_type TEXT DEFAULT 'absolute' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Logs Table
-- Stores daily completion status for each habit
-- Optional value field stores numeric data (e.g., pushup count, weight)
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    date DATE NOT NULL,
    status BOOLEAN NOT NULL,
    value REAL,
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    UNIQUE(habit_id, date)
);

-- Indexes for Performance
-- Index on logs.date for date-range queries
CREATE INDEX IF NOT EXISTS idx_logs_date ON logs(date);

-- Composite index on logs for habit+date lookups
CREATE INDEX IF NOT EXISTS idx_logs_habit_date ON logs(habit_id, date);

-- Composite index on habits for filtering public/active habits
CREATE INDEX IF NOT EXISTS idx_habits_public ON habits(is_public, is_active);

-- Index on habits.order_index for efficient ordering
CREATE INDEX IF NOT EXISTS idx_habits_order ON habits(order_index);
