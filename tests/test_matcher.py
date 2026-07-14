from pnp_watcher.matcher import matches


def make_notice(wohnort="", weitere_orte="", notice_text=""):
    return {
        "wohnort": wohnort,
        "weitere_orte": weitere_orte,
        "notice_text": notice_text,
    }


def test_matches_wohnort_case_insensitive():
    notice = make_notice(wohnort="Fiktingen/Nebendorf, zuletzt Ferneburg")
    assert matches(notice, "fiktingen") is True


def test_matches_weitere_orte():
    notice = make_notice(weitere_orte="Bergheim, Talstadt")
    assert matches(notice, "Bergheim") is True


def test_matches_notice_text():
    notice = make_notice(notice_text="aus Bergheim, zuletzt Ferneburg")
    assert matches(notice, "Bergheim") is True


def test_no_match():
    notice = make_notice(wohnort="Nebendorf", weitere_orte="", notice_text="In stiller Trauer.")
    assert matches(notice, "Bergheim") is False


def test_partial_word_does_not_falsely_exclude():
    # A short target can coincidentally match inside a longer, unrelated place
    # name. This test documents the current (accepted) substring-matching
    # behavior rather than asserting it should be avoided.
    notice = make_notice(wohnort="Fiktalburg")
    assert matches(notice, "Fiktal") is True


def test_handles_missing_fields_gracefully():
    notice = {}
    assert matches(notice, "Bergheim") is False


def test_handles_none_target_city_field_values():
    notice = make_notice(wohnort=None, weitere_orte=None, notice_text="aus Bergheim")
    assert matches(notice, "Bergheim") is True
