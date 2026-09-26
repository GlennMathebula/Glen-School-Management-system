from collections import OrderedDict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
)

from app.models.payfast import (
    PayFastStartRequest,
)
from app.services.payfast_service import (
    process_verified_itn,
    start_payfast_payment,
    verify_itn_signature,
    verify_payfast_server,
    verify_payfast_source,
)
from app.student_auth_dependency import (
    require_full_student_access,
)

router = APIRouter(
    tags=[
        "PayFast"
    ]
)


# ============================================================
# START PAYMENT
# ============================================================

@router.post(
    "/api/student/finance/payfast/start"
)
def start_payment(
    payload: PayFastStartRequest,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        result = (
            start_payfast_payment(
                student_number=(
                    student_number
                ),
                requested_amount=(
                    payload.amount
                ),
            )
        )

        return {
            "success": True,
            "data": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR starting PayFast payment:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to start PayFast payment."
            ),
        )


# ============================================================
# RETURN
# ============================================================

@router.get(
    "/api/payments/payfast/return",
    response_class=HTMLResponse,
)
def payfast_return():

    return """
    <html>
        <head>
            <title>Payment Processing</title>
        </head>
        <body style="
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 60px;
        ">
            <h2>Payment submitted</h2>
            <p>
                Your payment is being verified.
            </p>
            <p>
                You may return to the Glen Moniques
                Student Portal and refresh your finance page.
            </p>
        </body>
    </html>
    """


# ============================================================
# CANCEL
# ============================================================

@router.get(
    "/api/payments/payfast/cancel",
    response_class=HTMLResponse,
)
def payfast_cancel():

    return """
    <html>
        <head>
            <title>Payment Cancelled</title>
        </head>
        <body style="
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 60px;
        ">
            <h2>Payment cancelled</h2>
            <p>
                No payment has been recorded.
            </p>
            <p>
                You can return to the Student Portal
                and try again later.
            </p>
        </body>
    </html>
    """


# ============================================================
# ITN NOTIFICATION
# ============================================================

@router.post(
    "/api/payments/payfast/notify",
    response_class=PlainTextResponse,
)
async def payfast_notify(
    request: Request,
):

    try:

        form = await request.form()

        form_data = OrderedDict()

        for key, value in form.multi_items():

            form_data[
                key
            ] = str(
                value
            )

        signature_verified = (
            verify_itn_signature(
                form_data
            )
        )

        client_ip = (
            request.client.host
            if request.client
            else None
        )

        source_verified = (
            verify_payfast_source(
                client_ip
            )
        )

        server_verified = (
            await verify_payfast_server(
                form_data
            )
        )

        result = (
            process_verified_itn(
                form_data=(
                    form_data
                ),
                signature_verified=(
                    signature_verified
                ),
                source_verified=(
                    source_verified
                ),
                server_verified=(
                    server_verified
                ),
            )
        )

        if not result[
            "completed"
        ]:

            print(
                "PayFast ITN rejected:",
                result,
            )

        return PlainTextResponse(
            content="OK",
            status_code=200,
        )

    except Exception as error:

        print(
            "ERROR processing PayFast ITN:",
            error,
        )

        return PlainTextResponse(
            content="ERROR",
            status_code=400,
        )