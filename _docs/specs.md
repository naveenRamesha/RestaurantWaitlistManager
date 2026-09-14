# Restaurant Waitlist Manager

## 1. Overview

**Restaurant Waitlist Manager** is a web-based application that helps restaurants manage customers waiting for tables.

The application allows restaurant staff to:

- Add customers to a waitlist.
- Record party size and seating preferences.
- Track estimated waiting time.
- Monitor table availability.
- Seat customers when a suitable table becomes available.
- Notify customers when their table is ready.
- Track waitlist history and statistics.
- Manage multiple restaurants or locations.
- Use AI to improve wait-time estimation, customer prioritisation, and operational insights.

The application should be designed using **Spec-Driven Development (SDD)** principles, where this specification acts as the source of truth for requirements, behaviour, APIs, data models, and acceptance criteria.

---

# 2. Goals

## Primary Goals

1. Provide a simple interface for restaurant staff to manage a live waitlist.
2. Reduce manual tracking of waiting customers.
3. Provide accurate estimated wait times.
4. Make table assignment easier.
5. Notify customers when their table is ready.
6. Provide visibility into current restaurant capacity.
7. Maintain historical waitlist and seating information.
8. Use AI to provide useful recommendations and predictions.
9. Provide an API-first architecture for future mobile applications and integrations.

## Non-Goals for MVP

The following are outside the initial MVP:

- Online food ordering.
- Restaurant delivery management.
- Full restaurant POS replacement.
- Payment processing.
- Employee payroll.
- Inventory management.
- Built-in voice calling.
- Complex loyalty/rewards management.
- Full reservation management.

---

# 3. Target Users

## 3.1 Restaurant Owner

Can:

- Configure restaurant settings.
- Manage tables.
- Manage staff.
- View reports.
- View waitlist history.
- Configure notification settings.

## 3.2 Manager

Can:

- Manage waitlist.
- Manage tables.
- Seat customers.
- View operational statistics.
- Override AI recommendations.

## 3.3 Host / Front Desk Staff

Can:

- Add customers.
- Update customer information.
- Check customers in.
- Notify customers.
- Seat customers.
- Remove customers from the waitlist.

## 3.4 Customer

Customers do not require an account for MVP.

They can:

- Join the waitlist through staff or a public waitlist page.
- Receive a waitlist reference.
- View estimated waiting time.
- Receive notifications.
- Confirm they are ready when notified.
- Cancel their waitlist entry.

---

# 4. Application Architecture

The application should initially be a web application with a REST API.

## Recommended Technology

### Frontend

- React
- TypeScript
- Responsive UI
- Modern component library

### Backend

- Python
- Django
- Django REST Framework

### Database

- PostgreSQL

### Authentication

- JWT-based authentication for API clients.
- Secure password hashing.
- Role-based access control.

### Infrastructure

The application should be container-friendly and support:

- Docker
- Docker Compose
- Environment-based configuration
- CI/CD

### AI

AI functionality should be implemented behind a dedicated service/interface so that the AI provider can be changed without modifying core business logic.

---

# 5. Core Concepts

## 5.1 Restaurant

A restaurant represents a physical location.

Attributes:

- ID
- Name
- Address
- Phone
- Email
- Time zone
- Opening hours
- Configuration
- Created date
- Updated date

---

# 5.2 User

Attributes:

- ID
- Name
- Email
- Password hash
- Role
- Restaurant
- Active status
- Created date
- Last login

Roles:

- OWNER
- MANAGER
- HOST

---

# 5.3 Table

Represents a physical restaurant table.

Attributes:

- ID
- Restaurant ID
- Table number/name
- Minimum capacity
- Maximum capacity
- Location
- Status
- Active status

Table statuses:

- AVAILABLE
- OCCUPIED
- RESERVED
- CLEANING
- OUT_OF_SERVICE

Example:

```text
Table 12
Capacity: 2-4
Location: Main Dining
Status: AVAILABLE
```

