from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
import schemas # import schemas.py
from fastapi.middleware.cors import CORSMiddleware

# --- UPDATED DATABASE IMPORTS ---
from database import engine, get_db
import models  # Import entire models.py
from sqlalchemy.orm import Session

# Connects to Firebase project
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Initialize FastAPI
app = FastAPI()
security = HTTPBearer()

models.Base.metadata.create_all(bind=engine)

# CORSMiddleware, enables our backend to connect to chrome
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The Security Lock (Dependency)
# This function intercepts the request, grabs the token, and asks Firebase if it's valid.
def verify_firebase_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    token = creds.credentials
    try:
        # Firebase checks if the token is real and hasn't expired
        decoded_token = auth.verify_id_token(token)
        return decoded_token # This contains the user's uid, email, etc.
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Public Route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Sneaker API. Server is running."}

# A Protected Route (Login REQUIRED)
# (verify_firebase_token)` - only runs if the token is valid
@app.get("/api/inventory")
def get_user_inventory(user_data: dict = Depends(verify_firebase_token)):
    # Extract the unique Firebase User ID
    user_uid = user_data.get("uid")
    
    # UID will be useed for database authentication
    return {
        "message": "Authentication successful!",
        "user_id": user_uid,
        "data": "This is where the user's shoes will go."
    }

@app.post("/api/inventory/add")
def add_shoe(
    shoe: schemas.ShoeCreate, 
    db: Session = Depends(get_db), 
    user_data: dict = Depends(verify_firebase_token)
):
    user_uid = user_data.get("uid")
    user_email = user_data.get("email")
    
    # 1. Look for the user by UID
    db_user = db.query(models.User).filter(models.User.firebase_uid == user_uid).first()
    
    # 2. If not found by UID, check if the email exists to avoid collisions
    if not db_user:
        db_user = db.query(models.User).filter(models.User.email == user_email).first()
        
        if db_user:
            # If found by email but not UID, update UID
            db_user.firebase_uid = user_uid
            db.commit()
        else:
            # If they do not exist, create the user
            db_user = models.User(
                firebase_uid=user_uid, 
                email=user_email
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

    # 3. Add shoe
    new_shoe = models.InventoryItem(
        upc=shoe.upc,
        name=shoe.name,
        size=shoe.size,
        condition=shoe.condition,
        purchase_price=shoe.purchase_price,
        owner_id=db_user.id
    )
    
    db.add(new_shoe)
    db.commit()
    
    return {"message": f"Successfully added {new_shoe.name} to inventory!"}

# --- TEMPORARY TESTING OVERRIDE ---
# We will delete this once Flutter is connected!
#def mock_firebase_token():
    # This fakes a successful Firebase login
#    return {"uid": "fake_test_user_123", "email": "reseller@test.com"}

# This tells FastAPI: "Whenever a route asks for verify_firebase_token, use my mock function instead."
#app.dependency_overrides[verify_firebase_token] = mock_firebase_token