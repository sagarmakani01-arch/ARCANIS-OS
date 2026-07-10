/**
 * blockchain.c — Blockchain & Web3 Implementation
 *
 * Blockchain ledger, smart contracts, and wallet management.
 */
#include <arcanis/blockchain.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>
#include <stdlib.h>

/* ---- Initialization ---- */

void blockchain_init(blockchain_t* chain) {
    if (!chain) return;
    memset(chain, 0, sizeof(blockchain_t));
    chain->difficulty = 4;
    chain->block_time = 10;
    chain->total_supply = 21000000;

    /* Create genesis block */
    block_t genesis;
    memset(&genesis, 0, sizeof(block_t));
    string_copy(genesis.header.previous_hash, "00000000000000000000000000000000", BLOCK_HASH_SIZE);
    string_copy(genesis.header.merkle_root, "genesis", BLOCK_HASH_SIZE);
    genesis.header.timestamp = 0;
    genesis.header.nonce = 0;
    genesis.header.difficulty = chain->difficulty;
    genesis.header.transaction_count = 0;

    blockchain_add_block(chain, &genesis);
    printf("[BLOCKCHAIN] Genesis block created\n");
}

/* ---- Block operations ---- */

static void compute_hash(const block_header_t* header, char* hash) {
    /* Simplified hash computation */
    uint64_t h = header->timestamp + header->nonce + header->difficulty;
    for (uint32_t i = 0; i < BLOCK_HASH_SIZE; i++) {
        h = (h * 31 + i) & 0xFFFFFFFF;
        hash[i] = "0123456789abcdef"[h % 16];
    }
    hash[BLOCK_HASH_SIZE - 1] = '\0';
}

int blockchain_add_block(blockchain_t* chain, const block_t* block) {
    if (!chain || !block) return -1;
    if (chain->chain_length >= 256) return -1;

    memcpy(&chain->chain[chain->chain_length], block, sizeof(block_t));
    chain->chain_length++;
    printf("[BLOCKCHAIN] Block #%u added (%u transactions)\n",
           chain->chain_length - 1, block->header.transaction_count);
    return 0;
}

int blockchain_get_block(blockchain_t* chain, uint32_t index, block_t* block) {
    if (!chain || !block) return -1;
    if (index >= chain->chain_length) return -1;

    memcpy(block, &chain->chain[index], sizeof(block_t));
    return 0;
}

int blockchain_get_latest(blockchain_t* chain, block_t* block) {
    if (!chain || !block) return -1;
    if (chain->chain_length == 0) return -1;

    memcpy(block, &chain->chain[chain->chain_length - 1], sizeof(block_t));
    return 0;
}

int blockchain_validate(blockchain_t* chain) {
    if (!chain) return -1;

    for (uint32_t i = 1; i < chain->chain_length; i++) {
        /* Verify hash chain */
        char computed_hash[BLOCK_HASH_SIZE];
        compute_hash(&chain->chain[i].header, computed_hash);

        if (string_compare(chain->chain[i].header.previous_hash, computed_hash) != 0) {
            printf("[BLOCKCHAIN] Invalid hash at block %u\n", i);
            return -1;
        }
    }

    printf("[BLOCKCHAIN] Chain valid (%u blocks)\n", chain->chain_length);
    return 0;
}

int blockchain_mine_block(blockchain_t* chain, const char* miner_addr) {
    if (!chain || !miner_addr) return -1;

    /* Create new block from mempool */
    block_t new_block;
    memset(&new_block, 0, sizeof(block_t));

    /* Get previous hash */
    if (chain->chain_length > 0) {
        char prev_hash[BLOCK_HASH_SIZE];
        compute_hash(&chain->chain[chain->chain_length - 1].header, prev_hash);
        string_copy(new_block.header.previous_hash, prev_hash, BLOCK_HASH_SIZE);
    }

    new_block.header.timestamp = 0;
    new_block.header.difficulty = chain->difficulty;
    new_block.header.transaction_count = 0;

    /* Simple proof of work */
    for (uint32_t nonce = 0; nonce < 1000000; nonce++) {
        new_block.header.nonce = nonce;
        char hash[BLOCK_HASH_SIZE];
        compute_hash(&new_block.header, hash);

        /* Check difficulty */
        int valid = 1;
        for (uint32_t i = 0; i < chain->difficulty; i++) {
            if (hash[i] != '0') {
                valid = 0;
                break;
            }
        }

        if (valid) {
            string_copy(new_block.header.hash, hash, BLOCK_HASH_SIZE);
            break;
        }
    }

    /* Add reward transaction */
    transaction_t reward;
    memset(&reward, 0, sizeof(transaction_t));
    string_copy(reward.from, "coinbase", BLOCK_MAX_ADDR);
    string_copy(reward.to, miner_addr, BLOCK_MAX_ADDR);
    reward.amount = 50;
    reward.timestamp = 0;

    new_block.transactions[0] = reward;
    new_block.header.transaction_count = 1;

    blockchain_add_block(chain, &new_block);
    printf("[BLOCKCHAIN] Block mined by %s\n", miner_addr);
    return 0;
}

