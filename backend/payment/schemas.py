from pydantic import BaseModel, Field
from typing import Optional

class CreateIntentBody(BaseModel):
    student_id: Optional[str] = None      # MSSV nếu nộp hộ
    semester_id: Optional[str] = None     # lọc my-invoice (nếu nộp cho mình)

class SendOtpResp(BaseModel):
    intent_id: str
    otp_sent: bool = True

class ConfirmBody(BaseModel):
    otp: str = Field(pattern=r"^\d{6}$")

class IntentPublic(BaseModel):
    id: str
    payer_user_id: str
    payer_email: str
    student_id: str
    invoice_id: str
    amount: float
    status: str

class PaymentPublic(BaseModel):
    id: str
    intent_id: str
    paid_at: str
    amount: float
    payer_balance_before: float
    payer_balance_after: float

class ConfirmResp(BaseModel):
    intent: IntentPublic
    payment: PaymentPublic
