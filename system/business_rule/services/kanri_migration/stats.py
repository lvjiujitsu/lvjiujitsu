class KanriStatsMixin:
    def _empty_stats(self):
        return {
            "persons_created": 0,
            "persons_updated": 0,
            "relationships_created": 0,
            "relationships_updated": 0,
            "graduations_created": 0,
            "migration_cpfs": 0,
            "financial_skipped": 0,
            "attendance_skipped": 0,
        }
