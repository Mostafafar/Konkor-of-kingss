import sqlite3
from typing import List, Dict, Tuple

def init_db():
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_text TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_option TEXT NOT NULL CHECK(correct_option IN ('A', 'B', 'C', 'D')),
        explanation TEXT,
        difficulty INTEGER CHECK(difficulty BETWEEN 1 AND 5),
        category TEXT,
        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats (
        user_id INTEGER PRIMARY KEY,
        questions_added INTEGER DEFAULT 0,
        last_active TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str, first_name: str, last_name: str):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
    VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    
    cursor.execute('''
    INSERT OR IGNORE INTO user_stats (user_id)
    VALUES (?)
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def add_question(user_id: int, question_data: Dict):
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO questions (
        user_id, question_text, option_a, option_b, option_c, option_d, 
        correct_option, explanation, difficulty, category
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        question_data['question_text'],
        question_data['option_a'],
        question_data['option_b'],
        question_data['option_c'],
        question_data['option_d'],
        question_data['correct_option'],
        question_data.get('explanation', ''),
        question_data.get('difficulty', 3),
        question_data.get('category', 'General')
    ))
    
    cursor.execute('''
    UPDATE user_stats
    SET questions_added = questions_added + 1,
        last_active = CURRENT_TIMESTAMP
    WHERE user_id = ?
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def get_user_stats(user_id: int) -> Dict:
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT questions_added FROM user_stats WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return {'questions_added': result[0] if result else 0}

def get_random_question(category: str = None) -> Dict:
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    if category:
        cursor.execute('''
        SELECT * FROM questions 
        WHERE category = ?
        ORDER BY RANDOM()
        LIMIT 1
        ''', (category,))
    else:
        cursor.execute('''
        SELECT * FROM questions 
        ORDER BY RANDOM()
        LIMIT 1
        ''')
    
    question = cursor.fetchone()
    conn.close()
    
    if not question:
        return None
    
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, question))

def get_categories() -> List[str]:
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT DISTINCT category FROM questions
    ''')
    
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return categories

def get_questions_count() -> int:
    conn = sqlite3.connect('quiz_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM questions')
    count = cursor.fetchone()[0]
    conn.close()
    
    return count