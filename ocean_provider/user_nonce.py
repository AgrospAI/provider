#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os
import sqlite3

import jwt
from flask_caching import Cache
from ocean_provider import models
from ocean_provider.myapp import app
from ocean_provider.utils.basics import get_provider_private_key
from web3.main import Web3

logger = logging.getLogger(__name__)
db = app.session

cache = Cache(
    app,
    config={
        "CACHE_TYPE": "redis",
        "CACHE_KEY_PREFIX": "ocean_provider",
        "CACHE_REDIS_URL": os.getenv("REDIS_CONNECTION"),
    },
)


def get_nonce(address):
    """
    :return: `nonce` for the given address stored in the database
    """
    if os.getenv("REDIS_CONNECTION"):
        result = cache.get(address)
        return result if result else None

    result = models.UserNonce.query.filter_by(address=address).first()

    return result.nonce if result else None


def update_nonce(address, nonce_value):
    """
    Updates the value of `nonce` in the database
    :param: address
    :param: nonce_value
    """
    if nonce_value is None:
        logger.debug("Nonce value is not provided.")
        return

    logger.debug("Received nonce value: %d", nonce_value)

    if os.getenv("REDIS_CONNECTION"):
        cache.set(address, nonce_value)

        return

    try:
        result = db.execute(
            """
            INSERT INTO user_nonce (address, nonce)
            VALUES (:address, :nonce)
            ON CONFLICT(address)
            DO UPDATE SET nonce = excluded.nonce
            WHERE excluded.nonce > user_nonce.nonce
            """,
            {"address": address, "nonce": nonce_value},
        )
        db.commit()

        if result.rowcount == 0:
            logger.debug(
                "Nonce not updated: existing nonce >= %d for %s",
                nonce_value,
                address,
            )
    except Exception:
        db.rollback()
        logger.exception("Database update failed.")
        raise


def force_expire_token(token):
    """
    Creates the token in the database of Revoked Tokens.
    :param: token
    """
    if os.getenv("REDIS_CONNECTION"):
        cache.set("token//" + token, True)

        return

    existing_token = models.RevokedToken.query.filter_by(token=token).first()
    if existing_token:
        return

    existing_token = models.RevokedToken(token=token)
    try:
        db.add(existing_token)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Database update failed.")
        raise


def force_restore_token(token):
    """
    Removes the token from the database of Revoked Tokens.
    :param: token
    """
    if os.getenv("REDIS_CONNECTION"):
        cache.delete("token//" + token)

        return

    existing_token = models.RevokedToken.query.filter_by(token=token).first()
    if not existing_token:
        return

    try:
        db.delete(existing_token)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Database update failed.")
        raise


def is_token_valid(token, address):
    """
    Decodes the token, checks expiration, ownership and presence in the blacklist.

    Returns a tuple of boolean, message representing validity and issue (only if invalid).
    :param: token
    """
    try:
        pk = get_provider_private_key(use_universal_key=True)
        decoded = jwt.decode(token, pk, algorithms=["HS256"])
        if Web3.toChecksumAddress(decoded["address"]) != Web3.toChecksumAddress(
            address
        ):
            return False, "Token is invalid."
    except jwt.ExpiredSignatureError:
        return False, "Token is expired."
    except Exception:
        return False, "Token is invalid."

    if os.getenv("REDIS_CONNECTION"):
        valid = not cache.get("token//" + token)
    else:
        valid = not models.RevokedToken.query.filter_by(token=token).first()

    message = "" if valid else "Token is deleted."

    return valid, message
