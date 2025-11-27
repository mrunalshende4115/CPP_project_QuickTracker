from webapp.application import application
import os

# Optional: if you want to run locally
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    application.run(host="0.0.0.0", port=port)