---

# 5.4 Waitlist Entry

Represents a customer currently waiting for a table.

Attributes:

- ID
- Restaurant ID
- Customer name
- Phone number
- Email
- Party size
- Seating preference
- Special requirements
- Join time
- Estimated wait time
- Estimated seating time
- Actual notification time
- Actual seating time
- Status
- Priority
- Notes
- Created by
- Updated date

---

# 5.5 Seating Preference

MVP options:

- ANY
- INDOOR
- OUTDOOR
- BAR
- BOOTH
- WINDOW

Future options can be added without changing the waitlist model.

---

# 6. Waitlist Status

A waitlist entry can have the following statuses:

```text
WAITING
NOTIFIED
CONFIRMED
SEATED
CANCELLED
NO_SHOW
EXPIRED
```

### State Flow

```text
WAITING
   |
   v
NOTIFIED
   |
   +----> CONFIRMED ----> SEATED
   |
   +----> NO_SHOW
   |
   +----> EXPIRED

WAITING ----> CANCELLED
```

Invalid state transitions must be rejected by the API.

---

# 7. Waitlist Management

## 7.1 Add Customer

Staff should be able to add a customer using:

- Customer name
- Phone number
- Email
- Party size
- Seating preference
- Special requirements
- Optional notes

After creation:

1. Customer receives a waitlist number/reference.
2. System calculates an estimated wait time.
3. Customer is added to the active waitlist.
4. Staff dashboard is updated.
5. Notification may be sent.

### Acceptance Criteria

- Required information must be validated.
- Party size must be greater than zero.
- Customer must receive a unique waitlist reference.
- Estimated wait must be displayed.
- Entry must appear in the live waitlist.

---

# 8. Waitlist Queue

The dashboard should display:

| Position | Customer | Party | Preference | Waited | ETA | Status |
|---|---|---:|---|---:|---:|---|
| 1 | Customer A | 2 | Booth | 12m | 8m | Waiting |
| 2 | Customer B | 4 | Any | 20m | 15m | Waiting |

The queue should automatically update as:

- Customers join.
- Customers cancel.
- Tables become available.
- Customers are seated.
- Customers are notified.

---

# 9. Queue Prioritisation

The default queue should use **FIFO (First In, First Out)**.

However, the system may adjust the recommended seating order based on:

- Party size.
- Table availability.
- Seating preference.
- Wait duration.
- Customer priority.
- Restaurant configuration.

The system must not silently change the queue.

If AI recommends a different customer, staff should be able to see the reason.

Example:

```text
Recommended next customer:

John Smith - Party of 4

Reason:
Table 8 has capacity for 4 and matches the customer's
indoor seating preference.

Waiting time: 31 minutes
```

Staff must be able to override the recommendation.

---

# 10. Table Management

The restaurant dashboard should provide a visual table overview.

Example:

```text
+--------+   +--------+   +--------+
| T1     |   | T2     |   | T3     |
| 2 pax  |   | 4 pax  |   | 6 pax  |
| FREE   |   | BUSY   |   | FREE   |
+--------+   +--------+   +--------+
```

Staff can:

- Mark table available.
- Mark table occupied.
- Mark table cleaning.
- Mark table out of service.
- View capacity.
- Assign waiting customers.

---

# 11. Table Assignment

When a table becomes available, the system should identify suitable waitlist entries.

Matching factors:

1. Party size.
2. Table capacity.
3. Seating preference.
4. Table location.
5. Customer priority.
6. Waiting duration.

The system should display recommended matches.

Example:

```text
Table 8 is now available.

Recommended:
1. John Smith - Party of 4 - 31 min wait
2. Sarah Jones - Party of 3 - 24 min wait
3. David Kumar - Party of 4 - 18 min wait
```

Staff selects the customer.

---

# 12. Customer Notification

The application should support notification through configurable providers.

MVP:

- SMS
- Email

Future:

- WhatsApp
- Push notifications

