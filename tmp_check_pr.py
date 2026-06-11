import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lvjiujitsu.settings')
django.setup()

from system.models import PreRegistration
for pr in PreRegistration.objects.order_by('-created_at')[:5]:
    s = pr.form_snapshot or {}
    print(f"pk={pr.pk} status={pr.status} email={s.get('holder_email','?')} action={s.get('checkout_action','?')}")
print('total:', PreRegistration.objects.count())
