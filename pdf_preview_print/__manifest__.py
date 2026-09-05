# Copyright 2026 Naim OUDAYET
# License LGPL-3
{
    "name": "PDF Preview Before Print",
    "summary": "Preview PDF reports in a dialog before printing or downloading",
    "description": """
PDF Preview Before Print
========================

Intercepts the Print / Download action and shows a clean full-screen preview
before the document is printed or downloaded.

**Features:**

- Full-screen PDF preview dialog
- Print directly from preview
- Download from preview
- Keyboard shortcuts: **P** Print · **D** Download · **Esc** Close
- Works with single records and batch printing
- Zero configuration — install and it just works
""",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "website": "https://www.oudayet.com",
    "author": "Naim OUDAYET",
    "maintainers": ["naimoudayet"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "auto_install": False,
    "depends": ["web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "pdf_preview_print/static/src/scss/preview.scss",
            "pdf_preview_print/static/src/xml/preview_dialog.xml",
            "pdf_preview_print/static/src/js/preview_dialog.js",
            "pdf_preview_print/static/src/js/preview_service.js",
        ],
            "web.assets_unit_tests": [
            "pdf_preview_print/static/tests/**/*.test.js",
        ],
    },
    "images": [
        "static/description/banner.png",
    ],
    "price": 0,
    "currency": "EUR",
    "support": "contact@oudayet.com",
}
