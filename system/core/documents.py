CPF_LENGTH = 11


def only_digits(value) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())


def cpf_check_digit(digits: str, length: int) -> int:
    total = sum(
        int(digits[index]) * (length + 1 - index) for index in range(length)
    )
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def is_valid_cpf(value) -> bool:
    digits = only_digits(value)
    if len(digits) != CPF_LENGTH:
        return False
    if len(set(digits)) == 1:
        return False
    return (
        cpf_check_digit(digits, 9) == int(digits[9])
        and cpf_check_digit(digits, 10) == int(digits[10])
    )


def normalize_cpf(value) -> str:
    digits = only_digits(value)
    return digits if is_valid_cpf(digits) else ""


def format_cpf(value) -> str:
    digits = only_digits(value)
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def format_cpf_digits(value) -> str:
    digits = only_digits(value)
    if len(digits) != CPF_LENGTH:
        raise ValueError("CPF deve conter 11 dígitos.")
    return format_cpf(digits)


def ensure_formatted_cpf(value) -> str:
    digits = only_digits(value)
    if len(digits) != CPF_LENGTH:
        raise ValueError("CPF deve conter 11 dígitos.")
    if not is_valid_cpf(digits):
        raise ValueError("CPF inválido.")
    return format_cpf(digits)
