from src.legaltech_watermark import CreatorImage, prepare_for_publishing


class UnusedClient:
    def watermark(self, payload):
        raise AssertionError("watermark must not run for an incomplete matter")


def test_missing_case_reference_blocks_publish():
    item = CreatorImage(image="img-123", filename="cover.png", case_reference=" ")
    result = prepare_for_publishing(item, UnusedClient())
    assert result == {
        "status": "rejected",
        "reason": "case_reference_required",
        "filename": "cover.png",
    }
