# Demostraciones de Principios SOLID

Este documento contiene ejemplos sencillos para demostrar cómo aplicar los principios SOLID en situaciones similares a las de la tarea asignada.

## Demostración 1: Procesador de Archivos de Texto

### Código Original (Violación de SRP)

El siguiente código combina múltiples responsabilidades en un solo archivo:
1. Leer archivos de texto
2. Procesar el texto (dividirlo en frases)
3. Manejar rutas HTTP

```python
# archivo: text_processor.py (código espagueti)
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import re
import uuid
from typing import List, Dict, Any

router = APIRouter()

def extract_text_from_file(file_content: bytes) -> str:
    """Extrae el texto de un archivo."""
    try:
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        # Intentar con otra codificación si utf-8 falla
        return file_content.decode('latin-1')

def split_into_sentences(text: str, min_length: int = 20) -> List[Dict[str, Any]]:
    """Divide el texto en frases."""
    # Patrón simple para dividir por puntos, exclamaciones o interrogaciones
    sentence_endings = r'[.!?]'
    raw_sentences = re.split(sentence_endings, text)

    sentences = []
    for i, sentence in enumerate(raw_sentences):
        sentence = sentence.strip()
        # Omitir frases muy cortas
        if len(sentence) >= min_length:
            sentence_obj = {
                "id": i,
                "text": sentence,
                "length": len(sentence)
            }
            sentences.append(sentence_obj)

    return sentences

@router.post("/upload-text")
async def upload_text_file(file: UploadFile = File(...)):
    """Sube un archivo de texto, extrae y divide en frases."""
    try:
        # Leer el contenido del archivo
        file_content = await file.read()

        # Extraer texto del archivo
        text = extract_text_from_file(file_content)

        # Generar un ID único para este archivo
        file_id = str(uuid.uuid4())

        # Dividir el texto en frases
        sentences = split_into_sentences(text)

        # Crear metadata
        file_metadata = {
            "file_id": file_id,
            "filename": file.filename,
            "total_sentences": len(sentences)
        }

        # Guardar el resultado (simulado)
        output_dir = f"./processed/{file_id}"
        os.makedirs(output_dir, exist_ok=True)

        # Simular guardado del resultado
        print(f"Guardando {len(sentences)} frases en {output_dir}")

        return {
            "file_id": file_id,
            "filename": file.filename,
            "num_sentences": len(sentences),
            "first_sentence": sentences[0]["text"] if sentences else ""
        }

    except Exception as e:
        print(f"Error procesando archivo de texto: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
```

### Problema con el código original:

El código viola el **Principio de Responsabilidad Única (SRP)** porque:
1. La clase maneja múltiples responsabilidades: extraer texto, procesar texto y manejar rutas HTTP
2. Si cambia la forma de extraer texto o procesarlo, hay que modificar este mismo archivo
3. Es difícil reutilizar las funcionalidades por separado
4. Probar cada parte de forma aislada es complicado

### Solución Refactorizada:

Para seguir SRP, dividiremos el código en tres clases separadas, cada una con una única responsabilidad:

1. **TextExtractor**: Para extraer texto de archivos
2. **SentenceSplitter**: Para dividir el texto en frases
3. **Mantener el Router**: Pero delegar el trabajo a las clases específicas

#### 1. services/text/extractor.py
```python
class TextExtractor:
    """Clase responsable de extraer texto de archivos."""

    def extract_text(self, file_content: bytes) -> str:
        """Extrae el texto de un archivo."""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Intentar con otra codificación si utf-8 falla
            return file_content.decode('latin-1')
```

#### 2. services/text/splitter.py
```python
import re
from typing import List, Dict, Any

class SentenceSplitter:
    """Clase responsable de dividir texto en frases."""

    def __init__(self, min_length: int = 20):
        self.min_length = min_length

    def split_into_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Divide el texto en frases."""
        # Patrón simple para dividir por puntos, exclamaciones o interrogaciones
        sentence_endings = r'[.!?]'
        raw_sentences = re.split(sentence_endings, text)

        sentences = []
        for i, sentence in enumerate(raw_sentences):
            sentence = sentence.strip()
            # Omitir frases muy cortas
            if len(sentence) >= self.min_length:
                sentence_obj = {
                    "id": i,
                    "text": sentence,
                    "length": len(sentence)
                }
                sentences.append(sentence_obj)

        return sentences
```

