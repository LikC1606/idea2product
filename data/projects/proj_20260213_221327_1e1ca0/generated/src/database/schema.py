```python
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    completed = Column(Boolean, default=False)
    
def init_db(uri='sqlite:///todo.db'):
    engine = create_engine(uri)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

# Usage:
# Session = init_db()
# session = Session()
# new_task = Task(name="Sample Task", description="This is a sample task.")
# session.add(new_task)
# session.commit()
```