Notification events:

- Added to waitlist.
- Wait time updated.
- Table nearly ready.
- Table ready.
- Reminder.
- Cancellation.

Example:

```text
Your table at ABC Restaurant is ready.

Please check in with the host within 10 minutes.

Waitlist reference: WL-1042
```

Notification delivery status should be recorded.

---

# 13. Customer Check-In

When notified, the customer can confirm that they are ready.

Possible statuses:

```text
CONFIRMED
NO_RESPONSE
NO_SHOW
```

Restaurant configuration should determine how long a customer has to respond.

Default:

```text
10 minutes
```

After the timeout, the system can mark the customer as `EXPIRED` or `NO_SHOW`.

---

# 14. Estimated Wait Time

The system should initially calculate estimated wait time using a deterministic algorithm.

Inputs:

- Current waitlist size.
- Party sizes.
- Available tables.
- Table turnover rate.
- Historical average seating time.
- Current restaurant occupancy.

Example:

```text
Estimated Wait =
Expected customers ahead × Average seating interval
```

The architecture must allow the estimation engine to be replaced by an AI model later.

---

# 15. AI Features

AI should enhance the application rather than control critical restaurant operations automatically.

## 15.1 AI Wait-Time Prediction

AI can predict:

- Estimated waiting time.
- Expected table availability.
- Expected seating time.

Inputs may include:

- Historical wait times.
- Day of week.
- Time of day.
- Party size.
- Current occupancy.
- Table turnover.
- Historical customer flow.

The prediction should include confidence information where possible.

Example:

```text
Estimated wait: 24 minutes

Prediction confidence: High
Expected range: 20–30 minutes
```

---

# 16. AI Seating Recommendation

AI can recommend the best customer/table combination.

The recommendation should explain:

- Why the customer was selected.
- Why the table is suitable.
- Expected impact on queue.
- Whether seating preference is satisfied.

AI recommendations must remain advisory.

Staff makes the final decision.

---

# 17. AI Operational Insights

The manager dashboard may provide insights such as:

```text
Today's Insight

Average wait time is 18% higher than your normal Saturday.

The largest increase occurred between 7:00 PM and 8:30 PM.

Recommendation:
Consider opening Table 14 during this period.
```

Other insights:

- Peak hours.
- Average wait time.
- Average party size.
- No-show rate.
- Table utilisation.
- Customer abandonment.
- Bottleneck periods.

---

# 18. AI Natural Language Assistant

Future/MVP+ feature.

Managers can ask questions such as:

```text
"What was our busiest period yesterday?"

"Why was the average wait time high tonight?"

"Which tables are causing the longest delays?"

"How many parties did we seat after waiting more than 30 minutes?"
```

The assistant should only access data the logged-in user is authorised to see.

---

# 19. Dashboard

The main dashboard should display:

### Current Metrics

- Customers waiting.
- Average wait time.
- Longest wait.
- Available tables.
- Occupied tables.
- Customers notified.
- Customers ready to be seated.

### Live Waitlist

Show active waitlist entries.

### Table Status

Show current table availability.

### AI Recommendation

Show the next recommended seating action.

---

# 20. Reporting

Reports should include:

- Total customers served.
- Average wait time.
- Maximum wait time.
- Average party size.
- Customers cancelled.
- No-show count.
- Table utilisation.
- Seating time.
- Waitlist volume by hour.
- Waitlist volume by day.

Reports should support:

- Today
- Yesterday
- Last 7 days
- Last 30 days
- Custom date range

---

# 21. Search

Staff should be able to search active and historical waitlist entries using:

- Customer name.
- Phone number.
- Waitlist reference.

Search results should display:

- Customer.
- Party size.
- Join time.
- Status.
- Seating time.

---

# 22. Authentication

Users must authenticate before accessing restaurant management functionality.

Authentication flow:

