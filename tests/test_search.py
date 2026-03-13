from api.search import clamp_limit, execute_search


class StubYTMusic:
    def __init__(self):
        self.calls = []

    def search(self, query, filter=None, limit=10):
        self.calls.append((query, filter, limit))
        return [{"title": query, "limit": limit, "filter": filter}]


def test_clamp_limit_bounds():
    assert clamp_limit(0) == 1
    assert clamp_limit(-10) == 1
    assert clamp_limit(25) == 25
    assert clamp_limit(100) == 25


def test_execute_search_calls_client():
    client = StubYTMusic()
    result = execute_search(client, "Oasis", "songs", 5)
    assert result == [{"title": "Oasis", "limit": 5, "filter": "songs"}]
    assert client.calls == [("Oasis", "songs", 5)]
