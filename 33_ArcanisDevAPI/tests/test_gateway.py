import pytest
from arcanis_devapi.contracts import APIContract, APIVersion, APIResponse
from arcanis_devapi.gateway import APIGateway


class TestAPIGateway:
    def setup_method(self):
        self.gateway = APIGateway()
        self.gateway.initialize()

    def test_initialized(self):
        assert self.gateway._initialized

    def test_list_endpoints(self):
        endpoints = self.gateway.list_endpoints()
        assert len(endpoints) >= 10

    def test_handle_status(self):
        resp = self.gateway.handle_request("GET", "/api/v1/status")
        assert resp.status == 200

    def test_handle_not_found(self):
        resp = self.gateway.handle_request("GET", "/api/v1/nonexistent")
        assert resp.status == 404

    def test_auth_required(self):
        resp = self.gateway.handle_request("POST", "/api/v1/brain/chat")
        assert resp.status == 401

    def test_auth_bypass_for_public(self):
        resp = self.gateway.handle_request("POST", "/api/v1/brain/classify")
        assert resp.status == 200

    def test_contract_v1(self):
        contract = self.gateway.get_contract("v1")
        assert contract is not None
        assert contract.stable

    def test_stats(self):
        stats = self.gateway.get_stats()
        assert stats["routes"] >= 10

    def test_deprecated_endpoint(self):
        from arcanis_devapi.contracts import APIEndpoint
        contract = self.gateway.get_contract("v1")
        ep = APIEndpoint(path="/old", method="GET", deprecated=True)
        contract.endpoints.append(ep)
        key = f"GET:{contract.base_url}/old"
        self.gateway._routes[key] = ep
        resp = self.gateway.handle_request("GET", "/api/v1/old")
        assert resp.status == 410
