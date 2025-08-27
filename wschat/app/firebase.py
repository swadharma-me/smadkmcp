import firebase_admin
from firebase_admin import credentials, auth, app_check
from fastapi import HTTPException
import logging
from app.config import config
import os

FIREBASE_CREDENTIALS = config.FIREBASE_SERVICE_CREDENTIALS # Update with your actual path

logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK if it isn't already initialized.
    """
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized in firebase.py")
    else:
        logger.debug("Firebase Admin SDK was already initialized.")

async def auth_with_firebase(id_token: str, app_check_token: str = None) -> str:
    """
    Verifies a Firebase ID token and optionally an App Check token.
    Raises HTTPException if verification fails.
    Returns the user's Firebase UID on success.
    """
    try:
        decoded_id_token = auth.verify_id_token(id_token)
        print (f"decoded token is {decoded_id_token}")
        firebase_uid = decoded_id_token.get("user_id")
        logger.info(f"ID token verified successfully for user {firebase_uid}")

        # If there's an App Check token, verify it
        if app_check_token:
            try:
                decoded_app_check = app_check.verify_token(app_check_token)
                app_id = decoded_app_check.get("app_id")
                logger.info(f"App Check token verified successfully for app {app_id}")
            except Exception as e:
                logger.warning(f"App Check verification failed: {e}")
                raise HTTPException(status_code=403, detail="App Check verification failed.")

        return firebase_uid

    except auth.ExpiredIdTokenError:
        logger.warning("Expired ID token.")
        raise HTTPException(status_code=401, detail="ID token has expired.")
    except auth.InvalidIdTokenError:
        logger.warning("Invalid ID token.")
        raise HTTPException(status_code=401, detail="Invalid ID token.")
    except Exception as e:
        logger.error(f"Unexpected error in authentication: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
