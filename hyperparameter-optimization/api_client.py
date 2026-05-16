from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

import requests


class ApiError(RuntimeError):
    pass


@dataclass
class RunStatus:
    status: str
    created_at: Optional[str]
    updated_at: Optional[str]


class ApiClient:
    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._token: Optional[str] = None

    def login(self) -> None:
        payload = {"username": self.username, "password": self.password}
        res = requests.post(f"{self.base_url}/api/auth/login", json=payload, timeout=30)
        if res.status_code != 200:
            raise ApiError(f"Login failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"Login failed: {data.get('error')}")
        self._token = data["data"]["access_token"]

    def _headers(self) -> Dict[str, str]:
        if not self._token:
            raise ApiError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self._token}"}

    def create_job(self) -> str:
        payload = {"username": self.username}
        res = requests.post(
            f"{self.base_url}/api/job/init",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        if res.status_code not in {200, 201}:
            raise ApiError(f"Job init failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"Job init failed: {data.get('error')}")
        return data["data"]["id"]

    def load_settings(self, job_id: str, settings: Dict[str, Any]) -> None:
        payload = {"settings": settings}
        res = requests.post(
            f"{self.base_url}/api/job/{self.username}/{job_id}/settings",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        self._expect_success(res, "settings")

    def load_stores(self, job_id: str, stores: Dict[str, Any]) -> None:
        payload = {"stores": stores}
        res = requests.post(
            f"{self.base_url}/api/job/{self.username}/{job_id}/stores",
            json=payload,
            headers=self._headers(),
            timeout=60,
        )
        self._expect_success(res, "stores")

    def load_stores_with_radius(
        self, job_id: str, stores: Dict[str, Any], radius_calc: str
    ) -> None:
        payload = {"stores": stores, "radius_calc": radius_calc}
        res = requests.post(
            f"{self.base_url}/api/job/{self.username}/{job_id}/stores-with-radius",
            json=payload,
            headers=self._headers(),
            timeout=120,
        )
        self._expect_success(res, "stores-with-radius")

    def load_constraints(self, job_id: str, constraints: Dict[str, Any]) -> None:
        payload = {"constraints": constraints}
        res = requests.post(
            f"{self.base_url}/api/job/{self.username}/{job_id}/constraints",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        self._expect_success(res, "constraints")

    def load_calc(self, job_id: str, calc: str) -> None:
        payload = {"calc": calc}
        res = requests.post(
            f"{self.base_url}/api/job/{self.username}/{job_id}/calc",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        self._expect_success(res, "calc")

    def load_description(self, job_id: str, description: str | None) -> None:
        payload = {"description": description}
        res = requests.post(
            f"{self.base_url}/api/job/{self.username}/{job_id}/description",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        self._expect_success(res, "description")

    def run_job(self, job_id: str) -> None:
        res = requests.post(
            f"{self.base_url}/api/job/{self.username}/{job_id}/run",
            headers=self._headers(),
            timeout=30,
        )
        if res.status_code not in {200, 202}:
            raise ApiError(f"Run failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"Run failed: {data.get('error')}")

    def get_run_info(self, job_id: str) -> RunStatus:
        res = requests.get(
            f"{self.base_url}/api/job/{self.username}/{job_id}/run-info",
            headers=self._headers(),
            timeout=30,
        )
        if res.status_code != 200:
            raise ApiError(f"Run info failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"Run info failed: {data.get('error')}")
        info = data["data"]
        return RunStatus(
            status=info.get("status", "unknown"),
            created_at=info.get("created_at"),
            updated_at=info.get("updated_at"),
        )

    def get_job_result(self, job_id: str) -> Dict[str, Any]:
        res = requests.get(
            f"{self.base_url}/api/job/{self.username}/{job_id}/result",
            headers=self._headers(),
            timeout=30,
        )
        if res.status_code != 200:
            raise ApiError(f"Result fetch failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"Result fetch failed: {data.get('error')}")
        return data.get("data", {})

    def get_results_stats(self, job_id: str, random_name: str = None, opt_name: str = None) -> Dict[str, Any]:
        params = {}
        if random_name:
            params["random"] = random_name
        if opt_name:
            params["optimized"] = opt_name
        res = requests.get(
            f"{self.base_url}/api/job/{self.username}/{job_id}/results/stats",
            headers=self._headers(),
            params=params if params else None,
            timeout=60,
        )
        if res.status_code != 200:
            raise ApiError(f"Result stats fetch failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"Result stats fetch failed: {data.get('error')}")
        return data.get("data", {})

    def wait_for_run(self, job_id: str, timeout_sec: float, poll_interval_sec: float) -> RunStatus:
        start = time.time()
        last = None
        while time.time() - start < timeout_sec:
            last = self.get_run_info(job_id)
            if last.status in {"Complete", "Error"}:
                return last
            time.sleep(poll_interval_sec)
        raise ApiError(f"Run timed out after {timeout_sec:.0f}s (last status: {last.status if last else 'unknown'})")

    def delete_job(self, job_id: str) -> None:
        res = requests.delete(
            f"{self.base_url}/api/job/{self.username}/{job_id}",
            headers=self._headers(),
            timeout=30,
        )
        if res.status_code != 200:
            raise ApiError(f"Delete failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"Delete failed: {data.get('error')}")

    @staticmethod
    def _expect_success(res: requests.Response, name: str) -> None:
        if res.status_code != 200:
            raise ApiError(f"{name} failed ({res.status_code}): {res.text}")
        data = res.json()
        if not data.get("success"):
            raise ApiError(f"{name} failed: {data.get('error')}")
