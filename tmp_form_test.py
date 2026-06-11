import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lvjiujitsu.settings')
django.setup()

from django.http import QueryDict
from system.forms import PortalRegistrationForm

# Simular o QueryDict real como o browser envia
raw = (
    "registration_profile=holder&include_dependent=&other_type_code=&extra_dependents_payload=%5B%5D"
    "&holder_name=Carlos+Teste+PIX&holder_cpf=104.332.181-00&holder_birthdate=15%2F03%2F1990"
    "&holder_biological_sex=male&holder_phone=%2811%29+91234-5678&holder_email=carlos.pix%40teste.com"
    "&holder_password=Senha%40123&holder_password_confirm=Senha%40123"
    "&holder_class_groups=1%3A%3AJiu+Jitsu"
    "&holder_blood_type=O%2B&holder_allergies=&holder_injuries="
    "&holder_emergency_contact=Maria+Teste+%2811%29+99999-0001"
    "&holder_has_martial_art=no&holder_martial_art=&holder_martial_art_graduation="
    "&holder_jiu_jitsu_belt=&holder_jiu_jitsu_stripes=0"
    "&holder_martial_art_started_at=&holder_martial_art_last_graduation_at=&holder_previous_academy="
    "&holder_postal_code=01310-100&holder_address=Avenida+Paulista&holder_address_number=1000"
    "&holder_address_complement=Apto+10&holder_address_neighborhood=Bela+Vista&holder_city=S%C3%A3o+Paulo"
    "&dependent_class_groups=%5B%27%27%5D&student_class_groups=%5B%27%27%5D"
    "&selected_plan=4"
    "&selected_plans_payload=%5B%7B%22person_index%22%3A0%2C%22label%22%3A%22Carlos+Teste+PIX%22%2C%22plan_id%22%3A4%7D%5D"
    "&selected_products_payload=%5B%5D&coupon_code=&checkout_action=pix"
)
qd = QueryDict(raw)

form = PortalRegistrationForm(data=qd)
print('valid:', form.is_valid())
if not form.is_valid():
    for field, errs in form.errors.items():
        print(f'  ERRO [{field}]: {list(errs)}')
else:
    print('  checkout_action:', form.cleaned_data.get('checkout_action'))
    print('  holder_cpf:', form.cleaned_data.get('holder_cpf'))
    print('  holder_class_groups:', form.cleaned_data.get('holder_class_groups'))
