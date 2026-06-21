import sys
import os

# Ensures the script can find the 'app' package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Organization, Base

def init_organizations():
    # Create tables if they don't exist yet
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    # Strictly the roles/orgs you requested
    org_names = ["admin", "corp", "auditor", "bank"]
    
    try:
        print("--- Initializing Organizations ---")
        for name in org_names:
            # Check if it already exists to avoid duplicates
            exists = db.query(Organization).filter(Organization.name == name).first()
            if not exists:
                new_org = Organization(name=name)
                db.add(new_org)
                print(f"✅ Added: {name}")
            else:
                print(f"ℹ️ {name} already exists. Skipping.")
        
        db.commit()
        print("----------------------------------")
        print("Initialization Complete Successfully.")
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_organizations()