```text
User
 |
 | Login
 v
Frontend
 |
 | POST /api/auth/login
 v
Backend
 |
 | Validate credentials
 v
Database
 |
 | User verified
 v
Backend
 |
 | Access + Refresh Token
 v
Frontend
```

Protected APIs must validate the access token.

Role-based authorization must be enforced server-side.

---

# 23. REST API

API base path:

```text
/api/v1
```

## Authentication

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

## Waitlist

```text
GET    /api/v1/waitlist
POST   /api/v1/waitlist
GET    /api/v1/waitlist/{id}
PATCH  /api/v1/waitlist/{id}
DELETE /api/v1/waitlist/{id}
POST   /api/v1/waitlist/{id}/notify
POST   /api/v1/waitlist/{id}/confirm
POST   /api/v1/waitlist/{id}/seat
POST   /api/v1/waitlist/{id}/cancel
```

## Tables

```text
GET   /api/v1/tables
POST  /api/v1/tables
GET   /api/v1/tables/{id}
PATCH /api/v1/tables/{id}
```

## Reports

```text
GET /api/v1/reports/waitlist
GET /api/v1/reports/tables
GET /api/v1/reports/operations
```

## AI

```text
GET  /api/v1/ai/wait-estimate/{waitlist_id}
GET  /api/v1/ai/table-recommendations
GET  /api/v1/ai/insights
POST /api/v1/ai/assistant
```

---

# 24. Real-Time Updates

The dashboard should support real-time waitlist updates.

Preferred approach:

- WebSockets

Events:

```text
WAITLIST_CREATED
WAITLIST_UPDATED
WAITLIST_CANCELLED
CUSTOMER_NOTIFIED
CUSTOMER_CONFIRMED
CUSTOMER_SEATED
TABLE_UPDATED
WAIT_TIME_UPDATED
```

If WebSockets are unavailable, the application should gracefully fall back to polling.

---

# 25. Data Model

Core entities:

```text
Restaurant
    |
    +--- User
    |
    +--- Table
    |
    +--- WaitlistEntry
             |
             +--- Notification
             |
             +--- SeatingEvent

AIRecommendation
AIInsight
AuditLog
```

---

# 26. Audit Logging

Important actions must be logged.

Examples:

- Customer added.
- Customer updated.
- Customer cancelled.
- Customer notified.
- Customer seated.
- Table status changed.
- Queue priority changed.
- AI recommendation overridden.

Audit record:

```text
ID
Restaurant ID
User ID
Action
Entity Type
Entity ID
Previous Value
New Value
Timestamp
```

---

# 27. Security Requirements

The application must:

- Use HTTPS in production.
- Hash passwords using a secure password hashing algorithm.
- Never store plaintext passwords.
- Validate all API input.
- Prevent SQL injection.
- Prevent XSS.
- Apply CSRF protection where applicable.
- Apply rate limiting to authentication APIs.
- Enforce role-based access.
- Ensure restaurant data isolation.
- Avoid exposing sensitive customer information unnecessarily.
- Secure notification-provider credentials.
- Store secrets in environment/configuration management.
- Maintain audit logs for important operations.

---

# 28. Privacy

Customer information should be treated as sensitive operational data.

The application should:

- Collect only required customer information.
- Provide configurable data-retention policies.
- Avoid exposing customer phone numbers unnecessarily.
- Restrict historical data access by role.
- Provide mechanisms to remove/anonymise old customer information.

---

# 29. Error Handling

API errors should use a consistent format.

Example:

```json
{
  "error": {
    "code": "INVALID_WAITLIST_STATUS",
    "message": "Customer cannot be seated because they have been cancelled."
  }
}
```

The frontend should display user-friendly error messages.

Technical details should be logged but not exposed to customers.

---

# 30. Observability

The application should provide:

- Structured application logs.
- Error logging.
- API request metrics.
- Database performance metrics.
- Notification delivery metrics.
- AI request/response metrics.
- Health-check endpoint.

Health endpoint:

```text
GET /health
```

---

# 31. Configuration

Configuration should be environment-based.

