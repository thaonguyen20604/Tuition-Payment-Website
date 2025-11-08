from fastapi import HTTPException, status
from . import repo
from .schemas import TuitionInvoicePublic, InvoiceItemPublic
from .utils import calc_total_amount

# USER_SVC = "http://localhost:8002/user"

def get_invoice_with_items(student_id: str, semester_id: str = None) -> TuitionInvoicePublic:
    # 1. Lấy hóa đơn
    invoice = repo.get_invoice_by_student(student_id, semester_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    # 2. Lấy items theo invoice_id
    items = repo.get_items_by_invoice(invoice["id"])
    invoice["invoice_items"] = [InvoiceItemPublic(**it) for it in items]
    
    # 3. Tính tổng tiền
    total = calc_total_amount(items)
    invoice["total_amount"] = total

    print("DEBUG invoice data:", invoice)

    return TuitionInvoicePublic(**invoice)


def pay_invoice(invoice_id: str) -> TuitionInvoicePublic:
    # 1. Đánh dấu hóa đơn đã thanh toán
    updated_invoice = repo.mark_invoice_as_paid(invoice_id)
    if not updated_invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found or not updated")
    
    # 2. Lấy items để trả về kèm hóa đơn
    items = repo.get_items_by_invoice(invoice_id)
    updated_invoice["invoice_items"] = [InvoiceItemPublic(**it) for it in items]

    return TuitionInvoicePublic(**updated_invoice)


def list_semesters():
    return repo.get_all_semesters()

def get_my_invoice(student_id: str, semester_id: str = None) -> TuitionInvoicePublic:
    # Nếu FE không truyền semester_id → tự động lấy kỳ hiện tại
    if semester_id is None:
        current = repo.get_current_semester()
        if not current:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current semester found"
            )
        semester_id = current["semester_id"]

    return get_invoice_with_items(student_id, semester_id)

def get_other_invoice(student_id: str) -> TuitionInvoicePublic:
    current = repo.get_current_semester()
    if not current:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current semester found"
        )
    return get_invoice_with_items(student_id, current["semester_id"])

# def get_other_invoice(username: str) -> TuitionInvoicePublic:
#     # gọi user-service để tìm user theo username
#     try:
#         res = requests.get(f"{USER_SVC}/find-by-username/{username}", timeout=5)
#         if res.status_code != 200:
#             raise HTTPException(status_code=404, detail="Student not found")
#         user = res.json()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"User lookup failed: {e}")

#     user_id = user["id"]  # uuid

#     current = repo.get_current_semester()
#     if not current:
#         raise HTTPException(
#             status_code=404,
#             detail="No current semester found"
#         )

#     return get_invoice_with_items(user_id, current["semester_id"])