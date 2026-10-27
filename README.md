# YATRIVO — Travel Management System (Enterprise Edition)

> **Brand Identity:** *YATRIVO — Discover More. Travel Smarter.*  
> **Brand Mark:** Modern Compass Navigator Emblem  
> **Architecture:** Relational Database Architecture & Enterprise Travel Management Application  
> **Target OS:** Microsoft Windows (PowerShell)

---

## 1. Executive Summary & Enterprise Architecture

**YATRIVO** is a production-grade, enterprise-modeled Travel Booking and Trip Management System built strictly with **Python**, **Streamlit**, **MySQL 8.0**, **Pandas**, and **Plotly**.

Featuring our signature compass brand mark, YATRIVO includes an enterprise-grade **Two-Stage Authentication & Cybersecurity Engine**, an enforced **Mandatory Gatekeeper**, a **Customer Experience Portal**, an **Administrator Control Center with Peer Approval Workflows**, and a **large-scale relational dataset (2,000+ records across 60 destinations, 500 flights, 150 hotels, 100 packages, 300 bookings)**.

```
                           +-------------------------------------+
                           |            YATRIVO Portal           |
                           |       (Streamlit UI + Plotly)       |
                           +------------------+------------------+
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
        +----------v----------+                               +----------v----------+
        | Mandatory Auth Gate |                               | Server Role Guard   |
        | PBKDF2-HMAC-SHA256  |                               | Customer vs Admin   |
        | 2-Stage Admin Enrol |                               | Session State RBAC  |
        +----------+----------+                               +----------+----------+
                   |                                                     |
                   +--------------------------+--------------------------+
                                              |
                                   +----------v----------+
                                   |     database.py     |
                                   | Parameterized SQL   |
                                   | Transactions & Pool |
                                   +----------+----------+
                                              |
                        +---------------------+---------------------+
                        |                                           |
             +----------v----------+                     +----------v----------+
             |   MySQL 8.0 DB      |                     | Local CSV Datasets  |
             |   (travelnest_db)   |                     | (data/*.csv exports)|
             +---------------------+                     +---------------------+
```

---

## 2. Technology Stack & Design Compliance

| Layer | Technology | Implementation & Security Standard |
| :--- | :--- | :--- |
| **Frontend Framework** | Streamlit | Streamlit-native UI components, scoped CSS, and modern travel-tech theme (Navy `#0F172A`, Cyan `#06B6D4`, Teal `#0D9488`). |
| **Backend & Logic** | Python 3.10+ | Pure Python standard library, modular service architecture, and strict role guards. |
| **Relational DBMS** | MySQL 8.0 | MySQL 8.0 Server running on `localhost:3306`, InnoDB engine, UTF-8 MB4 charset, ACID transactions. |
| **Driver** | `mysql-connector-python` | Native binary connector using `%s` parameterized queries. |
| **Data Analytics** | Pandas & Plotly | Interactive analytics, booking trends, and CSV dataset export. |
| **Security & Auth** | `hashlib` & `secrets` | PBKDF2-HMAC-SHA256 (100,000 rounds) + 16-byte cryptographic salt + two-stage admin authorization. |

---

## 3. Cybersecurity & Access Control Architecture

### 3.1 Mandatory Authentication Gatekeeper
- Unauthenticated users cannot view or bypass customer or administrator pages.
- Access to the application is strictly blocked until authenticated via `render_auth_page()`.
- Session state is validated on the server on every interaction.

### 3.2 Two-Stage Administrator Enrollment Workflow
1. **Server Secret Verification:** When an applicant selects **Administrator Account**, they must provide the `ADMIN_ENROLLMENT_CODE` configured in the server's `.env` file (`YATRIVO_ADMIN_2026`). The secret is never exposed in the UI or client-side code.
2. **Pending Queue:** Valid token entry does **not** grant immediate administrator access. The account is created with `account_status = 'pending'`, and a request is queued in `admin_enrollment_requests`.
3. **Peer Authorization:** An existing active administrator must review the applicant's details in the **Admin Control Panel** and explicitly click **Approve Administrator**.
4. **Activation:** Only after approval is the user's `account_status` switched to `'active'` in an atomic database transaction.

### 3.3 Server-Side Role Enforcement
- Hiding sidebar links alone is insufficient; server-side guards (`is_admin()`) verify both role and active account status on page execution.
- Customers attempting to reach administrator views are immediately denied access and redirected.

