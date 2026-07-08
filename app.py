 # Khởi động Flask
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = "restaurant_secret_key_2026"

# ==========================
# Import Blueprints
# ==========================
from routes.auth import auth_bp
from routes.waiter import waiter_bp
from routes.kitchen import kitchen_bp
from routes.cashier import cashier_bp
from routes.admin import admin_bp

# ==========================
# Register Blueprints
# ==========================
app.register_blueprint(auth_bp)
app.register_blueprint(waiter_bp)
app.register_blueprint(kitchen_bp)
app.register_blueprint(cashier_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True)
  

