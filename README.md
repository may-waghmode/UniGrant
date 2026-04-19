# UniGrant - University Grant Management System

UniGrant is a modern Database Management System (DBMS) web application built with Python, Flask, and MySQL. It is designed to streamline the process of submitting, reviewing, and tracking university grant proposals and fund allocations.

## 🚀 Features

- **Professor Flow:** Professors can log in, submit grant proposals, upload proposal PDF documents, and track their proposal status.
- **Reviewer Flow:** Secure access for reviewers to evaluate pending proposals, make approval/rejection decisions, allocate funds, and leave remarks.
- **Grant & Fund Management:** Track allocated amounts, amount spent, and automatically calculate remaining balances.
- **Automated Audit Logging:** Uses MySQL triggers to maintain a comprehensive audit log of insertions and status changes for accountability.
- **Department Summaries:** Real-time views of department-wise proposal statistics and funding amounts.

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask framework
- **Database:** MySQL (relational database with usage of Triggers, Stored Procedures, and Views)
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
   - *This will drop any existing `unigrant` databases and create a fresh one with all tables, stored procedures, triggers, views, and seed data.*

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
- **Foreign Keys:** Maintains referential integrity between Professors, Departments, Proposals, and Reviewers.
- **Stored Procedures:** Example methods like `submit_proposal`, `approve_proposal`, and `reject_proposal` handle complex mutiple-table inserts securely.
- **Triggers:** Automated Audit Logs (`trg_proposal_insert`, `trg_proposal_status`, etc.) track when critical actions occur in the DB.
- **Views:** Virtual tables like `pending_proposals`, `department_summary`, and `active_grants` simplify large data queries.

## 👥 Usage Guide (Seed Data)

The `workbench_setup.sql` script loads the database with some seed data so you can test the system immediately:
- **Reviewer Emails for login:** `turing@uni.edu`, `hopper@uni.edu`, `curie@uni.edu`
- To login as a Professor, you simply enter your email. If it doesn't exist, the system creates a profile for you on the spot!
