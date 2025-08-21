from scrapers.formatter import format_opportunities_cal

def test_format_cal_basic():
    raw = [{
        "event_id": "0001",
        "event_name": "Janitorial Services",
        "department": "Dept of Corrections & Rehab",
        "end_date": "08/21/2025 1:00PM PDT",
        "status": "Posted",
    }]
    out = format_opportunities_cal(raw)
    assert len(out) == 1
    row = out[0]
    assert row["opportunity_id"] == "0001"
    assert row["title"] == "Janitorial Services"
    assert row["agency"] == "Dept of Corrections & Rehab"
    assert row["deadline"] == "08/21/2025 1:00PM PDT"
    assert row["checksum"]
