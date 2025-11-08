from fastapi import APIRouter, HTTPException, Depends, Query
from .schemas import TuitionInvoicePublic, SemesterPublic
from .service import (
    get_my_invoice as get_my_invoice_service,
    pay_invoice,
    list_semesters,
    get_other_invoice,
)
from .utils import get_current_user



router = APIRouter(prefix="/studentfee", tags=["studentfee"])


# Lấy chi tiết hóa đơn (của chính sinh viên đang login)
# @router.get("/my-invoice", response_model=TuitionInvoicePublic)
# def get_my_invoice(claims: dict = Depends(get_current_user)):
#     student_id = claims.get("sub")
#     invoice = get_invoice_with_items(student_id)
#     if not invoice:
#         raise HTTPException(status_code=404, detail="Invoice not found")
#     return invoice


# Lấy chi tiết hóa đơn (của chính sinh viên đang login)
@router.get("/my-invoice", response_model=TuitionInvoicePublic)
def get_my_invoice(
    semester_id: str | None = Query(None),
    claims: dict = Depends(get_current_user)
):
    student_id = claims["sub"]
    invoice = get_my_invoice_service(student_id, semester_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

# Lấy chi tiết hóa đơn của người khác (chỉ học kỳ hiện tại)
# @router.get("/invoice/{student_id}", response_model=TuitionInvoicePublic)
# def get_invoice_for_other(student_id: str):
#     invoice = get_other_invoice(student_id)
#     if not invoice:
#         raise HTTPException(status_code=404, detail="Invoice not found")
#     return invoice
@router.get("/invoice/{username}", response_model=TuitionInvoicePublic)
def get_invoice_for_other(username: str):
    invoice = get_other_invoice(username)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


# Thanh toán hóa đơn (đánh dấu đã trả)
@router.post("/pay/{invoice_id}", response_model=TuitionInvoicePublic)
def pay_my_invoice(invoice_id: str, claims: dict = Depends(get_current_user)):
    invoice = pay_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


# Lấy danh sách học kỳ
@router.get("/semesters", response_model=list[SemesterPublic])
def get_semesters(claims: dict = Depends(get_current_user)):
    semesters = list_semesters()
    if not semesters:
        raise HTTPException(status_code=404, detail="No semesters found")
    return semesters

