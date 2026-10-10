// Preload shim: log dialog/message strings emitted by the VMP LightBurn.exe under Wine.
// Hooks MessageBox*, TaskDialogIndirect, and GDI text-drawing (DrawText/ExtTextOut/TextOut)
// so we capture the message regardless of whether it is a Win32 box or a custom/GDI dialog.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dlfcn.h>
#include <unistd.h>

static FILE *logf = NULL;

static void init_log(void) {
    if (logf) return;
    const char *p = getenv("VMP_HOOK_LOG");
    if (!p || !*p) p = "/var/home/Dcs102/lightburn/work/native/vmp_dialog/hook.log";
    logf = fopen(p, "a");
    if (logf) setvbuf(logf, NULL, _IONBF, 0);
}

static void tag(const char *api) {
    if (!logf) return;
    fprintf(logf, "[%s] ", api);
}

// Print a wide string, escaping non-ASCII. Cap length to avoid runaway.
static void log_wstr(const wchar_t *w, int cap) {
    if (!logf) return;
    if (!w) { fputs("(null)", logf); return; }
    for (int i = 0; w[i] && i < cap; i++) {
        unsigned short c = (unsigned short)w[i];
        if (c >= 32 && c < 127) fputc(c, logf);
        else if (c == 0x2026) fputs("...", logf);
        else fprintf(logf, "\\u%04x", c);
    }
}

// Print an ANSI string.
static void log_astr(const char *s, int cap) {
    if (!logf) return;
    if (!s) { fputs("(null)", logf); return; }
    for (int i = 0; s[i] && i < cap; i++) {
        unsigned char c = (unsigned char)s[i];
        if (c >= 32 && c < 127) fputc(c, logf);
        else fprintf(logf, "\\x%02x", c);
    }
}

__attribute__((constructor))
static void shim_ctor(void) {
    init_log();
    if (logf) { fprintf(logf, "=== SHIM LOADED pid=%d ===\n", getpid()); fflush(logf); }
}

/* ---------------- canary: confirm ELF interposition reaches PE->builtin calls ---- */
typedef unsigned (*fn_GetTickCount_t)(void);
unsigned GetTickCount(void) {
    static int n = 0;
    init_log();
    if (logf && n < 3) { fprintf(logf, "[canary:GetTickCount] called #%d\n", ++n); fflush(logf); }
    static fn_GetTickCount_t orig = NULL;
    if (!orig) orig = (fn_GetTickCount_t)dlsym(RTLD_NEXT, "GetTickCount");
    return orig ? orig() : 0;
}

/* ---------------- MessageBox family -------------------------------------------- */
typedef int (*fn_MBW_t)(void*, const wchar_t*, const wchar_t*, unsigned);
int MessageBoxW(void *hWnd, const wchar_t *text, const wchar_t *caption, unsigned type) {
    init_log();
    if (logf) {
        tag("MessageBoxW");
        fprintf(logf, "hwnd=%p type=0x%x caption=", hWnd, type); log_wstr(caption, 512);
        fprintf(logf, " || text="); log_wstr(text, 4096); fputc('\n', logf); fflush(logf);
    }
    static fn_MBW_t orig = NULL;
    if (!orig) orig = (fn_MBW_t)dlsym(RTLD_NEXT, "MessageBoxW");
    return orig ? orig(hWnd, text, caption, type) : 1;
}

typedef int (*fn_MBA_t)(void*, const char*, const char*, unsigned);
int MessageBoxA(void *hWnd, const char *text, const char *caption, unsigned type) {
    init_log();
    if (logf) {
        tag("MessageBoxA");
        fprintf(logf, "hwnd=%p type=0x%x caption=", hWnd, type); log_astr(caption, 512);
        fprintf(logf, " || text="); log_astr(text, 4096); fputc('\n', logf); fflush(logf);
    }
    static fn_MBA_t orig = NULL;
    if (!orig) orig = (fn_MBA_t)dlsym(RTLD_NEXT, "MessageBoxA");
    return orig ? orig(hWnd, text, caption, type) : 1;
}

