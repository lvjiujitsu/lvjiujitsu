from system.core.password_reset.contracts import AccountAdapter


class EmailAccountAdapter(AccountAdapter):
    lookup_field = "email"
    display_name_fields = ("name", "full_name", "contact_name")
    saved_password_fields = ("password", "updated_at")
    login_path = "/login/"

    def find(self, lookup_value):
        return self.model.objects.filter(
            **{f"{self.lookup_field}__iexact": lookup_value}
        ).first()

    def password_hash(self, account):
        return account.password

    def email(self, account):
        return (getattr(account, "email", "") or "").strip()

    def display_name(self, account):
        for field in self.display_name_fields:
            value = getattr(account, field, "")
            if value:
                return value
        return self.email(account)

    def is_active(self, account):
        return bool(getattr(account, "is_active", True))

    def set_password(self, account, raw_password):
        account.set_password(raw_password)
        account.save(update_fields=list(self.saved_password_fields))

    def login_url(self, account):
        return self.login_path
