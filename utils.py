import sqlite3
from datetime import datetime
import os

def save_lecture_notes(title, notes, date):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if notes table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
    if c.fetchone() is None:
        # Create notes table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (date TEXT, title TEXT, content TEXT, tags TEXT)''')
        conn.commit()

    # Insert the lecture note with provided date
    c.execute("""
        INSERT INTO notes (date, title, content, tags)
        VALUES (?, ?, ?, ?)
    """, (date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date), title, notes, 'lecture'))
    conn.commit()
    conn.close()

def save_flashcard(word, definition, usage, category):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if flashcards table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flashcards'")
    if c.fetchone() is None:
        # Create flashcards table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS flashcards
                     (word TEXT, definition TEXT, usage TEXT, category TEXT, mastered BOOLEAN, date TEXT)''')
        conn.commit()
    else:
        # Check if the date column exists
        c.execute("PRAGMA table_info(flashcards)")
        columns = [info[1] for info in c.fetchall()]
        if 'date' not in columns:
            # Add the date column if it doesn't exist
            c.execute("ALTER TABLE flashcards ADD COLUMN date TEXT")
            conn.commit()

    # Insert the flashcard with current date
    c.execute("""
        INSERT INTO flashcards (word, definition, usage, category, mastered, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (word, definition, usage, category, False, datetime.now().strftime('%Y-%m-%d')))
    conn.commit()
    conn.close()

def save_question(question, answer, topic, difficulty):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if questions table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
    if c.fetchone() is None:
        # Create questions table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS questions
                     (date TEXT, question TEXT, answer TEXT, topic TEXT, difficulty TEXT, correct INTEGER DEFAULT 0)''')
        conn.commit()

    # Insert the question with current date
    c.execute("""
        INSERT INTO questions (date, question, answer, topic, difficulty, correct)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime('%Y-%m-%d'), question, answer, topic, difficulty, 0))
    conn.commit()
    conn.close()

def save_notes(title, content, tags):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if notes table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
    if c.fetchone() is None:
        # Create notes table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (date TEXT, title TEXT, content TEXT, tags TEXT)''')
        conn.commit()

    # Insert the note with current date
    c.execute("""
        INSERT INTO notes (date, title, content, tags)
        VALUES (?, ?, ?, ?)
    """, (datetime.now().strftime('%Y-%m-%d'), title, content, tags))
    conn.commit()
    conn.close()

def save_study_session(topic, subtopic, time_spent, notes=""):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if study_log table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_log'")
    if c.fetchone() is None:
        # Create study_log table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS study_log
                     (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')
        conn.commit()
    else:
        # Check if the subtopic column exists
        c.execute("PRAGMA table_info(study_log)")
        columns = [info[1] for info in c.fetchall()]
        if 'subtopic' not in columns:
            # Add the subtopic column if it doesn't exist
            c.execute("ALTER TABLE study_log ADD COLUMN subtopic TEXT")
            conn.commit()

    # Insert the study session with current date
    c.execute("""
        INSERT INTO study_log (date, topic, subtopic, time_spent, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().strftime('%Y-%m-%d'), topic, subtopic, time_spent, notes))
    conn.commit()
    conn.close()

