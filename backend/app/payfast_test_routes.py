from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(
    tags=[
        "PayFast Test"
    ]
)


@router.get(
    "/payfast/test",
    response_class=HTMLResponse,
)
def payfast_test_page():

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>PayFast Sandbox Test</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 40px;
            }

            .card {
                max-width: 600px;
                margin: auto;
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.10);
            }

            h1 {
                margin-top: 0;
            }

            label {
                display: block;
                margin-top: 18px;
                font-weight: bold;
            }

            input {
                width: 100%;
                padding: 12px;
                margin-top: 6px;
                box-sizing: border-box;
            }

            button {
                margin-top: 24px;
                padding: 14px 22px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
            }

            #fullButton {
                background: #111;
                color: white;
            }

            #partialButton {
                background: #e6e6e6;
                color: #111;
                margin-left: 8px;
            }

            .status {
                margin-top: 20px;
                padding: 12px;
                background: #f2f2f2;
                border-radius: 8px;
                white-space: pre-wrap;
            }
        </style>
    </head>

    <body>

        <div class="card">

            <h1>PayFast Sandbox Test</h1>

            <p>
                This page starts a PayFast payment using the
                student finance API and then submits the returned
                fields directly to PayFast.
            </p>

            <label>
                Student Portal JWT Token
            </label>

            <input
                id="token"
                type="text"
                placeholder="Paste Bearer token here"
            >

            <label>
                Partial Amount
            </label>

            <input
                id="amount"
                type="number"
                step="0.01"
                min="5"
                placeholder="Example: 500"
            >

            <button
                id="fullButton"
                onclick="startPayment(false)"
            >
                Pay Full Outstanding Balance
            </button>

            <button
                id="partialButton"
                onclick="startPayment(true)"
            >
                Pay Partial Amount
            </button>

            <div
                id="status"
                class="status"
            >
                Waiting...
            </div>

        </div>


        <script>

            async function startPayment(
                partial
            ) {

                const token =
                    document
                    .getElementById(
                        "token"
                    )
                    .value
                    .trim();

                const amount =
                    document
                    .getElementById(
                        "amount"
                    )
                    .value
                    .trim();

                const statusBox =
                    document
                    .getElementById(
                        "status"
                    );

                if (!token) {

                    statusBox.innerText =
                        "Please paste the student JWT token first.";

                    return;
                }


                let payload = {};


                if (partial) {

                    if (!amount) {

                        statusBox.innerText =
                            "Enter a partial payment amount.";

                        return;
                    }

                    payload = {
                        amount: Number(
                            amount
                        )
                    };
                }


                statusBox.innerText =
                    "Starting PayFast transaction...";


                try {

                    const response =
                        await fetch(
                            "/api/student/finance/payfast/start",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json",

                                    "Authorization":
                                        "Bearer " + token
                                },

                                body:
                                    JSON.stringify(
                                        payload
                                    )
                            }
                        );


                    const result =
                        await response.json();


                    if (!response.ok) {

                        statusBox.innerText =
                            "Error:\\n"
                            + JSON.stringify(
                                result,
                                null,
                                2
                            );

                        return;
                    }


                    const payment =
                        result.data;


                    statusBox.innerText =
                        "Transaction created:\\n"
                        + payment.merchant_payment_id
                        + "\\nAmount: R"
                        + payment.amount
                        + "\\nRedirecting to PayFast...";


                    submitToPayFast(
                        payment.payment_url,
                        payment.fields
                    );


                } catch (error) {

                    statusBox.innerText =
                        "Request failed:\\n"
                        + error;
                }
            }


            function submitToPayFast(
                paymentUrl,
                fields
            ) {

                const form =
                    document.createElement(
                        "form"
                    );

                form.method =
                    "POST";

                form.action =
                    paymentUrl;


                Object
                    .entries(
                        fields
                    )
                    .forEach(
                        (
                            [
                                key,
                                value
                            ]
                        ) => {

                            const input =
                                document
                                .createElement(
                                    "input"
                                );

                            input.type =
                                "hidden";

                            input.name =
                                key;

                            input.value =
                                value;

                            form.appendChild(
                                input
                            );
                        }
                    );


                document.body.appendChild(
                    form
                );


                form.submit();
            }

        </script>

    </body>
    </html>
    """