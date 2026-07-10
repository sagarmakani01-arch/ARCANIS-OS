#include "timemarket.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    int offer_id;
    char resource[32];
    float price;
    float rating;
    int available;
} ResourceOffer;

typedef struct {
    int trade_id;
    int offer_id;
    char buyer[32];
    float amount;
    float time_tokens;
    int completed;
} TimeTrade;

typedef struct {
    char owner[32];
    float balance;
} Account;

typedef struct {
    ResourceOffer offers[20];
    int offer_count;
    TimeTrade trades[20];
    int trade_count;
    Account accounts[10];
    int account_count;
    float avg_price;
} TimeMarket;

static TimeMarket tm;

void tmarket_init(void) {
    tm.offer_count = 0;
    tm.trade_count = 0;
    tm.account_count = 2;
    tm.avg_price = 1.0f;
    srand((unsigned)time(NULL));

    snprintf(tm.accounts[0].owner, sizeof(tm.accounts[0].owner), "TraderA");
    tm.accounts[0].balance = 100.0f;
    snprintf(tm.accounts[1].owner, sizeof(tm.accounts[1].owner), "TraderB");
    tm.accounts[1].balance = 50.0f;
}

void tmarket_create_offer(const char *resource, float price) {
    if (tm.offer_count >= 20) return;
    ResourceOffer *o = &tm.offers[tm.offer_count++];
    o->offer_id = tm.offer_count;
    snprintf(o->resource, sizeof(o->resource), "%s", resource);
    o->price = price;
    o->rating = 3.5f + ((float)rand() / RAND_MAX) * 1.5f;
    o->available = 1;
    printf("Offer #%d: %s at %.2f (rating=%.1f)\n", o->offer_id, resource, price, o->rating);
}

void tmarket_buy(int offer_id, const char *buyer, float amount) {
    if (tm.trade_count >= 20) return;
    ResourceOffer *o = NULL;
    for (int i = 0; i < tm.offer_count; i++) {
        if (tm.offers[i].offer_id == offer_id && tm.offers[i].available) {
            o = &tm.offers[i];
            break;
        }
    }
    if (!o) { printf("Offer not available\n"); return; }
    TimeTrade *t = &tm.trades[tm.trade_count++];
    t->trade_id = tm.trade_count;
    t->offer_id = offer_id;
    snprintf(t->buyer, sizeof(t->buyer), "%s", buyer);
    t->amount = amount;
    t->time_tokens = amount * o->price;
    t->completed = 1;
    o->available = 0;

    for (int i = 0; i < tm.account_count; i++) {
        if (strcmp(tm.accounts[i].owner, buyer) == 0) {
            tm.accounts[i].balance -= t->time_tokens;
            break;
        }
    }
    printf("Trade #%d: %s bought %.1f of %s for %.1f tokens\n",
           t->trade_id, buyer, amount, o->resource, t->time_tokens);
}

void tmarket_settle(void) {
    float total = 0.0f;
    for (int i = 0; i < tm.trade_count; i++) {
        if (tm.trades[i].completed) total += tm.trades[i].time_tokens;
    }
    printf("Settled %d trades: %.2f tokens transferred\n", tm.trade_count, total);
    for (int i = 0; i < tm.account_count; i++) {
        printf("  %s: %.2f\n", tm.accounts[i].owner, tm.accounts[i].balance);
    }
}

float tmarket_calculate_price(float qos, float availability) {
    return tm.avg_price * qos * (1.0f + availability);
}

void tmarket_show_market(void) {
    printf("\n%-6s %-20s %-8s %-8s %s\n", "ID", "Resource", "Price", "Rating", "Avail");
    printf("------------------------------------------------\n");
    for (int i = 0; i < tm.offer_count; i++) {
        printf("%-6d %-20s %-8.2f %-8.1f %s\n",
               tm.offers[i].offer_id, tm.offers[i].resource,
               tm.offers[i].price, tm.offers[i].rating,
               tm.offers[i].available ? "yes" : "no");
    }
}

void tmarket_show_trades(void) {
    printf("\n%-6s %-8s %-20s %-8s %-10s %s\n",
           "ID", "Offer", "Buyer", "Amount", "Tokens", "Done");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < tm.trade_count; i++) {
        printf("%-6d %-8d %-20s %-8.1f %-10.1f %s\n",
               tm.trades[i].trade_id, tm.trades[i].offer_id,
               tm.trades[i].buyer, tm.trades[i].amount,
               tm.trades[i].time_tokens,
               tm.trades[i].completed ? "yes" : "no");
    }
}

void tmarket_show_accounts(void) {
    printf("\n%-20s %s\n", "Owner", "Balance");
    printf("--------------------------\n");
    for (int i = 0; i < tm.account_count; i++) {
        printf("%-20s %.2f\n", tm.accounts[i].owner, tm.accounts[i].balance);
    }
}
