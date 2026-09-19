"""项目正常启动 / 健康检查测试。"""
def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_openapi_docs_available(client):
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200


def test_seed_data_loaded(client):
    trains = client.get("/api/trains").json()
    tracks = client.get("/api/tracks").json()
    locos = client.get("/api/locomotives").json()
    assert trains["total"] == 8
    assert tracks["total"] == 4
    assert locos["total"] == 3
