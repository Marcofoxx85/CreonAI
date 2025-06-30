from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import stripe
import os

load_dotenv()

router = APIRouter()

# Load secret Stripe key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Define your product credit tiers
CREDIT_TIERS = {
    "500_credits": {"price": 5, "amount": 500},
    "1000_credits": {"price": 9, "amount": 1000},
    "2500_credits": {"price": 20, "amount": 2500},
}

# Stripe checkout session creation
@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    data = await request.json()
    selected_tier = data.get("tier")

    if selected_tier not in CREDIT_TIERS:
        raise HTTPException(status_code=400, detail="Invalid credit tier.")

    credit_data = CREDIT_TIERS[selected_tier]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": credit_data["price"] * 100,  # in cents
                    "product_data": {
                        "name": f"{credit_data['amount']} CreonAI Credits"
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=os.getenv("FRONTEND_SUCCESS_URL", "https://creonai.com/success?session_id={CHECKOUT_SESSION_ID}"),
            cancel_url=os.getenv("FRONTEND_CANCEL_URL", "https://creonai.com/cancel"),
            metadata={
                "credits": str(credit_data["amount"]),
                # you can add user_id, email, etc here
            }
        )

        return JSONResponse({"checkout_url": session.url})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