/* ---------------- TaskDialogIndirect ------------------------------------------- */
typedef int (*fn_TDI_t)(const void*, int*, int*, void*);
int TaskDialogIndirect(const void *cfg, int *pnButton, int *pnRadioButton, void *phResult) {
    init_log();
    if (logf) {
        tag("TaskDialogIndirect");
        // TASKDIALOGCONFIG layout (x64): hwndOwner(8), hInstance(8), dwFlags(4), dwButtons(4),
        //   pszWindowTitle(8), hMainIcon(8), pszContent(8), cLinesOfContent(4), pszMainInstruction(8) ...
        const unsigned char *p = (const unsigned char*)cfg;
        if (cfg) {
            const wchar_t *title  = *(const wchar_t**)(p + 0x20);
            const wchar_t *content = *(const wchar_t**)(p + 0x38);
            const wchar_t *instr  = *(const wchar_t**)(p + 0x50);
            fprintf(logf, "title="); log_wstr(title, 512);
            fprintf(logf, " || content="); log_wstr(content, 4096);
            fprintf(logf, " || instruction="); log_wstr(instr, 4096); fputc('\n', logf); fflush(logf);
        } else {
            fputc('\n', logf); fflush(logf);
        }
    }
    static fn_TDI_t orig = NULL;
    if (!orig) orig = (fn_TDI_t)dlsym(RTLD_NEXT, "TaskDialogIndirect");
    return orig ? orig(cfg, pnButton, pnRadioButton, phResult) : 0;
}

/* ---------------- GDI text drawing (robust catch-all for rendered text) -------- */
typedef int (*fn_DrawTextW_t)(void*, wchar_t*, int, void*, unsigned);
int DrawTextW(void *hdc, wchar_t *text, int count, void *rect, unsigned format) {
    init_log();
    if (logf && text) {
        // Only log reasonably long strings to cut noise.
        int len = 0; while (len < 4096 && text[len]) len++;
        if (len >= 12) {
            tag("DrawTextW"); fprintf(logf, "len=%d ", len); log_wstr(text, 4096); fputc('\n', logf); fflush(logf);
        }
    }
    static fn_DrawTextW_t orig = NULL;
    if (!orig) orig = (fn_DrawTextW_t)dlsym(RTLD_NEXT, "DrawTextW");
    return orig ? orig(hdc, text, count, rect, format) : 0;
}

typedef int (*fn_ExtTextOutW_t)(void*, long, long, unsigned, const void*, const wchar_t*, int, const void*);
int ExtTextOutW(void *hdc, long x, long y, unsigned flags, const void *rect, const wchar_t *str, int count, const void *lpRef) {
    init_log();
    if (logf && str) {
        int len = 0; while (len < 4096 && str[len]) len++;
        if (len >= 12) {
            tag("ExtTextOutW"); fprintf(logf, "len=%d ", len); log_wstr(str, 4096); fputc('\n', logf); fflush(logf);
        }
    }
    static fn_ExtTextOutW_t orig = NULL;
    if (!orig) orig = (fn_ExtTextOutW_t)dlsym(RTLD_NEXT, "ExtTextOutW");
    return orig ? orig(hdc, x, y, flags, rect, str, count, lpRef) : 0;
}

typedef int (*fn_TextOutW_t)(void*, long, long, const wchar_t*, int);
int TextOutW(void *hdc, long x, long y, const wchar_t *str, int count) {
    init_log();
    if (logf && str) {
        int len = 0; while (len < 4096 && str[len]) len++;
        if (len >= 12) {
            tag("TextOutW"); fprintf(logf, "len=%d ", len); log_wstr(str, 4096); fputc('\n', logf); fflush(logf);
        }
    }
    static fn_TextOutW_t orig = NULL;
    if (!orig) orig = (fn_TextOutW_t)dlsym(RTLD_NEXT, "TextOutW");
    return orig ? orig(hdc, x, y, str, count) : 0;
}

/* ---------------- CreateWindowExW: log dialog class names ---------------------- */
typedef void* (*fn_CWEW_t)(unsigned, const wchar_t*, const wchar_t*, unsigned, long,long,long,long, void*, void*, void*, void*);
void* CreateWindowExW(unsigned exstyle, const wchar_t *cls, const wchar_t *title, unsigned style,
                      long x, long y, long w, long h, void *parent, void *menu, void *inst, void *lp) {
    init_log();
    if (logf && cls) {
        // Log only dialog-ish / interesting classes to reduce noise.
        int len = 0; while (len < 256 && cls[len]) len++;
        char cbuf[257]; for (int i=0;i<len && i<256;i++) cbuf[i]=(cls[i]>=32&&cls[i]<127)?(char)cls[i]:'?'; cbuf[len]=0;
        if (strstr(cbuf,"#327") || strstr(cbuf,"Dialog") || strstr(cbuf,"Qt") || strstr(cbuf,"Message")) {
            tag("CreateWindowExW"); fprintf(logf, "class=%s title=", cbuf); log_wstr(title, 256); fputc('\n', logf); fflush(logf);
        }
    }
    static fn_CWEW_t orig = NULL;
    if (!orig) orig = (fn_CWEW_t)dlsym(RTLD_NEXT, "CreateWindowExW");
    return orig ? orig(exstyle, cls, title, style, x, y, w, h, parent, menu, inst, lp) : (void*)0;
}
