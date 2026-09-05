// Copyright 2026 Naim OUDAYET
// License LGPL-3
import { describe, expect, test } from "@odoo/hoot";
import { PreviewDialog } from "@pdf_preview_print/js/preview_dialog";

function makeKeyEvent(key, opts) {
    opts = opts || {};
    let prevented = false;
    return {
        key: key,
        ctrlKey: !!opts.ctrlKey,
        metaKey: !!opts.metaKey,
        altKey: !!opts.altKey,
        target: { tagName: opts.tagName || "BODY" },
        preventDefault() { prevented = true; },
        wasPrevented() { return prevented; },
    };
}

function makeMockThis() {
    const mock = {
        printCalled: 0,
        state: { loading: true, error: false },
        iframeRef: { el: null },
        props: {
            _onDownloadCalls: 0,
            _closeCalls: 0,
            onDownload() { mock.props._onDownloadCalls++; },
            close() { mock.props._closeCalls++; },
        },
        onPrint() { mock.printCalled++; },
        onDownload() { PreviewDialog.prototype.onDownload.call(mock); },
    };
    return mock;
}

describe("pdf_preview_print / PreviewDialog - dialogTitle", () => {
    test("uses props.reportName when provided", () => {
        const desc = Object.getOwnPropertyDescriptor(PreviewDialog.prototype, "dialogTitle");
        const title = desc.get.call({ props: { reportName: "Invoice 0001" } });
        expect(title).toBe("Invoice 0001");
    });
    test("empty reportName triggers fallback branch", () => {
        const desc = Object.getOwnPropertyDescriptor(PreviewDialog.prototype, "dialogTitle");
        let result = null, threw = false;
        try {
            result = desc.get.call({ props: { reportName: "" } });
        } catch (e) {
            threw = true;
        }
        expect(threw || result !== "").toBe(true);
    });
});

describe("pdf_preview_print / PreviewDialog - _onKeydown", () => {
    test("lowercase p triggers onPrint", () => {
        const mock = makeMockThis();
        const ev = makeKeyEvent("p");
        PreviewDialog.prototype._onKeydown.call(mock, ev);
        expect(mock.printCalled).toBe(1);
        expect(ev.wasPrevented()).toBe(true);
    });
    test("uppercase P triggers onPrint", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("P"));
        expect(mock.printCalled).toBe(1);
    });
    test("lowercase d triggers onDownload and close", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("d"));
        expect(mock.props._onDownloadCalls).toBe(1);
        expect(mock.props._closeCalls).toBe(1);
    });
    test("uppercase D triggers onDownload", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("D"));
        expect(mock.props._onDownloadCalls).toBe(1);
    });
    test("Ctrl+P is ignored", () => {
        const mock = makeMockThis();
        const ev = makeKeyEvent("p", { ctrlKey: true });
        PreviewDialog.prototype._onKeydown.call(mock, ev);
        expect(mock.printCalled).toBe(0);
        expect(ev.wasPrevented()).toBe(false);
    });
    test("Meta+P is ignored", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("p", { metaKey: true }));
        expect(mock.printCalled).toBe(0);
    });
    test("Alt+P is ignored", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("p", { altKey: true }));
        expect(mock.printCalled).toBe(0);
    });
    test("Ctrl+D is ignored", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("d", { ctrlKey: true }));
        expect(mock.props._onDownloadCalls).toBe(0);
    });
    test("focus inside INPUT ignores P and D", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("p", { tagName: "INPUT" }));
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("d", { tagName: "INPUT" }));
        expect(mock.printCalled).toBe(0);
        expect(mock.props._onDownloadCalls).toBe(0);
    });
    test("focus inside TEXTAREA ignores P", () => {
        const mock = makeMockThis();
        PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent("p", { tagName: "TEXTAREA" }));
        expect(mock.printCalled).toBe(0);
    });
    test("unrelated keys are ignored", () => {
        const mock = makeMockThis();
        const ignored = ["Enter", "Tab", " ", "ArrowDown", "Escape", "x"];
        for (const k of ignored) {
            PreviewDialog.prototype._onKeydown.call(mock, makeKeyEvent(k));
        }
        expect(mock.printCalled).toBe(0);
        expect(mock.props._onDownloadCalls).toBe(0);
    });
});

describe("pdf_preview_print / PreviewDialog - onPrint", () => {
    test("focuses and prints the iframe contentWindow", () => {
        let focused = 0, printed = 0;
        const mock = {
            iframeRef: { el: { contentWindow: {
                focus() { focused++; },
                print() { printed++; },
            } } },
        };
        PreviewDialog.prototype.onPrint.call(mock);
        expect(focused).toBe(1);
        expect(printed).toBe(1);
    });
    test("no-op when iframe element is null", () => {
        PreviewDialog.prototype.onPrint.call({ iframeRef: { el: null } });
        expect(true).toBe(true);
    });
    test("no-op when contentWindow is missing", () => {
        PreviewDialog.prototype.onPrint.call({ iframeRef: { el: { contentWindow: null } } });
        expect(true).toBe(true);
    });
});

describe("pdf_preview_print / PreviewDialog - onDownload", () => {
    test("calls props.onDownload then props.close in order", () => {
        const order = [];
        const mock = {
            props: {
                onDownload() { order.push("download"); },
                close() { order.push("close"); },
            },
        };
        PreviewDialog.prototype.onDownload.call(mock);
        expect(order).toEqual(["download", "close"]);
    });
});

describe("pdf_preview_print / PreviewDialog - iframe lifecycle", () => {
    test("onIframeLoad clears loading flag", () => {
        const mock = { state: { loading: true, error: false } };
        PreviewDialog.prototype.onIframeLoad.call(mock);
        expect(mock.state.loading).toBe(false);
    });
    test("onIframeError sets error and clears loading", () => {
        const mock = { state: { loading: true, error: false } };
        PreviewDialog.prototype.onIframeError.call(mock);
        expect(mock.state.loading).toBe(false);
        expect(mock.state.error).toBe(true);
    });
});
