from flask import Flask

# Initialize the Flask application
app: Flask = Flask(__name__)


@app.route("/")
def health_check() -> str:
    """
    Root endpoint serving as a basic health check for network connectivity.

    Returns:
        str: A simple confirmation message that the server is active.
    """
    return "Servidor Activo"


if __name__ == "__main__":
    # Binding to 0.0.0.0 exposes the server to the local network (LAN).
    # Port 5000 is the default Flask development port.
    app.run(host="0.0.0.0", port=5000, debug=True)
