from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
import smtplib
from email.message import EmailMessage
import requests
import json
import os
from datetime import datetime

router = APIRouter()

@router.post("/notify/email")
async def send_email_notification(request: Dict[str, Any] = Body(...)):
    """Envía una notificación por email."""
    try:
        # Validar los datos
        if "email" not in request or "subject" not in request or "message" not in request:
            raise HTTPException(status_code=400, detail="Faltan datos requeridos: email, subject, message")

        # Preparar el mensaje
        msg = EmailMessage()
        msg['Subject'] = request["subject"]
        msg['From'] = "noreply@example.com"
        msg['To'] = request["email"]
        msg.set_content(request["message"])

        # Configurar el servidor SMTP (simulado)
        print(f"Conectando al servidor SMTP: smtp.example.com")
        print(f"Enviando email a {request['email']}")
        print(f"Asunto: {request['subject']}")

        # Registrar la notificación
        notification_id = f"email-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Guardar un registro (simulado)
        log_entry = {
            "notification_id": notification_id,
            "type": "email",
            "recipient": request["email"],
            "subject": request["subject"],
            "timestamp": datetime.now().isoformat(),
            "status": "sent"
        }

        print(f"Registro guardado: {json.dumps(log_entry)}")

        return {
            "notification_id": notification_id,
            "status": "sent",
            "recipient": request["email"],
            "type": "email"
        }

    except Exception as e:
        print(f"Error enviando email: {e}")
        raise HTTPException(status_code=500, detail=f"Error enviando email: {str(e)}")

@router.post("/notify/sms")
async def send_sms_notification(request: Dict[str, Any] = Body(...)):
    """Envía una notificación por SMS."""
    try:
        # Validar los datos
        if "phone_number" not in request or "message" not in request:
            raise HTTPException(status_code=400, detail="Faltan datos requeridos: phone_number, message")

        # Preparar el mensaje SMS (simulado)
        sms_api_url = "https://sms-api.example.com/send"

        # Configurar la solicitud SMS (simulada)
        print(f"Conectando a la API de SMS: {sms_api_url}")
        print(f"Enviando SMS a {request['phone_number']}")
        print(f"Mensaje: {request['message'][:20]}...")

        # Registrar la notificación
        notification_id = f"sms-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Guardar un registro (simulado)
        log_entry = {
            "notification_id": notification_id,
            "type": "sms",
            "recipient": request["phone_number"],
            "message": request["message"],
            "timestamp": datetime.now().isoformat(),
            "status": "sent"
        }

        print(f"Registro guardado: {json.dumps(log_entry)}")

        return {
            "notification_id": notification_id,
            "status": "sent",
            "recipient": request["phone_number"],
            "type": "sms"
        }

    except Exception as e:
        print(f"Error enviando SMS: {e}")
        raise HTTPException(status_code=500, detail=f"Error enviando SMS: {str(e)}")