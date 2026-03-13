from api import ytmusic as ytm


class StubYTMusic:
    def get_song(self, video_id):
        return {"videoId": video_id}


def test_validate_method_missing():
    assert ytm.validate_method(StubYTMusic(), "") == "Missing required method"


def test_validate_method_not_allowed():
    assert ytm.validate_method(StubYTMusic(), "delete_account") == "Method is not allowed without auth"


def test_validate_method_not_supported():
    assert ytm.validate_method(StubYTMusic(), "get_album") == "Method not supported by installed ytmusicapi"


def test_call_method_success():
    result = ytm.call_method(StubYTMusic(), "get_song", ["abc123"], {})
    assert result == {"videoId": "abc123"}


def test_call_method_disallowed():
    try:
        ytm.call_method(StubYTMusic(), "delete_account", [], {})
        assert False, "Expected ValueError for disallowed method"
    except ValueError as exc:
        assert "Method is not allowed without auth" in str(exc)
