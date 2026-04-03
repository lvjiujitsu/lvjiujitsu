import factory
from django.utils import timezone

from system.models import ConsentTerm, DocumentRecord, EmergencyRecord, GuardianRelationship, LgpdRequest, StudentProfile
from system.tests.factories.auth_factories import SystemUserFactory


class StudentProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentProfile

    user = factory.SubFactory(SystemUserFactory)
    student_type = StudentProfile.TYPE_HOLDER
    operational_status = StudentProfile.STATUS_ACTIVE
    join_date = factory.LazyFunction(timezone.localdate)
    self_service_access = True
    is_active = True


class EmergencyRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmergencyRecord

    student = factory.SubFactory(StudentProfileFactory)
    emergency_contact_name = "Contato de Emergencia"
    emergency_contact_phone = "11999990000"
    emergency_contact_relationship = "Mae"


class ConsentTermFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConsentTerm

    code = factory.Sequence(lambda index: f"term_{index}")
    title = factory.Sequence(lambda index: f"Termo {index}")
    version = 1
    content = "Conteudo de teste"
    is_active = True
    required_for_onboarding = True
    attachment = factory.django.FileField(filename="term.pdf", data=b"term-content")


class GuardianRelationshipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GuardianRelationship

    responsible_user = factory.SubFactory(SystemUserFactory)
    student = factory.SubFactory(StudentProfileFactory)
    relationship_type = GuardianRelationship.RELATIONSHIP_GUARDIAN
    is_primary = True
    is_financial_responsible = True


class LgpdRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LgpdRequest

    user = factory.SubFactory(SystemUserFactory)
    request_type = LgpdRequest.TYPE_ACCESS
    status = LgpdRequest.STATUS_OPEN
    confirmation_code = factory.Sequence(lambda index: f"LGPD{index:08d}")


class DocumentRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DocumentRecord

    owner_user = factory.SubFactory(SystemUserFactory)
    student = factory.SubFactory(StudentProfileFactory)
    subscription = None
    uploaded_by = factory.SubFactory(SystemUserFactory)
    document_type = DocumentRecord.TYPE_CONTRACT
    title = factory.Sequence(lambda index: f"Documento {index}")
    version_label = "v1"
    file = factory.django.FileField(filename="contract.pdf", data=b"contract-content")
    original_filename = "contract.pdf"
    issued_at = factory.LazyFunction(timezone.now)
    is_visible_to_owner = True
