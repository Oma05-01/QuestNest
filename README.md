## 🏢 QuestNest
A context-aware, multi-tenant PropTech platform empowering seamless operational switching between personal tenant hubs and corporate property management portfolios.

## ✨ Architectural Highlights
* Multi-Tenant Workspace Engine: Unlike traditional SaaS platforms that lock users into rigid silos, QuestNest utilizes a dynamic Workspace and Membership relationship matrix. Users can belong to multiple workspaces with distinct operational roles.

* Granular Role-Based Access Control (RBAC): Tiered permissions (Owner, Admin, Manager, Member) safeguard sensitive financial ledgers, lease files, and escrow workflows.

* Unified Auth & Onboarding Wizard: A frictionless authentication gate separates user creation from workspace provisioning, automatically routing new sign-ups into the correct organizational context.

* High-Performance ASGI Backend: Powered by Django 6.0 and Daphne, ensuring asynchronous capability and low-latency API endpoints for real-time asset tracking.

* Context-Driven Frontend: React 18 state management (WorkspaceContext) instantly reacts to workspace switching, re-skinning layouts, navigation menus, and data pipes on the fly.

## 🛠️ Tech Stack
**Backend**
* Framework: Django 6.0 (ASGI / Daphne)

* API Layer: Django REST Framework (DRF)

* Database: PostgreSQL

* Authentication: JWT (JSON Web Tokens)

* Email Service: Resend (via Django Anymail)

**Frontend**
* Library: React 18

* Bundler: Vite

* Styling: Tailwind CSS v4 (with custom @theme utilities)

* Routing: React Router v6

## 📊 Database Schema Overview
The core data architecture centers on relational multi-tenancy, bridging users to workspaces securely through an active membership mapping:

Plaintext
```User [1] <---> [*] Membership [*] <---> [1] Workspace```

* User: Base authentication entity storing baseline credentials and verification status.

* Workspace: Represents either an individual personal tenant hub or a multi-unit business property management portfolio.

* Membership: The pivotal join table binding users to workspaces while assigning explicit roles (owner, admin, manager, member) and active status flags.

## 🚀 Local Development Setup
**1. Clone the Repository**
Bash
```
git clone https://github.com/Oma05-01/QuestNest.git
cd QuestNest
```

**2. Backend Setup (Django)**
Bash
```
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Start the Daphne ASGI server
python manage.py runserver

```
(The backend will be live at [http://127.0.0.1:8000](http://127.0.0.1:8000))

**3. Frontend Setup (React/Vite)**
Open a separate terminal window for the client:

Bash
```
# Navigate to your frontend directory
cd frontend

# Install packages
npm install

# Start the Vite development server
npm run dev
```
(The frontend will be live at http://localhost:5173)

## 🔐 Environment Variables
Create a .env file in your root backend folder:

**Code snippet**
```
SECRET_KEY=your_django_secret_key_here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
RESEND_API_KEY=re_your_resend_api_key_here
```

(Tip: For local testing without an active Resend API key, you can fall back to Django's console email backend by setting EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' in your settings).