def save_progress(section, topic, subtopic, score):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if progress table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='progress'")
    if c.fetchone() is None:
        # Create progress table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS progress
                     (date TEXT, section TEXT, topic TEXT, subtopic TEXT, score REAL)''')
        conn.commit()
    else:
        # Check if the subtopic column exists
        c.execute("PRAGMA table_info(progress)")
        columns = [info[1] for info in c.fetchall()]
        if 'subtopic' not in columns:
            # Add the subtopic column if it doesn't exist
            c.execute("ALTER TABLE progress ADD COLUMN subtopic TEXT")
            conn.commit()

    # Insert the progress with current date
    c.execute("""
        INSERT INTO progress (date, section, topic, subtopic, score)
        VALUES (?, ?, ?, ?, ?)
    """, (datetime.now().strftime('%Y-%m-%d'), section, topic, subtopic, score))
    conn.commit()
    conn.close()

def save_settings(daily_goal, reminder_time):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if productivity_settings table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='productivity_settings'")
    if c.fetchone() is None:
        # Create productivity_settings table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS productivity_settings
                     (user_id TEXT, focus_duration INTEGER, break_duration INTEGER,
                      reminder_frequency TEXT, notification_enabled BOOLEAN,
                      daily_goal INTEGER, reminder_time TEXT)''')
        conn.commit()
    else:
        # Check if the columns exist
        c.execute("PRAGMA table_info(productivity_settings)")
        columns = [info[1] for info in c.fetchall()]
        if 'daily_goal' not in columns:
            c.execute("ALTER TABLE productivity_settings ADD COLUMN daily_goal INTEGER")
        if 'reminder_time' not in columns:
            c.execute("ALTER TABLE productivity_settings ADD COLUMN reminder_time TEXT")
        conn.commit()

    # Check if default user exists
    c.execute("SELECT * FROM productivity_settings WHERE user_id = ?", ("default",))
    if c.fetchone() is None:
        # Insert new settings
        c.execute("""
            INSERT INTO productivity_settings
            (user_id, focus_duration, break_duration, daily_goal, reminder_time)
            VALUES (?, ?, ?, ?, ?)
        """, ("default", 25, 5, daily_goal, reminder_time.strftime("%H:%M") if hasattr(reminder_time, 'strftime') else str(reminder_time)))
    else:
        # Update existing settings
        c.execute("""
            UPDATE productivity_settings
            SET daily_goal = ?, reminder_time = ?
            WHERE user_id = ?
        """, (daily_goal, reminder_time.strftime("%H:%M") if hasattr(reminder_time, 'strftime') else str(reminder_time), "default"))

    conn.commit()
    conn.close()

def save_timer_session(start_time, end_time, duration, completed, topic):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Check if timer_logs table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='timer_logs'")
    if c.fetchone() is None:
        # Create timer_logs table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS timer_logs
                     (date TEXT, start_time TEXT, end_time TEXT, duration INTEGER,
                      completed BOOLEAN, topic TEXT)''')
        conn.commit()

    # Insert the timer session
    c.execute("""
        INSERT INTO timer_logs (date, start_time, end_time, duration, completed, topic)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime('%Y-%m-%d'),
        start_time.strftime('%H:%M:%S') if hasattr(start_time, 'strftime') else str(start_time),
        end_time.strftime('%H:%M:%S') if hasattr(end_time, 'strftime') else str(end_time),
        duration,
        completed,
        topic
    ))
    conn.commit()
    conn.close()

def get_recent_activities(limit=5):
    """
    Get recent activities across all tables (notes, flashcards, questions, study_log)
    """
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    activities = []

    # Get recent notes
    try:
        c.execute("""
            SELECT date, title, tags, 'note' as type
            FROM notes
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table might not exist yet

    # Get recent flashcards
    try:
        c.execute("""
            SELECT date, word, category, 'flashcard' as type
            FROM flashcards
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table might not exist yet

    # Get recent questions
    try:
        c.execute("""
            SELECT date, question, topic, 'question' as type
            FROM questions
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table might not exist yet

    # Get recent study sessions
    try:
        c.execute("""
            SELECT date, topic, time_spent, 'study' as type
            FROM study_log
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table might not exist yet

    # Sort all activities by date (newest first)
    activities.sort(key=lambda x: x[0], reverse=True)

    # Limit to the requested number
    activities = activities[:limit]

    conn.close()
    return activities

def get_section_progress(section):
    """
    Get the average progress score for a specific section
    """
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    try:
        c.execute("""
            SELECT AVG(score)
            FROM progress
            WHERE section = ?
        """, (section,))
        result = c.fetchone()
        avg_score = result[0] if result and result[0] is not None else 0
    except sqlite3.OperationalError:
        avg_score = 0  # Table might not exist yet

    conn.close()
    return avg_score

def get_study_time_distribution():
    """
    Get the distribution of study time across different topics
    """
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    distribution = {}

    try:
        c.execute("""
            SELECT topic, SUM(time_spent)
            FROM study_log
            GROUP BY topic
        """)
        results = c.fetchall()

        for topic, time_spent in results:
            distribution[topic] = time_spent
    except sqlite3.OperationalError:
        pass  # Table might not exist yet

    conn.close()
    return distribution

def mark_flashcard_mastery(word, mastered):
    """
    Update the mastery status of a flashcard
    """
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    try:
        c.execute("""
            UPDATE flashcards
            SET mastered = ?
            WHERE word = ?
        """, (mastered, word))
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Table might not exist yet

    conn.close()

def mark_question_correctness(question, correct):
    """
    Update the correctness status of a question
    """
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    try:
        c.execute("""
            UPDATE questions
            SET correct = ?
            WHERE question = ?
        """, (1 if correct else 0, question))
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Table might not exist yet

    conn.close()
