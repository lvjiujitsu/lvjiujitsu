class AccountAdapter:
    model = None

    def find(self, lookup_value):
        raise NotImplementedError

    def get(self, pk):
        return self.model.objects.filter(pk=pk).first()

    def password_hash(self, account):
        raise NotImplementedError

    def email(self, account):
        raise NotImplementedError

    def display_name(self, account):
        raise NotImplementedError

    def is_active(self, account):
        raise NotImplementedError

    def set_password(self, account, raw_password):
        raise NotImplementedError

    def login_url(self, account):
        raise NotImplementedError
