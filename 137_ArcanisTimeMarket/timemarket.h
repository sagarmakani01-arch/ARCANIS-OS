#ifndef TIMEMARKET_H
#define TIMEMARKET_H

typedef struct {
    char id[32];
    char owner[64];
    double compute_hours;
    double price_per_hour;
    double quality_of_service;
    double expiration;
    int active;
} ComputeToken;

typedef struct {
    char id[32];
    char seller[64];
    char unit_type[32];
    double capacity;
    double price;
    double availability;
    double rating;
    int offers_count;
} ResourceOffer;

typedef struct {
    char id[32];
    char buyer[64];
    char seller[64];
    ComputeToken tokens[8];
    double total_price;
    double executed_at;
    double settlement;
    int completed;
} TimeTrade;

typedef struct {
    char id[32];
    double balance;
    double reputation;
} Account;

typedef struct {
    Account accounts[16];
    TimeTrade trades[32];
    int trade_count;
    ResourceOffer offers[16];
    double market_volume;
    double avg_price;
    double volatility;
    int clearing_active;
    int distributed_ledger;
} TimeMarket;

void tmarket_init(TimeMarket *market);
void tmarket_create_offer(TimeMarket *market, const char *seller, const char *type, double capacity, double price);
void tmarket_buy(TimeMarket *market, const char *buyer_id, const char *offer_id, double hours);
void tmarket_settle(TimeMarket *market, TimeTrade *trade);
double tmarket_calculate_price(const ResourceOffer *offer);
void tmarket_show_market(const TimeMarket *market);
void tmarket_show_trades(const TimeMarket *market);
void tmarket_show_accounts(const TimeMarket *market);

#endif
