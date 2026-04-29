/**
 * SA HR Onboarding - Employee Form Client Script
 * 
 * Features:
 * 1. Auto-preview matching template when key fields are filled
 * 2. Show onboarding status banner
 * 3. Simplify form for new employees (hide irrelevant tabs)
 * 4. Manual "Re-Run Onboarding" button for HR Managers
 */

frappe.ui.form.on('Employee', {

    // ─────────────────────────────────────
    // FORM LOAD
    // ─────────────────────────────────────

    refresh: function (frm) {
        irsaa_hrms.setup_form(frm);
        irsaa_hrms.show_onboarding_banner(frm);
        irsaa_hrms.add_action_buttons(frm);
    },

    onload: function (frm) {
        if (frm.is_new()) {
            irsaa_hrms.simplify_new_form(frm);
        }
    },

    // ─────────────────────────────────────
    // TRIGGER TEMPLATE PREVIEW
    // ─────────────────────────────────────

    employment_type: function (frm) {
        irsaa_hrms.preview_template(frm);
    },

    department: function (frm) {
        irsaa_hrms.preview_template(frm);
    },

    grade: function (frm) {
        irsaa_hrms.preview_template(frm);
    },

    nationality: function (frm) {
        irsaa_hrms.preview_template(frm);
    }
});

// ─────────────────────────────────────────────
// SA HR ONBOARDING NAMESPACE
// ─────────────────────────────────────────────