#### 3. routes/text_routes.py
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
from ..services.text.extractor import TextExtractor
from ..services.text.splitter import SentenceSplitter

router = APIRouter()

# Inicializar servicios
text_extractor = TextExtractor()
sentence_splitter = SentenceSplitter()

@router.post("/upload-text")
async def upload_text_file(file: UploadFile = File(...)):
    """Sube un archivo de texto, extrae y divide en frases."""
    try:
        # Leer el contenido del archivo
        file_content = await file.read()

        # Extraer texto del archivo usando TextExtractor
        text = text_extractor.extract_text(file_content)

        # Generar un ID único para este archivo
        file_id = str(uuid.uuid4())

        # Dividir el texto en frases usando SentenceSplitter
        sentences = sentence_splitter.split_into_sentences(text)

        # Crear metadata
        file_metadata = {
            "file_id": file_id,
            "filename": file.filename,
            "total_sentences": len(sentences)
        }

        # Guardar el resultado (simulado)
        output_dir = f"./processed/{file_id}"
        os.makedirs(output_dir, exist_ok=True)

        # Simular guardado del resultado
        print(f"Guardando {len(sentences)} frases en {output_dir}")

        return {
            "file_id": file_id,
            "filename": file.filename,
            "num_sentences": len(sentences),
            "first_sentence": sentences[0]["text"] if sentences else ""
        }

    except Exception as e:
        print(f"Error procesando archivo de texto: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
```

### Beneficios de la Refactorización:

1. **Mejor organización**: Cada clase tiene una única responsabilidad bien definida
2. **Mayor reusabilidad**: Las clases `TextExtractor` y `SentenceSplitter` pueden usarse en otros contextos
3. **Mejor testabilidad**: Podemos probar cada componente por separado
4. **Mantenimiento más sencillo**: Si cambia la forma de extraer texto o procesarlo, solo necesitamos modificar la clase correspondiente

## Demostración 2: Sistema de Notificaciones

### Código Original (Violación de SRP y Duplicación)

El siguiente código maneja el envío de notificaciones de dos tipos (email y SMS) con mucha duplicación:

```python
# archivo: notification_system.py (código espagueti)
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
```

### Problema con el código original:

El código tiene varios problemas:

1. **Violación del Principio de Responsabilidad Única (SRP)**: Las funciones hacen demasiadas cosas: validación, envío de mensajes y registro de eventos.

2. **Duplicación de código**: Los dos endpoints tienen lógica muy similar, violando el principio DRY (Don't Repeat Yourself).

3. **Difícil de mantener**: Si cambia la forma de registrar notificaciones, hay que modificar dos lugares.

### Solución Refactorizada:

Para resolver estos problemas, crearemos:
1. Un servicio de notificaciones con una interfaz común
2. Implementaciones específicas para email y SMS
3. Un servicio para registrar las notificaciones

#### 1. services/notifications/notification_service.py
```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any

class NotificationService(ABC):
    """Interfaz base para servicios de notificación."""

    @abstractmethod
    def send(self, recipient: str, content: Dict[str, Any]) -> str:
        """
        Envía una notificación y devuelve el ID de notificación.
        """
        pass

    def _generate_notification_id(self, prefix: str) -> str:
        """Genera un ID único para la notificación."""
        return f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _log_notification(self, notification_id: str, notification_type: str,
                         recipient: str, content: Dict[str, Any], status: str) -> None:
        """Registra la notificación enviada."""
        log_entry = {
            "notification_id": notification_id,
            "type": notification_type,
            "recipient": recipient,
            "timestamp": datetime.now().isoformat(),
            "status": status
        }

        # Agregar contenido específico al registro
        for key, value in content.items():
            log_entry[key] = value

        print(f"Registro guardado: {log_entry}")
```

#### 2. services/notifications/email_service.py
```python
from typing import Dict, Any
from .notification_service import NotificationService
from email.message import EmailMessage

class EmailService(NotificationService):
    """Servicio para enviar notificaciones por email."""

    def __init__(self, sender_email: str = "noreply@example.com", smtp_server: str = "smtp.example.com"):
        self.sender_email = sender_email
        self.smtp_server = smtp_server

    def send(self, recipient: str, content: Dict[str, Any]) -> str:
        """Envía una notificación por email."""
        if "subject" not in content or "message" not in content:
            raise ValueError("El contenido debe incluir 'subject' y 'message'")

        # Preparar el mensaje
        msg = EmailMessage()
        msg['Subject'] = content["subject"]
        msg['From'] = self.sender_email
        msg['To'] = recipient
        msg.set_content(content["message"])

        # Configurar el servidor SMTP (simulado)
        print(f"Conectando al servidor SMTP: {self.smtp_server}")
        print(f"Enviando email a {recipient}")
        print(f"Asunto: {content['subject']}")

        # Generar ID y registrar la notificación
        notification_id = self._generate_notification_id("email")
        self._log_notification(
            notification_id=notification_id,
            notification_type="email",
            recipient=recipient,
            content=content,
            status="sent"
        )

        return notification_id
```

#### 3. services/notifications/sms_service.py
```python
from typing import Dict, Any
from .notification_service import NotificationService

class SMSService(NotificationService):
    """Servicio para enviar notificaciones por SMS."""

    def __init__(self, api_url: str = "https://sms-api.example.com/send"):
        self.api_url = api_url

    def send(self, recipient: str, content: Dict[str, Any]) -> str:
        """Envía una notificación por SMS."""
        if "message" not in content:
            raise ValueError("El contenido debe incluir 'message'")

        # Configurar la solicitud SMS (simulada)
        print(f"Conectando a la API de SMS: {self.api_url}")
        print(f"Enviando SMS a {recipient}")
        print(f"Mensaje: {content['message'][:20]}...")

        # Generar ID y registrar la notificación
        notification_id = self._generate_notification_id("sms")
        self._log_notification(
            notification_id=notification_id,
            notification_type="sms",
            recipient=recipient,
            content=content,
            status="sent"
        )

        return notification_id
```

#### 4. routes/notification_routes.py
```python
from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any

from ..services.notifications.email_service import EmailService
from ..services.notifications.sms_service import SMSService

router = APIRouter()

# Inicializar servicios
email_service = EmailService()
sms_service = SMSService()

@router.post("/notify/email")
async def send_email_notification(request: Dict[str, Any] = Body(...)):
    """Envía una notificación por email."""
    try:
        # Validar los datos
        if "email" not in request or "subject" not in request or "message" not in request:
            raise HTTPException(status_code=400, detail="Faltan datos requeridos: email, subject, message")

        # Usar el servicio de email para enviar la notificación
        notification_id = email_service.send(
            recipient=request["email"],
            content={
                "subject": request["subject"],
                "message": request["message"]
            }
        )

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

        # Usar el servicio de SMS para enviar la notificación
        notification_id = sms_service.send(
            recipient=request["phone_number"],
            content={
                "message": request["message"]
            }
        )

        return {
            "notification_id": notification_id,
            "status": "sent",
            "recipient": request["phone_number"],
            "type": "sms"
        }

    except Exception as e:
        print(f"Error enviando SMS: {e}")
        raise HTTPException(status_code=500, detail=f"Error enviando SMS: {str(e)}")
```

### Beneficios de la Refactorización:

1. **Mejor SRP**: Cada clase tiene una responsabilidad única y bien definida.
2. **Eliminación de duplicación**: La lógica común está en la clase base `NotificationService`.
3. **Extensibilidad**: Es fácil agregar nuevos tipos de notificaciones (por ejemplo, notificaciones push).
4. **Mejor testabilidad**: Podemos probar cada componente de forma aislada.
5. **Más mantenible**: Si cambia la forma de registrar notificaciones, solo hay que modificar un lugar.

## Resumen de las Refactorizaciones

Estas demostraciones muestran cómo aplicar los principios SOLID a código con problemas comunes:

1. **Demostración 1 (SRP)**: Separar responsabilidades de procesamiento de archivos en clases específicas.
2. **Demostración 2 (SRP + DRY)**: Eliminar duplicación y crear una jerarquía para manejar diferentes tipos de notificaciones.

Los beneficios clave de estas refactorizaciones son:
- Código más organizado y fácil de entender
- Mayor reutilización de código
- Mejor testabilidad
- Mantenimiento más sencillo
- Mayor flexibilidad para futuros cambios