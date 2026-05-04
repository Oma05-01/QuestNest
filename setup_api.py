import os

# List of app names extracted from your urlpatterns
apps = [
    "accounts", "assets", "leases", "rentals", "payments", "wallet",
    "escrow", "notifications", "operations", "organisations",
    "verification", "user_messages", "dashboards"
]


def create_api_structure():
    for app in apps:
        # Define the path to the api directory
        api_path = os.path.join(app, "api")

        try:
            # Create the directories (parents=True handles the app folder too)
            os.makedirs(api_path, exist_ok=True)

            # Create the empty files
            for filename in ["serializers.py", "views.py", "urls.py"]:
                file_path = os.path.join(api_path, filename)
                with open(file_path, 'w') as f:
                    # Optional: Add a basic comment to each file
                    f.write(f"# {filename} for {app} api\n")

            print(f"✅ Created structure for: {app}")
        except Exception as e:
            print(f"❌ Failed to create {app}: {e}")


if __name__ == "__main__":
    create_api_structure()
