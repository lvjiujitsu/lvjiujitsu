def only_digits(value: str) -> str:
    return "".join(character for character in value if character.isdigit())


def ensure_formatted_cpf(value: str) -> str:
    digits = only_digits(value)
    if len(digits) != 11:
        raise ValueError("CPF deve conter 11 dígitos.")

    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
