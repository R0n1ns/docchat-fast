import os
from main import app, db
from models import User

def init_db():
    """
    Initialize the database and create admin user if not exists
    """
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin user exists
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            # Create admin user
            admin = User(
                email=admin_email,
                full_name='Admin User',
                role='admin',
                is_active=True
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
            
            db.session.add(admin)
            db.session.commit()
            
            print(f"Admin user created with email: {admin_email}")
        else:
            print(f"Admin user already exists with email: {admin_email}")

if __name__ == "__main__":
    init_db()