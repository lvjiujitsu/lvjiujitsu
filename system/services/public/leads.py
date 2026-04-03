from django.db import transaction

from system.models import Lead, TrialClassRequest


def capture_lead(**validated_data):
    return Lead.objects.create(**validated_data)


@transaction.atomic
def create_trial_class_request(**validated_data):
    lead = Lead.objects.create(
        full_name=validated_data["full_name"],
        email=validated_data.get("email", ""),
        phone=validated_data.get("phone", ""),
        source=validated_data["source"],
        interest_note=validated_data.get("notes", ""),
    )
    return TrialClassRequest.objects.create(
        lead=lead,
        preferred_date=validated_data["preferred_date"],
        preferred_period=validated_data["preferred_period"],
        notes=validated_data.get("notes", ""),
    )
