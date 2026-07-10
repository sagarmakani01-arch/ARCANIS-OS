#ifndef ARCANIS_LOCALE_H
#define ARCANIS_LOCALE_H

typedef struct {
    char code[8];
    char name[64];
    char native_name[64];
    char date_format[32];
    char time_format[32];
    char currency_symbol[8];
    char decimal_sep[4];
    char thousands_sep[4];
    int first_day_of_week;
} Locale;

typedef struct {
    char key[128];
    char translation[512];
} Translation;

typedef struct {
    Locale current;
    Translation strings[512];
    int string_count;
    int initialized;
} LocaleManager;

void locale_init(const char* lang_code);
void locale_set(const char* lang_code);
const char* locale_tr(const char* key);
void locale_list(void);
void locale_add_translation(const char* lang, const char* key, const char* value);
void locale_format_date(int year, int month, int day);
void locale_format_time(int hour, int min, int sec);
void locale_format_currency(double amount);
void locale_show_info(void);

#endif
