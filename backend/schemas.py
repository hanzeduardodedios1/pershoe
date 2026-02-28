from pydantic import BaseModel

# Takes Flutter user input into a JSON, to prevent bad requests
class ShoeCreate(BaseModel):
    upc: str
    name: str
    size: str
    condition: str
    purchase_price: float
