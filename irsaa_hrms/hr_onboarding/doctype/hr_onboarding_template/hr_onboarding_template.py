"""
HR Onboarding Template - DocType Controller
Saudi HR Auto-Onboarding System
"""
import frappe
from frappe.model.document import Document


class HROnboardingTemplate(Document):

    def validate(self):
        self.validate_gosi_percentage()
        self.validate_uniqueness()

    def validate_gosi_percentage(self):
        if self.apply_gosi:
            if self.gosi_type == "Saudi Employee" and self.gosi_percentage != 10:
                frappe.msgprint(
                    "⚠️ Standard GOSI for Saudi Employees is 10%. "
                    f"You have set {self.gosi_percentage}%. Please confirm.",
                    indicator="orange"
                )
            elif self.gosi_type == "Non-Saudi Employee" and self.gosi_percentage != 2:
                frappe.msgprint(
                    "⚠️ Standard GOSI for Non-Saudi Employees is 2%. "
                    f"You have set {self.gosi_percentage}%. Please confirm.",
                    indicator="orange"
                )

    def validate_uniqueness(self):
        """Warn if a very similar template already exists"""
        filters = {"name": ("!=", self.name), "is_active": 1}
        if self.employment_type:
            filters["employment_type"] = self.employment_type
        if self.department:
            filters["department"] = self.department
        if self.grade:
            filters["grade"] = self.grade

        duplicate = frappe.db.get_value("HR Onboarding Template", filters, "name")
        if duplicate:
            frappe.msgprint(
                f"⚠️ A similar active template already exists: <b>{duplicate}</b>. "
                "Check Priority field to ensure correct template is applied.",
                indicator="orange"
            )
