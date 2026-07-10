#include "locale.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define MAX_LOCALES 16
#define MAX_STRINGS 1024

static struct {
    Locale locale;
    Translation strings[MAX_STRINGS];
    int count;
} locale_store[MAX_LOCALES];
static int locale_count = 0;
static LocaleManager mgr;

void locale_init(const char* lang_code) {
    memset(&mgr, 0, sizeof(mgr));
    locale_set(lang_code);
}

static void load_builtin(const char* code) {
    for (int i = 0; i < locale_count; i++) {
        if (strcmp(locale_store[i].locale.code, code) == 0) {
            mgr.current = locale_store[i].locale;
            memcpy(mgr.strings, locale_store[i].strings, sizeof(Translation) * locale_store[i].count);
            mgr.string_count = locale_store[i].count;
            mgr.initialized = 1;
            return;
        }
    }
    // fallback to en-US
    if (strcmp(code, "en-US") != 0) { load_builtin("en-US"); return; }
}

void locale_set(const char* lang_code) {
    // Check if already loaded
    for (int i = 0; i < locale_count; i++) {
        if (strcmp(locale_store[i].locale.code, lang_code) == 0) {
            mgr.current = locale_store[i].locale;
            memcpy(mgr.strings, locale_store[i].strings, sizeof(Translation) * locale_store[i].count);
            mgr.string_count = locale_store[i].count;
            mgr.initialized = 1;
            printf("Locale set to %s (%s)\n", mgr.current.name, mgr.current.native_name);
            return;
        }
    }
    printf("Locale '%s' not found, loading en-US\n", lang_code);
    locale_set("en-US");
}

static Locale* add_locale(const char* code, const char* name, const char* native,
                          const char* date_fmt, const char* time_fmt,
                          const char* currency, const char* dec, const char* thou, int dow) {
    if (locale_count >= MAX_LOCALES) return NULL;
    Locale* l = &locale_store[locale_count].locale;
    locale_store[locale_count].count = 0;
    snprintf(l->code, 8, "%s", code);
    snprintf(l->name, 64, "%s", name);
    snprintf(l->native_name, 64, "%s", native);
    snprintf(l->date_format, 32, "%s", date_fmt);
    snprintf(l->time_format, 32, "%s", time_fmt);
    snprintf(l->currency_symbol, 8, "%s", currency);
    snprintf(l->decimal_sep, 4, "%s", dec);
    snprintf(l->thousands_sep, 4, "%s", thou);
    l->first_day_of_week = dow;
    locale_count++;
    return l;
}

void locale_list(void) {
    if (locale_count == 0) {
        // Load defaults
        add_locale("en-US", "English (US)", "English (US)", "MM/DD/YYYY", "hh:mm:ss A", "$", ".", ",", 0);
        add_locale("en-GB", "English (UK)", "English (UK)", "DD/MM/YYYY", "HH:mm:ss", "\u00a3", ".", ",", 1);
        add_locale("fr-FR", "French", "Fran\u00e7ais", "DD/MM/YYYY", "HH:mm:ss", "\u20ac", ",", " ", 1);
        add_locale("de-DE", "German", "Deutsch", "DD.MM.YYYY", "HH:mm:ss", "\u20ac", ",", ".", 1);
        add_locale("es-ES", "Spanish", "Espa\u00f1ol", "DD/MM/YYYY", "H:mm:ss", "\u20ac", ",", ".", 1);
        add_locale("ja-JP", "Japanese", "\u65e5\u672c\u8a9e", "YYYY/MM/DD", "HH:mm:ss", "\u00a5", ".", ",", 0);
        add_locale("zh-CN", "Chinese (Simplified)", "\u4e2d\u6587", "YYYY-MM-DD", "HH:mm:ss", "\u00a5", ".", ",", 1);
        add_locale("ko-KR", "Korean", "\ud55c\uad6d\uc5b4", "YYYY-MM-DD", "HH:mm:ss", "\u20a9", ".", ",", 1);
        add_locale("ar-SA", "Arabic", "\u0627\u0644\u0639\u0631\u0628\u064a\u0629", "DD/MM/YYYY", "HH:mm:ss", "\ufdfc", ",", ".", 6);
        add_locale("hi-IN", "Hindi", "\u0939\u093f\u0928\u094d\u0926\u0940", "DD/MM/YYYY", "hh:mm:ss A", "\u20b9", ".", ",", 1);
    }
    printf("\nAvailable Locales:\n");
    printf("  %-8s %-22s %-20s %-14s %s\n", "CODE", "NAME", "NATIVE", "DATE FMT", "CURRENCY");
    printf("  -------- -------------------- -------------------- -------------- --------\n");
    for (int i = 0; i < locale_count; i++) {
        Locale* l = &locale_store[i].locale;
        printf("  %-8s %-22s %-20s %-14s %s\n", l->code, l->name, l->native_name, l->date_format, l->currency_symbol);
    }
}

