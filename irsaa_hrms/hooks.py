"""
SA HR Onboarding - hooks.py
Saudi HR Auto-Onboarding System
"""

app_name = "irsaa_hrms"
app_title = "SA HR Onboarding"
app_publisher = "Your Company"
app_description = "Saudi HR Auto-Onboarding: Auto-assigns Leave Policy, Shift, Holiday List & Salary Structure"
app_icon = "octicon octicon-person"
app_color = "#00843D"  # Saudi Green
app_email = "hr@yourcompany.com"
app_license = "MIT"

# ─────────────────────────────────────────────
# DOC EVENTS
# ─────────────────────────────────────────────

doc_events = {
    "Employee": {
        "after_insert": "irsaa_hrms.api.onboarding.auto_assign_all",
        "on_update":    "irsaa_hrms.api.onboarding.auto_assign_all",
    }
}

# ─────────────────────────────────────────────
# SCHEDULED TASKS
# ─────────────────────────────────────────────

scheduler_events = {
    "daily": [
        "irsaa_hrms.api.scheduler.alert_incomplete_onboarding",
        "irsaa_hrms.api.scheduler.check_document_expiry",
    ],
    "weekly": [
        "irsaa_hrms.api.scheduler.weekly_onboarding_report",
    ]
}

# ─────────────────────────────────────────────
# FIXTURES (data to export with app)
# ─────────────────────────────────────────────

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["module", "=", "SA HR Onboarding"]]
    },
    {
        "doctype": "Property Setter",
        "filters": [["module", "=", "SA HR Onboarding"]]
    },
    {
        "doctype": "Workflow",
        "filters": [["name", "in", ["Employee Onboarding Approval"]]]
    },
    {
        "doctype": "Workflow State",
        "filters": [["workflow_state_name", "in", [
            "Pending HR Review",
            "Pending Manager Approval",
            "Approved",
            "Rejected"
        ]]]
    }
]

# ─────────────────────────────────────────────
# CUSTOM FIELDS ON EMPLOYEE
# ─────────────────────────────────────────────

# These are injected via fixtures or bench migrate
# Defined here for documentation purposes:
#
# Employee DocType additions:
# - onboarding_template     (Link → HR Onboarding Template)
# - onboarding_status       (Select: Pending/Complete/Partial)
# - onboarding_completed_on (Date)
# - onboarding_notes        (Small Text)

# ─────────────────────────────────────────────
# JINJA FILTERS
# ─────────────────────────────────────────────

jinja = {
    "filters": []
}
