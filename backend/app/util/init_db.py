from app.core.database import Base, engine
from app.db.models import user
from app.db.models import chat

def create_tables():
    Base.metadata.create_all(bind=engine)