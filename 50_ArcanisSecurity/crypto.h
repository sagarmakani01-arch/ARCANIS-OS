/**
 * aes.h — AES Encryption/Decryption
 *
 * AES-128/192/256 block cipher implementation.
 * Supports ECB and CBC modes.
 */
#ifndef ARCANIS_AES_H
#define ARCANIS_AES_H

#include <arcanis/types.h>

#define AES_BLOCK_SIZE   16
#define AES_MAX_ROUNDS   14
#define AES_MAX_KEY_SIZE 32

typedef enum {
    AES_128 = 16,
    AES_192 = 24,
    AES_256 = 32
} aes_key_size_t;

typedef struct {
    uint8_t  round_key[AES_BLOCK_SIZE * (AES_MAX_ROUNDS + 1)];
    uint32_t nr;  /* Number of rounds */
    uint8_t  iv[AES_BLOCK_SIZE]; /* IV for CBC mode */
} aes_ctx_t;

/* Initialize AES context */
int  aes_init(aes_ctx_t* ctx, const uint8_t* key, aes_key_size_t key_size);

/* Set IV for CBC mode */
void aes_set_iv(aes_ctx_t* ctx, const uint8_t* iv);

/* ECB mode */
int  aes_encrypt_ecb(aes_ctx_t* ctx, const uint8_t plaintext[AES_BLOCK_SIZE],
                     uint8_t ciphertext[AES_BLOCK_SIZE]);
int  aes_decrypt_ecb(aes_ctx_t* ctx, const uint8_t ciphertext[AES_BLOCK_SIZE],
                     uint8_t plaintext[AES_BLOCK_SIZE]);

/* CBC mode */
int  aes_encrypt_cbc(aes_ctx_t* ctx, const uint8_t* plaintext, uint32_t len,
                     uint8_t* ciphertext);
int  aes_decrypt_cbc(aes_ctx_t* ctx, const uint8_t* ciphertext, uint32_t len,
                     uint8_t* plaintext);

/* Utility */
void aes_xor_block(uint8_t* dst, const uint8_t* a, const uint8_t* b);
void aes_pkcs7_pad(const uint8_t* data, uint32_t len, uint8_t* padded, uint32_t* padded_len);
int  aes_pkcs7_unpad(const uint8_t* data, uint32_t len, uint8_t* unpadded, uint32_t* unpadded_len);

#endif
