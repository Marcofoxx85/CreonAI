# backend/stripe_webhook.py

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import stripe
import os
from .database import SessionLocal
from .models import User

router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")  # From your Stripe dashboard

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/api/webhook/stripe")
async def stripe_webhook(request: Request, db=Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle payment success
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        email = session['customer_email']
        credits_to_add = 100  # or read from metadata

        # Add credits to user
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.credits += credits_to_add
            db.commit()

    return JSONResponse(status_code=200, content={"message": "Success"})