Example:

```text
DATABASE_URL
SECRET_KEY
JWT_SECRET
SMS_PROVIDER
SMS_API_KEY
EMAIL_PROVIDER
EMAIL_API_KEY
AI_PROVIDER
AI_API_KEY
WAITLIST_TIMEOUT_MINUTES
CUSTOMER_DATA_RETENTION_DAYS
```

Secrets must never be committed to source control.

---

# 32. Testing Strategy

## Unit Tests

Test:

- Waitlist creation.
- Queue ordering.
- Status transitions.
- Table matching.
- Wait-time calculation.
- Permissions.
- Notification logic.

## Integration Tests

Test:

- API + database.
- Authentication.
- Waitlist workflow.
- Table assignment.
- Notification provider.

## Frontend Tests

Test:

- Dashboard.
- Waitlist creation.
- Waitlist updates.
- Table assignment.
- Error states.

## End-to-End Tests

Primary scenario:

```text
Login
  ↓
Add customer
  ↓
Customer appears in waitlist
  ↓
Table becomes available
  ↓
System recommends customer
  ↓
Staff assigns table
  ↓
Customer is notified
  ↓
Customer confirms
  ↓
Customer is seated
  ↓
Waitlist is updated
```

---

# 33. MVP Scope

The first release should contain:

### Authentication

- Login.
- Logout.
- User roles.

### Restaurant

- Restaurant configuration.
- Basic opening hours.

### Tables

- Create/edit tables.
- Table status.
- Capacity.

### Waitlist

- Add customer.
- View queue.
- Update entry.
- Cancel entry.
- Notify customer.
- Seat customer.

### Dashboard

- Live waitlist.
- Table availability.
- Current wait statistics.

### Notifications

- Basic SMS/email integration interface.
- Mock provider for development.

### AI

MVP AI should initially provide:

- Wait-time prediction.
- Table/customer recommendation.
- Basic operational insight.

The AI layer must have a deterministic fallback.

---

# 34. Future Features

Potential future releases:

## V2

- Customer self-service waitlist.
- QR-code check-in.
- WhatsApp notifications.
- Multiple restaurant locations.
- Advanced analytics.
- Customer history.
- Reservation integration.

## V3

- AI conversational assistant.
- Demand forecasting.
- Automatic staffing recommendations.
- POS integration.
- Reservation-system integration.
- Mobile application.
- Customer loyalty.
- Predictive table turnover.

---

# 35. Non-Functional Requirements

## Performance

The dashboard should load within approximately 2 seconds under normal conditions.

API response target:

```text
95th percentile < 500ms
```

excluding external notification/AI provider latency.

## Availability

Target:

```text
99.9%
```

for production deployment.

## Scalability

The system should support:

- Multiple restaurants.
- Multiple users per restaurant.
- Hundreds of active waitlist entries.
- Thousands of historical entries.

The architecture should allow horizontal scaling.

---

# 36. UX Principles

The application is intended for restaurant staff working in a fast-paced environment.

Therefore:

- Minimise clicks.
- Use large, readable controls.
- Make important actions obvious.
- Use clear status indicators.
- Avoid unnecessary forms.
- Support keyboard shortcuts where useful.
- Make wait times highly visible.
- Confirm destructive actions.
- Avoid requiring staff to interact with AI for routine operations.

---

# 37. Accessibility

The application should target WCAG 2.1 AA where practical.

Requirements:

- Keyboard navigation.
- Accessible form labels.
- Sufficient text contrast.
- Screen-reader compatible controls.
- Focus indicators.
- Accessible error messages.

---

# 38. Spec-Driven Development Rules

This project should follow the following development process:

```text
Requirements
     ↓
specs.md
     ↓
Architecture Specification
     ↓
Data Model Specification
     ↓
API Specification
     ↓
UI Specification
     ↓
Task Breakdown
     ↓
Implementation
     ↓
Automated Tests
     ↓
Code Review
     ↓
Acceptance Criteria
```

