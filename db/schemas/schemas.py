from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    senha: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    senha: str

    class Config:
        from_attributes = True

class LoginUser(BaseModel):
    email: str
    senha: str
    
    class Config:
        from_attributes: True