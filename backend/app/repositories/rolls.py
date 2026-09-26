from app.db import connect


def list_rolls():
    conn = connect()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM rolls ORDER BY id").fetchall()]
    finally:
        conn.close()


def get_roll(rid: int):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM rolls WHERE id=?", (rid,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
