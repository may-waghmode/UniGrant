-- ============================================================
-- UniGrant — Complete Database Setup (Advanced DBMS Edition)
-- Run this ENTIRE script in MySQL Workbench (Select All → Execute)
-- ============================================================

DROP DATABASE IF EXISTS unigrant;
CREATE DATABASE unigrant;
USE unigrant;

-- ═══════════════════════════════════════════════════════════
-- 1. TABLES
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
    description      TEXT,~
    budget_requested DECIMAL(12,2) NOT NULL,
    status           ENUM('Pending','Approved','Rejected','Under Review','Closed') DEFAULT 'Pending',
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

-- ── Progress Updates Table (Spending Tracker) ──────────────

CREATE TABLE ProgressUpdates (
    update_id        INT AUTO_INCREMENT PRIMARY KEY,
    proposal_id      INT NOT NULL,
    professor_id     INT NOT NULL,
    update_title     VARCHAR(200) NOT NULL,
    description      TEXT,
    amount_spent     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    spending_category ENUM('Equipment','Travel','Personnel','Materials','Software','Other') DEFAULT 'Other',
    doc_filename     VARCHAR(255),
    doc_data         LONGBLOB,
    update_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id)  REFERENCES Proposals(proposal_id),
    FOREIGN KEY (professor_id) REFERENCES Professors(professor_id)
);

-- ═══════════════════════════════════════════════════════════
-- 2. INDEXES — Speed up JOINs, WHERE filters, and searches
-- ═══════════════════════════════════════════════════════════

-- Foreign-key columns (MySQL auto-creates on FK, but we name explicitly)
CREATE INDEX idx_professors_dept    ON Professors(dept_id);
CREATE INDEX idx_proposals_prof     ON Proposals(professor_id);
CREATE INDEX idx_proposals_reviewer ON Proposals(reviewer_id);
CREATE INDEX idx_proposals_dept     ON Proposals(dept_id);
CREATE INDEX idx_approvals_proposal ON Approvals(proposal_id);
CREATE INDEX idx_approvals_reviewer ON Approvals(reviewer_id);
CREATE INDEX idx_fund_proposal      ON FundAllocations(proposal_id);

-- Search / filter columns
CREATE INDEX idx_proposals_status   ON Proposals(status);
CREATE INDEX idx_proposals_date     ON Proposals(submission_date);
CREATE INDEX idx_auditlog_time      ON AuditLog(changed_at);
CREATE INDEX idx_auditlog_table     ON AuditLog(table_name);

-- Composite index: reviewer looking up pending proposals
CREATE INDEX idx_proposals_reviewer_status ON Proposals(reviewer_id, status);

-- Progress updates indexes
CREATE INDEX idx_progress_proposal   ON ProgressUpdates(proposal_id);
CREATE INDEX idx_progress_professor  ON ProgressUpdates(professor_id);
CREATE INDEX idx_progress_date       ON ProgressUpdates(update_date);

-- ═══════════════════════════════════════════════════════════
-- 3. STORED PROCEDURES
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

CREATE PROCEDURE record_progress(
    IN p_proposal_id   INT,
    IN p_professor_id  INT,
    IN p_title         VARCHAR(200),
    IN p_description   TEXT,
    IN p_amount_spent  DECIMAL(12,2),
    IN p_category      VARCHAR(50)
)
BEGIN
    -- Insert the progress update
    INSERT INTO ProgressUpdates (proposal_id, professor_id, update_title, description, amount_spent, spending_category)
    VALUES (p_proposal_id, p_professor_id, p_title, p_description, p_amount_spent, p_category);

    -- Auto-update FundAllocations total spent from all progress updates
    UPDATE FundAllocations fa
    SET fa.amount_spent = (
        SELECT COALESCE(SUM(pu.amount_spent), 0)
        FROM ProgressUpdates pu
        WHERE pu.proposal_id = p_proposal_id
    )
    WHERE fa.proposal_id = p_proposal_id;

    SELECT LAST_INSERT_ID() AS new_id, 'Progress recorded and spending updated' AS message;
END$$

DELIMITER ;

-- ═══════════════════════════════════════════════════════════
-- 4. TRIGGERS (Audit Logging)
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

CREATE TRIGGER trg_progress_insert
AFTER INSERT ON ProgressUpdates FOR EACH ROW
BEGIN
    INSERT INTO AuditLog (table_name, action, record_id, new_value)
    VALUES ('ProgressUpdates', 'INSERT', NEW.update_id,
            CONCAT('Spent ₹', NEW.amount_spent, ' on ', NEW.update_title));
END$$

