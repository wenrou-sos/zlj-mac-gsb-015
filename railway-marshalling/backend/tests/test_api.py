"""API 启动与 CRUD 冒烟测试。"""
from datetime import datetime, timedelta


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_seed_data_loaded(client):
    """应用启动后种子数据已写入。"""
    assert len(client.get("/api/tracks").json()) >= 3
    assert len(client.get("/api/locomotives").json()) >= 2
    assert len(client.get("/api/rules").json()) >= 1
    assert len(client.get("/api/trains").json()) >= 5


def test_track_crud_roundtrip(client):
    payload = {"name": "测试道", "length_m": 800.0, "track_type": "arrival_departure"}
    created = client.post("/api/tracks", json=payload)
    assert created.status_code == 201
    track_id = created.json()["id"]

    updated = client.put(f"/api/tracks/{track_id}", json={"length_m": 950.0})
    assert updated.status_code == 200
    assert updated.json()["length_m"] == 950.0

    assert client.delete(f"/api/tracks/{track_id}").status_code == 204
    assert client.get(f"/api/tracks/{track_id}").status_code == 404


def test_duplicate_track_name_rejected(client):
    payload = {"name": "重复道", "length_m": 800.0}
    assert client.post("/api/tracks", json=payload).status_code == 201
    assert client.post("/api/tracks", json=payload).status_code == 409


def test_train_create_and_validation(client):
    track_id = client.get("/api/tracks").json()[0]["id"]
    base = datetime.now()
    payload = {
        "train_number": "T999",
        "arrival_time": base.isoformat(),
        "departure_time": (base + timedelta(hours=2)).isoformat(),
        "wagon_count": 30,
        "total_length_m": 420.0,
        "total_weight_t": 2400.0,
        "track_id": track_id,
    }
    resp = client.post("/api/trains", json=payload)
    assert resp.status_code == 201
    assert resp.json()["train_number"] == "T999"


def test_analysis_run_and_history(client):
    resp = client.post("/api/analysis/run")
    assert resp.status_code == 201
    body = resp.json()
    assert body["train_count"] >= 5
    assert body["conflict_count"] > 0  # 种子数据本身包含冲突
    types = {c["type"] for c in body["results"]}
    assert "track_occupation" in types
    assert "over_limit" in types
    # 每条冲突都带有调整建议
    assert all(c["suggestion"] for c in body["results"])

    latest = client.get("/api/analysis/latest")
    assert latest.status_code == 200
    assert latest.json()["id"] == body["id"]

    history = client.get("/api/analysis/runs")
    assert history.status_code == 200
    assert len(history.json()) >= 1
