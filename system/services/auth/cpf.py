def normalize_cpf(value):
    if not value:
        return ""
    digits = "".join(character for character in str(value) if character.isdigit())
    if len(digits) != 11:
        return ""
    return digits
