from sqlalchemy.orm import Session

class BaseRepository:
    def __init__(self, session : Session) -> None:
        # Session allows to connect with db
        self.session = session

# router -> service -> repository -> db
# router <- service <- repository <- db