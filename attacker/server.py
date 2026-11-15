"""Serve the local attacker-site demonstration on localhost:8000.

Run from the repository root:
    python attacker/server.py

Only serves static files from attacker/. No external services or packages needed.
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from functools import partial


def main():
    directory = Path(__file__).resolve().parent
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 8000), handler)
    print("Attacker demo: http://localhost:8000")
    print("Use only with the local fake bank at http://localhost:5000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping attacker demo.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
