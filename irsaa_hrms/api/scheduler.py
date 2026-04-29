"""
SA HR Onboarding - Scheduled Tasks
Daily alerts for incomplete onboarding, expiry checks, and weekly reports.
"""
import frappe
from frappe.utils import today, add_days, getdate, nowdate


def alert_incomplete_onboarding():
    """
    Daily task: Find employees missing required assignments.
    Sends email alert to HR Manager if any found.
    """
    from irsaa_hrms.api.onboarding import get_onboarding_status_dashboard

    try:
        incomplete = get_onboarding_status_dashboard()

        if not incomplete:
            return

        # Only alert for employees joined in last 30 days (new hires)
        new_hire_incomplete = [
            e for e in incomplete
            if e.get("date_of_joining") and
               getdate(e["date_of_joining"]) >= getdate(add_days(today(), -30))
        ]

        if not new_hire_incomplete:
            return

        hr_managers = frappe.get_all(
            "Has Role",
            filters={"role": "HR Manager", "parenttype": "User"},
            fields=["parent"],
            as_list=True
        )

        for (user,) in hr_managers:
            if not frappe.db.get_value("User", user, "enabled"):
                continue

            rows = ""
            for emp in new_hire_incomplete:
                missing_str = ", ".join(emp["missing"]) or "—"
                warning_str = ", ".join(emp["warnings"]) or "—"
                rows += f"""
                <tr>
                    <td style="padding:8px;border:1px solid #ddd;">{emp['employee_name']}</td>
                    <td style="padding:8px;border:1px solid #ddd;">{emp['department'] or '—'}</td>
                    <td style="padding:8px;border:1px solid #ddd;">{emp['date_of_joining'] or '—'}</td>
                    <td style="padding:8px;border:1px solid #ddd;color:#d32f2f;">{missing_str}</td>
                    <td style="padding:8px;border:1px solid #ddd;color:#f57c00;">{warning_str}</td>
                </tr>"""

            html = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #00843D;">🇸🇦 SA HR Onboarding Alert</h2>
                <p>The following <b>new employees</b> have incomplete onboarding assignments:</p>
                <table style="border-collapse:collapse; width:100%;">
                    <thead>
                        <tr style="background:#00843D; color:white;">
                            <th style="padding:8px;">Employee</th>
                            <th style="padding:8px;">Department</th>
                            <th style="padding:8px;">Joining Date</th>
                            <th style="padding:8px;">Missing (Critical)</th>
                            <th style="padding:8px;">Warnings</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
                <br>
                <p style="color:#666;">Please log in to Frappe HRMS and use the
                <b>SA HR Onboarding Dashboard</b> to resolve these items.</p>
            </div>"""

            frappe.sendmail(
                recipients=[user],
                subject=f"⚠️ SA HR: {len(new_hire_incomplete)} Employee(s) with Incomplete Onboarding",
                message=html,
                delayed=False
            )

    except Exception as e:
        frappe.log_error(str(e), "SA HR Onboarding: alert_incomplete_onboarding")


def check_document_expiry():
    """
    Daily task: Check for expiring documents.
    Alerts HR 30 days before expiry:
    - Iqama expiry
    - Passport expiry
    - Contract end date
    - Medical insurance expiry
    """
    alert_days = [30, 14, 7, 1]
    today_date = getdate(today())

    checks = [
        {
            "field": "iqama_expiry_date",   # custom field
            "label": "Iqama",
            "filter_nationality": "Non-Saudi"
        },
        {
            "field": "valid_upto",           # passport
            "label": "Passport",
            "filter_nationality": None
        },
        {
            "field": "contract_end_date",
            "label": "Contract",
            "filter_nationality": None
        },
        {
            "field": "medical_insurance_expiry_date",
            "label": "Medical Insurance",
            "filter_nationality": None
        }
    ]

    expiry_alerts = []

    for check in checks:
        filters = {"status": "Active"}
        if check.get("filter_nationality") == "Non-Saudi":
            filters["nationality"] = ("not in", ["Saudi Arabia", "Saudi"])

        employees = frappe.get_all(
            "Employee",
            filters=filters,
            fields=["name", "employee_name", "department", check["field"]]
        )

        for emp in employees:
            expiry = emp.get(check["field"])
            if not expiry:
                continue

            expiry_date = getdate(expiry)
            days_left = (expiry_date - today_date).days

            if days_left in alert_days:
                expiry_alerts.append({
                    "employee_name": emp.employee_name,
                    "department": emp.department,
                    "document": check["label"],
                    "expiry_date": str(expiry_date),
                    "days_left": days_left
                })

    if expiry_alerts:
        _send_expiry_alerts(expiry_alerts)


def _send_expiry_alerts(alerts):
    """Send document expiry alerts to HR"""
    hr_managers = frappe.get_all(
        "Has Role",
        filters={"role": "HR Manager", "parenttype": "User"},
        fields=["parent"],
        as_list=True
    )

    rows = ""
    for alert in alerts:
        color = "#d32f2f" if alert["days_left"] <= 7 else "#f57c00"
        rows += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">{alert['employee_name']}</td>
            <td style="padding:8px;border:1px solid #ddd;">{alert['department'] or '—'}</td>
            <td style="padding:8px;border:1px solid #ddd;">{alert['document']}</td>
            <td style="padding:8px;border:1px solid #ddd;">{alert['expiry_date']}</td>
            <td style="padding:8px;border:1px solid #ddd;color:{color};font-weight:bold;">
                {alert['days_left']} days
            </td>
        </tr>"""

    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #d32f2f;">🇸🇦 SA HR: Document Expiry Alert</h2>
        <table style="border-collapse:collapse; width:100%;">
            <thead>
                <tr style="background:#d32f2f; color:white;">
                    <th style="padding:8px;">Employee</th>
                    <th style="padding:8px;">Department</th>
                    <th style="padding:8px;">Document</th>
                    <th style="padding:8px;">Expiry Date</th>
                    <th style="padding:8px;">Days Remaining</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>"""

    for (user,) in hr_managers:
        frappe.sendmail(
            recipients=[user],
            subject=f"🔔 SA HR: {len(alerts)} Document(s) Expiring Soon",
            message=html,
            delayed=False
        )


def weekly_onboarding_report():
    """
    Weekly: Full onboarding status report to HR Manager.
    Runs every Monday.
    """
    from irsaa_hrms.api.onboarding import get_onboarding_status_dashboard

    try:
        all_incomplete = get_onboarding_status_dashboard()

        total_active = frappe.db.count("Employee", {"status": "Active"})
        total_incomplete = len(all_incomplete)
        total_complete = total_active - total_incomplete

        # Group by department
        dept_summary = {}
        for emp in all_incomplete:
            dept = emp.get("department") or "Unknown"
            dept_summary[dept] = dept_summary.get(dept, 0) + 1

        dept_rows = ""
        for dept, count in sorted(dept_summary.items(), key=lambda x: -x[1]):
            dept_rows += f"""
            <tr>
                <td style="padding:6px 10px;border:1px solid #ddd;">{dept}</td>
                <td style="padding:6px 10px;border:1px solid #ddd;text-align:center;">{count}</td>
            </tr>"""

        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #00843D;">🇸🇦 Weekly SA HR Onboarding Report</h2>
            <p>Week of: <b>{today()}</b></p>

            <div style="display:flex; gap:20px; margin:16px 0;">
                <div style="background:#e8f5e9;padding:16px;border-radius:8px;text-align:center;flex:1;">
                    <div style="font-size:32px;color:#00843D;font-weight:bold;">{total_active}</div>
                    <div>Active Employees</div>
                </div>
                <div style="background:#e8f5e9;padding:16px;border-radius:8px;text-align:center;flex:1;">
                    <div style="font-size:32px;color:#00843D;font-weight:bold;">{total_complete}</div>
                    <div>Fully Onboarded</div>
                </div>
                <div style="background:#ffeaea;padding:16px;border-radius:8px;text-align:center;flex:1;">
                    <div style="font-size:32px;color:#d32f2f;font-weight:bold;">{total_incomplete}</div>
                    <div>Incomplete Onboarding</div>
                </div>
            </div>

            <h3>By Department:</h3>
            <table style="border-collapse:collapse; width:50%;">
                <thead>
                    <tr style="background:#00843D;color:white;">
                        <th style="padding:8px;">Department</th>
                        <th style="padding:8px;">Incomplete</th>
                    </tr>
                </thead>
                <tbody>{dept_rows}</tbody>
            </table>
        </div>"""

        hr_managers = frappe.get_all(
            "Has Role",
            filters={"role": "HR Manager", "parenttype": "User"},
            fields=["parent"],
            as_list=True
        )

        for (user,) in hr_managers:
            frappe.sendmail(
                recipients=[user],
                subject=f"📊 Weekly SA HR Onboarding Report — {today()}",
                message=html,
                delayed=False
            )

    except Exception as e:
        frappe.log_error(str(e), "SA HR Onboarding: weekly_onboarding_report")
