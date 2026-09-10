from system.core.accounts import AbstractTechnicalUser


class User(AbstractTechnicalUser):

    class Meta(AbstractTechnicalUser.Meta):
        pass
