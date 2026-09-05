/** @odoo-module **/
// Copyright 2026 Naim OUDAYET
// License LGPL-3

import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class PreviewDialog extends Component {
    static template = "pdf_preview_print.PreviewDialog";
    static components = { Dialog };
    static props = {
        reportUrl: { type: String },
        reportName: { type: String, optional: true },
        onDownload: { type: Function },
        close: { type: Function },
    };

    setup() {
        this.iframeRef = useRef("previewIframe");
        this.state = useState({ loading: true, error: false });
        this._onKeydown = this._onKeydown.bind(this);

        onMounted(() => {
            document.addEventListener("keydown", this._onKeydown);
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", this._onKeydown);
        });
    }

    get dialogTitle() {
        return this.props.reportName || _t("PDF Preview");
    }

    // --- Event handlers ---

    _onKeydown(ev) {
        if (ev.target.tagName === "INPUT" || ev.target.tagName === "TEXTAREA") {
            return;
        }
        switch (ev.key.toLowerCase()) {
            case "p":
                if (!ev.ctrlKey && !ev.metaKey && !ev.altKey) {
                    ev.preventDefault();
                    this.onPrint();
                }
                break;
            case "d":
                if (!ev.ctrlKey && !ev.metaKey && !ev.altKey) {
                    ev.preventDefault();
                    this.onDownload();
                }
                break;
        }
    }

    onIframeLoad() {
        this.state.loading = false;
    }

    onIframeError() {
        this.state.loading = false;
        this.state.error = true;
    }

    onPrint() {
        const iframe = this.iframeRef.el;
        if (iframe?.contentWindow) {
            iframe.contentWindow.focus();
            iframe.contentWindow.print();
        }
    }

    onDownload() {
        this.props.onDownload();
        this.props.close();
    }
}
