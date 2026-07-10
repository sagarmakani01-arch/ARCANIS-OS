/**
 * blockchain.h — Blockchain & Web3
 *
 * Blockchain ledger, smart contracts, and wallet management.
 */
#ifndef ARCANIS_BLOCKCHAIN_H
#define ARCANIS_BLOCKCHAIN_H

#include <arcanis/types.h>

#define BLOCK_MAX_BLOCK_SIZE  1024
#define BLOCK_MAX_TX          256
#define BLOCK_MAX_ACCOUNTS    1024
#define BLOCK_MAX_CONTRACTS   256
#define BLOCK_MAX_NAME        64
#define BLOCK_MAX_ADDR        128
#define BLOCK_HASH_SIZE       64

typedef struct {
    char hash[BLOCK_HASH_SIZE];
    char previous_hash[BLOCK_HASH_SIZE];
    uint64_t timestamp;
    uint32_t nonce;
    uint32_t difficulty;
    uint32_t transaction_count;
    char merkle_root[BLOCK_HASH_SIZE];
    uint32_t size;
} block_header_t;

typedef struct {
    char hash[BLOCK_HASH_SIZE];
    char from[BLOCK_MAX_ADDR];
    char to[BLOCK_MAX_ADDR];
    uint64_t amount;
    uint64_t fee;
    uint64_t nonce;
    uint64_t timestamp;
    char data[512];
    int confirmed;
} transaction_t;

typedef struct {
    block_header_t header;
    transaction_t transactions[BLOCK_MAX_TX];
    char data[BLOCK_MAX_BLOCK_SIZE];
} block_t;

typedef struct {
    char address[BLOCK_MAX_ADDR];
    char public_key[256];
    char private_key[256];
    uint64_t balance;
    uint64_t nonce;
    char name[64];
    int is_contract;
} account_t;

typedef struct {
    char address[BLOCK_MAX_ADDR];
    char name[64];
    char code[4096];
    uint64_t balance;
    uint32_t gas_limit;
    uint32_t gas_used;
    char storage[4096];
    char owner[BLOCK_MAX_ADDR];
    int deployed;
} contract_t;

typedef struct {
    block_t chain[256];
    uint32_t chain_length;

    account_t accounts[BLOCK_MAX_ACCOUNTS];
    uint32_t num_accounts;

    contract_t contracts[BLOCK_MAX_CONTRACTS];
    uint32_t num_contracts;

    transaction_t mempool[BLOCK_MAX_TX];
    uint32_t mempool_size;

    uint32_t difficulty;
    uint32_t block_time;
    uint64_t total_supply;
    uint64_t total_transactions;
    char miner_address[BLOCK_MAX_ADDR];
} blockchain_t;

/* Initialize blockchain */
void blockchain_init(blockchain_t* chain);

/* Block operations */
int   blockchain_add_block(blockchain_t* chain, const block_t* block);
int   blockchain_get_block(blockchain_t* chain, uint32_t index, block_t* block);
int   blockchain_get_latest(blockchain_t* chain, block_t* block);
int   blockchain_validate(blockchain_t* chain);
int   blockchain_mine_block(blockchain_t* chain, const char* miner_addr);

/* Transaction operations */
int   blockchain_create_transaction(blockchain_t* chain,
                                   const char* from, const char* to,
                                   uint64_t amount, const char* data);
int   blockchain_add_to_mempool(blockchain_t* chain, const transaction_t* tx);
int   blockchain_process_mempool(blockchain_t* chain);
int   blockchain_get_transaction(blockchain_t* chain, const char* hash, transaction_t* tx);

/* Account operations */
int   blockchain_create_account(blockchain_t* chain, const char* name);
int   blockchain_get_balance(blockchain_t* chain, const char* address, uint64_t* balance);
int   blockchain_transfer(blockchain_t* chain, const char* from,
                         const char* to, uint64_t amount);
int   blockchain_list_accounts(blockchain_t* chain, char* buf, uint32_t buf_len);

/* Smart contracts */
int   blockchain_deploy_contract(blockchain_t* chain, const char* name,
                                const char* code, const char* owner);
int   blockchain_call_contract(blockchain_t* chain, const char* address,
                              const char* function, const char* args,
                              char* result);
int   blockchain_list_contracts(blockchain_t* chain, char* buf, uint32_t buf_len);

/* Mining */
int   blockchain_set_difficulty(blockchain_t* chain, uint32_t difficulty);
int   blockchain_set_block_time(blockchain_t* chain, uint32_t seconds);
int   blockchain_get_mining_info(blockchain_t* chain, char* buf, uint32_t buf_len);

/* Utility */
void  blockchain_hash(const char* data, char* hash);
int   blockchain_verify_signature(const char* public_key, const char* signature,
                                 const char* data);

#endif
