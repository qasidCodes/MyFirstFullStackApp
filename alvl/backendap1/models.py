from sqlalchemy import  Boolean,Column,Integer,String, Text, DateTime 
from database import base 
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

class StudentInfo(base):
    __tablename__ = "studentInfo"

    studentID = Column(Integer, primary_key=True,index = True)
    name = Column(String(100))
    email = Column(String(100))
    password = Column(String(100))

    educations = relationship("StudentEducation", back_populates="student")
    experiences = relationship("WorkExperience", back_populates="student")
    swipe_actions = relationship("SwipeAction", back_populates="student")  # Add this line


class StudentEducation(base):
    __tablename__ = "studentEducation"

    educationID = Column(Integer, primary_key=True, index=True)
    studentID = Column(Integer, ForeignKey("studentInfo.studentID"))
    qualificationName = Column(String(100))
    qualificationLevel = Column(String(100))
    grade = Column(String(10))
    institution = Column(String(100))

    student = relationship("StudentInfo", back_populates="educations")


class WorkExperience(base):
    __tablename__ = "workExperience"

    experienceID = Column(Integer, primary_key=True, index=True)
    studentID = Column(Integer, ForeignKey("studentInfo.studentID"))
    workplace = Column(String(100))
    jobRole = Column(String(100))
    description = Column(Text)

    student = relationship("StudentInfo", back_populates="experiences")



class Apprenticeship(base):
    __tablename__ = "apprenticeship"

    apprenticeshipID = Column(Integer, primary_key=True, index=True)
    companyName = Column(String(100))
    companyEmail = Column(String(100))
    companyPassword = Column(String(100))

    listings = relationship("ApprenticeshipListing", back_populates="apprenticeship")  # Add this line


class ApprenticeshipListing(base):
    __tablename__ = "apprenticeshipListing"

    listingID = Column(Integer, primary_key=True, index=True)
    apprenticeshipID = Column(Integer, ForeignKey("apprenticeship.apprenticeshipID"))
    jobTitle = Column(String(100))
    jobDescription = Column(Text)
    salary = Column(String(50))
    entryRequirements = Column(Text)
    closingDate = Column(String(50))

    apprenticeship = relationship("Apprenticeship", back_populates="listings")  # Add this line
    swipe_actions = relationship("SwipeAction", back_populates="apprenticeship_listing")  # Add this line


class SwipeAction(base):
    __tablename__ = "swipe_actions"

    SwipeID = Column(Integer, primary_key=True, index=True)
    studentID = Column(Integer, ForeignKey("studentInfo.studentID"))
    ApprenticeshipListingID = Column(Integer, ForeignKey("apprenticeshipListing.listingID"))  # Update this line
    swipe_action = Column(Boolean)

    student = relationship("StudentInfo", back_populates="swipe_actions")  # Update this line
    apprenticeship_listing = relationship("ApprenticeshipListing", back_populates="swipe_actions")  # Update this line


class StudentSession(base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    sessionID = Column(String(100))
    user_id = Column(Integer, ForeignKey("studentInfo.studentID"))
    expireTime = Column(Integer())


class ApprenticeshipSession(base):
    __tablename__ = "apprenticeship_sessions"

    id = Column(Integer, primary_key=True, index=True)
    sessionID = Column(String(100))
    apprenticeship_id = Column(Integer, ForeignKey("apprenticeship.apprenticeshipID"))
    expireTime = Column(Integer())