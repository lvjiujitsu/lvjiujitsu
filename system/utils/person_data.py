def only_digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def format_cpf_digits(value: str) -> str:
    digits = only_digits(value)
    if len(digits) != 11:
        raise ValueError("CPF deve conter 11 dígitos.")
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def _cpf_check_digit(digits: list[int], length: int) -> int:
    total = sum(digits[i] * (length + 1 - i) for i in range(length))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def ensure_formatted_cpf(value: str) -> str:
    digits = only_digits(value)
    if len(digits) != 11:
        raise ValueError("CPF deve conter 11 dígitos.")

    nums = [int(d) for d in digits]

    if len(set(nums)) == 1:
        raise ValueError("CPF inválido.")

    if nums[9] != _cpf_check_digit(nums, 9) or nums[10] != _cpf_check_digit(nums, 10):
        raise ValueError("CPF inválido.")

    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
