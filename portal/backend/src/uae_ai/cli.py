"""Explicit administrative operations. No network deployment or default credentials."""
import argparse
from pathlib import Path
import sqlite3
from sqlalchemy import select
from uae_ai.core.config import Settings
from uae_ai.db import Base, Tenant, User, make_database
from uae_ai.seed import seed


def main():
    parser = argparse.ArgumentParser(description="Nawa workspace administration")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("seed", help="Seed local synthetic data after migrations")
    commands.add_parser("adopt-local-schema", help="Validate and stamp an existing unversioned local baseline")
    provision = commands.add_parser("provision-user", help="Provision a verified OIDC subject membership")
    for name in ["tenant", "tenant-name", "name", "email", "subject"]:
        provision.add_argument("--"+name, required=True)
    provision.add_argument("--role", choices=["analyst", "reviewer", "requester", "auditor", "admin"], required=True)
    backup = commands.add_parser("backup-sqlite", help="Consistent local DB backup; copy uploads separately")
    backup.add_argument("destination")
    args = parser.parse_args()
    settings = Settings()
    settings.validate()
    engine, factory = make_database(settings.database_url)
    if args.command == "adopt-local-schema":
        if settings.app_env not in {"local", "test"}:
            parser.error("Schema adoption is restricted to an inspected local baseline")
        from uae_ai.core.migrations import adopt_local
        adopt_local(engine, settings.database_url)
        print("Existing local schema matched the baseline and was versioned. No records were removed.")
        return
    if args.command == "backup-sqlite":
        if not settings.database_url.startswith("sqlite:///"):
            parser.error("Use PostgreSQL native backup tools for a PostgreSQL database")
        destination = Path(args.destination)
        if destination.exists():
            parser.error("Refusing to overwrite an existing backup")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(settings.database_url.removeprefix("sqlite:///")) as source, sqlite3.connect(destination) as target:
            source.backup(target)
        print("Database backup created. Separately copy versioned uploads with their retention controls.")
        return
    with factory() as db:
        if args.command == "seed":
            if settings.app_env not in {"local", "test"}:
                parser.error("Synthetic demo seeding is disabled in production")
            seed(db, settings)
            print("Synthetic data is ready; existing data was preserved.")
        elif args.command == "provision-user":
            if not settings.oidc_issuer:
                parser.error("Set the trusted OIDC_ISSUER before provisioning a subject")
            if not db.get(Tenant, args.tenant):
                db.add(Tenant(id=args.tenant, name=args.tenant_name))
            subject = settings.oidc_issuer + "|" + args.subject
            if db.scalar(select(User).where(User.oidc_subject == subject)):
                parser.error("This OIDC subject is already provisioned")
            db.add(User(tenant_id=args.tenant, name=args.name, email=args.email, role=args.role, oidc_subject=subject, active=True, preferences={"language":"en","digest":True}))
            db.commit()
            print("Membership provisioned for the exact trusted issuer/subject.")


if __name__ == "__main__":
    main()
