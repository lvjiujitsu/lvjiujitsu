class DependentPasswordMixin:
    def _clean_passwords(self, cleaned_data):
        password = cleaned_data.get("dependent_password")
        confirmation = cleaned_data.get("dependent_password_confirm")
        if password and len(password) < 8:
            self.add_error("dependent_password", "Use no mínimo 8 caracteres.")
        if password and confirmation and password != confirmation:
            self.add_error("dependent_password_confirm", "As senhas não conferem.")
