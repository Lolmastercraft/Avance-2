from pipeline.run import decide


def full():
    return {name: {"ok": True} for name in ("secrets", "bandit", "checkov", "configuration", "dependencies", "tests", "sbom", "live")}


def test_final_gate_requires_all_stages():
    assert decide(full()) == "PERMITIR"
    assert decide({}) == "BLOQUEAR"
    report = full()
    del report["tests"]
    assert decide(report) == "BLOQUEAR"


def test_final_gate_rejects_failures_and_unknowns():
    for value in (False, None, "true", 1):
        report = full()
        report["bandit"]["ok"] = value
        assert decide(report) == "BLOQUEAR"
