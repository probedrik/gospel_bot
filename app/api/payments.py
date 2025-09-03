from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import os
import uuid
import requests
from requests.auth import HTTPBasicAuth
import re

router = APIRouter(prefix="/api", tags=["payments"])

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
CLIENT_ORIGIN = os.getenv("CLIENT_ORIGIN")
YOOKASSA_TAX_SYSTEM_CODE = os.getenv("YOOKASSA_TAX_SYSTEM_CODE")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")


class CreatePaymentRequest(BaseModel):
    amount: float = Field(default=50.0, gt=0)
    description: Optional[str] = Field(default="Пожертвование")
    email: Optional[str] = None
    phone: Optional[str] = None
    return_url: Optional[str] = None


class CreatePaymentSbpResponse(BaseModel):
    payment_id: str
    status: str
    confirmation_url: str


class CreatePaymentResponse(BaseModel):
    payment_id: str
    status: str
    confirmation_token: str


class MarkCompleteRequest(BaseModel):
    payment_id: str
    status: Optional[str] = Field(default="succeeded")
    email: Optional[str] = None


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    # Разрешаем 10-15 цифр. YooKassa ожидает цифры без знаков, для РФ — 7XXXXXXXXXX
    if 10 <= len(digits) <= 15:
        return digits
    return None


def _supabase_headers() -> dict:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(
            status_code=500, detail="SUPABASE_URL или SUPABASE_SERVICE_ROLE_KEY не заданы")
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }


def supabase_insert_donation(*, user_id: int, amount_rub: int, payment_id: str, email: Optional[str]) -> None:
    try:
        headers = _supabase_headers()
        payload = [{
            "user_id": user_id,
            "amount_rub": amount_rub,
            "payment_id": payment_id,
            "payment_status": "pending",
            "payment_method": "ruble",
            "email": email,
        }]
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/donations"
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception:
        # не падаем
        pass


def supabase_mark_complete(*, payment_id: str, status: str = "succeeded", email: Optional[str] = None) -> None:
    try:
        headers = _supabase_headers()
        url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/donations?payment_id=eq.{payment_id}"
        now = datetime.now(timezone.utc).replace(
            tzinfo=None).isoformat(timespec='seconds')
        payload = {
            "payment_status": status,
            "completed_at": now,
        }
        if email:
            payload["email"] = email
        requests.patch(url, json=payload, headers=headers, timeout=10)
    except Exception:
        # не падаем
        pass


@router.post("/yookassa/create-payment", response_model=CreatePaymentResponse)
def create_payment(body: CreatePaymentRequest) -> CreatePaymentResponse:
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        raise HTTPException(
            status_code=500, detail="YOOKASSA_SHOP_ID или YOOKASSA_SECRET_KEY не заданы в окружении")

    headers = {
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 54-ФЗ чек
    receipt: dict = {
        "items": [
            {
                "description": (body.description or "Пожертвование")[:128],
                "quantity": "1.0",
                "amount": {
                    "value": f"{body.amount:.2f}",
                    "currency": "RUB",
                },
                "vat_code": 1,
            }
        ]
    }
    try:
        if YOOKASSA_TAX_SYSTEM_CODE:
            receipt["tax_system_code"] = int(YOOKASSA_TAX_SYSTEM_CODE)
        else:
            receipt["tax_system_code"] = 1
    except ValueError:
        receipt["tax_system_code"] = 1

    customer: dict = {}
    if body.email:
        customer["email"] = body.email
    norm_phone = _normalize_phone(body.phone)
    if norm_phone:
        customer["phone"] = norm_phone
    if customer:
        receipt["customer"] = customer

    payload = {
        "amount": {
            "value": f"{body.amount:.2f}",
            "currency": "RUB",
        },
        "capture": True,
        "confirmation": {
            "type": "embedded",
        },
        "description": body.description or "Пожертвование",
        "receipt": receipt,
    }

    try:
        resp = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
            timeout=20,
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502, detail=f"Ошибка сети при обращении к YooKassa: {e}")

    if resp.status_code not in (200, 201):
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"text": resp.text}
        raise HTTPException(status_code=resp.status_code, detail={
            "message": "Ошибка ответа YooKassa", "upstream": err_json
        })

    data = resp.json()
    confirmation = data.get("confirmation") or {}
    token = confirmation.get("confirmation_token")
    if not token:
        raise HTTPException(status_code=500, detail={
            "message": "Нет confirmation_token в ответе YooKassa", "upstream": data
        })

    # best-effort запись в Supabase
    try:
        amount_int = int(round(float(body.amount)))
        supabase_insert_donation(
            user_id=0,
            amount_rub=amount_int,
            payment_id=str(data.get("id", "")),
            email=body.email,
        )
    except Exception:
        pass

    return CreatePaymentResponse(
        payment_id=data.get("id", ""),
        status=data.get("status", "unknown"),
        confirmation_token=token,
    )


class CreatePaymentRedirectResponse(BaseModel):
    payment_id: str
    status: str
    confirmation_url: str


