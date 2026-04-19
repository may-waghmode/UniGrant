-- ============================================================
-- UniGrant — Complete Database Setup
-- Run this ENTIRE script in MySQL Workbench (Select All → Execute)
-- ============================================================

DROP DATABASE IF EXISTS unigrant;
CREATE DATABASE unigrant;
USE unigrant;

-- ═══════════════════════════════════════════════════════════
-- TABLES
-- ═══════════════════════════════════════════════════════════

CREATE TABLE Departments (
    dept_id   INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Professors (
    professor_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(100) NOT NULL,
    email        VARCHAR(100) UNIQUE,
    dept_id      INT NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES Departments(dept_id)
);

CREATE TABLE Reviewers (
    reviewer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    designation VARCHAR(50),
    email       VARCHAR(100) UNIQUE
);

CREATE TABLE Proposals (
    proposal_id      INT AUTO_INCREMENT PRIMARY KEY,
    title            VARCHAR(200) NOT NULL,
    description      TEXT,
    budget_requested DECIMAL(12,2) NOT NULL,
    status           ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    submission_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    professor_id     INT NOT NULL,
    reviewer_id      INT,
    dept_id          INT NOT NULL,
    pdf_filename     VARCHAR(255),
    pdf_data         LONGBLOB,
    FOREIGN KEY (professor_id) REFERENCES Professors(professor_id),
    FOREIGN KEY (reviewer_id)  REFERENCES Reviewers(reviewer_id),
    FOREIGN KEY (dept_id)      REFERENCES Departments(dept_id)
);

CREATE TABLE Approvals (
    approval_id   INT AUTO_INCREMENT PRIMARY KEY,
    decision      ENUM('Approved','Rejected') NOT NULL,
    remarks       TEXT,
    decision_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    proposal_id   INT NOT NULL,
    reviewer_id   INT NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES Proposals(proposal_id),
    FOREIGN KEY (reviewer_id) REFERENCES Reviewers(reviewer_id)
);

CREATE TABLE FundAllocations (
    allocation_id    INT AUTO_INCREMENT PRIMARY KEY,
    amount_allocated DECIMAL(12,2) NOT NULL,
    amount_spent     DECIMAL(12,2) DEFAULT 0.00,
    amount_remaining DECIMAL(12,2) AS (amount_allocated - amount_spent) STORED,
    allocation_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    proposal_id      INT NOT NULL,
    FOREIGN KEY (proposal_id) REFERENCES Proposals(proposal_id)
);

CREATE TABLE AuditLog (
    log_id     INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50)  NOT NULL,
    action     VARCHAR(50)  NOT NULL,
    record_id  INT          NOT NULL,
    old_value  VARCHAR(255),
    new_value  VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════
-- STORED PROCEDURES
-- ═══════════════════════════════════════════════════════════

DELIMITER $$

CREATE PROCEDURE submit_proposal(
    IN p_title VARCHAR(200),
    IN p_description TEXT,
    IN p_budget DECIMAL(12,2),
    IN p_prof_id INT,
    IN p_dept_id INT
)
BEGIN
    INSERT INTO Proposals (title, description, budget_requested, professor_id, dept_id)
    VALUES (p_title, p_description, p_budget, p_prof_id, p_dept_id);
    SELECT LAST_INSERT_ID() AS new_id, 'Proposal submitted successfully' AS message;
END$$

CREATE PROCEDURE approve_proposal(
    IN p_proposal_id INT,
    IN p_reviewer_id INT,
    IN p_allocated   DECIMAL(12,2),
    IN p_remarks     TEXT
)
BEGIN
    UPDATE Proposals SET status = 'Approved' WHERE proposal_id = p_proposal_id;
    INSERT INTO Approvals (decision, remarks, proposal_id, reviewer_id)
    VALUES ('Approved', p_remarks, p_proposal_id, p_reviewer_id);
    INSERT INTO FundAllocations (amount_allocated, proposal_id)
    VALUES (p_allocated, p_proposal_id);
    SELECT 'Proposal approved and funds allocated' AS message;
END$$

CREATE PROCEDURE reject_proposal(
    IN p_proposal_id INT,
    IN p_reviewer_id INT,
    IN p_remarks     TEXT
)
BEGIN
    UPDATE Proposals SET status = 'Rejected' WHERE proposal_id = p_proposal_id;
    INSERT INTO Approvals (decision, remarks, proposal_id, reviewer_id)
    VALUES ('Rejected', p_remarks, p_proposal_id, p_reviewer_id);
    SELECT 'Proposal rejected' AS message;
END$$

DELIMITER ;

-- ═══════════════════════════════════════════════════════════
-- TRIGGERS (Audit Logging)
-- ═══════════════════════════════════════════════════════════

DELIMITER $$

CREATE TRIGGER trg_proposal_insert
AFTER INSERT ON Proposals FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (table_name, action, record_id, new_value)
    VALUES ('Proposals', 'INSERT', NEW.proposal_id, CONCAT('New: ', NEW.title));
END$$

CREATE TRIGGER trg_proposal_status
AFTER UPDATE ON Proposals FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO AuditLog (table_name, action, record_id, old_value, new_value)
        VALUES ('Proposals', 'STATUS_CHANGE', NEW.proposal_id, OLD.status, NEW.status);
    END IF;
END$$

CREATE TRIGGER trg_fund_insert
AFTER INSERT ON FundAllocations FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (table_name, action, record_id, new_value)
    VALUES ('FundAllocations', 'INSERT', NEW.allocation_id,
            CONCAT('Allocated ₹', NEW.amount_allocated));
END$$

DELIMITER ;

-- ═══════════════════════════════════════════════════════════
-- VIEWS
-- ═══════════════════════════════════════════════════════════

CREATE VIEW pending_proposals AS
SELECT p.proposal_id, p.title, p.budget_requested, p.submission_date,
       pr.full_name AS professor_name, d.dept_name AS department
FROM   Proposals p
JOIN   Professors pr ON p.professor_id = pr.professor_id
JOIN   Departments d ON p.dept_id = d.dept_id
WHERE  p.status = 'Pending';

CREATE VIEW department_summary AS
SELECT d.dept_name,
       COUNT(p.proposal_id) AS total_proposals,
       COALESCE(SUM(fa.amount_allocated), 0) AS total_funding,
       COALESCE(SUM(fa.amount_spent), 0) AS total_spent
FROM   Departments d
LEFT JOIN Proposals p ON d.dept_id = p.dept_id
LEFT JOIN FundAllocations fa ON p.proposal_id = fa.proposal_id
GROUP BY d.dept_id, d.dept_name;

CREATE VIEW active_grants AS
SELECT fa.allocation_id, p.title, p.proposal_id,
       fa.amount_allocated, fa.amount_spent, fa.amount_remaining,
       ROUND((fa.amount_spent / fa.amount_allocated) * 100, 1) AS utilization_pct,
       fa.allocation_date, pr.full_name AS professor_name, d.dept_name
FROM   FundAllocations fa
JOIN   Proposals p  ON fa.proposal_id = p.proposal_id
JOIN   Professors pr ON p.professor_id = pr.professor_id
JOIN   Departments d ON p.dept_id = d.dept_id;

-- ═══════════════════════════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════════════════════════

INSERT INTO Departments (dept_name) VALUES
('Computer Science'), ('Artificial Intelligence'), ('Physics');

INSERT INTO Reviewers (full_name, designation, email) VALUES
('Dr. Alan Turing',   'Senior Reviewer',  'turing@uni.edu'),
('Dr. Grace Hopper',  'Ethics Reviewer',  'hopper@uni.edu'),
('Dr. Marie Curie',   'Science Reviewer', 'curie@uni.edu');

-- ============================================================
-- DONE! Your database is ready. Now run: python app.py
-- ============================================================
