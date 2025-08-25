# 🔧 utils.py - Utilidades y Helpers v1.0
import requests
import logging
from config import *

logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, text, parse_mode=None):
    """Enviar mensaje a Telegram optimizado"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        if parse_mode:
            data["parse_mode"] = parse_mode
        
        # Dividir mensaje si es muy largo
        if len(text) > MAX_MESSAGE_LENGTH:
            chunks = split_long_message(text)
            success = True
            for chunk in chunks:
                chunk_data = {"chat_id": chat_id, "text": chunk}
                if parse_mode:
                    chunk_data["parse_mode"] = parse_mode
                response = requests.post(url, json=chunk_data, timeout=TELEGRAM_TIMEOUT)
                if response.status_code != 200:
                    success = False
                    logger.error(f"❌ Telegram chunk error: {response.status_code}")
            return success
        else:
            response = requests.post(url, json=data, timeout=TELEGRAM_TIMEOUT)
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"❌ Telegram error: {e}")
        return False

def setup_webhook():
    """Configurar webhook de Telegram"""
    try:
        # Delete webhook primero
        delete_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
        requests.post(delete_url, timeout=WEBHOOK_TIMEOUT)
        
        # Set nuevo webhook
        webhook_url = f"{WEBHOOK_URL}/telegram-webhook"
        set_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook"
        data = {"url": webhook_url}
        
        response = requests.post(set_url, json=data, timeout=WEBHOOK_TIMEOUT)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                logger.info(f"✅ Webhook configured: {webhook_url}")
                return True
        
        logger.error(f"❌ Webhook setup failed: {response.text}")
        return False
    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return False

def validate_telegram_token():
    """Validar token de Telegram"""
    if not TELEGRAM_TOKEN:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, timeout=WEBHOOK_TIMEOUT)
        return response.status_code == 200 and response.json().get('ok', False)
    except:
        return False

def split_long_message(text, max_length=MAX_MESSAGE_LENGTH):
    """Dividir mensaje largo en chunks"""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Dividir por líneas para mantener formato
    lines = text.split('\n')
    
    for line in lines:
        # Si una línea sola es muy larga, dividirla por palabras
        if len(line) > max_length:
            words = line.split(' ')
            current_line = ""
            
            for word in words:
                if len(current_line) + len(word) + 1 <= max_length:
                    current_line += word + " "
                else:
                    if current_line:
                        if len(current_chunk) + len(current_line) <= max_length:
                            current_chunk += current_line + "\n"
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = current_line + "\n"
                    current_line = word + " "
            
            if current_line:
                if len(current_chunk) + len(current_line) <= max_length:
                    current_chunk += current_line + "\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = current_line + "\n"
        else:
            # Línea normal
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def format_error_message(error, context=""):
    """Formatear mensaje de error para usuario"""
    error_str = str(error)
    
    # Errores comunes y sus traducciones
    error_mappings = {
        "timeout": "⏱️ Tiempo de espera agotado. Intenta nuevamente.",
        "connection": "🔌 Error de conexión. Verifica tu internet.",
        "unauthorized": "🔐 Error de autorización. Contacta soporte.",
        "not found": "🔍 Recurso no encontrado.",
        "server error": "🖥️ Error del servidor. Intenta más tarde.",
        "404": "🔍 No encontrado.",
        "400": "⚠️ Solicitud incorrecta.",
        "500": "🖥️ Error interno del servidor.",
        "502": "🔄 Servidor temporalmente no disponible.",
        "503": "⚠️ Servicio temporalmente no disponible."
    }
    
    for key, message in error_mappings.items():
        if key in error_str.lower():
            return f"{message}\n\n**Contexto:** {context}" if context else message
    
    return f"❌ Error: {error_str}\n\n**Contexto:** {context}" if context else f"❌ Error: {error_str}"

def clean_document_number(doc_number):
    """Limpiar número de documento"""
    if not doc_number:
        return ""
    
    return str(doc_number).strip().replace('-', '').replace('.', '').replace(' ', '').replace(',', '')

def format_document_number(doc_number, doc_type=""):
    """Formatear número de documento para visualización"""
    try:
        clean_num = clean_document_number(doc_number)
        
        if not clean_num.isdigit():
            return doc_number  # Retornar original si no es numérico
        
        # Formatear según tipo
        if doc_type.upper() == "NIT" and len(clean_num) >= 9:
            # Formato NIT: XXX.XXX.XXX-X
            if len(clean_num) == 9:
                return f"{clean_num[:3]}.{clean_num[3:6]}.{clean_num[6:9]}"
            elif len(clean_num) == 10:
                return f"{clean_num[:3]}.{clean_num[3:6]}.{clean_num[6:9]}-{clean_num[9]}"
            else:
                return clean_num
        elif doc_type.upper() == "CC" and len(clean_num) >= 7:
            # Formato CC: XX.XXX.XXX
            if len(clean_num) <= 8:
                return f"{clean_num[:-6]}.{clean_num[-6:-3]}.{clean_num[-3:]}"
            else:
                return f"{clean_num[:-6]}.{clean_num[-6:-3]}.{clean_num[-3:]}"
        else:
            return clean_num
            
    except:
        return doc_number

def safe_get(dictionary, key, default="N/A"):
    """Obtener valor de diccionario de forma segura"""
    try:
        value = dictionary.get(key, default)
        return value if value is not None and str(value).strip() != "" else default
    except:
        return default

def format_currency(amount, currency='COP'):
    """Formatear moneda"""
    try:
        if currency == 'COP':
            return f"${float(amount):,.0f} COP"
        elif currency == 'USD':
            return f"${float(amount):,.2f} USD"
        else:
            return f"{float(amount):,.2f} {currency}"
    except:
        return "N/A"

def format_phone_number(phone):
    """Formatear número de teléfono"""
    try:
        clean_phone = str(phone).strip().replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        if not clean_phone.isdigit():
            return phone
        
        # Formato colombiano
        if len(clean_phone) == 10 and clean_phone.startswith('3'):
            # Celular: 3XX XXX XXXX
            return f"{clean_phone[:3]} {clean_phone[3:6]} {clean_phone[6:]}"
        elif len(clean_phone) == 7:
            # Fijo: XXX XXXX
            return f"{clean_phone[:3]} {clean_phone[3:]}"
        elif len(clean_phone) == 10:
            # Fijo con código: (XX) XXX XXXX
            return f"({clean_phone[:2]}) {clean_phone[2:5]} {clean_phone[5:]}"
        else:
            return clean_phone
            
    except:
        return phone

def truncate_text(text, max_length=100, suffix="..."):
    """Truncar texto con sufijo"""
    try:
        if not text or len(str(text)) <= max_length:
            return str(text)
        
        return str(text)[:max_length-len(suffix)] + suffix
    except:
        return str(text)

def validate_email(email):
    """Validar formato de email básico"""
    try:
        if not email or '@' not in email:
            return False
        
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain or '.' not in domain:
            return False
        
        return True
    except:
        return False

def format_datetime(timestamp):
    """Formatear timestamp a fecha legible"""
    try:
        from datetime import datetime
        if isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
        
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(timestamp)

def log_performance(func_name, start_time, additional_info=""):
    """Log de performance para debugging"""
    import time
    end_time = time.time()
    duration = (end_time - start_time) * 1000  # en ms
    
    if duration > 2000:  # > 2 segundos
        logger.warning(f"⚠️ SLOW: {func_name} took {duration:.1f}ms {additional_info}")
    elif duration > 1000:  # > 1 segundo
        logger.info(f"⏱️ {func_name} took {duration:.1f}ms {additional_info}")
    else:
        logger.info(f"✅ {func_name} completed in {duration:.1f}ms {additional_info}")
    
    return duration

def get_client_summary_text(client_data):
    """Generar resumen textual de cliente"""
    try:
        if not isinstance(client_data, dict):
            return "Datos de cliente inválidos"
        
        # Campos prioritarios para mostrar
        summary_parts = []
        
        # Nombre/Razón Social
        name_fields = ['nombre', 'name', 'razon_social', 'business_name', 'company_name', 'client_name']
        for field in name_fields:
            if field in client_data and client_data[field]:
                summary_parts.append(f"**{client_data[field]}**")
                break
        
        # Documento
        doc_fields = ['nit', 'cedula', 'documento', 'doc_number', 'identification']
        for field in doc_fields:
            if field in client_data and client_data[field]:
                summary_parts.append(f"Doc: {client_data[field]}")
                break
        
        # Ubicación
        location_parts = []
        city_fields = ['ciudad', 'city', 'municipio']
        for field in city_fields:
            if field in client_data and client_data[field]:
                location_parts.append(str(client_data[field]))
                break
        
        state_fields = ['departamento', 'estado', 'state']
        for field in state_fields:
            if field in client_data and client_data[field]:
                location_parts.append(str(client_data[field]))
                break
        
        if location_parts:
            summary_parts.append(f"📍 {' - '.join(location_parts)}")
        
        # Contacto
        contact_parts = []
        if any(field in client_data and client_data[field] for field in ['email', 'correo']):
            for field in ['email', 'correo']:
                if field in client_data and client_data[field]:
                    contact_parts.append(f"📧 {client_data[field]}")
                    break
        
        if any(field in client_data and client_data[field] for field in ['telefono', 'phone', 'celular']):
            for field in ['telefono', 'phone', 'celular']:
                if field in client_data and client_data[field]:
                    formatted_phone = format_phone_number(client_data[field])
                    contact_parts.append(f"📞 {formatted_phone}")
                    break
        
        if contact_parts:
            summary_parts.extend(contact_parts)
        
        return "\n".join(summary_parts) if summary_parts else "Información de cliente disponible"
        
    except Exception as e:
        logger.error(f"❌ Error generating client summary: {e}")
        return "Error generando resumen de cliente"