const char* locale_tr(const char* key) {
    for (int i = 0; i < mgr.string_count; i++) {
        if (strcmp(mgr.strings[i].key, key) == 0)
            return mgr.strings[i].translation;
    }
    return key;
}

static void add_string(const char* code, const char* key, const char* value) {
    for (int i = 0; i < locale_count; i++) {
        if (strcmp(locale_store[i].locale.code, code) == 0) {
            if (locale_store[i].count >= MAX_STRINGS) return;
            Translation* t = &locale_store[i].strings[locale_store[i].count++];
            snprintf(t->key, 128, "%s", key);
            snprintf(t->translation, 512, "%s", value);
            return;
        }
    }
}

void locale_add_translation(const char* lang, const char* key, const char* value) {
    add_string(lang, key, value);
    printf("Translation added: [%s] %s = %s\n", lang, key, value);
    // Reload if current locale
    if (strcmp(mgr.current.code, lang) == 0) {
        load_builtin(lang);
    }
}

void locale_format_date(int year, int month, int day) {
    char buf[64];
    const char* fmt = mgr.current.date_format;
    if (strcmp(fmt, "MM/DD/YYYY") == 0)
        snprintf(buf, 64, "%02d/%02d/%04d", month, day, year);
    else if (strcmp(fmt, "DD/MM/YYYY") == 0)
        snprintf(buf, 64, "%02d/%02d/%04d", day, month, year);
    else if (strcmp(fmt, "DD.MM.YYYY") == 0)
        snprintf(buf, 64, "%02d.%02d.%04d", day, month, year);
    else if (strcmp(fmt, "YYYY/MM/DD") == 0 || strcmp(fmt, "YYYY-MM-DD") == 0)
        snprintf(buf, 64, "%04d/%02d/%02d", year, month, day);
    else
        snprintf(buf, 64, "%04d-%02d-%02d", year, month, day);
    printf("Date: %s\n", buf);
}

void locale_format_time(int hour, int min, int sec) {
    char buf[64];
    if (strstr(mgr.current.time_format, "A")) {
        const char* ampm = hour >= 12 ? "PM" : "AM";
        int h12 = hour % 12; if (h12 == 0) h12 = 12;
        snprintf(buf, 64, "%02d:%02d:%02d %s", h12, min, sec, ampm);
    } else {
        snprintf(buf, 64, "%02d:%02d:%02d", hour, min, sec);
    }
    printf("Time: %s\n", buf);
}

void locale_format_currency(double amount) {
    char buf[64];
    snprintf(buf, 64, "%s%.2f", mgr.current.currency_symbol, amount);
    printf("Currency: %s\n", buf);
}

void locale_show_info(void) {
    printf("\n=== Current Locale ===\n");
    printf("  Code:         %s\n", mgr.current.code);
    printf("  Name:         %s\n", mgr.current.name);
    printf("  Native:       %s\n", mgr.current.native_name);
    printf("  Date Format:  %s\n", mgr.current.date_format);
    printf("  Time Format:  %s\n", mgr.current.time_format);
    printf("  Currency:     %s\n", mgr.current.currency_symbol);
    printf("  Transl.:      %d strings loaded\n", mgr.string_count);
}
