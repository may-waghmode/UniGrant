# UniGrant Project Diagrams

This file contains the Entity-Relationship (ER) Diagram and System Architecture diagram. 
These diagrams are built using **Mermaid**. Many markdown viewers (like GitHub, VS Code, or Notion) will automatically render these into beautiful visual diagrams.

## 1. Entity-Relationship (ER) Diagram
This shows how all the tables in the database are connected to each other.

```mermaid
erDiagram
    Departments ||--o{ Professors : "has"
    Departments ||--o{ Proposals : "oversees"
    Professors ||--o{ Proposals : "submits"
    Reviewers ||--o{ Proposals : "reviews"
    Proposals ||--o| Approvals : "receives"
    Reviewers ||--o{ Approvals : "makes"
    Proposals ||--o| FundAllocations : "gets"
    Proposals ||--o{ ProgressUpdates : "tracks"
    Professors ||--o{ ProgressUpdates : "reports"

    Departments {
        int dept_id PK
        varchar dept_name
    }
    Professors {
        int professor_id PK
        varchar full_name
        varchar email
        int dept_id FK
    }
    Reviewers {
        int reviewer_id PK
        varchar full_name
        varchar designation
        varchar email
    }
    Proposals {
        int proposal_id PK
        varchar title
        decimal budget_requested
        enum status
        int professor_id FK
        int reviewer_id FK
        int dept_id FK
    }
    Approvals {
        int approval_id PK
        enum decision
        int proposal_id FK
        int reviewer_id FK
    }
    FundAllocations {
        int allocation_id PK
        decimal amount_allocated
        decimal amount_spent
        int proposal_id FK
    }
    ProgressUpdates {
        int update_id PK
        decimal amount_spent
        enum spending_category
        int proposal_id FK
        int professor_id FK
    }
    AuditLog {
        int log_id PK
        varchar table_name
        varchar action
        varchar old_value
        varchar new_value
    }
```

---

## 2. System Architecture Diagram
This diagram illustrates the flow of data from the User Interfaces (Frontend), through the Python Flask server, down into the advanced MySQL features.

```mermaid
flowchart TD
    %% Styling to make it look a bit more "human" or sketch-like
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px,font-family:Comic Sans MS,rx:10,ry:10;
    classDef browser fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,font-family:Comic Sans MS;
    classDef server fill:#fef08a,stroke:#ca8a04,stroke-width:2px,font-family:Comic Sans MS;
    classDef db fill:#dcfce7,stroke:#16a34a,stroke-width:2px,font-family:Comic Sans MS;

    subgraph User Layer
        P[Professor Interface]:::browser
        R[Reviewer Interface]:::browser
    end

    subgraph Application Layer [Python Flask Backend]
        App[app.py - App Entry]:::server
        R_Prof[Proposals Route]:::server
        R_Prog[Progress Route]:::server
        R_Anal[Analytics Route]:::server
    end

    subgraph Database Layer [MySQL Advanced DBMS]
        DB[(Tables & Data)]:::db
        SP[[Stored Procedures]]:::db
        Trig[[Audit Triggers]]:::db
        Views[[Window Function Views]]:::db
        Evt((Event Scheduler)):::db
    end

    %% Connections
    P <-->|HTTP Requests| App
    R <-->|HTTP Requests| App

    App --> R_Prof
    App --> R_Prog
    App --> R_Anal

    R_Prof <-->|Basic SQL| DB
    R_Prog <-->|CALL record_progress()| SP
    R_Anal <-->|SELECT FROM| Views

    SP -->|Inserts / Updates| DB
    DB -->|Fires on changes| Trig
    Trig -->|Saves to AuditLog| DB
    
    Evt -.->|Runs daily at midnight| DB
```
