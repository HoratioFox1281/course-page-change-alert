from page_change_alert import CourseWatch, WatchResult, monitor_once


class FakeClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.sent = False

    def scrape_page(self, url: str) -> str:
        return self.content

    def send_alert(self, watch: CourseWatch, current_content: str) -> str:
        self.sent = True
        return "msg-42"


def make_watch(snapshot: str) -> CourseWatch:
    return CourseWatch("Algebra", "Lee", "Patel", "https://example.edu/algebra", "Friday", "teacher@example.edu", snapshot)


def test_changed_course_page_sends_the_educator_alert() -> None:
    client = FakeClient("new lesson deadline: Friday")
    result = monitor_once(client, make_watch("old lesson deadline: Thursday"))
    assert result == WatchResult(True, "new lesson deadline: Friday", "msg-42")
    assert client.sent is True


def test_same_course_page_does_not_send_an_alert() -> None:
    client = FakeClient("unchanged")
    result = monitor_once(client, make_watch("unchanged"))
    assert result == WatchResult(False, "unchanged", None)
    assert client.sent is False
