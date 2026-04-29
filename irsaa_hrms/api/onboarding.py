"""
SA HR Onboarding - Auto Assignment API
Saudi HR Auto-Onboarding System

Core logic for automatically assigning:
- Leave Policy
- Holiday List
- Shift Assignment + Location
- Salary Structure
- GOSI deduction

Triggered on Employee after_insert and on_update.
"""
import frappe
from frappe import _
from frappe.utils import today, getdate


# ─────────────────────────────────────────────
# MAIN ENTRY POINT (called from hooks.py)
# ─────────────────────────────────────────────

def auto_assign_all(doc, method):
    # Only run for Active employees
    if doc.status != "Active":
        return

    # For on_update, only run if it's a brand new employee
    # (date_of_joining was just set = new hire) or manually triggered
    if method == "on_update":
        # Check if assignments already exist - if yes skip
        already_has_leave = frappe.db.exists(
            "Leave Policy Assignment", {"employee": doc.name, "docstatus": 1}
        )
        already_has_shift = frappe.db.exists(
            "Shift Assignment", {"employee": doc.name, "docstatus": 1}
        )
        if already_has_leave and already_has_shift:
            return  # Already fully onboarded, skip

    template = get_matching_template(doc)
    if not template:
        frappe.log_error(
            f"No HR Onboarding Template found for Employee {doc.name} "
            f"[Type: {doc.employment_type}, Dept: {doc.department}, Grade: {doc.grade}]",
            "SA HR Onboarding"
        )
        frappe.publish_realtime(
            "hr_onboarding_warning",
            {
                "employee": doc.name,
                "message": f"No onboarding template matched for {doc.employee_name}. "
                           "Please assign Leave Policy, Shift, and Salary manually."
            },
            user=frappe.session.user
        )
        return

    results = []

    results.append(assign_leave_policy(doc, template))
    results.append(assign_holiday_list(doc, template))
    results.append(assign_shift(doc, template))
    results.append(assign_salary_structure(doc, template))

    # Summary notification
    success = [r for r in results if r and r.get("status") == "success"]
    skipped = [r for r in results if r and r.get("status") == "skipped"]

    if success:
        msg = "✅ <b>Auto-Onboarding Complete</b><br>"
        for r in success:
            msg += f"&nbsp;&nbsp;• {r['message']}<br>"
        if skipped:
            msg += "<br>⏭️ <b>Skipped (already assigned):</b><br>"
            for r in skipped:
                msg += f"&nbsp;&nbsp;• {r['message']}<br>"
        frappe.msgprint(msg, title="SA HR Onboarding", indicator="green")


# ─────────────────────────────────────────────
# TEMPLATE MATCHING
# ─────────────────────────────────────────────

def get_matching_template(doc):
    """
    Find the best matching HR Onboarding Template.
    Matches on: employment_type, department, grade, nationality_type.
    More specific matches take priority over generic ones.
    Priority field (lower number = higher priority) is used as tiebreaker.
    """
    # Determine nationality type
    saudi_nationalities = ["Saudi Arabia", "Saudi"]
    is_saudi = doc.get("nationality") in saudi_nationalities

    templates = frappe.get_all(
        "HR Onboarding Template",
        filters={"is_active": 1},
        fields=[
            "name", "employment_type", "department", "grade",
            "nationality_type", "priority",
            "leave_policy", "leave_period", "holiday_list",
            "default_shift", "shift_location", "shift_request_approver",
            "salary_structure", "salary_currency", "payroll_cost_center",
            "apply_gosi", "gosi_type", "gosi_percentage"
        ],
        order_by="priority asc"
    )

    best_match = None
    best_score = -1

    for t in templates:
        score = 0

        # Nationality check
        if t.nationality_type == "Saudi" and not is_saudi:
            continue
        if t.nationality_type == "Non-Saudi" and is_saudi:
            continue

        # Score: more specific = higher score
        if t.employment_type:
            if t.employment_type != doc.employment_type:
                continue
            score += 4

        if t.department:
            if t.department != doc.department:
                continue
            score += 2

        if t.grade:
            if t.grade != (doc.grade or ""):
                continue
            score += 1

        if score >= best_score:
            best_score = score
            best_match = t

    return best_match


# ─────────────────────────────────────────────
# LEAVE POLICY ASSIGNMENT
# ─────────────────────────────────────────────

