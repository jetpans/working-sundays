"""
Swagger API documentation configuration using Flasgger.
Loads OpenAPI spec from external swagger.yml file.
"""

import os
from flasgger import Swagger


def setup_swagger(app):
    """
    Initialize Swagger/OpenAPI documentation for the Flask app.
    Loads spec from swagger.yml file in the same directory.

    Args:
        app: Flask application instance

    Returns:
        Swagger instance
    """
    # Get the directory where this script is located
    docs_dir = os.path.dirname(os.path.abspath(__file__))
    swagger_file = os.path.join(docs_dir, "swagger.yml")

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda x: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs",
    }

    # Load the swagger spec from file
    swagger = Swagger(
        app,
        config=swagger_config,
        template_file=swagger_file,

    )

    return swagger