`specs.md` is the product-level source of truth.

Developers/AI agents must not implement behaviour that contradicts this specification without first updating the specification.

---

# 39. AI Development Guidelines

AI coding agents should:

1. Read `specs.md` before modifying the application.
2. Understand existing architecture before making changes.
3. Break large requirements into small tasks.
4. Implement one task at a time.
5. Add/update tests with every functional change.
6. Never remove existing tests to make a change pass.
7. Avoid unnecessary refactoring.
8. Follow existing coding conventions.
9. Update documentation when behaviour changes.
10. Validate implementation against acceptance criteria.

AI-generated code must be reviewed by a developer before production use.

---

# 40. Definition of Done

A feature is considered complete only when:

- Requirements are implemented.
- Acceptance criteria pass.
- Unit tests are added.
- Integration tests are added where appropriate.
- API documentation is updated.
- Security considerations are addressed.
- Error handling is implemented.
- Logging is appropriate.
- No existing functionality is broken.
- Code review is completed.
- Specification and documentation are updated if required.

---

# 41. Initial MVP User Stories

## Authentication

### US-001 — User Login

As a restaurant staff member,  
I want to log in securely,  
so that I can access the restaurant dashboard.

### US-002 — Role-Based Access

As a restaurant owner,  
I want to control user permissions,  
so that staff can only perform authorised actions.

---

## Tables

### US-003 — Manage Tables

As a manager,  
I want to configure restaurant tables and capacities,  
so that the system knows which tables can seat customers.

### US-004 — Update Table Status

As a host,  
I want to change table status,  
so that the waitlist system knows which tables are available.

---

## Waitlist

### US-005 — Add Customer

As a host,  
I want to add a customer to the waitlist,  
so that their place in the queue is recorded.

### US-006 — View Waitlist

As a host,  
I want to see the current waitlist,  
so that I can manage waiting customers.

### US-007 — Cancel Waitlist Entry

As a host,  
I want to remove a customer from the waitlist,  
so that the queue remains accurate.

### US-008 — Notify Customer

As a host,  
I want to notify a customer when their table is ready,  
so that they can proceed to the restaurant.

### US-009 — Seat Customer

As a host,  
I want to assign a customer to a table,  
so that the waitlist and table status remain synchronised.

---

## AI

### US-010 — Predict Wait Time

As a host,  
I want the system to estimate waiting time,  
so that I can provide customers with a useful ETA.

### US-011 — Recommend Customer

As a host,  
I want the system to recommend the next customer to seat,  
so that I can make faster seating decisions.

### US-012 — Operational Insights

As a manager,  
I want AI-generated operational insights,  
so that I can identify bottlenecks and improve restaurant operations.

---

# 42. MVP Acceptance Scenario

Given:

- Restaurant has 10 tables.
- Table 4 has capacity for 4.
- Table 4 becomes available.
- Customer A is a party of 4.
- Customer A has been waiting for 25 minutes.
- Customer B is a party of 2 and has been waiting for 10 minutes.

When the host opens the available table recommendation,

Then:

- Table 4 should be identified as suitable for Customer A.
- Customer A should be recommended before Customer B when the matching rules favour Customer A.
- The recommendation should explain why.
- The host can accept or reject the recommendation.
- Accepting the recommendation assigns Table 4 to Customer A.
- Customer A's status changes appropriately.
- Table 4 changes to OCCUPIED after seating.
- The event is recorded in the audit log.

---

# 43. MVP Success Metrics

The MVP should measure:

- Average customer wait time.
- Average table turnover time.
- Waitlist abandonment rate.
- No-show rate.
- Average party size.
- Time from table availability to seating.
- AI recommendation acceptance rate.
- Wait-time prediction accuracy.
- Number of customers managed per staff member.

---

# 44. Product Principle

The core principle of the application is:

> **AI should help restaurant staff make faster and better decisions, while staff remain in control of customer seating.**
