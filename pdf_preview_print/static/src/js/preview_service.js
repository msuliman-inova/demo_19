/** @odoo-module **/
// Copyright 2026 Naim OUDAYET
// License LGPL-3

/**
 * PDF Preview Report Handler
 *
 * Registers a handler in Odoo 19's "ir.actions.report handlers" registry
 * to intercept qweb-pdf report actions. Instead of the browser downloading
 * the file immediately, a full-screen preview dialog is shown first.
 *
 * The user can then Print, Download, or Close from the dialog.
 */

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { PreviewDialog } from "./preview_dialog";
import { downloadReport } from "@web/webclient/actions/reports/utils";

export function pdfPreviewHandler(action, options, env) {
    if (action.report_type && action.report_type !== "qweb-pdf") {
        return false;
    }

    const activeIds = getActiveIds(action);
    if (!activeIds.length) {
        return false;
    }

    // Same context Download below already sends - without it, the preview
    // iframe fetches /report/pdf with no context at all, so the server falls
    // back to the session's own default company and raises a multi-company
    // AccessError for any record that isn't in that company, even though the
    // action that opened this dialog already knew the right one (e.g.
    // printing a record from a company the user has access to but isn't
    // currently their active one).
    const ctx = { ...user.context, ...action.context };
    const reportUrl = `/report/pdf/${action.report_name}/${activeIds.join(",")}` +
        `?context=${encodeURIComponent(JSON.stringify(ctx))}`;

    env.services.dialog.add(PreviewDialog, {
        reportUrl,
        reportName: action.name || action.display_name || "",
        onDownload() {
            downloadReport(rpc, action, "pdf", ctx);
        },
    });

    return true;
}

/**
 * Extract record IDs from the various places Odoo puts them.
 */
export function getActiveIds(action) {
    if (action.context?.active_ids?.length) {
        return action.context.active_ids;
    }
    if (action.context?.active_id) {
        return [action.context.active_id];
    }
    if (action.data?.ids?.length) {
        return action.data.ids;
    }
    if (action.data?.id) {
        return [action.data.id];
    }
    return [];
}

registry
    .category("ir.actions.report handlers")
    .add("pdf_preview_print", pdfPreviewHandler);
