from app.db import connect


def list_walls():
    conn = connect()
    try:
        return [dict(r) for r in conn.execute("SELECT * FROM walls ORDER BY id").fetchall()]
    finally:
        conn.close()


def get_wall(wid: int):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM walls WHERE id=?", (wid,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
