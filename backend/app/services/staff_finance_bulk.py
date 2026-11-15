"""Safe bulk finance operations for Glen Moniques SMS.

No schema changes. Requires existing public.student_accounts, sponsors,
student_sponsor_allocations, payments and invoices tables.
"""
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import text
from app.database import engine
from app.services.staff_finance_service import recalculate_student_account
from app.services.staff_audit_service import create_staff_audit_log


def money(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _audit(actor, action, entity_id, description, metadata):
    try:
        create_staff_audit_log(
            actor_staff_code=actor,
            action_code=action,
            module_code='FINANCE',
            entity_type='FINANCE',
            entity_id=str(entity_id),
            description=description,
            metadata=metadata,
        )
    except Exception as exc:
        # Core writes were committed, so audit failure must not be presented as a failed allocation.
        print(f'WARNING finance audit failed: {exc}')



def _modern_ledger(connection, student_number, lock=False):
    """Use registered finance accounts as contractual charges, not invoice totals.

    Invoice status is document status; cancelling a document does not waive fees.
    All money is calculated using Decimal and payments net of reversals.
    """
    sql = '''
        SELECT fa.id, fa.tuition_fee, fa.other_fees
        FROM public.finance_accounts fa
        JOIN public.registrations r ON r.id = fa.registration_id
        WHERE r.student_number = :student_number
          AND fa.account_status = 'Active'
        ORDER BY fa.id
    ''' + (' FOR UPDATE OF fa' if lock else '')
    accounts = connection.execute(text(sql), {'student_number': student_number}).mappings().all()
    if not accounts:
        return None
    account_ids = [a['id'] for a in accounts]
    # Bound PostgreSQL UUID array; no interpolation of user-provided IDs.
    paid = money(connection.execute(text('''
        SELECT COALESCE(SUM(amount), 0)
        FROM public.finance_payments
        WHERE finance_account_id = ANY(:account_ids)
          AND status = 'Completed' AND is_reversed = FALSE
    '''), {'account_ids': account_ids}).scalar_one())
    charges = sum((money(a['tuition_fee']) + money(a['other_fees']) for a in accounts), Decimal('0.00'))
    return {'charges': charges, 'payments': paid, 'account_count': len(accounts)}


def _student_due(connection, number, *, lock=False):
    """Return effective outstanding amount; modern finance takes precedence."""
    account_sql = '''
        SELECT student_number, registration_fee, tuition_fee, other_charges, credits
        FROM public.student_accounts
        WHERE student_number = :student_number
    ''' + (' FOR UPDATE' if lock else '')
    legacy = connection.execute(text(account_sql), {'student_number': number}).mappings().first()
    if not legacy:
        raise ValueError(f'Learner {number} has no student account. Complete registration first.')
    modern = _modern_ledger(connection, number, lock=lock)
    sponsored = money(connection.execute(text('''
        SELECT COALESCE(SUM(amount_covered), 0)
        FROM public.student_sponsor_allocations
        WHERE student_number = :student_number
    '''), {'student_number': number}).scalar_one())
    if modern:
        # The modern ledger is authoritative for this student; avoid double-counting legacy charges/payments.
        due = max(Decimal('0.00'), modern['charges'] - modern['payments'] - sponsored)
        return {'due': due, 'source': 'Finance account', 'charges': modern['charges'],
                'payments': modern['payments'], 'sponsored': sponsored, 'accounts': modern['account_count']}
    payments = money(connection.execute(text('''
        SELECT COALESCE(SUM(amount), 0) FROM public.payments
        WHERE student_number = :student_number AND status = 'Completed'
    '''), {'student_number': number}).scalar_one())
    charges = money(legacy['registration_fee']) + money(legacy['tuition_fee']) + money(legacy['other_charges'])
    credits = money(legacy['credits'])
    due = max(Decimal('0.00'), charges - credits - payments - sponsored)
    return {'due': due, 'source': 'Legacy account', 'charges': charges - credits,
            'payments': payments, 'sponsored': sponsored, 'accounts': 0}


def list_sponsor_candidates(*, search=None, limit=500):
    """Search eligible learners, showing the same due calculation used for allocation."""
    from app.services.staff_finance_service import search_finance_students
    rows = search_finance_students(search=search, limit=min(max(int(limit), 1), 500))
    results = []
    with engine.connect() as connection:
        for row in rows:
            item = dict(row)
            try:
                snapshot = _student_due(connection, str(row['student_number']))
                item['effective_due'] = str(snapshot['due'])
                item['balance_source'] = snapshot['source']
                item['charges_total'] = str(snapshot['charges'])
                item['payments_net'] = str(snapshot['payments'])
                item['sponsorship_total'] = str(snapshot['sponsored'])
                item['finance_account_count'] = snapshot['accounts']
            except ValueError as exc:
                item['effective_due'] = '0.00'
                item['balance_source'] = 'Unavailable'
                item['balance_error'] = str(exc)
            results.append(item)
    return results

def bulk_assign_sponsor(*, actor_staff_code, sponsor_id, allocations, reference=None):
    """Atomic, all-or-nothing allocation; each amount must fit student balance."""
    if not allocations or len(allocations) > 500:
        raise ValueError('Select between 1 and 500 learners.')
    normalized = []
    for entry in allocations:
        number = str(entry.student_number).strip()
        amt = money(entry.amount_covered)
        if not number or amt <= 0:
            raise ValueError('Each learner needs a student number and a positive amount.')
        normalized.append((number, amt))
    if len({n for n, _ in normalized}) != len(normalized):
        raise ValueError('Duplicate learner in selection.')
    normalized.sort(key=lambda x: x[0])  # consistent student locking order
    total = sum((a for _, a in normalized), Decimal('0.00'))
    sponsor_token = str(sponsor_id).strip()
    with engine.begin() as connection:
        sponsor = connection.execute(text('''
            SELECT sponsor_id, sponsor_name, remaining_amount FROM public.sponsors
            WHERE (sponsor_id = :token OR id::text = :token)
              AND status = 'Active' FOR UPDATE
        '''), {'token': sponsor_token}).mappings().first()
        if not sponsor:
            raise ValueError('Active sponsor not found.')
        official = sponsor['sponsor_id']
        if total > money(sponsor['remaining_amount']):
            raise ValueError('Total exceeds available sponsor funding.')
        due_by_student = {}
        source_by_student = {}
        for number, amount in normalized:
            snapshot = _student_due(connection, number, lock=True)
            due = snapshot['due']
            if amount > due:
                raise ValueError(f'{number}: allocation R{amount} exceeds amount due R{due}.')
            due_by_student[number] = due
            source_by_student[number] = snapshot['source']
        results = []
        for number, amount in normalized:
            item = connection.execute(text('''
                INSERT INTO public.student_sponsor_allocations
                    (student_number,sponsor_id,amount_covered,reference,allocated_by)
                VALUES (:student_number,:sponsor_id,:amount,:reference,:actor)
                RETURNING id
            '''), {'student_number': number, 'sponsor_id': official,
                   'amount': amount, 'reference': reference, 'actor': actor_staff_code}).mappings().one()
            # Keep the legacy sponsor tracking fields in sync without copying
            # modern contractual charges into the separate legacy ledger.
            connection.execute(text('''
                UPDATE public.student_accounts SET
                    sponsor_amount_covered = (
                      SELECT COALESCE(SUM(amount_covered),0)
                      FROM public.student_sponsor_allocations
                      WHERE student_number=:student_number
                    ),
                    sponsor_name=:sponsor_name,
                    updated_at=now()
                WHERE student_number=:student_number
            '''), {'sponsor_name': sponsor['sponsor_name'], 'student_number': number})
            if source_by_student[number] == 'Legacy account':
                connection.execute(text('''
                    UPDATE public.student_accounts
                    SET outstanding_balance=:new_balance, updated_at=now()
                    WHERE student_number=:student_number
                '''), {'new_balance': due_by_student[number] - amount,
                            'student_number': number})
            results.append({'student_number': number, 'amount_covered': str(amount), 'allocation_id': str(item['id'])})
        connection.execute(text('''
            UPDATE public.sponsors
            SET remaining_amount = remaining_amount - :total, updated_at=now()
            WHERE sponsor_id=:sponsor_id
        '''), {'total': total, 'sponsor_id': official})
    # Account balances are updated inside the allocation transaction.
    _audit(actor_staff_code, 'BULK_SPONSOR_ASSIGNED', official,
           'Bulk funding allocated', {'learners': len(results), 'total': str(total), 'reference': reference})
    return {'sponsor_id': official, 'student_count': len(results), 'total_allocated': str(total),
            'allocations': results}


def cancel_unpaid_invoice(*, actor_staff_code, student_number, invoice_number, reason):
    """Void a legacy issued/unpaid charge; never erase a paid document."""
    if len((reason or '').strip()) < 5:
        raise ValueError('A cancellation reason of at least five characters is required.')
    with engine.begin() as connection:
        invoice = connection.execute(text('''
            SELECT * FROM public.invoices
            WHERE invoice_number=:invoice AND student_number=:student FOR UPDATE
        '''), {'invoice': invoice_number, 'student': student_number}).mappings().first()
        if not invoice:
            raise ValueError('Invoice not found for this learner.')
        if str(invoice['status']).lower() in ('cancelled', 'void', 'voided'):
            raise ValueError('Invoice is already cancelled.')
        if str(invoice['status']).lower() not in ('unpaid', 'draft', 'issued'):
            raise ValueError('Only unpaid invoices can be cancelled. Use an adjustment for paid invoices.')
        linked = connection.execute(text('''
            SELECT 1 FROM public.payments
            WHERE invoice_number=:invoice AND status='Completed' LIMIT 1
        '''), {'invoice': invoice_number}).first()
        if linked:
            raise ValueError('Invoice has a completed payment. Use a formal credit/refund workflow.')
        mapping = {'registration': 'registration_fee', 'tuition': 'tuition_fee', 'other': 'other_charges'}
        kind = str(invoice['charge_type'] or '').lower()
        if kind not in mapping:
            raise ValueError('Unsupported charge type. Manual finance review is required.')
        column = mapping[kind]
        amount = money(invoice['amount'])
        account = connection.execute(text('''
            SELECT registration_fee,tuition_fee,other_charges,credits,
                   sponsor_amount_covered, payments_total
            FROM public.student_accounts WHERE student_number=:student FOR UPDATE
        '''), {'student': student_number}).mappings().first()
        if not account or money(account[column]) < amount:
            raise ValueError('Account charge does not reconcile; cancellation stopped.')
        post_charges = (money(account['registration_fee']) + money(account['tuition_fee'])
                        + money(account['other_charges']) - amount)
        if post_charges - money(account['credits']) < money(account['sponsor_amount_covered']) + money(account['payments_total']):
            raise ValueError('Allocated sponsor funding or payments exceed balance after cancellation. Reconcile first.')
        connection.execute(text(f'''
            UPDATE public.student_accounts SET {column}={column}-:amount, updated_at=now()
            WHERE student_number=:student
        '''), {'amount': amount, 'student': student_number})
        connection.execute(text('''
            UPDATE public.invoices SET status='Cancelled',
                description=description || :reason_suffix, updated_at=now()
            WHERE invoice_number=:invoice
        '''), {'reason_suffix': '\nCANCELLED: ' + reason.strip(), 'invoice': invoice_number})
    recalculate_student_account(student_number=student_number)
    _audit(actor_staff_code, 'INVOICE_CANCELLED', invoice_number,
           'Unpaid invoice cancelled', {'student_number': student_number, 'reason': reason, 'amount': str(amount)})
    return {'invoice_number': invoice_number, 'status': 'Cancelled', 'amount_removed': str(amount)}


# Modern invoices live in finance_invoices and are tied to finance_accounts/registrations.
# They must NOT be treated as legacy invoices or deducted from student_accounts.
def list_modern_student_invoices(*, student_number):
    student_number = str(student_number or '').strip()
    if not student_number:
        raise ValueError('Student number is required.')
    with engine.connect() as connection:
        rows = connection.execute(text('''
            SELECT fi.invoice_number, fi.status, fi.total_amount, fi.invoice_date,
                   fi.due_date, fi.charge_type, fi.description, fi.notes,
                   fi.id AS invoice_id
            FROM public.finance_invoices fi
            JOIN public.finance_accounts fa ON fa.id = fi.finance_account_id
            JOIN public.registrations r ON r.id = fa.registration_id
            WHERE r.student_number = :student_number
            ORDER BY fi.invoice_date DESC, fi.created_at DESC
        '''), {'student_number': student_number}).mappings().all()
    return [dict(row) for row in rows]


def cancel_modern_unpaid_invoice(*, actor_staff_code, student_number, invoice_number, reason):
    '''Void a modern invoice only if there is no financial payment on its account.

    A payment may be unapplied to an invoice; reject any completed account payment
    until reconciliation is explicitly designed. Keep nominal tuition untouched.
    '''
    reason = str(reason or '').strip()
    if len(reason) < 5:
        raise ValueError('A cancellation reason of at least five characters is required.')
    student_number = str(student_number or '').strip()
    invoice_number = str(invoice_number or '').strip()
    if not student_number or not invoice_number:
        raise ValueError('Student and invoice are required.')
    with engine.begin() as connection:
        row = connection.execute(text('''
            SELECT fi.id, fi.invoice_number, fi.status, fi.total_amount,
                   fi.finance_account_id, fi.notes
            FROM public.finance_invoices fi
            JOIN public.finance_accounts fa ON fa.id = fi.finance_account_id
            JOIN public.registrations r ON r.id = fa.registration_id
            WHERE r.student_number = :student_number
              AND fi.invoice_number = :invoice_number
            FOR UPDATE OF fi
        '''), {'student_number': student_number, 'invoice_number': invoice_number}).mappings().first()
        if row is None:
            raise ValueError('Invoice not found for this learner.')
        if row['status'] == 'Cancelled':
            raise ValueError('This invoice is already cancelled.')
        if row['status'] not in ('Draft', 'Issued'):
            raise ValueError('Only unpaid Draft or Issued invoices can be cancelled.')
        # Prevent cancellation against a paid account even if invoice_id is NULL.
        payment_found = connection.execute(text('''
            SELECT 1 FROM public.finance_payments
            WHERE finance_account_id = :account_id
              AND status = 'Completed'
              AND is_reversed = FALSE
            LIMIT 1
        '''), {'account_id': row['finance_account_id']}).first()
        if payment_found:
            raise ValueError('This finance account has completed payments. Reconcile payments before cancelling invoices.')
        # Preserve original details and reason in notes, never delete the invoice or line items.
        cancellation_note = 'CANCELLED by ' + str(actor_staff_code) + ': ' + reason
        notes = ((row['notes'] or '').rstrip() + '\n' + cancellation_note).strip()
        result = connection.execute(text('''
            UPDATE public.finance_invoices SET status = 'Cancelled',
                notes = :notes, updated_at = NOW()
            WHERE id = :invoice_id AND status IN ('Draft','Issued')
            RETURNING invoice_number,status,total_amount
        '''), {'notes': notes, 'invoice_id': row['id']}).mappings().one()
    _audit(actor_staff_code, 'MODERN_INVOICE_CANCELLED', invoice_number,
           'Modern unpaid invoice cancelled', {'student_number': student_number,
           'reason': reason, 'amount': str(result['total_amount'])})
    return {'invoice_number': result['invoice_number'], 'status': result['status'],
            'total_amount': str(result['total_amount']),
            'note': 'Invoice cancelled; finance account tuition fee was not modified.'}
