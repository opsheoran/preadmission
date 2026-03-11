from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from app.config import Config

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)

    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.config_mgmt import config_mgmt_bp
    app.register_blueprint(config_mgmt_bp)

    from app.blueprints.transactions import transactions_bp
    app.register_blueprint(transactions_bp)

    from app.blueprints.seat_allocation import seat_allocation_bp
    app.register_blueprint(seat_allocation_bp)

    from app.blueprints.invigilator import invigilator_bp
    app.register_blueprint(invigilator_bp)

    from app.blueprints.merit_reports import merit_reports_bp
    app.register_blueprint(merit_reports_bp)

    from app.blueprints.reports import reports_bp
    app.register_blueprint(reports_bp)
    
    from app.blueprints.invigilator_reports import invigilator_reports_bp
    app.register_blueprint(invigilator_reports_bp)

    from app.blueprints.online_admission import online_admission_bp
    app.register_blueprint(online_admission_bp)

    return app