@router.post("/yookassa/create-payment-sbp", response_model=CreatePaymentRedirectResponse)
def create_payment_sbp(body: CreatePaymentRequest) -> CreatePaymentRedirectResponse:
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        raise HTTPException(
            status_code=500, detail="YOOKASSA_SHOP_ID или YOOKASSA_SECRET_KEY не заданы в окружении")

    headers = {
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    receipt: dict = {
        "items": [
            {
                "description": (body.description or "Пожертвование")[:128],
                "quantity": "1.0",
                "amount": {
                    "value": f"{body.amount:.2f}",
                    "currency": "RUB",
                },
                "vat_code": 1,
            }
        ]
    }
    try:
        if YOOKASSA_TAX_SYSTEM_CODE:
            receipt["tax_system_code"] = int(YOOKASSA_TAX_SYSTEM_CODE)
        else:
            receipt["tax_system_code"] = 1
    except ValueError:
        receipt["tax_system_code"] = 1

    customer: dict = {}
    if body.email:
        customer["email"] = body.email
    norm_phone = _normalize_phone(body.phone)
    if norm_phone:
        customer["phone"] = norm_phone
    if customer:
        receipt["customer"] = customer

    default_return = CLIENT_ORIGIN or "http://localhost:8080"
    payload = {
        "amount": {"value": f"{body.amount:.2f}", "currency": "RUB"},
        "capture": True,
        "payment_method_data": {"type": "sbp"},
        "confirmation": {"type": "redirect", "return_url": body.return_url or default_return},
        "description": body.description or "Пожертвование",
        "receipt": receipt,
    }

    try:
        resp = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
            timeout=20,
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502, detail=f"Ошибка сети при обращении к YooKassa: {e}")

    if resp.status_code not in (200, 201):
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"text": resp.text}
        raise HTTPException(status_code=resp.status_code, detail={
            "message": "Ошибка ответа YooKassa", "upstream": err_json
        })

    data = resp.json()
    confirmation = data.get("confirmation") or {}
    url = confirmation.get("confirmation_url")
    if not url:
        raise HTTPException(status_code=500, detail={
            "message": "Нет confirmation_url для СБП", "upstream": data
        })

    return CreatePaymentRedirectResponse(
        payment_id=data.get("id", ""),
        status=data.get("status", "unknown"),
        confirmation_url=url,
    )


@router.post("/yookassa/create-payment-redirect", response_model=CreatePaymentRedirectResponse)
def create_payment_redirect(body: CreatePaymentRequest) -> CreatePaymentRedirectResponse:
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        raise HTTPException(
            status_code=500, detail="YOOKASSA_SHOP_ID или YOOKASSA_SECRET_KEY не заданы в окружении")

    headers = {
        "Idempotence-Key": str(uuid.uuid4()),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    receipt: dict = {
        "items": [
            {
                "description": (body.description or "Пожертвование")[:128],
                "quantity": "1.0",
                "amount": {"value": f"{body.amount:.2f}", "currency": "RUB"},
                "vat_code": 1,
            }
        ]
    }
    try:
        if YOOKASSA_TAX_SYSTEM_CODE:
            receipt["tax_system_code"] = int(YOOKASSA_TAX_SYSTEM_CODE)
        else:
            receipt["tax_system_code"] = 1
    except ValueError:
        receipt["tax_system_code"] = 1

    customer: dict = {}
    if body.email:
        customer["email"] = body.email
    norm_phone = _normalize_phone(body.phone)
    if norm_phone:
        customer["phone"] = norm_phone
    if customer:
        receipt["customer"] = customer

    default_return = CLIENT_ORIGIN or "http://localhost:8080"
    payload = {
        "amount": {"value": f"{body.amount:.2f}", "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": body.return_url or default_return},
        "description": body.description or "Пожертвование",
        "receipt": receipt,
    }

    try:
        resp = requests.post(
            "https://api.yookassa.ru/v3/payments",
            json=payload,
            headers=headers,
            auth=HTTPBasicAuth(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY),
            timeout=20,
        )
    except requests.RequestException as e:
        raise HTTPException(
            status_code=502, detail=f"Ошибка сети при обращении к YooKassa: {e}")

    if resp.status_code not in (200, 201):
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"text": resp.text}
        raise HTTPException(status_code=resp.status_code, detail={
            "message": "Ошибка ответа YooKassa", "upstream": err_json
        })

    data = resp.json()
    confirmation = data.get("confirmation") or {}
    url = confirmation.get("confirmation_url")
    if not url:
        raise HTTPException(status_code=500, detail={
            "message": "Нет confirmation_url для redirect", "upstream": data
        })

    return CreatePaymentRedirectResponse(
        payment_id=data.get("id", ""),
        status=data.get("status", "unknown"),
        confirmation_url=url,
    )


@router.post("/donations/mark-complete")
def donations_mark_complete(body: MarkCompleteRequest) -> dict:
    if not body.payment_id:
        raise HTTPException(status_code=400, detail="payment_id is required")
    try:
        supabase_mark_complete(payment_id=body.payment_id,
                               status=body.status or "succeeded", email=body.email)
    except Exception:
        pass
    return {"ok": True}
