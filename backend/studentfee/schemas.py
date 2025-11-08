# from pydantic import BaseModel, Field
# from typing import List, Literal
# from datetime import date, datetime


# class SemesterBase(BaseModel):
#     semester_name: str
#     school_year: str
#     start_date: date
#     end_date: date

# class SemesterCreate(SemesterBase):
#     pass

# class SemesterPublic(BaseModel):
#     semester_id: str
#     semester_name: str
#     school_year: str
#     start_date: date
#     end_date: date


# class InvoiceItemBase(BaseModel):
#     subject_id: str
#     subject_name: str
#     registration_date: datetime
#     amount: float

# class InvoiceItemPublic(InvoiceItemBase):
#     invoice_items_id: str
#     invoice_id: str


# class TuitionInvoiceBase(BaseModel):
#     student_id: str
#     semester_id: str
#     # status: str 
#     status: Literal["unpaid", "paid", "processing", "failed"]

# class TuitionInvoiceCreate(BaseModel):
#     student_id: str
#     semester_id: str

# class TuitionInvoicePublic(TuitionInvoiceBase):
#     id: str
#     create_at: datetime
#     # invoice_items: List[InvoiceItemPublic] = []
#     invoice_items: List[InvoiceItemPublic] = Field(default_factory=list)
#     total_amount: float

from typing import List, Literal
from pydantic import BaseModel, Field
from datetime import date, datetime

class SemesterBase(BaseModel):
    semester_name: str
    school_year: str
    start_date: date
    end_date: date

class SemesterCreate(SemesterBase):
    pass

class SemesterPublic(BaseModel):
    semester_id: str
    semester_name: str
    school_year: str
    start_date: date
    end_date: date

class InvoiceItemBase(BaseModel):
    subject_id: str
    subject_name: str
    registration_date: datetime
    amount: float   # nhớ ép float khi build payload

class InvoiceItemPublic(InvoiceItemBase):
    invoice_items_id: str
    invoice_id: str

class TuitionInvoiceBase(BaseModel):
    student_id: str
    semester_id: str
    status: Literal["unpaid", "paid", "processing", "failed"]

class TuitionInvoiceCreate(BaseModel):
    student_id: str
    semester_id: str

class TuitionInvoicePublic(TuitionInvoiceBase):
    id: str
    create_at: datetime          # trùng tên cột DB của bạn
    invoice_items: List[InvoiceItemPublic] = Field(default_factory=list)
    total_amount: float = 0.0    # có default để không bị thiếu