---

## 4. Key Functional Modules

### 4.1 Dedicated Customer Dashboard
- Welcome greeting personalized with the customer's name.
- Global search across destinations, flights, hotels, and packages.
- Metric cards: Total Bookings, Active Trips, Total Travel Spend, Reviews Contributed.
- **My Upcoming Trips** card with itinerary dates and budget utilization.
- **Recent Booking Activity** feed with real-time status badges.
- Featured destinations and trending curated packages.

### 4.2 Administrator Control Center
- Real-time KPI metrics: Total Revenue, Total Bookings, Cancellations, Registered Customers, Active Admins.
- **Pending Administrator Approvals Tab:** One-click review, approval, or rejection of enrollment requests.
- **Executive Analytics:** Interactive Plotly charts for daily revenue trends, category share, and status distributions.
- **Catalog Management (Full CRUD):** Add, edit, and delete destinations, flight schedules, and hotel properties.
- **Booking Moderation:** Search and switch booking statuses (Confirmed, Completed, Cancelled, Pending).
- **Review Moderation:** Audit and remove inappropriate traveler reviews.
- **Database Statistics:** Real-time table record audit.

### 4.3 Integrated Travel Booking Engine
- **Destinations Explorer:** 60 global & Indian destinations with category and budget filters.
- **Flight Explorer:** 500 domestic and international routes with cabin classes and fare calculation.
- **Hotel Explorer:** 150 verified properties with star ratings and 450 room inventory options.
- **Packages & Activities:** 100 all-inclusive travel packages and 200 excursion tours.
- **My Bookings & Cancellation:** Booking reference tracking and self-service cancellation with mandatory reason logging.
- **Trip Planner & Budget Tracker:** Custom vacation planner with budget progress bar.
- **Reviews & Ratings:** Duplicate-checked traveler feedback.

---

## 5. Quick Start & Execution Guide (Windows PowerShell)

### Step 1: Open Terminal in Project Directory
```powershell
cd c:\Users\dasar\.gemini\antigravity-ide\scratch\travel_booking_system
```

### Step 2: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Run Database Setup & Verification (One Command)
```powershell
python connect_mysql.py
```
*(Prompts for your MySQL root password, verifies connection, creates `travelnest_db`, applies schema, seeds all data, and saves `.env`)*

### Step 4: Run the Automated 12-Point Test Suite
```powershell
python test_app.py
```
*Validates all 12 enterprise security, role isolation, and database criteria with 100% pass.*

### Step 5: Launch the Yatrivo Web Application
```powershell
python -m streamlit run app.py
```
The application opens in your browser at `http://localhost:8501`.

---

## 6. Pre-Seeded Demonstration Accounts (Viva Ready)

The login screen provides **One-Click Quick Evaluation Buttons** for instant presentation:

| Role | Email Address | Password | Demonstration Scope |
| :--- | :--- | :--- | :--- |
| **Chief Administrator** | `admin@yatrivo.com` | `Admin@123` | Full admin control, enrollment approvals, CRUD on catalog, booking management. |
| **Verified Customer** | `user@yatrivo.com` | `User@123` | Aarav Sharma — Customer dashboard, booking flights/hotels, trip planning, cancellations. |
| **Fallback Admin** | `admin@travelnest.com` | `Admin@123` | Secondary administrator account. |
| **Fallback Customer** | `user@travelnest.com` | `User@123` | Secondary customer account. |

---

## 7. Automated Test Suite Results (12 / 12 Scenarios Passed)

Run `python test_app.py` to verify:

1. `[PASS]` **Scenario 12:** Database connectivity verified (`mysql` backend at `localhost:3306`).
2. `[PASS]` **Scenario 1:** Customer registered and authenticated successfully.
3. `[PASS]` **Scenario 2:** Customer login redirects directly to Customer Dashboard.
4. `[PASS]` **Scenario 3:** Server-side role guard verified (Customer cannot access admin functions).
5. `[PASS]` **Scenario 4:** Admin registration queued as pending approval in database.
6. `[PASS]` **Scenario 5:** Incorrect administrator codes rejected with access denial.
7. `[PASS]` **Scenario 6:** Pending administrator account blocked from logging in.
8. `[PASS]` **Scenario 7:** Active admin approval & rejection workflow verified.
9. `[PASS]` **Scenario 8:** Approved administrator logs in and accesses Admin Dashboard.
10. `[PASS]` **Scenario 9:** Logout cleared authentication session and returned to login state.
11. `[PASS]` **Scenario 10:** Input validation (duplicate emails, password length, format) verified.
12. `[PASS]` **Scenario 11:** Existing booking, cancellation, and review workflows operating flawlessly.