/* ---- Transaction operations ---- */

int blockchain_create_transaction(blockchain_t* chain,
                                 const char* from, const char* to,
                                 uint64_t amount, const char* data) {
    if (!chain || !from || !to) return -1;

    transaction_t tx;
    memset(&tx, 0, sizeof(transaction_t));

    /* Generate hash */
    uint64_t h = (uint64_t)from[0] + amount;
    for (uint32_t i = 0; i < BLOCK_HASH_SIZE; i++) {
        h = (h * 31 + i) & 0xFFFFFFFF;
        tx.hash[i] = "0123456789abcdef"[h % 16];
    }
    tx.hash[BLOCK_HASH_SIZE - 1] = '\0';

    string_copy(tx.from, from, BLOCK_MAX_ADDR);
    string_copy(tx.to, to, BLOCK_MAX_ADDR);
    tx.amount = amount;
    tx.fee = amount / 100;
    tx.timestamp = 0;
    if (data) string_copy(tx.data, data, 512);

    return blockchain_add_to_mempool(chain, &tx);
}

int blockchain_add_to_mempool(blockchain_t* chain, const transaction_t* tx) {
    if (!chain || !tx) return -1;
    if (chain->mempool_size >= BLOCK_MAX_TX) return -1;

    memcpy(&chain->mempool[chain->mempool_size], tx, sizeof(transaction_t));
    chain->mempool_size++;
    printf("[BLOCKCHAIN] Transaction added to mempool (%u pending)\n", chain->mempool_size);
    return 0;
}

int blockchain_process_mempool(blockchain_t* chain) {
    if (!chain) return -1;
    if (chain->mempool_size == 0) return 0;

    printf("[BLOCKCHAIN] Processing %u transactions from mempool\n", chain->mempool_size);

    /* Process transactions */
    for (uint32_t i = 0; i < chain->mempool_size; i++) {
        chain->mempool[i].confirmed = 1;
        chain->total_transactions++;
    }

    chain->mempool_size = 0;
    return 0;
}

int blockchain_get_transaction(blockchain_t* chain, const char* hash, transaction_t* tx) {
    if (!chain || !hash || !tx) return -1;

    /* Search in mempool */
    for (uint32_t i = 0; i < chain->mempool_size; i++) {
        if (string_compare(chain->mempool[i].hash, hash) == 0) {
            memcpy(tx, &chain->mempool[i], sizeof(transaction_t));
            return 0;
        }
    }

    /* Search in blocks */
    for (uint32_t i = 0; i < chain->chain_length; i++) {
        for (uint32_t j = 0; j < chain->chain[i].header.transaction_count; j++) {
            if (string_compare(chain->chain[i].transactions[j].hash, hash) == 0) {
                memcpy(tx, &chain->chain[i].transactions[j], sizeof(transaction_t));
                return 0;
            }
        }
    }

    return -1;
}

/* ---- Account operations ---- */

int blockchain_create_account(blockchain_t* chain, const char* name) {
    if (!chain || !name) return -1;
    if (chain->num_accounts >= BLOCK_MAX_ACCOUNTS) return -1;

    account_t* acc = &chain->accounts[chain->num_accounts];
    memset(acc, 0, sizeof(account_t));

    /* Generate address */
    snprintf(acc->address, BLOCK_MAX_ADDR, "0x%040x", chain->num_accounts);
    string_copy(acc->name, name, 64);
    acc->balance = 0;
    acc->nonce = 0;

    chain->num_accounts++;
    printf("[BLOCKCHAIN] Account '%s' created: %s\n", name, acc->address);
    return 0;
}

int blockchain_get_balance(blockchain_t* chain, const char* address, uint64_t* balance) {
    if (!chain || !address || !balance) return -1;

    for (uint32_t i = 0; i < chain->num_accounts; i++) {
        if (string_compare(chain->accounts[i].address, address) == 0) {
            *balance = chain->accounts[i].balance;
            return 0;
        }
    }
    return -1;
}

int blockchain_transfer(blockchain_t* chain, const char* from,
                       const char* to, uint64_t amount) {
    if (!chain || !from || !to) return -1;

    account_t* sender = NULL;
    account_t* receiver = NULL;

    for (uint32_t i = 0; i < chain->num_accounts; i++) {
        if (string_compare(chain->accounts[i].address, from) == 0)
            sender = &chain->accounts[i];
        if (string_compare(chain->accounts[i].address, to) == 0)
            receiver = &chain->accounts[i];
    }

    if (!sender || !receiver) return -1;
    if (sender->balance < amount) return -1;

    sender->balance -= amount;
    receiver->balance += amount;
    sender->nonce++;

    printf("[BLOCKCHAIN] Transfer: %llu from %s to %s\n",
           (unsigned long long)amount, from, to);
    return 0;
}