DELIMITER ;

-- ═══════════════════════════════════════════════════════════
-- 5. VIEWS (Basic)
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
-- 6. WINDOW FUNCTION VIEWS — Advanced SQL Analytics
-- ═══════════════════════════════════════════════════════════

-- 6a. Budget Ranking — RANK, DENSE_RANK, PERCENT_RANK per department
CREATE VIEW vw_budget_rankings AS
SELECT
    p.proposal_id,
    p.title,
    d.dept_name,
    p.budget_requested,
    p.status,
    RANK()         OVER (PARTITION BY d.dept_id ORDER BY p.budget_requested DESC) AS dept_rank,
    DENSE_RANK()   OVER (PARTITION BY d.dept_id ORDER BY p.budget_requested DESC) AS dept_dense_rank,
    ROUND(PERCENT_RANK() OVER (PARTITION BY d.dept_id ORDER BY p.budget_requested) * 100, 1) AS percentile,
    RANK()         OVER (ORDER BY p.budget_requested DESC) AS overall_rank
FROM Proposals p
JOIN Departments d ON p.dept_id = d.dept_id;

-- 6b. Running Totals — cumulative budget allocation over time
CREATE VIEW vw_running_totals AS
SELECT
    fa.allocation_id,
    p.title,
    d.dept_name,
    fa.amount_allocated,
    fa.allocation_date,
    SUM(fa.amount_allocated) OVER (ORDER BY fa.allocation_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_total,
    SUM(fa.amount_allocated) OVER (PARTITION BY d.dept_id ORDER BY fa.allocation_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS dept_cumulative,
    COUNT(*) OVER (ORDER BY fa.allocation_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_count,
    AVG(fa.amount_allocated) OVER (ORDER BY fa.allocation_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg_3
FROM FundAllocations fa
JOIN Proposals p   ON fa.proposal_id = p.proposal_id
JOIN Departments d ON p.dept_id = d.dept_id;

-- 6c. Professor Analytics — ROW_NUMBER, NTILE, LAG, LEAD
CREATE VIEW vw_professor_analytics AS
SELECT
    pr.full_name AS professor_name,
    p.title,
    p.budget_requested,
    p.submission_date,
    d.dept_name,
    ROW_NUMBER() OVER (PARTITION BY pr.professor_id ORDER BY p.submission_date) AS submission_order,
    NTILE(4)     OVER (ORDER BY p.budget_requested) AS budget_quartile,
    LAG(p.budget_requested, 1)  OVER (PARTITION BY pr.professor_id ORDER BY p.submission_date) AS prev_budget,
    LEAD(p.budget_requested, 1) OVER (PARTITION BY pr.professor_id ORDER BY p.submission_date) AS next_budget,
    p.budget_requested - COALESCE(
        LAG(p.budget_requested, 1) OVER (PARTITION BY pr.professor_id ORDER BY p.submission_date), 
        p.budget_requested
    ) AS budget_change
FROM Proposals p
JOIN Professors pr ON p.professor_id = pr.professor_id
JOIN Departments d ON p.dept_id = d.dept_id;

-- 6d. Department-level Window Stats
CREATE VIEW vw_dept_window_stats AS
SELECT
    d.dept_name,
    COUNT(p.proposal_id) AS total_proposals,
    COALESCE(SUM(p.budget_requested), 0) AS total_requested,
    COALESCE(AVG(p.budget_requested), 0) AS avg_budget,
    RANK() OVER (ORDER BY COALESCE(SUM(p.budget_requested), 0) DESC) AS funding_rank,
    ROUND(
        COALESCE(SUM(p.budget_requested), 0) / NULLIF(SUM(SUM(p.budget_requested)) OVER (), 0) * 100
    , 1) AS pct_of_total_budget
FROM Departments d
LEFT JOIN Proposals p ON d.dept_id = p.dept_id
GROUP BY d.dept_id, d.dept_name;

-- ═══════════════════════════════════════════════════════════
-- 7. MYSQL EVENT SCHEDULER — Pure DB Automation (No Flask!)
-- ═══════════════════════════════════════════════════════════

-- Enable the event scheduler globally
SET GLOBAL event_scheduler = ON;

DELIMITER $$

-- Event 7a: Auto-flag proposals pending > 7 days as "Under Review"
-- Runs every day at midnight — zero involvement from Flask
CREATE EVENT evt_auto_flag_stale_proposals
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    -- Flag proposals stuck in 'Pending' for more than 7 days
    UPDATE Proposals
    SET    status = 'Under Review'
    WHERE  status = 'Pending'
      AND  submission_date < NOW() - INTERVAL 7 DAY;

    -- Log this automated action in audit trail
    INSERT INTO AuditLog (table_name, action, record_id, old_value, new_value)
    SELECT 'Proposals', 'AUTO_FLAG_STALE', proposal_id, 'Pending', 'Under Review'
    FROM   Proposals
    WHERE  status = 'Under Review'
      AND  submission_date < NOW() - INTERVAL 7 DAY;
END$$

-- Event 7b: Auto-close grants that hit 100% budget utilization
-- Runs every day — marks proposal as "Closed" when fully spent
CREATE EVENT evt_auto_close_fully_spent
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    UPDATE Proposals p
    JOIN   FundAllocations fa ON p.proposal_id = fa.proposal_id
    SET    p.status = 'Closed'
    WHERE  fa.amount_remaining <= 0
      AND  p.status = 'Approved';

    -- Audit log for auto-closures
    INSERT INTO AuditLog (table_name, action, record_id, old_value, new_value)
    SELECT 'Proposals', 'AUTO_CLOSE_SPENT', p.proposal_id, 'Approved', 'Closed'
    FROM   Proposals p
    JOIN   FundAllocations fa ON p.proposal_id = fa.proposal_id
    WHERE  fa.amount_remaining <= 0
      AND  p.status = 'Closed';
END$$

-- Event 7c: Daily stats snapshot — logs system health metrics
CREATE EVENT evt_daily_stats_log
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    INSERT INTO AuditLog (table_name, action, record_id, new_value)
    SELECT 'SYSTEM', 'DAILY_STATS', 0,
           CONCAT(
               'Pending:', (SELECT COUNT(*) FROM Proposals WHERE status='Pending'),
               ' | Approved:', (SELECT COUNT(*) FROM Proposals WHERE status='Approved'),
               ' | TotalFunding:₹', (SELECT COALESCE(SUM(amount_allocated),0) FROM FundAllocations)
           );
END$$

DELIMITER ;

-- ═══════════════════════════════════════════════════════════
-- 8. DATABASE-LEVEL SECURITY — GRANT / REVOKE
-- ═══════════════════════════════════════════════════════════

-- Create MySQL users with different privilege levels
-- (If users already exist, drop them first to avoid errors)

-- 8a. Professor User — can only SELECT and INSERT (no DELETE, no schema changes)
DROP USER IF EXISTS 'unigrant_professor'@'localhost';
CREATE USER 'unigrant_professor'@'localhost' IDENTIFIED BY 'Prof@2024secure';

GRANT SELECT ON unigrant.Proposals      TO 'unigrant_professor'@'localhost';
GRANT SELECT ON unigrant.Departments    TO 'unigrant_professor'@'localhost';
GRANT SELECT ON unigrant.FundAllocations TO 'unigrant_professor'@'localhost';
GRANT INSERT ON unigrant.Proposals      TO 'unigrant_professor'@'localhost';
GRANT SELECT ON unigrant.Reviewers      TO 'unigrant_professor'@'localhost';
-- Professor CANNOT delete proposals or modify funds

-- 8b. Reviewer User — can SELECT + UPDATE status, INSERT approvals
DROP USER IF EXISTS 'unigrant_reviewer'@'localhost';
CREATE USER 'unigrant_reviewer'@'localhost' IDENTIFIED BY 'Rev@2024secure';

GRANT SELECT ON unigrant.Proposals       TO 'unigrant_reviewer'@'localhost';
GRANT UPDATE ON unigrant.Proposals       TO 'unigrant_reviewer'@'localhost';
GRANT SELECT, INSERT ON unigrant.Approvals TO 'unigrant_reviewer'@'localhost';
GRANT SELECT, INSERT ON unigrant.FundAllocations TO 'unigrant_reviewer'@'localhost';
GRANT SELECT ON unigrant.Departments     TO 'unigrant_reviewer'@'localhost';
GRANT SELECT ON unigrant.Professors      TO 'unigrant_reviewer'@'localhost';
-- Reviewer CANNOT drop tables, create users, or access audit log

-- 8c. Admin User — full control on unigrant database
DROP USER IF EXISTS 'unigrant_admin'@'localhost';
CREATE USER 'unigrant_admin'@'localhost' IDENTIFIED BY 'Admin@2024secure';

GRANT ALL PRIVILEGES ON unigrant.* TO 'unigrant_admin'@'localhost';
GRANT EVENT ON unigrant.* TO 'unigrant_admin'@'localhost';

-- 8d. Read-Only Auditor — can only view, cannot modify anything
DROP USER IF EXISTS 'unigrant_auditor'@'localhost';
CREATE USER 'unigrant_auditor'@'localhost' IDENTIFIED BY 'Audit@2024secure';

GRANT SELECT ON unigrant.* TO 'unigrant_auditor'@'localhost';
-- Auditor can view everything but change nothing

-- Apply all privilege changes
FLUSH PRIVILEGES;

-- ═══════════════════════════════════════════════════════════
-- 9. SEED DATA
-- ═══════════════════════════════════════════════════════════

INSERT INTO Departments (dept_name) VALUES
('Computer Science'), ('Artificial Intelligence'), ('Physics');

INSERT INTO Reviewers (full_name, designation, email) VALUES
('Dr. Alan Turing',   'Senior Reviewer',  'turing@uni.edu'),
('Dr. Grace Hopper',  'Ethics Reviewer',  'hopper@uni.edu'),
('Dr. Marie Curie',   'Science Reviewer', 'curie@uni.edu');

-- Insert sample professors for demo
INSERT INTO Professors (full_name, email, dept_id) VALUES
('Prof. Raj Sharma',     'raj@uni.edu',     1),
('Prof. Priya Patel',    'priya@uni.edu',   2),
('Prof. Amit Desai',     'amit@uni.edu',    3),
('Prof. Neha Kulkarni',  'neha@uni.edu',    1);

-- Insert sample proposals (some old dates for event scheduler demo)
INSERT INTO Proposals (title, description, budget_requested, professor_id, dept_id, reviewer_id, submission_date) VALUES
('AI-Powered Campus Security',     'Deep learning based surveillance system',     500000, 1, 1, 1, NOW() - INTERVAL 2 DAY),
('Quantum Computing Research Lab',  'Setting up a quantum computing facility',    1200000, 2, 2, 1, NOW() - INTERVAL 10 DAY),
('IoT Smart Classroom',             'Sensor-based classroom automation',           300000, 1, 1, 2, NOW() - INTERVAL 15 DAY),
('Neural Machine Translation',      'Multilingual NMT for Indian languages',       800000, 2, 2, 2, NOW() - INTERVAL 3 DAY),
('Particle Physics Simulation',     'High-energy particle collision simulation',   950000, 3, 3, 3, NOW() - INTERVAL 12 DAY),
('Blockchain Academic Records',     'Tamper-proof degree verification system',     450000, 4, 1, 3, NOW() - INTERVAL 1 DAY),
('Autonomous Drone Research',       'Drone-based agricultural monitoring',         700000, 3, 3, 1, NOW() - INTERVAL 8 DAY),
('NLP Chatbot for Students',        'AI chatbot for academic queries',             350000, 4, 1, 2, NOW() - INTERVAL 5 DAY);

-- Approve some proposals to create fund allocations for analytics
CALL approve_proposal(1, 1, 480000, 'Excellent security proposal');
CALL approve_proposal(4, 2, 750000, 'Strong NMT research plan');
CALL approve_proposal(6, 3, 420000, 'Innovative blockchain approach');

-- Add some spending for utilization analytics
UPDATE FundAllocations SET amount_spent = 120000 WHERE proposal_id = 1;
UPDATE FundAllocations SET amount_spent = 300000 WHERE proposal_id = 4;
UPDATE FundAllocations SET amount_spent = 420000 WHERE proposal_id = 6;  -- This one is fully spent!

-- ═══════════════════════════════════════════════════════════
-- 10. VERIFICATION QUERIES — Run these to test everything
-- ═══════════════════════════════════════════════════════════

-- Check indexes
SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME 
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = 'unigrant' 
ORDER BY TABLE_NAME, INDEX_NAME;

-- Check event scheduler status
SHOW EVENTS FROM unigrant;

-- Check window function views
SELECT * FROM vw_budget_rankings;
SELECT * FROM vw_running_totals;
SELECT * FROM vw_professor_analytics;
SELECT * FROM vw_dept_window_stats;

-- Check user privileges
SHOW GRANTS FOR 'unigrant_professor'@'localhost';
SHOW GRANTS FOR 'unigrant_reviewer'@'localhost';
SHOW GRANTS FOR 'unigrant_admin'@'localhost';
SHOW GRANTS FOR 'unigrant_auditor'@'localhost';

-- ============================================================
-- DONE! Your database is ready with:
--   ✅ Indexes on all FK and search columns
--   ✅ Event Scheduler (auto-flag stale, auto-close spent)
--   ✅ Window Functions (RANK, DENSE_RANK, running totals, etc.)
--   ✅ GRANT/REVOKE security (4 user roles)
-- Now run: python app.py
-- ============================================================
