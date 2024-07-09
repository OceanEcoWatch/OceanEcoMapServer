from app.db.connect import Session


def percent_to_accuracy(percent: int):
    return 255 / 100 * percent


def accuracy_limit_to_percent(accuracy: int):
    return accuracy / 255 * 100


def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
