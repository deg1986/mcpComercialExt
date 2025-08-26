# 🏢 nocodb_service.py - Servicio de Comerciales NocoDB v1.0
import requests
import logging
import re
from config import *

logger = logging.getLogger(__name__)

def validate_email_format(email):
    """Validar formato de email con regex mejorado"""
    try:
        if not email or not isinstance(email, str):
            return {"valid": False, "error": "Email requerido"}
        
        email = email.strip().lower()
        
        # Regex para validar formato básico de email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            return {"valid": False, "error": "Formato de email inválido"}
        
        # Validar dominios comunes
        valid_extensions = ['.com', '.co', '.net', '.org', '.edu', '.gov', '.mil']
        if not any(email.endswith(ext) for ext in valid_extensions):
            return {"valid": False, "error": "Extensión de email no válida (debe terminar en .com, .co, .net, etc.)"}
        
        return {"valid": True, "cleaned_email": email}
        
    except Exception as e:
        logger.error(f"❌ Error validating email: {e}")
        return {"valid": False, "error": f"Error validando email: {str(e)}"}

def validate_cedula_format(cedula):
    """Validar formato de cédula para comercial"""
    try:
        if not cedula:
            return {"valid": False, "error": "Cédula requerida"}
        
        # Limpiar cédula
        clean_cedula = str(cedula).strip().replace('-', '').replace('.', '').replace(' ', '')
        
        # Validar que solo contenga números
        if not clean_cedula.isdigit():
            return {"valid": False, "error": "La cédula debe contener solo números"}
        
        # Validar longitud
        if len(clean_cedula) < MIN_CEDULA_LENGTH or len(clean_cedula) > MAX_CEDULA_LENGTH:
            return {"valid": False, "error": f"La cédula debe tener entre {MIN_CEDULA_LENGTH} y {MAX_CEDULA_LENGTH} dígitos"}
        
        return {"valid": True, "cleaned_cedula": clean_cedula}
        
    except Exception as e:
        return {"valid": False, "error": f"Error validando cédula: {str(e)}"}

def validate_name_format(name):
    """Validar formato de nombre"""
    try:
        if not name or not isinstance(name, str):
            return {"valid": False, "error": "Nombre requerido"}
        
        name = name.strip()
        
        # Validar longitud
        if len(name) < MIN_NAME_LENGTH:
            return {"valid": False, "error": f"El nombre debe tener al menos {MIN_NAME_LENGTH} caracteres"}
        
        if len(name) > MAX_NAME_LENGTH:
            return {"valid": False, "error": f"El nombre no puede tener más de {MAX_NAME_LENGTH} caracteres"}
        
        # Validar caracteres (solo letras, espacios y algunos caracteres especiales)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\.\-\']+$', name):
            return {"valid": False, "error": "El nombre solo puede contener letras, espacios, puntos, guiones y apostrofes"}
        
        return {"valid": True, "cleaned_name": name.title()}  # Capitalizar primera letra
        
    except Exception as e:
        return {"valid": False, "error": f"Error validando nombre: {str(e)}"}

def validate_phone_format(phone):
    """Validar formato de teléfono"""
    try:
        if not phone:
            return {"valid": False, "error": "Teléfono requerido"}
        
        phone = str(phone).strip()
        
        # Permitir números, espacios, guiones, paréntesis y signo +
        clean_phone = re.sub(r'[^\d\+\-\(\)\s]', '', phone)
        
        # Extraer solo números para validar longitud
        digits_only = re.sub(r'[^\d]', '', clean_phone)
        
        if len(digits_only) < MIN_PHONE_LENGTH:
            return {"valid": False, "error": f"El teléfono debe tener al menos {MIN_PHONE_LENGTH} dígitos"}
        
        if len(digits_only) > MAX_PHONE_LENGTH:
            return {"valid": False, "error": f"El teléfono no puede tener más de {MAX_PHONE_LENGTH} dígitos"}
        
        return {"valid": True, "cleaned_phone": clean_phone}
        
    except Exception as e:
        return {"valid": False, "error": f"Error validando teléfono: {str(e)}"}

