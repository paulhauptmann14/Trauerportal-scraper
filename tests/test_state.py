import json

from pnp_watcher.state import State


def test_new_state_has_no_seen_ids(tmp_path):
    state = State.load(tmp_path / "state.json")
    assert state.is_new(123) is True


def test_mark_seen_persists_after_save_and_reload(tmp_path):
    path = tmp_path / "state.json"
    state = State.load(path)
    state.mark_seen(123)
    state.save()

    reloaded = State.load(path)
    assert reloaded.is_new(123) is False


def test_unseen_id_remains_new(tmp_path):
    path = tmp_path / "state.json"
    state = State.load(path)
    state.mark_seen(1)
    state.save()

    reloaded = State.load(path)
    assert reloaded.is_new(2) is True


def test_is_first_run_true_when_no_file_exists(tmp_path):
    state = State.load(tmp_path / "state.json")
    assert state.is_first_run is True


def test_is_first_run_false_after_reload(tmp_path):
    path = tmp_path / "state.json"
    state = State.load(path)
    state.mark_seen(1)
    state.save()

    reloaded = State.load(path)
    assert reloaded.is_first_run is False


def test_load_tolerates_corrupt_file(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("not valid json")

    state = State.load(path)
    assert state.is_new(1) is True


def test_save_writes_valid_json(tmp_path):
    path = tmp_path / "state.json"
    state = State.load(path)
    state.mark_seen(42)
    state.save()

    data = json.loads(path.read_text())
    assert 42 in data["seen_ids"]
