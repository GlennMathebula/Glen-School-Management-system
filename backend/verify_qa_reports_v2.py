from app.main import app

print("FASTAPI APP IMPORT: OK")
print("TOTAL ROUTES:", len(app.routes))
print()
print("REPORT ROUTES:")

for route in app.routes:
    path = getattr(route, "path", "")
    if path.startswith("/api/staff/reports"):
        methods = getattr(route, "methods", None)
        method_text = ",".join(sorted(methods)) if methods else "ROUTER"
        print(method_text, path)
