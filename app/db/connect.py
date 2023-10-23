from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.config.config import DATABASE_URL

class DatabaseError(Exception):
    def __init__(self, message):
        super().__init__(message)

def create_db_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()

def _execute_query(session, query):
    result = session.execute(query)
    return result.fetchall()

from sqlalchemy.exc import SQLAlchemyError

def safe_execute_query(session, query):
    try:
        result = _execute_query(session, query)
        return result
    except SQLAlchemyError as e:
        session.rollback()
        error_message = f"Database error: {str(e)}"
        raise DatabaseError(error_message)        