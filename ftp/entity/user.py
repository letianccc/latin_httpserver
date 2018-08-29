from sqlalchemy import Column, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool


Base = declarative_base()

class User(Base):
    # 表的名字:
    __tablename__ = 'user'

    # 表的结构:
    id = Column(String(20), primary_key=True)
    name = Column(String(20))
    password = Column(String(20))


engine = create_engine('sqlite:///:test:', poolclass=StaticPool,
    connect_args={'check_same_thread':False})
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
new_user = User(id='1', name='latin', password='123')
session.add(new_user)
session.commit()
