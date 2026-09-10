class PersonMartialArtMixin:
    def _clear_martial_art_history(self, cleaned_data):
        cleaned_data["martial_art"] = ""
        cleaned_data["martial_art_graduation"] = ""
        cleaned_data["jiu_jitsu_belt"] = ""
        cleaned_data["jiu_jitsu_stripes"] = None
        cleaned_data["martial_art_started_at"] = None
        cleaned_data["martial_art_last_graduation_at"] = None
        cleaned_data["previous_academy"] = ""

    def _martial_art_detail_field_names(self):
        return [
            field_name
            for field_name in self.martial_art_field_names
            if field_name != "has_martial_art"
        ]
