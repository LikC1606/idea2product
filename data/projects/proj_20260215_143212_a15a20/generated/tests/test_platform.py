import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Problem, Solution, User, Leaderboard, Discussion

# Setup the test database
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
Session = sessionmaker(bind=engine)

@pytest.fixture(scope='module')
def session():
    # Create all tables
    Problem.metadata.create_all(engine)
    Solution.metadata.create_all(engine)
    User.metadata.create_all(engine)
    Leaderboard.metadata.create_all(engine)
    Discussion.metadata.create_all(engine)
    
    session = Session()
    yield session
    session.close()

def test_problem_repository(session):
    # Test problem creation
    problem = Problem(title="Sample Problem", description="Solve this sample problem.")
    session.add(problem)
    session.commit()

    retrieved_problem = session.query(Problem).filter_by(title="Sample Problem").first()
    assert retrieved_problem is not None
    assert retrieved_problem.description == "Solve this sample problem."

def test_solution_submission(session):
    # Test solution submission
    user = User(name="Test User")
    problem = Problem(title="Sample Problem")
    session.add_all([user, problem])
    session.commit()

    solution = Solution(content="Sample solution", user_id=user.id, problem_id=problem.id)
    session.add(solution)
    session.commit()

    retrieved_solution = session.query(Solution).filter_by(user_id=user.id, problem_id=problem.id).first()
    assert retrieved_solution is not None
    assert retrieved_solution.content == "Sample solution"

def test_user_profile(session):
    # Test user profile creation
    user = User(name="Test User", profile_info="This is a test user.")
    session.add(user)
    session.commit()

    retrieved_user = session.query(User).filter_by(name="Test User").first()
    assert retrieved_user is not None
    assert retrieved_user.profile_info == "This is a test user."

def test_leaderboard(session):
    # Test leaderboard entry
    user = User(name="Test User")
    session.add(user)
    session.commit()

    leaderboard_entry = Leaderboard(user_id=user.id, score=100)
    session.add(leaderboard_entry)
    session.commit()

    retrieved_entry = session.query(Leaderboard).filter_by(user_id=user.id).first()
    assert retrieved_entry is not None
    assert retrieved_entry.score == 100

def test_discussion_forum(session):
    # Test discussion creation
    user = User(name="Test User")
    problem = Problem(title="Sample Problem")
    session.add_all([user, problem])
    session.commit()

    discussion = Discussion(content="This is a test discussion.", user_id=user.id, problem_id=problem.id)
    session.add(discussion)
    session.commit()

    retrieved_discussion = session.query(Discussion).filter_by(user_id=user.id, problem_id=problem.id).first()
    assert retrieved_discussion is not None
    assert retrieved_discussion.content == "This is a test discussion."