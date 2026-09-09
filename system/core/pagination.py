from django.conf import settings
from django.core.paginator import Paginator

PAGE_PARAM = "page"


def list_page_size() -> int:
    return settings.LIST_PAGE_SIZE


def page_url(query_params, number) -> str:
    params = query_params.copy()
    params.setlist(PAGE_PARAM, [str(number)])
    return f"?{params.urlencode()}"


def _page_items(page, query_params):
    paginator = page.paginator
    items = []
    for entry in paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1):
        if entry == Paginator.ELLIPSIS:
            items.append({"is_gap": True, "is_current": False, "label": "", "url": ""})
            continue
        items.append(
            {
                "is_gap": False,
                "is_current": entry == page.number,
                "label": entry,
                "url": page_url(query_params, entry),
            }
        )
    return items


def pagination_context(page, query_params, unit):
    paginator = page.paginator
    singular, plural = unit
    return {
        "has_results": paginator.count > 0,
        "count": paginator.count,
        "unit": singular if paginator.count == 1 else plural,
        "range_start": page.start_index(),
        "range_end": page.end_index(),
        "current": page.number,
        "num_pages": paginator.num_pages,
        "show_nav": paginator.num_pages > 1,
        "previous_url": (
            page_url(query_params, page.previous_page_number())
            if page.has_previous()
            else ""
        ),
        "next_url": (
            page_url(query_params, page.next_page_number()) if page.has_next() else ""
        ),
        "items": _page_items(page, query_params),
    }


def paginate(object_list, request, unit, page_size=None):
    paginator = Paginator(object_list, page_size or list_page_size())
    page = paginator.get_page(request.GET.get(PAGE_PARAM))
    return page, pagination_context(page, request.GET, unit)
