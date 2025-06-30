# stripe.py

import os
import stripe
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.database import get_db
from backend.models import User, CreditTransaction, Subscription
from backend.utils import log_action

load_dotenv()

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# ───────────────────────────────────────────────
# Stripe Webhook Entry Point
# ───────────────────────────────────────────────
@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})

    print(f"⚡ Stripe event received: {event_type}")
    # ───── Handle Events ───────────────────────────────

    if event_type == "checkout.session.completed":
        customer_email = data.get("customer_email")
        metadata = data.get("metadata", {})
        topup_amount = int(metadata.get("credits", 0))

        if not customer_email or not topup_amount:
            print("⚠️ Missing metadata or email in session.")
            return {"status": "ignored"}

        user = db.query(User).filter(User.email == customer_email).first()
        if user:
            user.credits += topup_amount
            tx = CreditTransaction(
                user_id=user.id,
                amount=topup_amount,
                type="topup",
                description="Stripe credit purchase"
            )
            db.add(tx)
            db.commit()
            log_action(db, user.id, "stripe_topup", f"Added {topup_amount} credits")

    elif event_type == "invoice.payment_succeeded":
        print("✅ Payment succeeded.")
        # Optionally update user subscription status here

    elif event_type == "invoice.payment_failed":
        print("❌ Payment failed.")
        # Optionally email or alert user

    elif event_type == "customer.subscription.deleted":
        stripe_id = data.get("id")
        sub = db.query(Subscription).filter(Subscription.stripe_subscription_id == stripe_id).first()
        if sub:
            sub.status = "canceled"
            sub.canceled_at = data.get("canceled_at")
            db.commit()
            log_action(db, sub.user_id, "subscription_canceled")

    return {"status": "processed"}
