def form_error_payload(form):
    return {
        field_name: [str(error) for error in error_list]
        for field_name, error_list in form.errors.items()
    }
