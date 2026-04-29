# 🇸🇦 SA HR Onboarding — Frappe HRMS Custom App

> **Auto-assign Leave Policy, Holiday List, Shift & Salary Structure for new employees in Saudi Arabia**

---

## 📋 Overview

This Frappe custom app solves the pain point of HR teams manually completing 7+ steps
for every new employee in Saudi HRMS implementations.

### ✅ What It Does

| Before | After |
|--------|-------|
| 7 manual steps per employee | Fill form → Save → Done |
| ~45 minutes per new hire | ~10 minutes |
| Risk of missing assignments | Template-driven, 100% accurate |
| No audit trail | Full comment log on every assignment |

---

## 🚀 Installation

```bash
# 1. Get the app
bench get-app https://github.com/Neoadmin23/irsaa_hrms.git

# 2. Install on your site
bench --site your-site.com install-app irsaa_hrms

# 3. Run migrations
bench --site your-site.com migrate

# 4. Restart
bench restart
```

---

## ⚙️ Configuration (One-Time Setup)

### Step 1: Create HR Onboarding Templates

Go to: **SA HR Onboarding → HR Onboarding Template → New**

Create templates for each employee category. Examples:

| Template Name | Employment Type | Department | Grade | Leave Policy | Shift | Salary Structure |
|--------------|----------------|------------|-------|-------------|-------|-----------------|
| Saudi - Staff - Operations | Full Time | Operations | Staff | Saudi Annual Leave | Morning Shift | Saudi Staff Structure |
| Saudi - Manager - All | Full Time | (blank) | Manager | Saudi Annual Leave | Flex Shift | Saudi Manager Structure |
| Expat - Staff | Contract | (blank) | Staff | Expat Annual Leave | Morning Shift | Expat Staff Structure |
| Expat - Senior | Contract | (blank) | Senior | Expat Annual Leave | Flex Shift | Expat Senior Structure |

**Key fields per template:**

```
Matching Criteria:
  ├── Employment Type  → e.g., "Full Time"
  ├── Department       → e.g., "Operations" (or leave blank = all)
  ├── Grade            → e.g., "Staff"
  └── Nationality Type → Saudi / Non-Saudi / All

Auto-Assignment Config:
  ├── Leave Policy     → e.g., "Saudi Annual Leave Policy"
  ├── Holiday List     → e.g., "KSA Official Holidays 2025"
  ├── Default Shift    → e.g., "Morning Shift 8AM-5PM"
  ├── Shift Location   → e.g., "Head Office - Riyadh"
  ├── Salary Structure → e.g., "Saudi Staff Salary Structure"
  └── GOSI             → Type: Saudi Employee, 10%
```

### Step 2: Verify Existing Masters

Ensure these exist before creating templates:
- ✅ Leave Policies (Leaving Type per Saudi Labor Law)
- ✅ Holiday Lists (Saudi official + company holidays)
- ✅ Shift Types (Morning, Evening, Flex, etc.)
- ✅ Salary Structures (Basic + HRA + Transport + GOSI)

---

## 🔄 How It Works

```
HR fills New Employee form
        │
        ▼
Set: Employment Type + Department + Grade
        │
        ▼
Client Script previews matching template (real-time)
        │
        ▼
HR fills: CTC + Bank Details + Personal Info
        │
        ▼
Click SAVE
        │
        ▼
Workflow: Submit for HR Review → Manager Approval → Approve
        │
        ▼
on_submit hook fires → auto_assign_all()
        │
        ├── assign_leave_policy()  → Creates Leave Policy Assignment (submitted)
        ├── assign_holiday_list()  → Sets holiday_list on Employee
        ├── assign_shift()         → Creates Shift Assignment (submitted)
        │                             + adds Shift Location
        └── assign_salary_structure() → Creates Salary Structure Assignment (submitted)
                │
                ▼
        Green success message shown to HR
        Audit comment added to Employee record
```

---

## 📊 Onboarding Dashboard

Access via: **SA HR Onboarding → Onboarding Dashboard**

Shows:
- Total Active Employees vs Onboarded
- Employees with missing assignments (color-coded by severity)
- Department-wise completion rates
- Quick "Re-Run Onboarding" button per employee

---

## 🔔 Automated Alerts

### Daily Alerts (sent to HR Manager):
- New employees (joined last 30 days) with incomplete onboarding
- Expiring documents: Iqama, Passport, Contract, Medical Insurance

### Weekly Report (sent every Monday):
- Overall onboarding completion rate
- Department-wise breakdown
- List of all incomplete employees

---

## 🏛️ Saudi Labor Law Compliance

### GOSI (General Organization for Social Insurance)
- Saudi Employees: **10%** employee contribution
- Non-Saudi Employees: **2%** employee contribution
- Auto-configured per Nationality Type in template

### Leave Policy (per Saudi Labor Law - نظام العمل)
- Article 109: 21 days/year (< 5 years service)
- Article 109: 30 days/year (≥ 5 years service)
- Configure in Leave Policy master accordingly

### Contract Types
- Definite (محدد المدة) — Contract End Date required
- Indefinite (غير محدد المدة) — No end date

---

## 🛠️ Custom Fields Added to Employee

| Field | Type | Description |
|-------|------|-------------|
| onboarding_template | Link → HR Onboarding Template | Template matched |
| onboarding_status | Select | Pending / Partial / Complete |
| onboarding_completed_on | Date | When fully onboarded |
| iqama_expiry_date | Date | For expiry alerts |
| workflow_state | Data | Workflow tracking |

---

## 👥 Role Permissions

| Role | Can Do |
|------|--------|
| HR User | Create employees, submit for review |
| HR Manager | Approve employees, trigger onboarding, manage templates |
| System Manager | Full access, reset workflow states |

---

## 🐛 Troubleshooting

### "No template matched"
→ Check: Does an active template exist matching the employee's Type + Department?
→ Solution: Create a generic template (leave Type/Dept blank) as fallback.

### "Leave Policy already assigned"
→ Normal: The system skips if already assigned. No duplicate created.

### Salary Structure not assigned
→ Check: Is CTC (Cost to Company) filled on the Salary tab?
→ CTC is required for Salary Structure Assignment.

### Re-run onboarding manually
→ Employee form → SA HR Actions → 🔄 Re-Run Auto-Onboarding

---

## 📞 Support

- Module: SA HR Onboarding
- Frappe Version: v15+
- Frappe HRMS Version: v15+
- Saudi Labor Law: 2024 Edition
