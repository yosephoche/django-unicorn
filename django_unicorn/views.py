import hmac

from django.conf import settings
from django.http import JsonResponse

import orjson

from .components import get_component_class


def message(request, component_name):
    body = orjson.loads(request.body)
    data = body.get("data", {})
    checksum = body.get("checksum")

    unicorn_id = body.get("id")
    Component = get_component_class(component_name)
    component = Component(unicorn_id)

    for (name, value) in data.items():
        if hasattr(component, name):
            setattr(component, name, value)

    action_queue = body.get("actionQueue", [])

    for action in action_queue:
        action_type = action.get("type")
        payload = action.get("payload", {})

        if action_type == "syncInput":
            name = payload.get("name")
            value = payload.get("value")

            if hasattr(component, name):
                setattr(component, name, value)

    generated_checksum = hmac.new(
        str.encode(settings.SECRET_KEY), orjson.dumps(data), digestmod="sha256",
    ).hexdigest()

    assert checksum == generated_checksum, "Checksum does not match"

    rendered_component = component.render(component_name)

    res = {
        "id": unicorn_id,
        "dom": rendered_component,
    }

    return JsonResponse(res)