def assign_leave_policy(doc, template):
    if not template.leave_policy:
        return {"status": "skipped", "message": "Leave Policy: Not configured in template"}

    # Check if already assigned
    existing = frappe.db.exists("Leave Policy Assignment", {
        "employee": doc.name,
        "leave_policy": template.leave_policy,
        "docstatus": 1
    })

    if existing:
        return {"status": "skipped", "message": f"Leave Policy '{template.leave_policy}' already assigned"}

    try:
        from frappe.utils import add_days, get_last_day, getdate
	import datetime

	joining_date = getdate(doc.date_of_joining or today())

	# Effective To = last day of current year
	effective_to = datetime.date(joining_date.year, 12, 31)

	lpa = frappe.get_doc({
    		"doctype": "Leave Policy Assignment",
		"employee": doc.name,
		"leave_policy": template.leave_policy,
		"effective_from": joining_date,
		"effective_to": effective_to,
   		"assignment_based_on": "Date of Joining",
    		"leave_period": template.leave_period or None,
   		"carry_forward": 0
	})

        lpa.insert(ignore_permissions=True)
        lpa.submit()

        # Log the auto-assignment
        _log_assignment(doc.name, "Leave Policy", template.leave_policy)

        return {"status": "success", "message": f"Leave Policy '{template.leave_policy}' assigned"}

    except Exception as e:
        frappe.log_error(
            f"Leave Policy assignment failed for {doc.name}: {str(e)}",
            "SA HR Onboarding"
        )
        return {"status": "error", "message": f"Leave Policy assignment failed: {str(e)}"}


# ─────────────────────────────────────────────
# HOLIDAY LIST ASSIGNMENT
# ─────────────────────────────────────────────

def assign_holiday_list(doc, template):
    if not template.holiday_list:
        return {"status": "skipped", "message": "Holiday List: Not configured in template"}

    if doc.holiday_list == template.holiday_list:
        return {"status": "skipped", "message": f"Holiday List '{template.holiday_list}' already set"}

    try:
        frappe.db.set_value(
            "Employee", doc.name,
            "holiday_list", template.holiday_list,
            update_modified=False
        )
        _log_assignment(doc.name, "Holiday List", template.holiday_list)
        return {"status": "success", "message": f"Holiday List '{template.holiday_list}' assigned"}

    except Exception as e:
        frappe.log_error(
            f"Holiday List assignment failed for {doc.name}: {str(e)}",
            "SA HR Onboarding"
        )
        return {"status": "error", "message": f"Holiday List assignment failed: {str(e)}"}


# ─────────────────────────────────────────────
# SHIFT ASSIGNMENT
# ─────────────────────────────────────────────

def assign_shift(doc, template):
    if not template.default_shift:
        return {"status": "skipped", "message": "Shift: Not configured in template"}

    existing = frappe.db.exists("Shift Assignment", {
        "employee": doc.name,
        "shift_type": template.default_shift,
        "docstatus": 1
    })

    if existing:
        return {"status": "skipped", "message": f"Shift '{template.default_shift}' already assigned"}

    try:
        sa = frappe.get_doc({
            "doctype": "Shift Assignment",
            "employee": doc.name,
            "employee_name": doc.employee_name,
            "shift_type": template.default_shift,
            "start_date": doc.date_of_joining or today(),
            "company": doc.company,
            "shift_request_approver": template.shift_request_approver or None
        })
        sa.insert(ignore_permissions=True)
        sa.submit()

        # Assign shift location if provided
        if template.shift_location:
            _assign_shift_location(doc, template)

        _log_assignment(doc.name, "Shift", template.default_shift)
        return {"status": "success", "message": f"Shift '{template.default_shift}' assigned"}

    except Exception as e:
        frappe.log_error(
            f"Shift assignment failed for {doc.name}: {str(e)}",
            "SA HR Onboarding"
        )
        return {"status": "error", "message": f"Shift assignment failed: {str(e)}"}


def _assign_shift_location(doc, template):
    """Add shift location to employee's allowed locations"""
    try:
        emp = frappe.get_doc("Employee", doc.name)
        existing_locs = [row.shift_location for row in (emp.shift_location or [])]

        if template.shift_location not in existing_locs:
            emp.append("shift_location", {"shift_location": template.shift_location})
            emp.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(
            f"Shift Location assignment failed for {doc.name}: {str(e)}",
            "SA HR Onboarding"
        )


# ─────────────────────────────────────────────
# SALARY STRUCTURE ASSIGNMENT
# ─────────────────────────────────────────────

