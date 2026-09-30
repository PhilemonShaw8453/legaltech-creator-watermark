from datetime import date

from legal_image_service import MatterIntake, follow_up_required


def test_deadline_marks_matter_for_follow_up():
    matter = MatterIntake("matter-17", "Ava", date(2026, 9, 7))
    assert follow_up_required(matter, date(2026, 9, 7)) is True
    assert follow_up_required(matter, date(2026, 9, 6)) is False
