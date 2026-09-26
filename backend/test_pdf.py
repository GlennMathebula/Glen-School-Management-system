from app.services.pdf_service import generate_application_acknowledgement


test_application = {
    "student_number": "20260005",
    "first_name": "Test",
    "last_name": "Applicant",
    "email": "test.applicant@example.com",
    "app_status": "Pending",
}


pdf_path = generate_application_acknowledgement(
    test_application
)

print(f"PDF created successfully: {pdf_path}")