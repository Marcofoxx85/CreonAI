# init_db.py

"""
Run this script once to initialize the database schema.
Usage:
    $ python init_db.py
"""

from database import Base, engine
from models import User, Asset, Subscription, CreditTransaction, ActivityLog

# Create all tables
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully.")
