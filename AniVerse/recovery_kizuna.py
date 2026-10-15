
import json
import os
from pathlib import Path

import django
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load the Django project settings.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AniVerse.settings")
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection

BACKUP_FILE = BASE_DIR / "recovery_with_ids.json"

CONTENT_MODELS = [
    ("Posts", "Post"),
    ("Feeds_section", "Story"),
    ("Feeds_section", "Reel"),
    ("Profile", "Highlight"),
    ("Profile", "HighlightItem"),
]

def main():
    print("\n=== KIZUNA SAFE RESTORE CHECK ===")
    print("Database engine:", connection.vendor)
    print("Backup file:", BACKUP_FILE)

    if connection.vendor != "postgresql":
        print("\nSTOP: Django is not connected to PostgreSQL.")
        print("This check is intended for the Render database.")
        return

    if not BACKUP_FILE.exists():
        print("\nSTOP: Recovery file was not found.")
        print("Expected:", BACKUP_FILE)
        return

    with BACKUP_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    print("Backup records:", len(records))

    User = get_user_model()
    print("\nCurrent users:")
    for user in User.objects.order_by("id"):
        print(
            f"  ID={user.id}, username={user.username!r}, "
            f"active={user.is_active}"
        )

    print("\nCurrent content counts:")
    all_empty = True

    for app_label, model_name in CONTENT_MODELS:
        model = apps.get_model(app_label, model_name)
        count = model.objects.count()
        print(f"  {app_label}.{model_name}: {count}")

        if count:
            all_empty = False

    old_user_records = [
        item for item in records
        if item.get("model") == "auth.user"
    ]
    old_post_records = [
        item for item in records
        if item.get("model") == "Posts.post"
    ]
    old_story_records = [
        item for item in records
        if item.get("model") == "Feeds_section.story"
    ]
    old_reel_records = [
        item for item in records
        if item.get("model") == "Feeds_section.reel"
    ]

    print("\nOriginal backup counts:")
    print("  Users:", len(old_user_records))
    print("  Posts:", len(old_post_records))
    print("  Stories:", len(old_story_records))
    print("  Reels:", len(old_reel_records))

    current_account = User.objects.filter(
        email__iexact="skraffe446@gmail.com"
    ).first()

    print("\nExisting account match:")
    if current_account:
        print(
            f"  Found ID={current_account.id}, "
            f"username={current_account.username!r}"
        )
    else:
        print("  STOP: Existing account was not found by email.")

    if all_empty and current_account:
        print("\nPREVIEW CHECK PASSED.")
        print("No database records were changed.")
    else:
        print("\nSTOP: Review the counts and account match before proceeding.")
        print("No database records were changed.")


if __name__ == "__main__":
    main()
