from fastapi.testclient import TestClient


def test_health_and_mock_login(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "host@thegardenroom.example", "password": "demo"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["user"]["role"] == "HOST"
    assert client.get("/api/v1/auth/me").json()["email"] == "host@thegardenroom.example"


def test_create_lists_and_validates_waitlist_entry(client: TestClient) -> None:
    invalid = client.post("/api/v1/waitlist", json={"customer_name": "Ada", "phone_number": "555", "party_size": 0})
    assert invalid.status_code == 422

    created = client.post("/api/v1/waitlist", json={"customer_name": "Ada Lovelace", "phone_number": "555-0101", "party_size": 4, "seating_preference": "BOOTH"})
    assert created.status_code == 201
    entry = created.json()
    assert entry["reference"].startswith("WL-")
    assert entry["estimated_wait_minutes"] >= 0
    assert entry["status"] == "WAITING"
    assert client.get("/api/v1/waitlist").json() == [entry]


def test_waitlist_state_flow_assigns_available_table(client: TestClient) -> None:
    table = client.post("/api/v1/tables", json={"name": "T4", "minimum_capacity": 2, "maximum_capacity": 4, "location": "Main Dining"}).json()
    entry = client.post("/api/v1/waitlist", json={"customer_name": "Maya Patel", "phone_number": "555-0102", "party_size": 4, "seating_preference": "INDOOR"}).json()

    assert client.post(f"/api/v1/waitlist/{entry['id']}/seat", json={"table_id": table["id"]}).status_code == 409
    assert client.post(f"/api/v1/waitlist/{entry['id']}/notify").json()["status"] == "NOTIFIED"
    assert client.post(f"/api/v1/waitlist/{entry['id']}/confirm").json()["status"] == "CONFIRMED"

    seated = client.post(f"/api/v1/waitlist/{entry['id']}/seat", json={"table_id": table["id"]})
    assert seated.status_code == 200
    assert seated.json()["status"] == "SEATED"
    assert seated.json()["table_id"] == table["id"]
    assert client.get(f"/api/v1/tables/{table['id']}").json()["status"] == "OCCUPIED"


def test_cancel_update_and_not_found_errors(client: TestClient) -> None:
    entry = client.post("/api/v1/waitlist", json={"customer_name": "Grace", "phone_number": "555-0103", "party_size": 2}).json()
    updated = client.patch(f"/api/v1/waitlist/{entry['id']}", json={"notes": "Uses a cane", "party_size": 3})
    assert updated.json()["notes"] == "Uses a cane"
    assert client.post(f"/api/v1/waitlist/{entry['id']}/cancel").json()["status"] == "CANCELLED"
    missing = client.get("/api/v1/waitlist/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "WAITLIST_NOT_FOUND"


def test_tables_reports_and_ai_endpoints(client: TestClient) -> None:
    table = client.post("/api/v1/tables", json={"name": "Patio 1", "minimum_capacity": 2, "maximum_capacity": 6, "location": "Outdoor"}).json()
    client.post("/api/v1/waitlist", json={"customer_name": "Lin", "phone_number": "555-0104", "party_size": 3, "seating_preference": "OUTDOOR"})

    assert client.patch(f"/api/v1/tables/{table['id']}", json={"status": "CLEANING"}).json()["status"] == "CLEANING"
    assert client.get("/api/v1/reports/waitlist").json()["waiting_parties"] == 1
    assert client.get("/api/v1/reports/tables").json()["total_tables"] == 1
    assert client.get("/api/v1/reports/operations").json()["active_waitlist_entries"] == 1
    assert client.get("/api/v1/ai/wait-estimate/" + client.get("/api/v1/waitlist").json()[0]["id"]).json()["confidence"] == "HIGH"
    assert client.get("/api/v1/ai/table-recommendations").json()["recommendations"] == []
    assert "insight" in client.get("/api/v1/ai/insights").json()
    assert "answer" in client.post("/api/v1/ai/assistant", json={"question": "How busy are we?"}).json()
