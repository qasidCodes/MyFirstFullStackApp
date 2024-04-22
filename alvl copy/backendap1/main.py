from fastapi import FastAPI, HTTPException, Depends, status,Response, Request, File, UploadFile
from pydantic import BaseModel
import models
from database import engine, sessionLocal
from sqlalchemy.orm import Session,joinedload
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Annotated
from passlib.context import CryptContext
import jwt
from uuid import uuid4
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_ 

models.base.metadata.create_all(bind = engine)


app = FastAPI()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)




class SwipeAction(BaseModel):
    studentID: int
    listingID: int
    direction: str

class SessionBase(BaseModel):
    id: int
    sessionID: str
    user_id: int
    expireTime: int
    
    class Config:
        arbitrary_types_allowed = True


class LoginBase(BaseModel):
    username: str
    password: str


class StudentInfoBase(BaseModel):
    studentID: int
    name: str
    email: str
    password: str




class StudentEducationBase(BaseModel):
    studentID: int
    qualificationName: str
    qualificationLevel: str
    grade: str
    institution: str



class WorkExperienceBase(BaseModel):
    studentID: int
    workplace: str
    jobRole: str
    description: str


class ApprenticeshipBase(BaseModel):
    apprenticeshipID: Optional[int] = None
    companyName: str
    companyEmail: str
    companyPassword: str

class ApprenticeshipListingBase(BaseModel):
    listingID: Optional[int] = None
    apprenticeshipID: int
    jobTitle: str
    jobDescription: str
    salary: str
    entryRequirements: str
    closingDate: str


class ApprenticeshipListing2Base(BaseModel):
    apprenticeshipID: int
    jobTitle: str
    jobDescription: str
    salary: str
    entryRequirements: str
    closingDate: str




def get_db():
    db = sessionLocal()
    try:
        yield db
    finally:
        db.close()














