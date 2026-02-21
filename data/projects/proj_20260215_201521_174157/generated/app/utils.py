from sqlalchemy.orm.exc import NoResultFound
from app.database import db

def get_record_by_id(model_class, record_id):
    """
    Retrieve a record by its ID from the database.

    :param model_class: SQLAlchemy model class to query.
    :param record_id: ID of the record to retrieve.
    :return: Record object if found, None otherwise.
    """
    try:
        return db.session.query(model_class).filter_by(id=record_id).one()
    except NoResultFound:
        return None

def add_record(record):
    """
    Add a new record to the database.

    :param record: SQLAlchemy model instance to add.
    """
    db.session.add(record)
    db.session.commit()

def update_record():
    """
    Commit any pending updates to the database.
    """
    db.session.commit()

def delete_record(record):
    """
    Delete a record from the database.

    :param record: SQLAlchemy model instance to delete.
    """
    db.session.delete(record)
    db.session.commit()

def get_records(model_class, filters=None):
    """
    Retrieve multiple records from the database with optional filters.

    :param model_class: SQLAlchemy model class to query.
    :param filters: Optional dictionary of filters to apply.
    :return: List of records.
    """
    query = db.session.query(model_class)
    if filters:
        query = query.filter_by(**filters)
    return query.all()