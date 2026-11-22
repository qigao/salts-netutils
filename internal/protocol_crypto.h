#ifndef SALTSNET_PROTOCOL_CRYPTO_H
#define SALTSNET_PROTOCOL_CRYPTO_H

#include <crypto/symmetric.h>

enum { SALTSNET_SHA1_DIGEST_SIZE = 20 };

static inline int saltsnet_digest_sha1(const void *data, size_t size,
                                       uint8_t output[SALTSNET_SHA1_DIGEST_SIZE]) {
  size_t written;
  return salts_crypto_digest(SALTS_CRYPTO_SHA1, data, size,
                             output, SALTSNET_SHA1_DIGEST_SIZE, &written);
}

static inline int saltsnet_hmac_sha1(const void *key, size_t key_size,
                                     const void *data, size_t size,
                                     uint8_t output[SALTSNET_SHA1_DIGEST_SIZE]) {
  size_t written;
  return salts_crypto_hmac(SALTS_CRYPTO_SHA1, key, key_size, data, size,
                           output, SALTSNET_SHA1_DIGEST_SIZE, &written);
}

#endif
