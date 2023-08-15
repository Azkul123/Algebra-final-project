from sqlalchemy import create_engine,Column,String,Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = create_engine("sqlite:///images_and_data/user_info.db", echo=True)
Base.metadata.create_all(bind=engine)

Session = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "user_info"
    
    user_id = Column("id",Integer,primary_key=True)
    email = Column("email", String)
    username = Column("username", String)
    password = Column("password", Integer)

    def __init__(self,email,username,password):
        self.email = email
        self.username = username
        self.password = password


def create_user(email,username,password):
    '''
    Creates a new object in Database.db
    '''
    session = Session()
    user = User(email,username,password)
    session.add(user)
    session.commit()
    session.close()


def edit_user(email,username,new_pass):
    '''
    Edits an object based on its email in the database
    '''
    session = Session()
    person = session.query(User).filter_by(email=email).first()
    person.email = email
    person.username = username
    person.password = new_pass
    session.commit()
    session.close()


def delete_user(email):
    '''
    Deletes an object from the sql database: Database.db and updates the primary keys to be in the correct order
    '''
    session = Session()
    person = session.query(User).filter_by(email=email).first()
    del_user_id = person.user_id
    session.delete(person)
    session.commit()
    rows_to_update = session.query(User).filter(User.user_id > del_user_id).all()
    for row in rows_to_update:
        row.user_id -= 1
    session.commit()
    session.close()


def get_data():
    '''
    Gets the data about an object in Database.db
    '''
    session = Session()
    email = []
    username = []
    password = []
    
    num_of_ids = session.query(User).count()
    for i in range(1,num_of_ids+1):
        user = session.query(User).filter_by(user_id=i).first()
        email.append(user.email)
        username.append(user.username)
        password.append(user.password)
    session.close()
    return email, username, password