@app.post("/users/")
def create_user(student: StudentInfoBase, db: Session = Depends(get_db)):
    existing_student = db.query(models.StudentInfo).filter(models.StudentInfo.email == student.email).first()
    if existing_student is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_student = models.StudentInfo(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return {"message": "User created successfully"}



@app.get("/users/check_email/{email}")
def check_email(email: str, db: Session = Depends(get_db)):
    db_student = db.query(models.StudentInfo).filter(models.StudentInfo.email == email).first()
    if db_student:
        return {"exists": True}
    else:
        return {"exists": False}
    

@app.post("/studentLogin/")
async def login( response: Response,form_data: LoginBase = Depends, db: Session = Depends(get_db)):
    # Check in StudentInfo table
    user = db.query(models.StudentInfo).filter(models.StudentInfo.email == form_data.username).first()
    
    # If not found in StudentInfo, check in Apprenticeship table
  
    # If user not found in both tables or password doesn't match, raise exception
    if not user or (hasattr(user, 'password') and user.password != form_data.password) or (hasattr(user, 'companyPassword') and user.companyPassword != form_data.password):
        return{"message":"Login Failed"}
    if user:
        db_session = models.StudentSession(user_id=user.studentID, sessionID=str(uuid4()), expireTime = 1440)       
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        response.set_cookie(key="mysession", value = db_session.sessionID)


    return {"message": "Logged in successfully","sessionId": db_session.sessionID}




@app.get("/check_session/{session_id}")
def check_session(session_id: str, request: Request, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get("mysession")
    if session_cookie:
        # The cookie is there, you can now check the session
        db_session = db.query(models.StudentSession).filter(models.StudentSession.sessionID == session_cookie).first()
        if db_session:
            return {"exists": True,"user_id":db_session.user_id}
    return {"exists": False}


@app.get("/studentLogout/{session_id}")
def logout(session_id: str, request: Request, db: Session = Depends(get_db)):
        # The cookie is there, you can now remove the session
    db_session = db.query(models.StudentSession).filter(models.StudentSession.sessionID == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
        return {"response":"LogOut"} 
    return {"response":"noLogOut"}







@app.get("/listings")
def get_listings(db: Session = Depends(get_db)):
    listings = db.query(models.ApprenticeshipListing).all()
    return listings


@app.get("/student/{user_id}")
def get_student(user_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentInfo).filter(models.StudentInfo.studentID == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    educations = db.query(models.StudentEducation).filter(models.StudentEducation.studentID == student.studentID).all()
    experiences = db.query(models.WorkExperience).filter(models.WorkExperience.studentID == student.studentID).all()
    return {"student": student, "educations": educations, "experiences": experiences}

@app.post("/swipe")
def swipe_action(swipe: SwipeAction, db: Session = Depends(get_db)):
    apprenticeship = db.query(models.Apprenticeship).filter(models.Apprenticeship.apprenticeshipID == swipe.listingID).first()
    if not apprenticeship:
        raise HTTPException(status_code=404, detail="Apprenticeship not found")

    # Create a new SwipeAction record
    db_swipe = models.SwipeAction(ApprenticeshipListingID=swipe.listingID, swipe_action=(swipe.direction == 'right'),studentID = swipe.studentID)
    db.add(db_swipe)
    db.commit()
    db.refresh(db_swipe)

    return {"message": f"Swipe action recorded for listing ID {swipe.listingID}"}






@app.post("/studentEducation")
async def create_student_education(education: List[StudentEducationBase], db: Session = Depends(get_db)):
    for education_data in education:
        db_education = models.StudentEducation(**education_data.dict())
        db.add(db_education)
        db.commit()
        db.refresh(db_education)
    return {"message": "Education data saved successfully"}

@app.post("/workExperience")
async def create_work_experience(experience: List[WorkExperienceBase], db: Session = Depends(get_db)):
    for experience_data in experience:
        db_experience = models.WorkExperience(**experience_data.dict())
        db.add(db_experience)
        db.commit()
        db.refresh(db_experience)
    return {"message": "Work experience data saved successfully"}


@app.get("/studentInfo/{user_id}")
def get_student_info(user_id: int, db: Session = Depends(get_db)):
    student = db.query(models.StudentInfo).filter(models.StudentInfo.studentID == user_id).first()
  
    return {"student": student}

@app.delete("/student/{user_id}/deleteOldData")
def delete_old_data(user_id: int, db: Session = Depends(get_db)):
    # Delete old education data
    db.query(models.StudentEducation).filter(models.StudentEducation.studentID == user_id).delete()

    # Delete old experience data
    db.query(models.WorkExperience).filter(models.WorkExperience.studentID == user_id).delete()

    db.commit()

    return {"message": "Old data deleted successfully"}


@app.get("/matches/{user_id}")
def get_matches(user_id: int, db: Session = Depends(get_db)):
    # Query the SwipeAction table for the listings that the user has swiped right
    swiped_right_listings = db.query(models.SwipeAction).options(joinedload(models.SwipeAction.apprenticeship_listing)).filter(and_(models.SwipeAction.studentID == user_id, models.SwipeAction.swipe_action == 1)).all()  # 1 for yes

    # Extract the apprenticeship listing from each SwipeAction and store in a dictionary
    swiped_right_apprenticeships = {action.apprenticeship_listing.listingID: action.apprenticeship_listing for action in swiped_right_listings}

    return list(swiped_right_apprenticeships.values())











@app.get("/getApprenticeships") # updated to the new endpoint
def get_apprenticeships(db: Session = Depends(get_db)):
    apprenticeships = db.query(models.ApprenticeshipListing).all()
    return apprenticeships



@app.post("/apprenticeships/")
async def create_apprenticeship(apprenticeship: ApprenticeshipBase, db: Session = Depends(get_db)):
    existing_apprenticeship = db.query(models.Apprenticeship).filter(models.Apprenticeship.companyEmail == apprenticeship.companyEmail).first()
    if existing_apprenticeship is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_apprenticeship = models.Apprenticeship(**apprenticeship.dict())
    db.add(db_apprenticeship)
    db.commit()
    db.refresh(db_apprenticeship)
    return {"message": "Apprenticeship created successfully"}








@app.get("/apprenticeships/check_email/{email}")
def check_email(email: str, db: Session = Depends(get_db)):
    db_apprenticeship = db.query(models.Apprenticeship).filter(models.Apprenticeship.companyEmail == email).first()
    if db_apprenticeship:
        return {"exists": True}
    else:
        return {"exists": False}




@app.get("/check_apprenticeship_session/{session_id}")
def check_apprenticeship_session(session_id: str, request: Request, db: Session = Depends(get_db)):
    session_cookie = request.cookies.get("mysession")
    if session_cookie:
        # The cookie is there, you can now check the session
        db_session = db.query(models.ApprenticeshipSession).filter(models.ApprenticeshipSession.sessionID == session_cookie).first()
        if db_session:
            return {"exists": True,"apprenticeship_id":db_session.apprenticeship_id}
    return {"exists": False}

@app.get("/apprenticeshipLogout/{session_id}")
def logout_apprenticeship(session_id: str, request: Request, db: Session = Depends(get_db)):
    # The cookie is there, you can now remove the session
    db_session = db.query(models.ApprenticeshipSession).filter(models.ApprenticeshipSession.sessionID == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
        return {"response":"LogOut"} 
    return {"response":"noLogOut"}




@app.post("/apprenticeshipLogin/")
async def apprenticeship_login(response: Response, form_data: LoginBase = Depends, db: Session = Depends(get_db)):
    # Check in Apprenticeship table
    user = db.query(models.Apprenticeship).filter(models.Apprenticeship.companyEmail == form_data.username).first()
    
    # If user not found or password doesn't match, raise exception
    if not user or user.companyPassword != form_data.password:
        return {"message":"Login Failed"}
    
    if user:
        db_session = models.ApprenticeshipSession(apprenticeship_id=user.apprenticeshipID, sessionID=str(uuid4()), expireTime = 1440)       
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        response.set_cookie(key="mysession", value = db_session.sessionID)

    return {"message": "Logged in successfully","sessionId": db_session.sessionID}

@app.get("/apprenticeshipInfo/{apprenticeship_id}")
def get_apprenticeship_info(apprenticeship_id: int, db: Session = Depends(get_db)):
    apprenticeship = db.query(models.Apprenticeship).filter(models.Apprenticeship.apprenticeshipID == apprenticeship_id).first()
  
    return {"apprenticeship": apprenticeship}



@app.post("/ApprenticeshipListings")
async def create_listing(listing: ApprenticeshipListing2Base, db: Session = Depends(get_db)):
    db_listing = models.ApprenticeshipListing(**listing.dict())
    db.add(db_listing)
    db.commit()
    db.refresh(db_listing)
    return db_listing




@app.get("/studentsWhoSwipedRight/{listing_id}")
async def get_students_who_swiped_right(listing_id: int, db: Session = Depends(get_db)):
    # Fetch distinct student IDs who swiped right for the given listing
    distinct_student_ids = db.query(models.SwipeAction.studentID).filter_by(ApprenticeshipListingID=listing_id, swipe_action=True).distinct().all()

    # Fetch student info for each distinct student ID
    students = [db.query(models.StudentInfo).get(student_id) for (student_id,) in distinct_student_ids]

    return students



@app.get("/getApprenticeshipListing/{apprenticeship_id}")
async def get_apprenticeship_listing(apprenticeship_id: int, db: Session = Depends(get_db)):
    # Fetch the apprenticeship with the given ID
    apprenticeship = db.query(models.Apprenticeship).get(apprenticeship_id)
    if not apprenticeship:
        raise HTTPException(status_code=404, detail="Apprenticeship not found")

    # Fetch the listings for the apprenticeship
    listings = db.query(models.ApprenticeshipListing).filter_by(apprenticeshipID=apprenticeship_id).all()

    return listings

@app.get("/studentInfo/{student_id}")
async def read_student_info(student_id: int, db: Session = Depends(get_db)):
    student_info = db.query(models.StudentInfo).filter(models.StudentInfo.studentID == student_id).first()
    return student_info

@app.get("/studentEducation/{student_id}")
async def read_student_education(student_id: int, db: Session = Depends(get_db)):
    student_education = db.query(models.StudentEducation).filter(models.StudentEducation.studentID == student_id).all()
    return student_education

@app.get("/workExperience/{student_id}")
async def read_work_experience(student_id: int, db: Session = Depends(get_db)):
    work_experience = db.query(models.WorkExperience).filter(models.WorkExperience.studentID == student_id).all()
    return work_experience