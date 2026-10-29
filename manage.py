"""CIG Management CLI."""

import sys
import getpass
import argparse
from app import create_app
from app.extensions import db
from app.models.user import User, AdminInvitation, PasswordResetToken

app = create_app()


def init_db():
    """Create all database tables."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")


def create_admin(name, email, password, age_range="26-35", city="Malang"):
    """Create a new administrator."""
    with app.app_context():
        email = email.lower().strip()
        existing = User.query.filter_by(email=email).first()

        if existing:
            if existing.is_admin:
                print(f"Error: User {email} is already an administrator.")
                return False
            existing.role = 'admin'
            db.session.commit()
            print(f"Success: Existing user {email} promoted to administrator.")
            return True

        admin = User(
            full_name=name.strip(),
            email=email,
            role='admin',
            age_range=age_range,
            city=city.strip(),
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Success: Administrator {name} ({email}) created successfully.")
        return True


def create_user(name, email, password, age_range="18-25", city="Malang"):
    """Create a standard user."""
    with app.app_context():
        email = email.lower().strip()
        existing = User.query.filter_by(email=email).first()

        if existing:
            print(f"Error: User {email} already exists.")
            return False

        user = User(
            full_name=name.strip(),
            email=email,
            role='user',
            age_range=age_range,
            city=city.strip(),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Success: User {name} ({email}) created successfully.")
        return True


def list_users():
    """List all registered users."""
    with app.app_context():
        users = User.query.all()
        print(f"\nTotal users: {len(users)}")
        print(f"{'ID':<4} {'Role':<8} {'Name':<25} {'Email':<30} {'City':<15}")
        print("-" * 85)
        for u in users:
            print(f"{u.id:<4} {u.role:<8} {u.full_name[:24]:<25} {u.email[:29]:<30} {u.city[:14]:<15}")
        print()


def main():
    parser = argparse.ArgumentParser(description="CIG Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init-db
    subparsers.add_parser("init-db", help="Initialize database tables")

    # create-admin
    admin_parser = subparsers.add_parser("create-admin", help="Create an administrator account")
    admin_parser.add_argument("--name", required=True, help="Full name")
    admin_parser.add_argument("--email", required=True, help="Email address")
    admin_parser.add_argument("--password", required=False, default=None, help="Password (optional, prompts securely if omitted)")
    admin_parser.add_argument("--age-range", default="26-35", help="Age range (default: 26-35)")
    admin_parser.add_argument("--city", default="Malang", help="City (default: Malang)")

    # create-user
    user_parser = subparsers.add_parser("create-user", help="Create a standard user account")
    user_parser.add_argument("--name", required=True, help="Full name")
    user_parser.add_argument("--email", required=True, help="Email address")
    user_parser.add_argument("--password", required=False, default=None, help="Password (optional, prompts securely if omitted)")
    user_parser.add_argument("--age-range", default="18-25", help="Age range (default: 18-25)")
    user_parser.add_argument("--city", default="Malang", help="City (default: Malang)")

    # list-users
    subparsers.add_parser("list-users", help="List all users")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "create-admin":
        password = args.password
        if not password:
            password = getpass.getpass("Masukkan kata sandi administrator: ")
            confirm = getpass.getpass("Konfirmasi kata sandi administrator: ")
            if password != confirm:
                print("Error: Konfirmasi kata sandi tidak cocok.")
                sys.exit(1)
            if len(password) < 8:
                print("Error: Kata sandi minimal 8 karakter.")
                sys.exit(1)
        create_admin(args.name, args.email, password, args.age_range, args.city)
    elif args.command == "create-user":
        password = args.password
        if not password:
            password = getpass.getpass("Masukkan kata sandi pengguna: ")
            confirm = getpass.getpass("Konfirmasi kata sandi pengguna: ")
            if password != confirm:
                print("Error: Konfirmasi kata sandi tidak cocok.")
                sys.exit(1)
            if len(password) < 8:
                print("Error: Kata sandi minimal 8 karakter.")
                sys.exit(1)
        create_user(args.name, args.email, password, args.age_range, args.city)
    elif args.command == "list-users":
        list_users()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
