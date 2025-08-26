# 🏢 nocodb_service.py - Servicio de Comerciales NocoDB v1.0
import requests
import logging
import re
import json
import urllib.parse
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
        
        # Construir URL para consulta - EXACTAMENTE como tu CURL
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
        
        logger.info(f"📡 Making GET request to: {url}")
        logger.info(f"📋 Params: {params}")
        logger.info(f"📋 Headers: {headers}")
        
        # Debug: Log equivalent curl command
        import urllib.parse
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        curl_command = f"""
Equivalent CURL:
curl -X 'GET' '{full_url}' \\
  -H 'accept: application/json' \\
  -H 'xc-token: {NOCODB_TOKEN}'
"""
        logger.info(curl_command)
        
        response = requests.get(url, params=params, headers=headers, timeout=NOCODB_TIMEOUT)
        
        logger.info(f"📡 NocoDB Response Status: {response.status_code}")
        logger.info(f"📡 NocoDB Response Headers: {dict(response.headers)}")
        logger.info(f"📡 NocoDB Response Body: {response.text}")
        
        if response.status_code != 200:
            logger.error(f"❌ NocoDB HTTP Error: {response.status_code} - {response.text}")
            return {"success": False, "error": f"Error consultando base de datos: HTTP {response.status_code}"}
        
        try:
            data = response.json()
            page_info = data.get("pageInfo", {})
            total_rows = page_info.get("totalRows", 0)
            
            logger.info(f"📊 Query result: totalRows = {total_rows}")
            
            if total_rows > 0:
                # Comercial ya existe
                existing_records = data.get("list", [])
                existing_comercial = existing_records[0] if existing_records else {}
                
                logger.info(f"👤 Comercial already exists: {clean_cedula}")
                logger.info(f"👤 Existing data: {existing_comercial}")
                
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
        
        except json.JSONDecodeError as je:
            logger.error(f"❌ Invalid JSON response: {je}")
            logger.error(f"❌ Response text: {response.text}")
            return {"success": False, "error": f"Respuesta inválida del servidor: {je}"}
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout checking comercial existence")
        return {"success": False, "error": "Timeout al verificar comercial. Intenta nuevamente."}
    
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error checking comercial existence")
        return {"success": False, "error": "Error de conexión con NocoDB. Verifica la conectividad."}
        
    except Exception as e:
        logger.error(f"❌ Unexpected error checking comercial existence: {e}")
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
        
        # Construir request para creación - EXACTAMENTE como tu CURL
        url = f"{NOCODB_BASE_URL}/tables/{NOCODB_TABLE_ID}/records"
        
        headers = {
            "accept": "application/json",
            "xc-token": NOCODB_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = clean_data
        
        logger.info(f"📡 Making POST request to: {url}")
        logger.info(f"📋 Headers: {headers}")
        logger.info(f"📦 Payload: {payload}")
        
        # Debug: Log equivalent curl command
        import json
        curl_command = f"""
Equivalent CURL:
curl -X 'POST' '{url}' \\
  -H 'accept: application/json' \\
  -H 'xc-token: {NOCODB_TOKEN}' \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(payload)}'
"""
        logger.info(curl_command)
        
        response = requests.post(url, json=payload, headers=headers, timeout=NOCODB_TIMEOUT)
        
        logger.info(f"📡 NocoDB Response Status: {response.status_code}")
        logger.info(f"📡 NocoDB Response Headers: {dict(response.headers)}")
        logger.info(f"📡 NocoDB Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            try:
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
            except json.JSONDecodeError as je:
                logger.warning(f"⚠️ Response is not valid JSON: {je}")
                # Si la respuesta no es JSON válido, pero el status es 200/201, asumir éxito
                return {
                    "success": True,
                    "comercial_data": {"status": "created"},
                    "message": f"Comercial {clean_data['name']} creado exitosamente",
                    "details": clean_data,
                    "note": "Response was not JSON but creation appears successful"
                }
        else:
            logger.error(f"❌ NocoDB Create Error: {response.status_code}")
            logger.error(f"❌ Error details: {response.text}")
            
            # Intentar parsear el error
            try:
                error_data = response.json()
                error_message = error_data.get('message', response.text)
            except:
                error_message = response.text
            
            return {
                "success": False, 
                "error": f"Error creando comercial (HTTP {response.status_code}): {error_message}",
                "details": {
                    "status_code": response.status_code,
                    "response_body": response.text,
                    "url": url,
                    "payload": payload
                }
            }
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout error creating comercial")
        return {"success": False, "error": "Timeout al crear comercial. Intenta nuevamente."}
    
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error creating comercial")
        return {"success": False, "error": "Error de conexión con NocoDB. Verifica la conectividad."}
        
    except Exception as e:
        logger.error(f"❌ Unexpected error creating comercial: {e}")
        return {"success": False, "error": f"Error inesperado creando comercial: {str(e)}"}

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

# ===== FUNCIONES PARA ÓRDENES =====

def validate_order_number_format(order_number):
    """Validar y normalizar formato de número de orden"""
    try:
        if not order_number or not isinstance(order_number, str):
            return {"valid": False, "error": "Número de orden requerido"}
        
        # Limpiar y normalizar
        clean_order = order_number.strip().upper()
        
        # Si no tiene prefijo, agregarlo
        if not clean_order.startswith(ORDER_NUMBER_PREFIX):
            # Remover cualquier prefijo parcial (mp-, Mp-, etc)
            if clean_order.lower().startswith('mp'):
                clean_order = clean_order[2:].lstrip('-')
            
            # Agregar prefijo correcto
            clean_order = ORDER_NUMBER_PREFIX + clean_order
        
        # Validar formato final
        if not clean_order.startswith(ORDER_NUMBER_PREFIX):
            return {"valid": False, "error": f"El número de orden debe comenzar con {ORDER_NUMBER_PREFIX}"}
        
        # Extraer la parte numérica después del prefijo
        order_suffix = clean_order[len(ORDER_NUMBER_PREFIX):]
        
        # Validar longitud
        if len(order_suffix) < MIN_ORDER_LENGTH:
            return {"valid": False, "error": f"El número de orden debe tener al menos {MIN_ORDER_LENGTH} caracteres después de {ORDER_NUMBER_PREFIX}"}
        
        if len(order_suffix) > MAX_ORDER_LENGTH:
            return {"valid": False, "error": f"El número de orden no puede tener más de {MAX_ORDER_LENGTH} caracteres después de {ORDER_NUMBER_PREFIX}"}
        
        # Validar caracteres (solo números y guiones)
        if not re.match(r'^[0-9\-]+, order_suffix):
            return {"valid": False, "error": "El número de orden solo puede contener números y guiones después del prefijo"}
        
        return {"valid": True, "normalized_order": clean_order}
        
    except Exception as e:
        return {"valid": False, "error": f"Error validando número de orden: {str(e)}"}

def get_comercial_by_cedula(cedula):
    """Obtener comercial por cédula y retornar ID si existe"""
    try:
        logger.info(f"🔍 Getting comercial by cedula: {cedula}")
        
        # Reutilizar la función existente pero extraer el ID
        exists_check = check_comercial_exists(cedula)
        
        if not exists_check.get("success"):
            return {"success": False, "error": exists_check.get("error")}
        
        if not exists_check.get("exists"):
            return {
                "success": True,
                "found": False,
                "message": f"No se encontró comercial con cédula {cedula}"
            }
        
        comercial_data = exists_check.get("comercial_data", {})
        comercial_id = comercial_data.get("Id") or comercial_data.get("id")
        
        if not comercial_id:
            logger.warning(f"⚠️ Comercial found but no ID field: {comercial_data}")
            return {
                "success": False,
                "error": "Comercial encontrado pero sin ID válido"
            }
        
        logger.info(f"✅ Comercial found with ID: {comercial_id}")
        
        return {
            "success": True,
            "found": True,
            "comercial_id": comercial_id,
            "comercial_data": comercial_data,
            "message": f"Comercial encontrado: {comercial_data.get('name', 'Sin nombre')}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting comercial by cedula: {e}")
        return {"success": False, "error": f"Error obteniendo comercial: {str(e)}"}

def check_order_exists(order_number):
    """Verificar si la orden existe en NocoDB"""
    try:
        logger.info(f"📦 Checking if order exists: {order_number}")
        
        # Validar y normalizar número de orden
        validation = validate_order_number_format(order_number)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        normalized_order = validation["normalized_order"]
        
        # Construir URL para consulta de órdenes
        url = f"{NOCODB_BASE_URL}/tables/{NOCODB_ORDERS_TABLE_ID}/records"
        params = {
            "where": f"(order_number,eq,{normalized_order})",
            "limit": 1,
            "shuffle": 0,
            "offset": 0
        }
        
        headers = {
            "accept": "application/json",
            "xc-token": NOCODB_TOKEN
        }
        
        logger.info(f"📡 Making GET request to: {url}")
        logger.info(f"📋 Params: {params}")
        
        # Debug: Log equivalent curl command
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        curl_command = f"""
Equivalent CURL:
curl -X 'GET' '{full_url}' \\
  -H 'accept: application/json' \\
  -H 'xc-token: {NOCODB_TOKEN}'
"""
        logger.info(curl_command)
        
        response = requests.get(url, params=params, headers=headers, timeout=NOCODB_TIMEOUT)
        
        logger.info(f"📡 NocoDB Response Status: {response.status_code}")
        logger.info(f"📡 NocoDB Response Body: {response.text}")
        
        if response.status_code != 200:
            logger.error(f"❌ NocoDB HTTP Error: {response.status_code} - {response.text}")
            return {"success": False, "error": f"Error consultando órdenes: HTTP {response.status_code}"}
        
        try:
            data = response.json()
            page_info = data.get("pageInfo", {})
            total_rows = page_info.get("totalRows", 0)
            
            logger.info(f"📊 Query result: totalRows = {total_rows}")
            
            if total_rows > 0:
                # Orden existe
                existing_records = data.get("list", [])
                existing_order = existing_records[0] if existing_records else {}
                
                logger.info(f"📦 Order exists: {normalized_order}")
                logger.info(f"📦 Order data: {existing_order}")
                
                return {
                    "success": True,
                    "exists": True,
                    "order_data": existing_order,
                    "normalized_order": normalized_order,
                    "message": f"La orden {normalized_order} existe en el sistema"
                }
            else:
                logger.info(f"❌ Order does not exist: {normalized_order}")
                return {
                    "success": True,
                    "exists": False,
                    "normalized_order": normalized_order,
                    "message": f"La orden {normalized_order} no existe en el sistema"
                }
        
        except json.JSONDecodeError as je:
            logger.error(f"❌ Invalid JSON response: {je}")
            return {"success": False, "error": f"Respuesta inválida del servidor: {je}"}
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout checking order existence")
        return {"success": False, "error": "Timeout al verificar orden. Intenta nuevamente."}
    
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error checking order existence")
        return {"success": False, "error": "Error de conexión con NocoDB. Verifica la conectividad."}
        
    except Exception as e:
        logger.error(f"❌ Unexpected error checking order existence: {e}")
        return {"success": False, "error": f"Error verificando orden: {str(e)}"}

def assign_order_to_comercial(order_number, comercial_id):
    """Asignar una orden a un comercial externo"""
    try:
        logger.info(f"🎯 Assigning order {order_number} to comercial ID {comercial_id}")
        
        # Validar y normalizar número de orden
        validation = validate_order_number_format(order_number)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        normalized_order = validation["normalized_order"]
        
        # Construir request para asignación
        url = f"{NOCODB_BASE_URL}/tables/{NOCODB_ASSIGNMENTS_TABLE_ID}/records"
        
        headers = {
            "accept": "application/json",
            "xc-token": NOCODB_TOKEN,
            "Content-Type": "application/json"
        }
        
        payload = {
            "order_number": normalized_order,
            "commercial_ext": comercial_id
        }
        
        logger.info(f"📡 Making POST request to: {url}")
        logger.info(f"📋 Headers: {headers}")
        logger.info(f"📦 Payload: {payload}")
        
        # Debug: Log equivalent curl command
        curl_command = f"""
Equivalent CURL:
curl -X 'POST' '{url}' \\
  -H 'accept: application/json' \\
  -H 'xc-token: {NOCODB_TOKEN}' \\
  -H 'Content-Type: application/json' \\
  -d '{json.dumps(payload)}'
"""
        logger.info(curl_command)
        
        response = requests.post(url, json=payload, headers=headers, timeout=NOCODB_TIMEOUT)
        
        logger.info(f"📡 NocoDB Response Status: {response.status_code}")
        logger.info(f"📡 NocoDB Response Headers: {dict(response.headers)}")
        logger.info(f"📡 NocoDB Response Body: {response.text}")
        
        if response.status_code in [200, 201]:
            try:
                assignment_data = response.json()
                logger.info(f"✅ Order assigned successfully: {normalized_order} -> {comercial_id}")
                
                return {
                    "success": True,
                    "assignment_data": assignment_data,
                    "message": f"Orden {normalized_order} asignada exitosamente",
                    "details": {
                        "order_number": normalized_order,
                        "comercial_id": comercial_id
                    }
                }
            except json.JSONDecodeError as je:
                logger.warning(f"⚠️ Response is not valid JSON: {je}")
                # Si la respuesta no es JSON válido, pero el status es 200/201, asumir éxito
                return {
                    "success": True,
                    "assignment_data": {"status": "assigned"},
                    "message": f"Orden {normalized_order} asignada exitosamente",
                    "details": {
                        "order_number": normalized_order,
                        "comercial_id": comercial_id
                    },
                    "note": "Response was not JSON but assignment appears successful"
                }
        else:
            logger.error(f"❌ NocoDB Assignment Error: {response.status_code}")
            logger.error(f"❌ Error details: {response.text}")
            
            # Intentar parsear el error
            try:
                error_data = response.json()
                error_message = error_data.get('message', response.text)
            except:
                error_message = response.text
            
            return {
                "success": False,
                "error": f"Error asignando orden (HTTP {response.status_code}): {error_message}",
                "details": {
                    "status_code": response.status_code,
                    "response_body": response.text,
                    "url": url,
                    "payload": payload
                }
            }
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout error assigning order")
        return {"success": False, "error": "Timeout al asignar orden. Intenta nuevamente."}
    
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error assigning order")
        return {"success": False, "error": "Error de conexión con NocoDB. Verifica la conectividad."}
        
    except Exception as e:
        logger.error(f"❌ Unexpected error assigning order: {e}")
        return {"success": False, "error": f"Error inesperado asignando orden: {str(e)}"}

def process_order_assignment(cedula, order_number):
    """Procesar asignación completa de orden a comercial"""
    try:
        logger.info(f"🎯 Processing order assignment: {order_number} to cedula {cedula}")
        
        # Paso 1: Verificar comercial y obtener ID
        comercial_result = get_comercial_by_cedula(cedula)
        if not comercial_result.get("success"):
            return {"success": False, "error": comercial_result.get("error")}
        
        if not comercial_result.get("found"):
            return {"success": False, "error": comercial_result.get("message")}
        
        comercial_id = comercial_result.get("comercial_id")
        comercial_data = comercial_result.get("comercial_data")
        
        # Paso 2: Verificar que la orden existe
        order_result = check_order_exists(order_number)
        if not order_result.get("success"):
            return {"success": False, "error": order_result.get("error")}
        
        if not order_result.get("exists"):
            return {"success": False, "error": order_result.get("message")}
        
        normalized_order = order_result.get("normalized_order")
        
        # Paso 3: Asignar orden al comercial
        assignment_result = assign_order_to_comercial(normalized_order, comercial_id)
        if not assignment_result.get("success"):
            return {"success": False, "error": assignment_result.get("error")}
        
        # Éxito completo
        return {
            "success": True,
            "message": f"Orden {normalized_order} asignada exitosamente a {comercial_data.get('name', 'comercial')}",
            "details": {
                "order_number": normalized_order,
                "comercial_id": comercial_id,
                "comercial_name": comercial_data.get('name'),
                "comercial_cedula": comercial_data.get('cedula')
            },
            "assignment_data": assignment_result.get("assignment_data")
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing order assignment: {e}")
        return {"success": False, "error": f"Error procesando asignación: {str(e)}"}
