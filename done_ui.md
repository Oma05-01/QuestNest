🔐 Authentication & Accounts
These views handle the entry flow of the platform, using a dynamic, email-first logic.

CheckEmailView

UI Component: Login.jsx (Step 1)

Function: Determines if a user should proceed to the password screen or the registration flow.

LoginView

UI Component: Login.jsx (Step 2)

Function: Authenticates existing users and stores JWT tokens and user metadata in local storage.

RegisterView

UI Component: Login.jsx (Step 3)

Function: Collects name and password for new users and triggers the verification email.

VerifyEmailView

UI Component: VerifyEmail.jsx

Function: A standalone page that handshakes with the backend to activate an account via the email link.

📊 Dashboard & Metrics
These views provide the role-based experience for the different users on the platform.

TenantDashboardView

UI Component: TenantDashboard.jsx

Function: Displays rent paid, next due date, and active lease count for tenants.

LandlordDashboardView

UI Component: LandlordDashboard.jsx

Function: Summarizes total revenue, active tenant count, and current escrow balances.

Overview (Routing)

UI Component: Overview.jsx

Function: Acts as a "Traffic Controller" that reads the JWT role and renders either the Tenant or Landlord dashboard.

📝 Lists & Activity
These views populate the tables and utility components within the dashboards.

TenantPaymentHistoryView

UI Component: TenantPaymentHistory.jsx

Function: A detailed transaction table showing dates, amounts, and statuses for rent payments.

LandlordTenanciesView

UI Component: LandlordTenancies.jsx

Function: A management table for landlords to track tenant names, property units, and payment schedules.

NotificationInboxView & MarkNotificationReadView

UI Component: NotificationBell.jsx

Function: A real-time dropdown in the top navigation bar that displays updates and allows users to mark them as read.