---

## 8. Academic Viva Voce Technical Q&A

### Q1: How does Yatrivo prevent unauthorized administrator privilege escalation?
**Answer:** Yatrivo enforces a two-stage security protocol. During registration, selecting "Administrator" requires entering an unexposed server secret (`ADMIN_ENROLLMENT_CODE`). Furthermore, even with the secret, the account is saved in MySQL with `account_status = 'pending'`. The account is strictly prevented from logging in or calling admin functions until an existing active administrator reviews and approves the request in the Admin Control Panel.

### Q2: How is session security maintained across page refreshes in Streamlit?
**Answer:** We maintain verified user credentials in `st.session_state["user"]` and `st.session_state["is_authenticated"]`. Sensitive password hashes and salts are stripped from memory upon login. On every page execution, `is_authenticated()` and `is_admin()` perform server-side verification before rendering any view.

### Q3: How is password storage secured against rainbow tables and brute force?
**Answer:** Passwords are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and a cryptographically unique 16-byte random salt generated via `secrets.token_hex(16)`. During authentication, candidate verification uses `secrets.compare_digest` to prevent side-channel timing attacks.

### Q4: How are SQL injection vulnerabilities eliminated?
**Answer:** Every database interaction across all 11 modules utilizes parameterized queries with `%s` placeholders via `mysql.connector`. No user input is ever formatted or concatenated directly into SQL query strings.

### Q5: How is data consistency preserved during administrative approvals?
**Answer:** Account approvals and cancellations use atomic SQL transactions. If any update fails during the multi-table operation, a rollback is executed, ensuring no orphaned records exist.

---

## 9. Project Directory Structure

```
travel_booking_system/
│
├── app.py                      # Main entry point, mandatory gatekeeper & router
├── config.py                   # Environment loader & Yatrivo settings
├── database.py                 # MySQL database helper & connection engine
├── connect_mysql.py            # Automated MySQL connection & setup script
├── auth.py                     # RBAC, PBKDF2 security & admin approval workflow
├── migrate_voyanta.py          # Database schema migration script
├── seed_data.py                # Comprehensive relational dataset generator
├── test_app.py                 # Automated 12-point verification test suite
├── schema.sql                  # Normalized MySQL DDL schema (11 tables)
├── requirements.txt            # Python dependencies
├── .env                        # Local database & admin secret configuration
├── .env.example                # Configuration template
├── README.md                   # Complete documentation & viva guide
│
├── modules/
│   ├── dashboard.py            # Customer Dashboard, welcome hero & recent activity
│   ├── destinations.py         # 60 destinations catalog & details modal
│   ├── flights.py              # 500 flights explorer & booking workflow
│   ├── hotels.py               # 150 hotels explorer & room reservation
│   ├── packages.py             # 100 packages & 200 activities
│   ├── bookings.py             # User bookings history & cancellation
│   ├── trips.py                # Trip planner & budget utilization tracker
│   ├── reviews.py              # Ratings & duplicate-checked review submission
│   ├── admin.py                # Admin control center, approvals, charts & CRUD
│   └── analytics.py            # Interactive Plotly analytics & CSV report exports
│
├── utils/
│   ├── validators.py           # Email, phone, date range validation
│   ├── formatting.py           # Currency, date, stars & status badge helpers
│   └── helpers.py              # Booking reference generator & fallback images
│
├── assets/
│   ├── logo.png                # Modern compass emblem logo
│   └── logo.jpg                # High-res compass source image
│
└── data/                       # Exported CSV datasets (8 files)
    ├── destinations.csv
    ├── flights.csv
    ├── hotels.csv
    ├── packages.csv
    ├── activities.csv
    ├── bookings.csv
    ├── reviews.csv
    └── trips.csv
```
  execution process in tetminal:- 1) cd travel_booking_system
                                  2) py -m streamlit run app.py
---
*YATRIVO — Discover More. Travel Smarter. Built with Python, Streamlit, and MySQL 8.0.*
