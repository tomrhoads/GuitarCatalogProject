from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import GuitarShop, Base, GuitarItem, User

engine = create_engine('sqlite:///guitarselection.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
user1 = User(name="Tom Rhoads", email="terhoads1@gmail.com",
             picture='https://plus.google.com/u/0/photos/118294337716288502457/albums/profile/5722580177746756274')
session.add(user1)
session.commit()

# Items in Guitar Center
guitarshop1 = GuitarShop(user_id=1, name="Guitar Center")

session.add(guitarshop1)
session.commit()

guitarItem2 = GuitarItem(user_id=1, name="Taylor T5", description="Acoustic",
                         price="$2998", guitarshop=guitarshop1)

session.add(guitarItem2)
session.commit()
