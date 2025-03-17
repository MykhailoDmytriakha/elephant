from pydantic import BaseModel
from typing import List, Dict

class Metric(BaseModel):
    metric_name: str
    metric_value: str

class ValidationItem(BaseModel):
    item: str
    criteria: str
    
class IFR(BaseModel):
    success_criteria: List[str]
    expected_outcomes: List[str]
    quality_metrics: List[Metric]
    validation_checklist: List[ValidationItem]
    ideal_final_result: str