def check_comercial_exists(cedula):
    """Verificar si el comercial ya existe en NocoDB"""
    try:
        logger.info(f"🔍 Checking if comercial exists: {cedula}")
        
        # Validar cédula primero
        validation = validate_cedula_format(cedula)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        clean_cedula = validation["cleaned_cedula"]
        
        # Construir URL para consulta
        url = f"{NOCODB_BASE_URL}/tables/{NOCODB_TABLE_ID}/records"
        params = {
            "where": f"(cedula,eq,{clean_cedula})",
            "limit": 1,
            "shuffle": 0,
            "offset": 0
        }
        
        headers = {
            "accept": "application/json",
            "xc-token": NOCODB_TOKEN
        }
        
        logger.info(f"📡 Making request to NocoDB: {url}")
        response = requests.get(url, params=params, headers=headers, timeout=NOCODB_TIMEOUT)
        
        logger.info(f"📡 NocoDB Response: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"❌ NocoDB HTTP Error: {response.status_code} - {response.text}")
            return {"success": False, "error": f"Error consultando base de datos: HTTP {response.status_code}"}
        
        data = response.json()
        page_info = data.get("pageInfo", {})
        total_rows = page_info.get("totalRows", 0)
        
        logger.info(f"📊 Query result: totalRows = {total_rows}")
        
        if total_rows > 0:
            # Comercial ya existe
            existing_records = data.get("list", [])
            existing_comercial = existing_records[0] if existing_records else {}
            
            logger.info(f"👤 Comercial already exists: {clean_cedula}")
            return {
                "success": True, 
                "exists": True,
                "comercial_data": existing_comercial,
                "message": f"El comercial con cédula {clean_cedula} ya está registrado en el sistema"
            }
        else:
            logger.info(f"✅ Comercial does not exist: {clean_cedula}")
            return {
                "success": True, 
                "exists": False,
                "message": f"La cédula {clean_cedula} está disponible para registro"
            }
        
    except Exception as e:
        logger.error(f"❌ Error checking comercial existence: {e}")
        return {"success": False, "error": f"Error verificando comercial: {str(e)}"}

def create_comercial(cedula, email, name, phone):
    """Crear nuevo comercial en NocoDB"""
    try:
        logger.info(f"🏗️ Creating comercial: {cedula}")
        
        # Validar todos los campos
        validations = {
            "cedula": validate_cedula_format(cedula),
            "email": validate_email_format(email),
            "name": validate_name_format(name),
            "phone": validate_phone_format(phone)
        }
        
        # Verificar si hay errores de validación
        validation_errors = []
        for field, validation in validations.items():
            if not validation["valid"]:
                validation_errors.append(f"{field.capitalize()}: {validation['error']}")
        
        if validation_errors:
            error_message = "\n".join(validation_errors)
            logger.warning(f"⚠️ Validation errors: {error_message}")
            return {"success": False, "error": f"Errores de validación:\n{error_message}"}
        
        # Extraer valores limpios
        clean_data = {
            "cedula": validations["cedula"]["cleaned_cedula"],
            "email": validations["email"]["cleaned_email"],
            "name": validations["name"]["cleaned_name"],
            "phone": validations["phone"]["cleaned_phone"]
        }
        
        # Verificar que el comercial no exista antes de crear
        exists_check = check_comercial_exists(clean_data["cedula"])
        if not exists_check["success"]:
            return {"success": False, "error": f"Error verificando existencia: {exists_check['error']}"}
        
        if exists_check["exists"]:
            return {"success": False, "error": exists_check["message"]}
        
        # Construir request para creación
        url = f"{NOCODB_BASE_URL}/tables/{NOCODB_TABLE_ID}/records"
        
        headers = {
            "accept": "application/json",
            "xc-token": NOCODB_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = clean_data
        
        logger.info(f"📡 Making POST request to NocoDB: {url}")
        logger.info(f"📋 Payload: {payload}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=NOCODB_TIMEOUT)
        
        logger.info(f"📡 NocoDB Response: {response.status_code}")
        
        if response.status_code in [200, 201]:
            created_comercial = response.json()
            logger.info(f"✅ Comercial created successfully: {clean_data['cedula']}")
            
            return {
                "success": True,
                "comercial_data": created_comercial,
                "message": f"Comercial {clean_data['name']} creado exitosamente",
                "details": {
                    "cedula": clean_data["cedula"],
                    "email": clean_data["email"],
                    "name": clean_data["name"],
                    "phone": clean_data["phone"]
                }
            }
        else:
            logger.error(f"❌ NocoDB Create Error: {response.status_code} - {response.text}")
            return {
                "success": False, 
                "error": f"Error creando comercial: HTTP {response.status_code}\n{response.text}"
            }
        
    except Exception as e:
        logger.error(f"❌ Error creating comercial: {e}")
        return {"success": False, "error": f"Error creando comercial: {str(e)}"}

def get_comercial_info(cedula):
    """Obtener información detallada de un comercial"""
    try:
        exists_check = check_comercial_exists(cedula)
        
        if not exists_check["success"]:
            return exists_check
        
        if not exists_check["exists"]:
            return {"success": True, "found": False, "message": "Comercial no encontrado"}
        
        comercial_data = exists_check["comercial_data"]
        
        return {
            "success": True,
            "found": True,
            "comercial_data": comercial_data,
            "formatted_info": format_comercial_info(comercial_data)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting comercial info: {e}")
        return {"success": False, "error": f"Error obteniendo información: {str(e)}"}

def format_comercial_info(comercial_data):
    """Formatear información del comercial para mostrar"""
    try:
        if not isinstance(comercial_data, dict):
            return "Datos de comercial inválidos"
        
        info_parts = []
        
        # Información principal
        if "name" in comercial_data and comercial_data["name"]:
            info_parts.append(f"👤 Nombre: {comercial_data['name']}")
        
        if "cedula" in comercial_data and comercial_data["cedula"]:
            info_parts.append(f"🆔 Cédula: {comercial_data['cedula']}")
        
        if "email" in comercial_data and comercial_data["email"]:
            info_parts.append(f"📧 Email: {comercial_data['email']}")
        
        if "phone" in comercial_data and comercial_data["phone"]:
            info_parts.append(f"📞 Teléfono: {comercial_data['phone']}")
        
        # Información adicional si está disponible
        if "created_at" in comercial_data and comercial_data["created_at"]:
            info_parts.append(f"📅 Registrado: {comercial_data['created_at'][:10]}")
        
        return "\n".join(info_parts) if info_parts else "Información de comercial disponible"
        
    except Exception as e:
        logger.error(f"❌ Error formatting comercial info: {e}")
        return "Error mostrando información del comercial"
