from system.models.plan import SubscriptionPlan


def get_plan_list():
    return SubscriptionPlan.objects.all()


def get_active_plans():
    return SubscriptionPlan.objects.filter(is_active=True)


def get_plan_by_pk(pk):
    return SubscriptionPlan.objects.get(pk=pk)