window.irsaa_hrms = {

    setup_form: function (frm) {
        // Set SAR as default currency
        if (frm.is_new() && !frm.doc.salary_currency) {
            frm.set_value('salary_currency', 'SAR');
        }
    },

    simplify_new_form: function (frm) {
        /**
         * For new employees, hide tabs that are not needed initially.
         * HR will fill: Overview → Joining → Salary (CTC only)
         * Everything else auto-assigns.
         */

        // Show helper dashboard message
        frm.dashboard.set_headline_alert(
            `<div style="padding: 8px; background: #e8f5e9; border-left: 4px solid #00843D; border-radius: 4px;">
                <b>🇸🇦 SA HR Auto-Onboarding Active</b><br>
                Fill <b>Employment Type + Department + Grade + CTC</b> and Save.<br>
                Leave Policy, Shift, Holiday List & Salary Structure will be <b>auto-assigned</b>.
            </div>`,
            'green'
        );
    },

    show_onboarding_banner: function (frm) {
        if (frm.is_new()) return;

        const status = frm.doc.onboarding_status;

        if (status === 'Complete') {
            frm.dashboard.add_badge(__('✅ Onboarding Complete'), 'green');
        } else if (status === 'Partial') {
            frm.dashboard.add_badge(__('⚠️ Partial Onboarding'), 'orange');
        } else if (status === 'Pending') {
            frm.dashboard.add_badge(__('🔴 Onboarding Pending'), 'red');
        }
    },

    add_action_buttons: function (frm) {
        if (frm.is_new()) return;

        // HR Manager: Re-run onboarding button
        if (frappe.user.has_role('HR Manager')) {
            frm.add_custom_button(
                __('🔄 Re-Run Auto-Onboarding'),
                () => irsaa_hrms.manually_trigger_onboarding(frm),
                __('SA HR Actions')
            );

            frm.add_custom_button(
                __('📋 View Onboarding Checklist'),
                () => irsaa_hrms.show_onboarding_checklist(frm),
                __('SA HR Actions')
            );
        }
    },

    preview_template: function (frm) {
        /**
         * When employment_type + department are set, preview the matching template.
         * Shows what will be auto-assigned before save.
         */
        if (!frm.doc.employment_type || !frm.doc.department) return;

        frappe.call({
            method: 'irsaa_hrms.api.onboarding.get_onboarding_template',
            args: {
                employment_type: frm.doc.employment_type,
                department: frm.doc.department,
                grade: frm.doc.grade || '',
                nationality: frm.doc.nationality || 'Saudi Arabia'
            },
            callback: function (r) {
                if (r.message) {
                    const t = r.message;
                    irsaa_hrms.show_template_preview(frm, t);

                    // Auto-set holiday list immediately for UX
                    if (t.holiday_list && !frm.doc.holiday_list) {
                        frm.set_value('holiday_list', t.holiday_list);
                    }
                } else {
                    frappe.show_alert({
                        message: __('⚠️ No Onboarding Template matched. Please assign Leave Policy, Shift & Salary manually.'),
                        indicator: 'orange'
                    });
                }
            }
        });
    },

    show_template_preview: function (frm, t) {
        const fields = [
            ['Leave Policy', t.leave_policy, '📋'],
            ['Holiday List', t.holiday_list, '📅'],
            ['Shift', t.default_shift, '🕐'],
            ['Shift Location', t.shift_location, '📍'],
            ['Salary Structure', t.salary_structure, '💰'],
            ['GOSI Type', t.apply_gosi ? t.gosi_type : 'Not Applied', '🏛️'],
        ];

        let html = `<div style="font-size: 13px;">
            <b>Template:</b> ${t.name}<br><br>
            <table style="width:100%; border-collapse: collapse;">`;

        fields.forEach(([label, value, icon]) => {
            const color = value ? '#00843D' : '#999';
            const display = value || 'Not configured';
            html += `<tr>
                <td style="padding:4px 8px; color:#666;">${icon} ${label}</td>
                <td style="padding:4px 8px; color:${color}; font-weight:500;">${display}</td>
            </tr>`;
        });

        html += '</table><br><small style="color:#666;">These will be auto-assigned when you Save.</small></div>';

        frappe.show_alert({
            message: `✅ Onboarding Template Found: <b>${t.name}</b>`,
            indicator: 'green'
        });

        // Show as an inline indicator in the form
        if (frm._onboarding_preview_indicator) {
            frm._onboarding_preview_indicator.remove();
        }

        const indicator = $(`
            <div class="sa-onboarding-preview" style="
                margin: 10px 0;
                padding: 12px 16px;
                background: #f0faf4;
                border: 1px solid #b2dfdb;
                border-radius: 6px;
                border-left: 4px solid #00843D;
            ">${html}</div>
        `);

        frm._onboarding_preview_indicator = indicator;
        $(frm.fields_dict.employment_type.wrapper).after(indicator);
    },

    manually_trigger_onboarding: function (frm) {
        frappe.confirm(
            `Re-run auto-onboarding for <b>${frm.doc.employee_name}</b>?<br>
            This will assign missing: Leave Policy, Shift, Holiday List, and Salary Structure.`,
            () => {
                frappe.show_alert({ message: '⏳ Running auto-onboarding...', indicator: 'blue' });

                frappe.call({
                    method: 'irsaa_hrms.api.onboarding.manually_trigger_onboarding',
                    args: { employee: frm.doc.name },
                    callback: function (r) {
                        if (r.message) {
                            const results = r.message.results;
                            const success = results.filter(r => r && r.status === 'success');

                            if (success.length > 0) {
                                frappe.show_alert({
                                    message: `✅ Auto-onboarding complete! ${success.length} item(s) assigned.`,
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            } else {
                                frappe.show_alert({
                                    message: '⏭️ All items already assigned. Nothing to do.',
                                    indicator: 'blue'
                                });
                            }
                        }
                    }
                });
            }
        );
    },

    show_onboarding_checklist: function (frm) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Leave Policy Assignment',
                filters: { employee: frm.doc.name },
                fields: ['leave_policy', 'effective_from', 'docstatus'],
                limit: 5
            },
            callback: function (r) {
                const leave_policies = r.message || [];
                // Build a checklist dialog
                const d = new frappe.ui.Dialog({
                    title: `Onboarding Checklist: ${frm.doc.employee_name}`,
                    fields: [{ fieldtype: 'HTML', fieldname: 'checklist_html' }]
                });

                const items = [
                    { label: 'Leave Policy', done: leave_policies.some(l => l.docstatus === 1) },
                    { label: 'Holiday List', done: !!frm.doc.holiday_list },
                    { label: 'Shift Assignment', done: false }, // simplified
                    { label: 'Salary Structure', done: !!frm.doc.ctc },
                    { label: 'Bank Details (IBAN)', done: !!frm.doc.bank_ac_no },
                    { label: 'GOSI Registration', done: false },
                ];

                let html = '<div style="padding: 16px;">';
                items.forEach(item => {
                    const icon = item.done ? '✅' : '❌';
                    const color = item.done ? '#00843D' : '#d32f2f';
                    html += `<div style="padding: 8px 0; color: ${color}; font-size: 14px;">
                        ${icon} &nbsp; ${item.label}
                    </div>`;
                });
                html += '</div>';

                d.fields_dict.checklist_html.$wrapper.html(html);
                d.show();
            }
        });
    }
};
