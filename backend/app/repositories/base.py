from backend.app.database import db


class BaseRepository:
    def __init__(self):
        self.db = db
