from pydantic import BaseModel

class EnvVarsResponse(BaseModel):
    name: str
    value: str