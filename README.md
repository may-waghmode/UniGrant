# UniGrant - University Grant Management System

UniGrant is a modern Database Management System (DBMS) web application built with Python, Flask, and MySQL. It is designed to streamline the process of submitting, reviewing, and tracking university grant proposals and fund allocations.

## 🚀 Features

- **Professor Flow:** Professors can log in, submit grant proposals, upload proposal PDF documents, and track their proposal status.
- **Progress & Spending Tracker:** After a proposal is approved, professors can submit progress updates with proof documents (invoices/receipts), track category-wise spending, and monitor budget utilization in real-time.
- **Reviewer Flow:** Secure access for reviewers to evaluate pending proposals, make approval/rejection decisions, allocate funds, and leave remarks.
- **Grant & Fund Management:** Track allocated amounts, amount spent, and automatically calculate remaining balances.
- **Automated Audit Logging:** Uses MySQL triggers to maintain a comprehensive audit log of insertions, status changes, and spending updates for accountability.
- **Department Summaries:** Real-time views of department-wise proposal statistics and funding amounts.
- **Advanced Analytics Dashboard:** Window functions, event scheduler monitoring, index info, and GRANT/REVOKE security overview.

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask framework
- **Database:** MySQL (relational database with usage of Triggers, Stored Procedures, Views, Window Functions, Event Scheduler, GRANT/REVOKE)
- **Frontend:** HTML, CSS, Jinja2 Templates
- **Libraries:** `mysql-connector-python`

## 📋 Prerequisites

Before running the project, ensure you have the following installed:

1. [Python 3.x](https://www.python.org/downloads/)
2. [MySQL Server & MySQL Workbench](https://dev.mysql.com/downloads/)

## ⚙️ Setup Instructions

### 1. Database Setup

1. Open **MySQL Workbench**.
2. Open the `workbench_setup.sql` file included in the project directory.
3. Select all the code (`Ctrl+A`) and execute it (`Ctrl+Enter` or click the lightning bolt icon).
   - *This will drop any existing `unigrant` databases and create a fresh one with all tables, stored procedures, triggers, views, events, and seed data.*

### 2. Application Setup

1. Open your terminal and navigate to the project directory:
   ```bash
   cd path/to/uni_grant
   ```
2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configure Database Credentials

Open `config.py` and update the database configuration to match your local MySQL credentials. Specifically, ensure the `DB_PASSWORD` matches your local MySQL root password:

```python
class Config:
    # ── MySQL Database ───────────────────────────────────────
    DB_HOST     = 'localhost'
    DB_USER     = 'root'
    DB_PASSWORD = 'YOUR_MYSQL_PASSWORD' # <-- Update this
    DB_NAME     = 'unigrant'
    DB_PORT     = 3306
```

### 4. TO Run the Application

Start the Flask development server:

```bash
python app.py
```

The application will be accessible in your web browser at `http://127.0.0.1:5000/`.

## 🗄️ Database Schema Highlights

The system leverages several advanced database concepts:
- **Foreign Keys:** Maintains referential integrity between Professors, Departments, Proposals, ProgressUpdates, and Reviewers.
- **Stored Procedures:** `submit_proposal`, `approve_proposal`, `reject_proposal`, and `record_progress` handle complex multi-table operations securely.
- **Triggers:** Automated Audit Logs (`trg_proposal_insert`, `trg_proposal_status`, `trg_fund_insert`, `trg_progress_insert`) track when critical actions occur in the DB.
- **Views:** Virtual tables like `pending_proposals`, `department_summary`, `active_grants`, and window function views simplify complex queries.
- **Window Functions:** `RANK()`, `DENSE_RANK()`, `PERCENT_RANK()`, `ROW_NUMBER()`, `NTILE()`, `LAG()`, `LEAD()`, `SUM() OVER`, `AVG() OVER` used across 4 analytics views.
- **Event Scheduler:** Automated daily tasks — flag stale proposals after 7 days, auto-close fully spent grants, daily stats snapshots.
- **GRANT/REVOKE Security:** 4 MySQL user roles (professor, reviewer, admin, auditor) with different permission levels.

## 👥 Usage Guide (Seed Data)

The `workbench_setup.sql` script loads the database with some seed data so you can test the system immediately:
- **Reviewer Emails for login:** `turing@uni.edu`, `hopper@uni.edu`, `curie@uni.edu`
- To login as a Professor, you simply enter your email. If it doesn't exist, the system creates a profile for you on the spot!

---

## 💰 Progress Tracking & Spending Feature (Step-by-Step)

This feature allows professors to track how they are spending approved grant money, with proof documents.

### How It Works:

1. **Login as Professor** → Go to `http://127.0.0.1:5000/`, enter any email (e.g., `raj@uni.edu`)
2. **Submit a Proposal** → Fill in the form on the left (title, department, reviewer, budget, description) and click "Submit Proposal"
3. **Login as Reviewer** → Go back to login, select the reviewer who was assigned, click "Login as Reviewer"
4. **Approve the Proposal** → On the reviewer dashboard, find the proposal, set the approve amount, and click "✓ Approve"
5. **Login back as Professor** → Go back to login, enter the same professor email
6. **Scroll down to "Spending & Progress Tracker"** → You'll see the approved grant with:
   - A **spending progress bar** showing how much of the budget is utilized
   - **Spent / Remaining / Allocated** amounts
   - A **"📝 Add Update"** button
7. **Click "📝 Add Update"** → A modal opens where you fill in:
   - **Update Title** (e.g., "Purchased Lab Equipment")
   - **Amount Spent** (e.g., ₹50,000)
   - **Category** (Equipment / Travel / Personnel / Materials / Software / Other)
   - **Description** of what was done
   - **Proof Document** — upload an invoice, receipt, or any document as proof
8. **Click "📤 Submit Progress Update"** → The progress is recorded:
   - ✅ Amount is auto-added to `FundAllocations.amount_spent` via stored procedure
   - ✅ Progress bar updates in real-time
   - ✅ Entry appears in the audit log via trigger
9. **Click "📜 History"** → Opens a modal showing:
   - **Spending Overview** with utilization percentage
   - **Category Breakdown** (e.g., Equipment: ₹50K, Travel: ₹20K)
   - **Update Timeline** with dates, categories, amounts, and downloadable proof documents


