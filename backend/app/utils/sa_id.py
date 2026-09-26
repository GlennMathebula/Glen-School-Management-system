from datetime import datetime


def validate_sa_id(id_number: str) -> dict:
    """
    Validate a South African 13-digit ID number.

    Checks:
    - Exactly 13 digits
    - Valid date of birth
    - Valid citizenship/status digit
    - Luhn checksum
    """

    if not id_number:
        return {
            "valid": False,
            "message": "ID number is required."
        }

    id_number = id_number.strip()

    # 1. Must contain exactly 13 digits
    if len(id_number) != 13 or not id_number.isdigit():
        return {
            "valid": False,
            "message": "South African ID number must contain exactly 13 digits."
        }

    # 2. Validate date portion YYMMDD
    yy = int(id_number[0:2])
    mm = int(id_number[2:4])
    dd = int(id_number[4:6])

    current_year = datetime.now().year
    current_two_digits = current_year % 100

    # Determine century from the current year
    if yy <= current_two_digits:
        year = 2000 + yy
    else:
        year = 1900 + yy

    try:
        datetime(year, mm, dd)
    except ValueError:
        return {
            "valid": False,
            "message": "The date of birth in the ID number is invalid."
        }

    # 3. Citizenship/status digit
    citizenship_digit = int(id_number[10])

    if citizenship_digit not in (0, 1):
        return {
            "valid": False,
            "message": "Invalid citizenship/status digit."
        }

    # 4. Luhn checksum
    digits = [int(digit) for digit in id_number]

    # Sum digits in positions 1, 3, 5, 7, 9, 11
    odd_sum = sum(digits[0:12:2])

    # Concatenate positions 2, 4, 6, 8, 10, 12
    even_digits = ''.join(str(d) for d in digits[1:12:2])

    # Multiply by 2
    doubled = int(even_digits) * 2

    # Sum the digits of the result
    doubled_digit_sum = sum(int(digit) for digit in str(doubled))

    total = odd_sum + doubled_digit_sum

    # Luhn validation
    valid_checksum = (total + digits[12]) % 10 == 0

    if not valid_checksum:
        return {
            "valid": False,
            "message": "Invalid South African ID checksum."
        }

    return {
        "valid": True,
        "message": "Valid South African ID number.",
        "date_of_birth": f"{year:04d}-{mm:02d}-{dd:02d}",
        "citizenship_status": "Citizen" if citizenship_digit == 0 else "Permanent Resident"
    }