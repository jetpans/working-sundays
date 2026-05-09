from __future__ import annotations

import argparse
import sys
from getpass import getpass
from pathlib import Path

from flask import Flask
from flask_bcrypt import Bcrypt

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from security import AuthStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update a trusted API user.")
    parser.add_argument("username", help="Username to store")
    parser.add_argument("--password", help="Password to store. If omitted, you will be prompted.")
    parser.add_argument("--force", action="store_true", help="Replace an existing stored hash.")
    args = parser.parse_args()

    password = args.password or getpass("Password: ")
    app = Flask(__name__)
    bcrypt = Bcrypt(app)
    store = AuthStore()

    user = store.add_user(args.username, password, bcrypt, force=args.force)
    print(f"Stored user {user.username} at {store.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())