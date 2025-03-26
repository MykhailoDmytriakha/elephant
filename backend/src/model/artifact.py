from pydantic import BaseModel, Field

class Artifact(BaseModel):
    """
    Artifact of a checkpoint.
    """
    type: str = Field(..., description="Type of the artifact")
    name: str = Field(..., description="Name of the artifact")
    description: str = Field(..., description="Description of the artifact")
    location: str = Field(..., description="Location of the artifact") 