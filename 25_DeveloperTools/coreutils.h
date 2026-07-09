/**
 * coreutils.h — Arcanis Core Utilities
 *
 * Essential tools for a usable system:
 *   grep, sed, sort, wc, head, tail, diff, touch, chmod, ln,
 *   uptime, date, history, tee, xargs, env, printenv, yes,
 *   true, false, test, expr, seq, paste, cut, tr, uniq, rev
 */
#ifndef ARCANIS_COREUTILS_H
#define ARCANIS_COREUTILS_H

#include <stdint.h>

/* ---- grep ---- */
/* Search for pattern in file/stdin */
int cu_grep(int argc, char** argv);

/* ---- sed ---- */
/* Stream editor — substitute, delete, print */
int cu_sed(int argc, char** argv);

/* ---- sort ---- */
/* Sort lines of text */
int cu_sort(int argc, char** argv);

/* ---- wc ---- */
/* Word, line, character count */
int cu_wc(int argc, char** argv);

/* ---- head ---- */
/* Output first N lines */
int cu_head(int argc, char** argv);

/* ---- tail ---- */
/* Output last N lines */
int cu_tail(int argc, char** argv);

/* ---- diff ---- */
/* Compare files line by line */
int cu_diff(int argc, char** argv);

/* ---- touch ---- */
/* Create file or update timestamp */
int cu_touch(int argc, char** argv);

/* ---- chmod ---- */
/* Change file permissions */
int cu_chmod(int argc, char** argv);

/* ---- ln ---- */
/* Create links (hard/symbolic) */
int cu_ln(int argc, char** argv);

/* ---- uptime ---- */
/* Show system uptime and load */
int cu_uptime(int argc, char** argv);

/* ---- date ---- */
/* Display or set date/time */
int cu_date(int argc, char** argv);

/* ---- history ---- */
/* Show command history */
int cu_history(int argc, char** argv);

/* ---- tee ---- */
/* Read stdin, write to file and stdout */
int cu_tee(int argc, char** argv);

/* ---- xargs ---- */
/* Build and execute command from stdin */
int cu_xargs(int argc, char** argv);

/* ---- cut ---- */
/* Cut fields/columns from lines */
int cu_cut(int argc, char** argv);

/* ---- tr ---- */
/* Translate or delete characters */
int cu_tr(int argc, char** argv);

/* ---- uniq ---- */
/* Filter duplicate lines */
int cu_uniq(int argc, char** argv);

/* ---- paste ---- */
/* Merge lines of files side by side */
int cu_paste(int argc, char** argv);

/* ---- rev ---- */
/* Reverse lines of text */
int cu_rev(int argc, char** argv);

/* ---- seq ---- */
/* Print sequence of numbers */
int cu_seq(int argc, char** argv);

/* ---- yes ---- */
/* Repeatedly output a string */
int cu_yes(int argc, char** argv);

/* ---- true / false ---- */
int cu_true(int argc, char** argv);
int cu_false(int argc, char** argv);

/* ---- test ---- */
/* Evaluate conditional expression */
int cu_test(int argc, char** argv);

/* ---- expr ---- */
/* Evaluate expression */
int cu_expr(int argc, char** argv);

/* ---- printenv ---- */
/* Print environment variables */
int cu_printenv(int argc, char** argv);

/* ---- basename / dirname ---- */
int cu_basename(int argc, char** argv);
int cu_dirname(int argc, char** argv);

/* ---- wc helpers ---- */
typedef struct {
    uint32_t lines;
    uint32_t words;
    uint32_t chars;
} wc_result_t;

wc_result_t wc_count(const char* text, uint32_t length);

#endif
