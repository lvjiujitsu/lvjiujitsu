class PersonFieldGroupsMixin:
    @property
    def main_fields(self):
        return [self[name] for name in self.main_field_names]

    @property
    def identity_fields(self):
        return self._bound_fields(self.identity_field_names)

    @property
    def address_fields(self):
        return self._bound_fields(self.address_field_names)

    @property
    def health_fields(self):
        return self._bound_fields(self.health_field_names)

    @property
    def martial_art_fields(self):
        return self._bound_fields(self.martial_art_field_names)

    @property
    def martial_art_history_fields(self):
        return []

    @property
    def relationship_fields(self):
        return self._bound_fields(self.relationship_field_names)

    def _bound_fields(self, field_names):
        return [self[name] for name in field_names]
