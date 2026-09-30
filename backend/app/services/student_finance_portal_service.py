from sqlalchemy import text
from app.database import engine

def get_student_finance_summary(student_number: str) -> dict:
    student_number=student_number.strip().upper()
    with engine.connect() as c:
        a=c.execute(text("""SELECT fa.id,fa.registration_id,fa.tuition_fee,fa.other_fees,fa.funding_type,fa.account_status,fa.created_at,fa.updated_at FROM public.finance_accounts fa JOIN public.registrations r ON r.id=fa.registration_id WHERE r.student_number=:student_number LIMIT 1"""),{"student_number":student_number}).mappings().first()
        if not a:return {"student_number":student_number,"account":None,"summary":{"total_charges":0.0,"payments_total":0.0,"outstanding_balance":0.0},"invoices":[],"payments":[],"payment_plans":[]}
        a=dict(a);aid=a["id"]
        inv=c.execute(text("""SELECT invoice_number,invoice_date,due_date,subtotal,discount_amount,total_amount,status,charge_type,description FROM public.finance_invoices WHERE finance_account_id=:id ORDER BY invoice_date DESC,created_at DESC"""),{"id":aid}).mappings().all()
        pay=c.execute(text("""SELECT p.id,p.payment_reference,p.payment_date,p.amount,p.payment_method,p.external_reference,p.status,p.is_reversed,r.receipt_number FROM public.finance_payments p LEFT JOIN public.finance_receipts r ON r.payment_id=p.id WHERE p.finance_account_id=:id ORDER BY p.payment_date DESC,p.created_at DESC"""),{"id":aid}).mappings().all()
        plans=c.execute(text("""SELECT id,plan_name,start_date,end_date,total_plan_amount,status,notes FROM public.finance_payment_plans WHERE finance_account_id=:id ORDER BY created_at DESC"""),{"id":aid}).mappings().all()
    tuition=float(a.get("tuition_fee") or 0);other=float(a.get("other_fees") or 0);payments=[dict(x) for x in pay];paid=sum(float(x.get("amount") or 0) for x in payments if str(x.get("status") or "").lower() in {"completed","paid","successful","success"} and not bool(x.get("is_reversed")));total=tuition+other
    return {"student_number":student_number,"account":{**a,"tuition_fee":tuition,"other_fees":other},"summary":{"total_charges":round(total,2),"payments_total":round(paid,2),"outstanding_balance":round(total-paid,2)},"invoices":[dict(x) for x in inv],"payments":payments,"payment_plans":[dict(x) for x in plans]}
