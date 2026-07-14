MATCH_FIELDS = ("wohnort", "weitere_orte", "notice_text")


def matches(notice: dict, target_city: str) -> bool:
    target = target_city.lower()
    for field in MATCH_FIELDS:
        value = notice.get(field) or ""
        if target in value.lower():
            return True
    return False
