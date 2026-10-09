from app import create_app

app = create_app()

print("\n===== REGISTERED ROUTES =====")
print(app.url_map)
print("=============================\n")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)