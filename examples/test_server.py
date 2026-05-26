"""Simple local test API server for apix demo."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

USERS = [
    {"id": 1, "name": "Alice Johnson", "username": "alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob Smith", "username": "bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie Brown", "username": "charlie", "email": "charlie@example.com"},
]

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.path == "/users":
            self.wfile.write(json.dumps(USERS).encode())
        elif self.path.startswith("/users/"):
            uid = int(self.path.split("/")[-1])
            user = next((u for u in USERS if u["id"] == uid), None)
            self.wfile.write(json.dumps(user or {"error": "not found"}).encode())
        else:
            self.wfile.write(json.dumps({"message": "pong"}).encode())

    def log_message(self, format, *args):
        pass  # silence logs

server = HTTPServer(("0.0.0.0", 9999), Handler)
print("Test API server running on http://localhost:9999")
server.serve_forever()
