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

### Database Flow:
```
Professor submits progress update
  → Stored Procedure `record_progress()` fires
    → INSERT into ProgressUpdates table
    → UPDATE FundAllocations.amount_spent (auto-calculated from SUM of all updates)
    → Trigger `trg_progress_insert` fires
      → INSERT into AuditLog (for audit trail)
```

---

## 📊 Analytics Dashboard — Practical Guide for Teacher

The Analytics Dashboard shows **7 advanced DBMS features** in action. Here's how to present each tab to your teacher:

### How to Access:
1. Login as any **Reviewer** (e.g., `turing@uni.edu`)
2. Click the **"📊 Analytics"** button in the top-right navbar
3. You'll see 7 tabs at the top — each demonstrates a different advanced SQL concept

### Tab-by-Tab Explanation:

#### 🏆 Tab 1: Budget Rankings (Window Functions — RANK, DENSE_RANK, PERCENT_RANK)

**What it shows:** All proposals ranked by budget amount, both overall and within each department.

**What to tell the teacher:**
> "This view uses SQL Window Functions. `RANK()` gives each proposal a rank based on budget — if two proposals have the same budget, they get the same rank and the next rank is skipped. `DENSE_RANK()` does the same but without skipping. `PERCENT_RANK()` shows where each proposal stands as a percentile. The `PARTITION BY dept_id` clause makes the ranking restart for each department, so we get both department-level and overall rankings from a single query."

**Key columns to point out:**
- **Overall Rank** — Global rank across all proposals
- **Dept Rank** — Rank within the department
- **Dense Rank** — No gaps in ranking
- **Percentile** — What percentage of proposals have a lower budget

---

#### 📈 Tab 2: Running Totals (SUM() OVER, AVG() OVER with ROWS frame)

**What it shows:** Cumulative fund allocation over time with a 3-grant moving average.

**What to tell the teacher:**
> "This uses `SUM() OVER (ORDER BY allocation_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` to calculate a running total — each row shows the total money allocated up to that point. The `PARTITION BY dept_id` version shows department-wise running totals. The `AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` calculates a 3-grant moving average, which smooths out spikes in allocation amounts."

**Key columns to point out:**
- **Cumulative Total** — Running sum of all allocations
- **Dept Cumulative** — Running sum per department
- **Running Count** — How many grants have been approved so far
- **3-Grant Moving Avg** — Average of last 3 allocations

---

#### 👤 Tab 3: Professor Analytics (ROW_NUMBER, NTILE, LAG, LEAD)

**What it shows:** Each professor's submission history with budget trends.

**What to tell the teacher:**
> "This demonstrates 4 different window functions. `ROW_NUMBER()` numbers each professor's submissions in chronological order. `NTILE(4)` divides all proposals into 4 quartiles by budget — Q1 is lowest, Q4 is highest. `LAG()` looks at the previous proposal's budget, and `LEAD()` looks at the next one, so we can calculate `budget_change` to see if a professor is requesting more or less over time."

**Key columns to point out:**
- **#** — Submission order for that professor
- **Quartile** — Q1/Q2/Q3/Q4 badge (budget tier)
- **Prev/Next Budget** — Adjacent proposal budgets
- **Change** — Green (+) or Red (-) showing budget trend

---

#### 🏛 Tab 4: Dept Stats (GROUP BY + Window RANK)

**What it shows:** Department-level aggregated statistics with rankings.

**What to tell the teacher:**
> "This combines `GROUP BY` aggregation with window functions. First, it groups proposals by department to get totals and averages. Then `RANK() OVER (ORDER BY total_requested DESC)` ranks departments by total funding requested. The percentage column shows each department's share of the overall budget using `SUM() OVER()` as the denominator."

---

#### ⏰ Tab 5: Event Scheduler (MySQL Automation)

**What it shows:** Status of MySQL's Event Scheduler and all automated database events.

**What to tell the teacher:**
> "This is pure database-level automation — no Python, no cron jobs. We use `SET GLOBAL event_scheduler = ON` to enable MySQL's built-in scheduler. Then we create 3 events:
> 1. **Auto-flag stale proposals** — Every day, proposals pending for more than 7 days automatically get marked as 'Under Review'
> 2. **Auto-close fully spent grants** — When a grant's remaining balance hits ₹0, it automatically gets marked as 'Closed'
> 3. **Daily stats snapshot** — Logs system metrics (pending count, approved count, total funding) into the audit log every day
> 
> These run entirely inside MySQL — even if the Flask app is shut down, the database keeps maintaining itself."

**Key things to point out:**
- **Scheduler Status** should show "ON"
- **3 events** should be listed with status "ENABLED"
- Show the "Last Executed" column — these actually run!

---

#### ⚡ Tab 6: Indexes (Performance Optimization)

**What it shows:** All custom indexes created on the database tables.

**What to tell the teacher:**
> "Indexes speed up queries by creating a sorted lookup structure, similar to an index in a book. We created indexes on:
> - **Foreign key columns** (e.g., `professor_id`, `dept_id`) — speeds up JOINs
> - **Filter columns** (e.g., `status`, `submission_date`) — speeds up WHERE clauses
> - **Composite index** (`reviewer_id, status`) — speeds up the specific query 'find pending proposals for reviewer X'
> 
> Without indexes, MySQL would do a full table scan for every query. With them, it can jump directly to the relevant rows."

---

#### 🔒 Tab 7: GRANT/REVOKE Security (Database-Level Access Control)

**What it shows:** 4 MySQL user roles with different permission levels.

**What to tell the teacher:**
> "We created 4 separate MySQL users, each with restricted permissions:
> 1. **unigrant_professor** — Can only SELECT and INSERT on Proposals (cannot delete or modify funds)
> 2. **unigrant_reviewer** — Can SELECT + UPDATE proposals, INSERT approvals and fund allocations
> 3. **unigrant_admin** — Full ALL PRIVILEGES on the entire database
> 4. **unigrant_auditor** — SELECT only (read-only, for auditing)
> 
> This is the Principle of Least Privilege — each user only gets the minimum permissions needed for their role. Even if a professor account is compromised, they cannot delete data or change fund allocations."

**What to point out:**
- Each card shows the actual `GRANT` SQL statements
- Explain that these are real MySQL users that can be used to connect to the database
- Show that professor cannot DELETE, reviewer cannot DROP, auditor cannot INSERT

---

### Quick Demo Flow for Teacher:

1. Open the app → Login as Professor (`raj@uni.edu`) → Submit a proposal
2. Login as Reviewer (`turing@uni.edu`) → Approve it → Show the audit log updating in real-time
3. Login back as Professor → Scroll to Spending Tracker → Add a progress update with a document
4. Show the spending bar increase and the history timeline
5. From Reviewer dashboard → Click "📊 Analytics" → Walk through each of the 7 tabs
6. End with the Security tab to show database-level access control
