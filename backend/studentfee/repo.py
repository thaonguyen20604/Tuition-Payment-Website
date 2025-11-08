from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import Client
from .db import get_supabase_client

SCHEMA = "studentfee_svc"
TABLE_INVOICE = "tuition_invoice"
TABLE_ITEMS   = "invoice_items"
TABLE_SEMESTER = "semester"


def _tb(table: str):
    return get_supabase_client().schema(SCHEMA).table(table)

def get_invoice_by_student(student_id: str, \
                           semester_id: Optional[str] = None):
    
    query = _tb(TABLE_INVOICE).select("*").eq("student_id", student_id)
    if semester_id:
        query = query.eq("semester_id", semester_id)
    res = query.limit(1).execute()
    return res.data[0] if res.data else None

def get_items_by_invoice(invoice_id: str) -> List[Dict[str, Any]]:
    res = (
        _tb(TABLE_ITEMS)
        .select("*")
        .eq("invoice_id", invoice_id)
        .execute()
    )
    return res.data or []

def mark_invoice_as_paid(invoice_id: str):
    """Đánh dấu hóa đơn đã thanh toán"""
    res = (
        _tb(TABLE_INVOICE)
        .update({"status": "paid"})
        .eq("id", invoice_id)
        .execute()
    )
    return res.data[0] if res.data else None

def get_all_semesters():
    res = (
        _tb(TABLE_SEMESTER)
        .select("*")
        .execute()
    )
    return res.data or []

from datetime import date

def get_current_semester():
    today = date.today()
    res = (
        _tb(TABLE_SEMESTER)
        .select("*")
        .lte("start_date", today.isoformat())
        .gte("end_date", today.isoformat())
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None

