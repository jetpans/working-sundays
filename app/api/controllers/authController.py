from __future__ import annotations

from datetime import timedelta

from flask import request
from flask_jwt_extended import create_access_token, get_jwt_identity

from config import AppConfig
from security import AuthStore, api_user_required


class AuthController:
    def __init__(self, app, bcrypt):
        self.app = app
        self.bcrypt = bcrypt
        self.store = AuthStore()
        self.register_routes()

    def register_routes(self):
        @self.app.post("/api/auth/login")
        def login():
            body = request.get_json(silent=True) or {}
            username = (body.get("username") or "").strip()
            password = body.get("password") or ""

            if not username or not password:
                return {"success": False, "error": "username and password are required"}, 400

            user = self.store.authenticate(username, password, self.bcrypt)
            if not user:
                return {"success": False, "error": "invalid credentials"}, 401

            access_token = create_access_token(
                identity=username,
                additional_claims={"role": "user"},
                expires_delta=timedelta(hours=AppConfig.JWT_ACCESS_TOKEN_EXPIRES_HOURS),
            )

            return {
                "success": True,
                "data": {
                    "user": {"username": username},
                    "access_token": access_token,
                },
            }, 200

        @self.app.get("/api/auth/me")
        @api_user_required(match_username=False)
        def me():
            return {"success": True, "data": {"username": get_jwt_identity()}}, 200

        @self.app.post("/api/auth/logout")
        @api_user_required(match_username=False)
        def logout():
            """
            Logout endpoint placeholder
            ---
            tags:
              - Authentication
            security:
              - Bearer: []
            responses:
              200:
                description: Logout acknowledged client-side
              401:
                description: Unauthorized
            """
            return {"success": True, "data": "logout handled client-side"}, 200
