
from app.db.models import Base
from app.db.connect import engine


Base.metadata.create_all(bind=engine)