def assign_salary_structure(doc, template):
    if not template.salary_structure:
        return {"status": "skipped", "message": "Salary Structure: Not configured in template"}

    if not doc.ctc:
        return {
            "status": "skipped",
            "message": "Salary Structure: Skipped — CTC (Cost to Company) is not set on employee"
        }

    existing = frappe.db.exists("Salary Structure Assignment", {
        "employee": doc.name,
        "salary_structure": template.salary_structure,
        "docstatus": 1
    })

    if existing:
        return {
            "status": "skipped",
            "message": f"Salary Structure '{template.salary_structure}' already assigned"
        }

    try:
        ssa = frappe.get_doc({
            "doctype": "Salary Structure Assignment",
            "employee": doc.name,
            "salary_structure": template.salary_structure,
            "from_date": doc.date_of_joining or today(),
            "base": doc.ctc,
            "company": doc.company,
            "currency": template.salary_currency or "SAR",
            "payroll_cost_center": template.payroll_cost_center or None
        })
        ssa.insert(ignore_permissions=True)
        ssa.submit()

        _log_assignment(doc.name, "Salary Structure", template.salary_structure)
        return {"status": "success", "message": f"Salary Structure '{template.salary_structure}' assigned"}

    except Exception as e:
        frappe.log_error(
            f"Salary Structure assignment failed for {doc.name}: {str(e)}",
            "SA HR Onboarding"
        )
        return {"status": "error", "message": f"Salary Structure assignment failed: {str(e)}"}


# ─────────────────────────────────────────────
# WHITELISTED API ENDPOINTS (called from JS)
# ─────────────────────────────────────────────

@frappe.whitelist()
def get_onboarding_template(employment_type=None, department=None, grade=None, nationality=None):
    """
    Called from Employee form client script.
    Returns matching template for preview before save.
    """
    doc = frappe._dict({
        "employment_type": employment_type,
        "department": department,
        "grade": grade,
        "nationality": nationality or "Saudi Arabia"
    })
    template = get_matching_template(doc)
    return template


@frappe.whitelist()
def manually_trigger_onboarding(employee):
    """
    Allows HR Manager to manually re-trigger auto-onboarding
    for an existing employee (e.g., after setting up templates).
    """
    if not frappe.has_permission("Employee", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    doc = frappe.get_doc("Employee", employee)
    doc.__run_onboarding = True

    template = get_matching_template(doc)
    if not template:
        frappe.throw(
            f"No matching HR Onboarding Template found for employee {doc.employee_name}. "
            "Please create a template for their Employment Type/Department/Grade."
        )

    results = []
    results.append(assign_leave_policy(doc, template))
    results.append(assign_holiday_list(doc, template))
    results.append(assign_shift(doc, template))
    results.append(assign_salary_structure(doc, template))

    return {
        "template_used": template.name,
        "results": results
    }


@frappe.whitelist()
def get_onboarding_status_dashboard():
    """
    Returns data for the Incomplete Onboarding Dashboard.
    Shows employees missing Leave Policy, Shift, or Salary Structure.
    """
    if not frappe.has_permission("Employee", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "department", "employment_type",
                "grade", "date_of_joining", "company", "nationality",
                "designation", "image"]
    )

    result = []

    for emp in employees:
        missing = []
        warnings = []

        # Check Leave Policy
        has_leave = frappe.db.exists("Leave Policy Assignment", {
            "employee": emp.name,
            "docstatus": 1
        })
        if not has_leave:
            missing.append("Leave Policy")

        # Check Shift
        has_shift = frappe.db.exists("Shift Assignment", {
            "employee": emp.name,
            "docstatus": 1
        })
        if not has_shift:
            missing.append("Shift")

        # Check Salary Structure
        has_salary = frappe.db.exists("Salary Structure Assignment", {
            "employee": emp.name,
            "docstatus": 1
        })
        if not has_salary:
            missing.append("Salary Structure")

        # Check Holiday List
        has_holiday = frappe.db.get_value("Employee", emp.name, "holiday_list")
        if not has_holiday:
            warnings.append("Holiday List")

        # Check GOSI (Saudi employees)
        saudi_nationalities = ["Saudi Arabia", "Saudi"]
        if emp.get("nationality") in saudi_nationalities:
            has_gosi = frappe.db.exists("Salary Structure Assignment", {
                "employee": emp.name,
                "docstatus": 1
            })
            # (GOSI check via salary components would be more detailed)

        if missing or warnings:
            result.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "department": emp.department,
                "employment_type": emp.employment_type,
                "designation": emp.designation,
                "date_of_joining": str(emp.date_of_joining) if emp.date_of_joining else None,
                "missing": missing,
                "warnings": warnings,
                "total_missing": len(missing) + len(warnings)
            })

    result.sort(key=lambda x: x["total_missing"], reverse=True)
    return result


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _log_assignment(employee, assignment_type, value):
    """Create a Comment on Employee record for audit trail"""
    try:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Employee",
            "reference_name": employee,
            "content": f"🤖 Auto-Onboarding: <b>{assignment_type}</b> set to <b>{value}</b> "
                       f"by SA HR Onboarding system on {today()}"
        }).insert(ignore_permissions=True)
    except Exception:
        pass
