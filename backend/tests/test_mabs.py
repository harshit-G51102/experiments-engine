import copy
import os
from typing import Generator

from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture, mark
from sqlalchemy.orm import Session

from backend.app.mab.models import MABArmDB, MultiArmedBanditDB
from backend.app.models import NotificationsDB

base_mab_payload = {
    "name": "Test",
    "description": "Test description",
    "arms": [
        {
            "name": "arm 1",
            "description": "arm 1 description",
            "alpha_prior": 5,
            "beta_prior": 1,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description",
            "alpha_prior": 1,
            "beta_prior": 4,
        },
    ],
    "notifications": {
        "onTrialCompletion": True,
        "numberOfTrials": 2,
        "onDaysElapsed": False,
        "daysElapsed": 3,
        "onPercentBetter": False,
        "percentBetterThreshold": 5,
    },
}


@fixture
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/login",
        data={
            "username": os.environ.get("ADMIN_USERNAME", ""),
            "password": os.environ.get("ADMIN_PASSWORD", ""),
        },
    )
    token = response.json()["access_token"]
    return token


@fixture()
def clean_mabs(db_session: Session) -> Generator:
    yield
    db_session.query(NotificationsDB).delete()
    db_session.query(MABArmDB).delete()
    db_session.query(MultiArmedBanditDB).delete()
    db_session.commit()


class TestMab:
    @fixture
    def create_mab_payload(self, request: FixtureRequest) -> dict:
        payload: dict = copy.deepcopy(base_mab_payload)
        payload["arms"] = list(payload["arms"])

        if request.param == "base":
            return payload
        if request.param == "one_arm":
            payload["arms"].pop()
            return payload
        if request.param == "no_notifications":
            payload["notifications"]["onTrialCompletion"] = False
            return payload
        else:
            raise ValueError("Invalid parameter")

    @mark.parametrize(
        "create_mab_payload, expected_response",
        [("base", 200), ("one_arm", 422), ("no_notifications", 200)],
        indirect=["create_mab_payload"],
    )
    def test_create_mab(
        self,
        create_mab_payload: dict,
        client: TestClient,
        expected_response: int,
        admin_token: str,
        clean_mabs: None,
    ) -> None:
        response = client.post(
            "/mab",
            json=create_mab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response

    @fixture
    def create_mabs(
        self, client: TestClient, admin_token: str, request: FixtureRequest
    ) -> Generator:
        mabs = []
        n_mabs = request.param if hasattr(request, "param") else 1
        for _ in range(n_mabs):
            response = client.post(
                "/mab",
                json=base_mab_payload,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            mabs.append(response.json())
        yield mabs
        for mab in mabs:
            client.delete(
                f"/mab/{mab['experiment_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    @mark.parametrize(
        "create_mabs, n_expected",
        [(0, 0), (2, 2), (5, 5)],
        indirect=["create_mabs"],
    )
    def test_get_all_mabs(
        self, client: TestClient, admin_token: str, n_expected: int, create_mabs: list
    ) -> None:
        response = client.get(
            "/mab", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == n_expected

    @mark.parametrize(
        "create_mabs, expected_response",
        [(0, 404), (2, 200)],
        indirect=["create_mabs"],
    )
    def test_get_mab(
        self,
        client: TestClient,
        admin_token: str,
        create_mabs: list,
        expected_response: int,
    ) -> None:
        id = create_mabs[0]["experiment_id"] if create_mabs else 999

        response = client.get(
            f"/mab/{id}", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == expected_response

    def test_draw_arm(self, client: TestClient, create_mabs: list) -> None:
        id = create_mabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.get(
            f"/mab/{id}/draw",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200


class TestNotifications:
    @fixture()
    def create_mab_payload(self, request: FixtureRequest) -> dict:
        payload: dict = copy.deepcopy(base_mab_payload)
        payload["arms"] = list(payload["arms"])

        match request.param:
            case "base":
                pass
            case "daysElapsed_only":
                payload["notifications"]["onTrialCompletion"] = False
                payload["notifications"]["onDaysElapsed"] = True
            case "trialCompletion_only":
                payload["notifications"]["onTrialCompletion"] = True
            case "percentBetter_only":
                payload["notifications"]["onTrialCompletion"] = False
                payload["notifications"]["onPercentBetter"] = True
            case "all_notifications":
                payload["notifications"]["onDaysElapsed"] = True
                payload["notifications"]["onPercentBetter"] = True
            case "no_notifications":
                payload["notifications"]["onTrialCompletion"] = False
            case "daysElapsed_missing":
                payload["notifications"]["daysElapsed"] = 0
                payload["notifications"]["onDaysElapsed"] = True
            case "trialCompletion_missing":
                payload["notifications"]["numberOfTrials"] = 0
                payload["notifications"]["onTrialCompletion"] = True
            case "percentBetter_missing":
                payload["notifications"]["percentBetterThreshold"] = 0
                payload["notifications"]["onPercentBetter"] = True
            case _:
                raise ValueError("Invalid parameter")

        return payload

    @mark.parametrize(
        "create_mab_payload, expected_response",
        [
            ("base", 200),
            ("daysElapsed_only", 200),
            ("trialCompletion_only", 200),
            ("percentBetter_only", 200),
            ("all_notifications", 200),
            ("no_notifications", 200),
            ("daysElapsed_missing", 422),
            ("trialCompletion_missing", 422),
            ("percentBetter_missing", 422),
        ],
        indirect=["create_mab_payload"],
    )
    def test_notifications(
        self,
        client: TestClient,
        admin_token: str,
        create_mab_payload: dict,
        expected_response: int,
        clean_mabs: None,
    ) -> None:
        response = client.post(
            "/mab",
            json=create_mab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response