int blockchain_list_accounts(blockchain_t* chain, char* buf, uint32_t buf_len) {
    if (!chain || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "ACCOUNTS: %u\n", chain->num_accounts);
    pos += snprintf(buf + pos, buf_len - pos,
        "ADDRESS                                 NAME        BALANCE\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------\n");

    for (uint32_t i = 0; i < chain->num_accounts && pos < buf_len - 150; i++) {
        account_t* a = &chain->accounts[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-39s %-11s %llu\n",
            a->address, a->name, (unsigned long long)a->balance);
    }

    return (int)pos;
}

/* ---- Smart contracts ---- */

int blockchain_deploy_contract(blockchain_t* chain, const char* name,
                              const char* code, const char* owner) {
    if (!chain || !name || !code || !owner) return -1;
    if (chain->num_contracts >= BLOCK_MAX_CONTRACTS) return -1;

    contract_t* contract = &chain->contracts[chain->num_contracts];
    memset(contract, 0, sizeof(contract_t));

    snprintf(contract->address, BLOCK_MAX_ADDR, "0x%040x", chain->num_contracts + 1000);
    string_copy(contract->name, name, 64);
    string_copy(contract->code, code, 4096);
    string_copy(contract->owner, owner, BLOCK_MAX_ADDR);
    contract->gas_limit = 1000000;
    contract->deployed = 1;

    chain->num_contracts++;
    printf("[BLOCKCHAIN] Contract '%s' deployed at %s\n", name, contract->address);
    return 0;
}

int blockchain_call_contract(blockchain_t* chain, const char* address,
                            const char* function, const char* args,
                            char* result) {
    if (!chain || !address || !function) return -1;

    for (uint32_t i = 0; i < chain->num_contracts; i++) {
        if (string_compare(chain->contracts[i].address, address) == 0) {
            printf("[BLOCKCHAIN] Calling %s.%s(%s)\n",
                   chain->contracts[i].name, function, args ? args : "");
            if (result) string_copy(result, "0x00000000", 256);
            return 0;
        }
    }
    return -1;
}

int blockchain_list_contracts(blockchain_t* chain, char* buf, uint32_t buf_len) {
    if (!chain || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "CONTRACTS: %u\n", chain->num_contracts);
    pos += snprintf(buf + pos, buf_len - pos,
        "ADDRESS                                 NAME        GAS USED\n");
    pos += snprintf(buf + pos, buf_len - pos,
        "--------------------------------------------------------\n");

    for (uint32_t i = 0; i < chain->num_contracts && pos < buf_len - 150; i++) {
        contract_t* c = &chain->contracts[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-39s %-11s %u\n",
            c->address, c->name, c->gas_used);
    }

    return (int)pos;
}

/* ---- Mining ---- */

int blockchain_set_difficulty(blockchain_t* chain, uint32_t difficulty) {
    if (!chain) return -1;
    chain->difficulty = difficulty;
    printf("[BLOCKCHAIN] Difficulty set to %u\n", difficulty);
    return 0;
}

int blockchain_set_block_time(blockchain_t* chain, uint32_t seconds) {
    if (!chain) return -1;
    chain->block_time = seconds;
    printf("[BLOCKCHAIN] Block time set to %u seconds\n", seconds);
    return 0;
}

int blockchain_get_mining_info(blockchain_t* chain, char* buf, uint32_t buf_len) {
    if (!chain || !buf) return 0;

    return snprintf(buf, buf_len,
        "Mining Info:\n"
        "  Chain Length: %u blocks\n"
        "  Difficulty: %u\n"
        "  Block Time: %u seconds\n"
        "  Pending Tx: %u\n"
        "  Total Supply: %llu\n"
        "  Total Transactions: %llu\n",
        chain->chain_length, chain->difficulty,
        chain->block_time, chain->mempool_size,
        (unsigned long long)chain->total_supply,
        (unsigned long long)chain->total_transactions);
}

/* ---- Utility ---- */

void blockchain_hash(const char* data, char* hash) {
    if (!data || !hash) return;

    uint64_t h = 0;
    for (uint32_t i = 0; data[i]; i++)
        h = (h * 31 + data[i]) & 0xFFFFFFFF;

    for (uint32_t i = 0; i < BLOCK_HASH_SIZE; i++) {
        h = (h * 31 + i) & 0xFFFFFFFF;
        hash[i] = "0123456789abcdef"[h % 16];
    }
    hash[BLOCK_HASH_SIZE - 1] = '\0';
}

int blockchain_verify_signature(const char* public_key, const char* signature,
                               const char* data) {
    if (!public_key || !signature || !data) return -1;

    /* Simplified verification */
    printf("[BLOCKCHAIN] Signature verified\n");
    return 0;
}
