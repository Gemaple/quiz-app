"""
数据库模块：科目、题目、错题本、设置、考试记录、笔记、错题历史的持久化存储
使用 SQLite，Python 内置，无需额外数据库服务
V9 升级：添加作答次数、错误次数、笔记字段、错题历史表、考试单题作答表
"""
import sqlite3
import json
import os
import sys
from datetime import datetime

# 数据库路径适配：安卓用应用私有目录，其他用当前目录
try:
    from android import mActivity
    APP_DIR = mActivity.getFilesDir().getAbsolutePath()
except ImportError:
    if getattr(sys, 'frozen', False):
        APP_DIR = os.path.dirname(sys.executable)
    else:
        APP_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(APP_DIR, "quiz_data.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # 科目表（支持二级目录：parent_id=0为一级科目）
    c.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER DEFAULT 0,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    try:
        c.execute("ALTER TABLE subjects ADD COLUMN parent_id INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # 题目表（V9升级：添加作答次数、错误次数、笔记字段）
    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER DEFAULT 0,
            q_type TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options TEXT DEFAULT '[]',
            answer TEXT NOT NULL,
            analysis TEXT DEFAULT '',
            source TEXT DEFAULT '',
            try_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0,
            note_text TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    try:
        c.execute("ALTER TABLE questions ADD COLUMN subject_id INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE questions ADD COLUMN try_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE questions ADD COLUMN wrong_count INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE questions ADD COLUMN note_text TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # 错题本表
    c.execute("""
        CREATE TABLE IF NOT EXISTS wrong_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_answer TEXT DEFAULT '',
            wrong_count INTEGER DEFAULT 1,
            last_wrong_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        )
    """)

    # 错题历史表（V9新增：保存每次答错的记录，用于导出历史作答）
    c.execute("""
        CREATE TABLE IF NOT EXISTS wrong_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            user_answer TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        )
    """)

    # 考试单题作答表（V9新增：保存每次考试每道题的用户作答，用于导出考试记录）
    c.execute("""
        CREATE TABLE IF NOT EXISTS exam_question_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            question_index INTEGER DEFAULT 0,
            user_answer TEXT DEFAULT '',
            is_correct INTEGER DEFAULT 0,
            FOREIGN KEY (exam_id) REFERENCES exam_records(id) ON DELETE CASCADE
        )
    """)

    # 设置表
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # 考试记录表
    c.execute("""
        CREATE TABLE IF NOT EXISTS exam_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER DEFAULT 0,
            total_count INTEGER,
            correct_count INTEGER,
            score REAL,
            duration INTEGER,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    try:
        c.execute("ALTER TABLE exam_records ADD COLUMN subject_id INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # 默认科目
    c.execute("SELECT COUNT(*) as cnt FROM subjects")
    if c.fetchone()["cnt"] == 0:
        c.execute("INSERT INTO subjects (name, description) VALUES (?, ?)", ("默认科目", "未分类的题目"))

    conn.commit()
    conn.close()


# ============ 科目操作（支持二级目录） ============

def add_subject(name, description="", parent_id=0):
    conn = get_conn()
    try:
        c = conn.cursor()
        c.execute(
            "INSERT INTO subjects (name, description, parent_id) VALUES (?, ?, ?)",
            (name, description, parent_id)
        )
        sid = c.lastrowid
        conn.commit()
        return sid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_subjects():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM subjects ORDER BY parent_id, id").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_subject_tree():
    all_subjects = get_subjects()
    top_level = [s for s in all_subjects if s.get("parent_id", 0) == 0]
    tree = []
    for top in top_level:
        children = [s for s in all_subjects if s.get("parent_id", 0) == top["id"]]
        tree.append((top, children))
    return tree


def get_child_subjects(parent_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM subjects WHERE parent_id=? ORDER BY id", (parent_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_subject(sid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM subjects WHERE id=?", (sid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_subject(sid, name, description="", parent_id=None):
    conn = get_conn()
    if parent_id is not None:
        conn.execute(
            "UPDATE subjects SET name=?, description=?, parent_id=? WHERE id=?",
            (name, description, parent_id, sid)
        )
    else:
        conn.execute(
            "UPDATE subjects SET name=?, description=? WHERE id=?",
            (name, description, sid)
        )
    conn.commit()
    conn.close()


def delete_subject(sid):
    conn = get_conn()
    conn.execute("UPDATE subjects SET parent_id=0 WHERE parent_id=?", (sid,))
    conn.execute("UPDATE questions SET subject_id=1 WHERE subject_id=?", (sid,))
    conn.execute("DELETE FROM subjects WHERE id=?", (sid,))
    conn.commit()
    conn.close()


def get_subject_question_count(sid):
    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) as cnt FROM questions WHERE subject_id=?", (sid,)).fetchone()
    conn.close()
    return row["cnt"]


# ============ 题目操作 ============

def add_question(q_type, question_text, options, answer, analysis="", source="", subject_id=0, note_text=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO questions (subject_id, q_type, question_text, options, answer, analysis, source, note_text) VALUES (?,?,?,?,?,?,?,?)",
        (subject_id, q_type, question_text, json.dumps(options, ensure_ascii=False), answer, analysis, source, note_text)
    )
    qid = c.lastrowid
    conn.commit()
    conn.close()
    return qid


def add_questions_batch(questions_list):
    conn = get_conn()
    c = conn.cursor()
    count = 0
    for q in questions_list:
        try:
            c.execute(
                "INSERT INTO questions (subject_id, q_type, question_text, options, answer, analysis, source, note_text) VALUES (?,?,?,?,?,?,?,?)",
                (
                    q.get("subject_id", 0),
                    q.get("q_type", "single"),
                    q.get("question_text", ""),
                    json.dumps(q.get("options", []), ensure_ascii=False),
                    q.get("answer", ""),
                    q.get("analysis", ""),
                    q.get("source", ""),
                    q.get("note_text", ""),
                )
            )
            count += 1
        except Exception:
            continue
    conn.commit()
    conn.close()
    return count


def get_question(qid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["options"] = json.loads(d["options"])
        return d
    return None


def get_questions_by_ids(qid_list):
    """根据ID列表获取题目（用于手动勾选题目组卷）"""
    if not qid_list:
        return []
    conn = get_conn()
    placeholders = ",".join("?" * len(qid_list))
    rows = conn.execute(
        f"SELECT * FROM questions WHERE id IN ({placeholders})", qid_list
    ).fetchall()
    conn.close()
    result = []
    id_map = {qid: i for i, qid in enumerate(qid_list)}
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d["options"])
        result.append(d)
    # 按用户选择的顺序排序
    result.sort(key=lambda x: id_map.get(x["id"], 9999))
    return result


def get_all_questions(q_type=None, subject_id=None):
    conn = get_conn()
    query = "SELECT * FROM questions WHERE 1=1"
    params = []
    if q_type:
        query += " AND q_type=?"
        params.append(q_type)
    if subject_id is not None and subject_id > 0:
        query += " AND subject_id=?"
        params.append(subject_id)
    query += " ORDER BY id"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d["options"])
        result.append(d)
    return result


def get_random_questions(count, q_type=None, subject_id=None, id_range=None):
    """随机抽题，支持题型、科目、题号范围筛选"""
    conn = get_conn()
    query = "SELECT * FROM questions WHERE 1=1"
    params = []
    if q_type:
        query += " AND q_type=?"
        params.append(q_type)
    if subject_id is not None and subject_id > 0:
        query += " AND subject_id=?"
        params.append(subject_id)
    if id_range and id_range[0] and id_range[1]:
        query += " AND id BETWEEN ? AND ?"
        params.extend([id_range[0], id_range[1]])
    query += " ORDER BY RANDOM() LIMIT ?"
    params.append(count)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d["options"])
        result.append(d)
    return result


def update_question(qid, q_type, question_text, options, answer, analysis="", subject_id=None, note_text=None):
    conn = get_conn()
    if subject_id is not None and note_text is not None:
        conn.execute(
            "UPDATE questions SET subject_id=?, q_type=?, question_text=?, options=?, answer=?, analysis=?, note_text=? WHERE id=?",
            (subject_id, q_type, question_text, json.dumps(options, ensure_ascii=False), answer, analysis, note_text, qid)
        )
    elif subject_id is not None:
        conn.execute(
            "UPDATE questions SET subject_id=?, q_type=?, question_text=?, options=?, answer=?, analysis=? WHERE id=?",
            (subject_id, q_type, question_text, json.dumps(options, ensure_ascii=False), answer, analysis, qid)
        )
    elif note_text is not None:
        conn.execute(
            "UPDATE questions SET q_type=?, question_text=?, options=?, answer=?, analysis=?, note_text=? WHERE id=?",
            (q_type, question_text, json.dumps(options, ensure_ascii=False), answer, analysis, note_text, qid)
        )
    else:
        conn.execute(
            "UPDATE questions SET q_type=?, question_text=?, options=?, answer=?, analysis=? WHERE id=?",
            (q_type, question_text, json.dumps(options, ensure_ascii=False), answer, analysis, qid)
        )
    conn.commit()
    conn.close()


def update_question_note(qid, note_text):
    """更新题目笔记"""
    conn = get_conn()
    conn.execute("UPDATE questions SET note_text=? WHERE id=?", (note_text, qid))
    conn.commit()
    conn.close()


def increment_question_try(qid):
    """增加题目作答次数"""
    conn = get_conn()
    conn.execute("UPDATE questions SET try_count = try_count + 1 WHERE id=?", (qid,))
    conn.commit()
    conn.close()


def increment_question_wrong(qid):
    """增加题目错误次数"""
    conn = get_conn()
    conn.execute("UPDATE questions SET wrong_count = wrong_count + 1 WHERE id=?", (qid,))
    conn.commit()
    conn.close()


def delete_question(qid):
    conn = get_conn()
    conn.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.execute("DELETE FROM wrong_questions WHERE question_id=?", (qid,))
    conn.execute("DELETE FROM wrong_history WHERE question_id=?", (qid,))
    conn.commit()
    conn.close()


def get_question_count(q_type=None, subject_id=None):
    conn = get_conn()
    query = "SELECT COUNT(*) as cnt FROM questions WHERE 1=1"
    params = []
    if q_type:
        query += " AND q_type=?"
        params.append(q_type)
    if subject_id is not None and subject_id > 0:
        query += " AND subject_id=?"
        params.append(subject_id)
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row["cnt"]


# ============ 错题本操作 ============

def add_wrong_question(question_id, user_answer=""):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM wrong_questions WHERE question_id=?", (question_id,)
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE wrong_questions SET wrong_count=wrong_count+1, user_answer=?, last_wrong_at=datetime('now','localtime') WHERE question_id=?",
            (user_answer, question_id)
        )
    else:
        conn.execute(
            "INSERT INTO wrong_questions (question_id, user_answer) VALUES (?,?)",
            (question_id, user_answer)
        )
    # 同时记录错题历史
    conn.execute(
        "INSERT INTO wrong_history (question_id, user_answer) VALUES (?,?)",
        (question_id, user_answer)
    )
    conn.commit()
    conn.close()


def get_wrong_questions(subject_id=None, q_type=None):
    conn = get_conn()
    query = """
        SELECT w.*, q.subject_id, q.q_type, q.question_text, q.options, q.answer, q.analysis, q.note_text, q.try_count, q.wrong_count as q_wrong_count
        FROM wrong_questions w
        JOIN questions q ON w.question_id = q.id
        WHERE 1=1
    """
    params = []
    if subject_id is not None and subject_id > 0:
        query += " AND q.subject_id=?"
        params.append(subject_id)
    if q_type:
        query += " AND q.q_type=?"
        params.append(q_type)
    query += " ORDER BY w.wrong_count DESC, w.last_wrong_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d["options"])
        result.append(d)
    return result


def get_wrong_history(question_id):
    """获取某题的错题历史记录"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM wrong_history WHERE question_id=? ORDER BY id", (question_id,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def remove_wrong_question(question_id):
    conn = get_conn()
    conn.execute("DELETE FROM wrong_questions WHERE question_id=?", (question_id,))
    conn.commit()
    conn.close()


def clear_wrong_questions():
    conn = get_conn()
    conn.execute("DELETE FROM wrong_questions")
    conn.commit()
    conn.close()


# ============ 设置操作 ============

def get_setting(key, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
        (key, str(value))
    )
    conn.commit()
    conn.close()


# ============ 考试记录 ============

def add_exam_record(total, correct, score, duration, subject_id=0):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO exam_records (subject_id, total_count, correct_count, score, duration) VALUES (?,?,?,?,?)",
        (subject_id, total, correct, score, duration)
    )
    exam_id = c.lastrowid
    conn.commit()
    conn.close()
    return exam_id


def add_exam_question_answers(exam_id, answers_list):
    """批量保存考试单题作答记录
    answers_list: [(question_id, question_index, user_answer, is_correct), ...]
    """
    conn = get_conn()
    c = conn.cursor()
    for item in answers_list:
        c.execute(
            "INSERT INTO exam_question_answers (exam_id, question_id, question_index, user_answer, is_correct) VALUES (?,?,?,?,?)",
            (exam_id, item[0], item[1], item[2], 1 if item[3] else 0)
        )
    conn.commit()
    conn.close()


def get_exam_question_answers(exam_id):
    """获取某次考试的所有单题作答记录"""
    conn = get_conn()
    rows = conn.execute(
        """SELECT eqa.*, q.q_type, q.question_text, q.options, q.answer, q.analysis, q.note_text
           FROM exam_question_answers eqa
           JOIN questions q ON eqa.question_id = q.id
           WHERE eqa.exam_id=? ORDER BY eqa.question_index""",
        (exam_id,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        d = dict(row)
        d["options"] = json.loads(d["options"])
        result.append(d)
    return result


def get_exam_records(limit=20, subject_id=None):
    conn = get_conn()
    query = "SELECT * FROM exam_records WHERE 1=1"
    params = []
    if subject_id is not None and subject_id > 0:
        query += " AND subject_id=?"
        params.append(subject_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_exam_record(exam_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM exam_records WHERE id=?", (exam_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_exam_record(exam_id):
    """删除考试记录及其单题作答记录"""
    conn = get_conn()
    conn.execute("DELETE FROM exam_question_answers WHERE exam_id=?", (exam_id,))
    conn.execute("DELETE FROM exam_records WHERE id=?", (exam_id,))
    conn.commit()
    conn.close()


def get_stats():
    """获取统计数据"""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM questions")
    total_questions = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM exam_records")
    total_exams = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions WHERE wrong_count > 0")
    total_wrong = c.fetchone()[0]
    conn.close()
    return {
        "total_questions": total_questions,
        "total_subjects": total_subjects,
        "total_exams": total_exams,
        "total_wrong": total_wrong,
    }


def update_question_stats(qid, is_correct):
    """更新题目作答统计"""
    conn = get_conn()
    c = conn.cursor()
    if is_correct:
        c.execute("UPDATE questions SET try_count = try_count + 1 WHERE id=?", (qid,))
    else:
        c.execute("UPDATE questions SET try_count = try_count + 1, wrong_count = wrong_count + 1 WHERE id=?", (qid,))
    conn.commit()
    conn.close()


def get_questions_by_type(q_type, subject_id=None):
    """按题型获取题目"""
    return get_all_questions(q_type, subject_id)
