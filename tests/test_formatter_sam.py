from scrapers.formatter import format_opportunities_sam

def test_format_sam_minimal():
    raw = [{
        "noticeId": "ABC123",
        "title": "School Cleaning",
        "solicitationNumber": "SC-001",
        "fullParentPathName": "Dept of Education",
        "fullParentPathCode": "EDU",
        "postedDate": "2025-08-20T12:34:56Z",
        "responseDeadLine": "2025-08-25T00:00:00Z",
        "naicsCode": "561720",
        "classificationCode": "S201",
        "type": "Solicitation",
        "active": "Yes",
        "award": {"date": None, "number": None, "amount": None, "awardee": {}},
    }]
    out = format_opportunities_sam(raw)
    row = out[0]
    assert row["opportunity_id"] == "ABC123"
    assert row["agency"] == "Dept of Education"
    assert row["active"] is True
    assert row["naics_code"] == "561720"
