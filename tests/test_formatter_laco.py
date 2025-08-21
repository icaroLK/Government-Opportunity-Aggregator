from scrapers.formatter import format_opportunities_laco

def test_format_laco_minimal():
    raw = [{
        "solicitation_number": "RFB-IS-26200090",
        "bid_id": "2581315240139",
        "title": "Lab Coats - Embroidery",
        "type": "Commodity / Service",
        "department": "Internal Services",
        "close_date": "8/25/2025 12:00 PM",
    }]
    out = format_opportunities_laco(raw)
    assert len(out) == 1
    row = out[0]
    assert row["opportunity_id"] == "2581315240139"
    assert row["type"] == "Solicitation"
    assert row["active"] is True
