"""REST API 接口测试。"""
BASE = "/api"


def test_analysis_endpoint(client):
    resp = client.get(f"{BASE}/analysis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["train_count"] == 8
    assert data["track_count"] == 4
    assert data["locomotive_count"] == 3
    assert "summary" in data
    assert "track_stats" in data
    assert "loco_stats" in data
    assert data["timeline_start"] and data["timeline_end"]


def test_train_crud(client):
    payload = {
        "code": "T90001",
        "train_type": "normal",
        "arrival_time": "2026-09-20T08:00:00",
        "departure_time": "2026-09-20T09:00:00",
        "length_m": 500,
        "weight_t": 2000,
        "max_width_m": 3.2,
        "max_height_m": 4.4,
        "track_id": 1,
        "locomotive_id": 1,
        "sequence_no": 1,
        "destination": "测试站",
        "note": "",
    }
    resp = client.post(f"{BASE}/trains", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    train_id = created["id"]

    created["weight_t"] = 2300
    resp = client.put(f"{BASE}/trains/{train_id}", json=created)
    assert resp.status_code == 200
    assert resp.json()["weight_t"] == 2300

    assert client.delete(f"{BASE}/trains/{train_id}").status_code == 204
    assert client.get(f"{BASE}/trains/{train_id}").status_code == 404


def test_train_validation_departure_before_arrival(client):
    payload = {
        "code": "BAD1",
        "arrival_time": "2026-09-20T10:00:00",
        "departure_time": "2026-09-20T09:00:00",
    }
    assert client.post(f"{BASE}/trains", json=payload).status_code == 422


def test_train_invalid_track_ref(client):
    payload = {
        "code": "BAD2",
        "arrival_time": "2026-09-20T10:00:00",
        "departure_time": "2026-09-20T11:00:00",
        "track_id": 999,
    }
    assert client.post(f"{BASE}/trains", json=payload).status_code == 422


def test_track_and_locomotive_crud(client):
    tk = client.post(f"{BASE}/tracks", json={
        "name": "G9", "length_m": 900, "max_load_t": 4000,
    }).json()
    assert tk["id"] > 0

    loco = client.post(f"{BASE}/locomotives", json={
        "name": "DF9", "model": "DF7", "power_kw": 1500, "status": "available",
    }).json()
    assert loco["id"] > 0

    assert client.delete(f"{BASE}/tracks/{tk['id']}").status_code == 204
    assert client.delete(f"{BASE}/locomotives/{loco['id']}").status_code == 204


def test_rules_get_and_update_reset(client):
    items = client.get(f"{BASE}/rules").json()["items"]
    keys = {r["key"] for r in items}
    assert "track_safety_buffer_min" in keys
    assert "gauge_max_width_m" in keys

    resp = client.put(f"{BASE}/rules/track_safety_buffer_min",
                      json={"value": 30})
    assert resp.status_code == 200

    items = client.get(f"{BASE}/rules").json()["items"]
    row = next(r for r in items if r["key"] == "track_safety_buffer_min")
    assert row["value"] == 30
    assert row["customized"] is True

    assert client.delete(f"{BASE}/rules/track_safety_buffer_min").status_code == 200
    row = next(r for r in client.get(f"{BASE}/rules").json()["items"]
               if r["key"] == "track_safety_buffer_min")
    assert row["value"] == 15
    assert row["customized"] is False


def test_unknown_rule_rejected(client):
    assert client.put(f"{BASE}/rules/not_exist", json={"value": 1}).status_code == 404


def test_apply_resolution_suggestion_flow(client):
    """模拟前端采纳 C02 建议：把超长货列改派到建议股道，冲突应消除。"""
    result = client.get(f"{BASE}/analysis").json()
    c02 = next(c for c in result["conflicts"]
               if c["code"] == "C02" and c["train_code"] == "X85004")
    sugg = next(s for s in c02["suggestions"] if s["action"] == "reassign_track")

    train = client.get(f"{BASE}/trains").json()["items"]
    t85004 = next(t for t in train if t["code"] == "X85004")
    t85004["track_id"] = sugg["target_track_id"]
    assert client.put(f"{BASE}/trains/{t85004['id']}", json=t85004).status_code == 200

    result = client.get(f"{BASE}/analysis").json()
    assert all(not (c["code"] == "C02" and c["train_code"] == "X85004")
               for c in result["conflicts"])
