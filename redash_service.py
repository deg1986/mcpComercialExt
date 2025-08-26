# 🗄️ redash_service.py - Servicio de Datos Redash v1.0
import requests
import logging
import time
from config import *

logger = logging.getLogger(__name__)

def get_clients_from_redash():
    """Obtener clientes desde Redash con cache optimizado"""
    current_time = time.time()
    
    # Verificar cache
    if (clients_cache["data"] is not None and 
        current_time - clients_cache["timestamp"] < clients_cache["ttl"]):
        logger.info("✅ Using cached clients data")
        return {"success": True, "data": clients_cache["data"], "cached": True, "total": len(clients_cache["data"])}
    
    # Fetch fresh data
    try:
        url = f"{REDASH_BASE_URL}/api/queries/{REDASH_QUERY_ID}/results.json"
        params = {'api_key': REDASH_API_KEY}
        
        logger.info(f"🔄 Fetching clients from Redash Query {REDASH_QUERY_ID}")
        response = requests.get(url, params=params, timeout=REDASH_TIMEOUT)
        
        logger.info(f"📡 Redash Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer datos de la estructura de Redash
            query_result = data.get('query_result', {})
            clients = query_result.get('data', {}).get('rows', [])
            columns = query_result.get('data', {}).get('columns', [])
            
            logger.info(f"📊 Columns available: {[col.get('name') for col in columns]}")
            logger.info(f"✅ Retrieved {len(clients)} clients from Redash")
            
            # Actualizar cache
            clients_cache["data"] = {
                "clients": clients,
                "columns": columns,
                "metadata": {
                    "total_rows": len(clients),
                    "columns_count": len(columns),
                    "last_updated": current_time
                }
            }
            clients_cache["timestamp"] = current_time
            
            return {
                "success": True, 
                "data": clients_cache["data"], 
                "cached": False,
                "total": len(clients)
            }
        else:
            logger.error(f"❌ Redash HTTP {response.status_code}: {response.text}")
            # Fallback a cache expirado si existe
            if clients_cache["data"] is not None:
                logger.info("⚠️ Using expired cache due to API error")
                return {"success": True, "data": clients_cache["data"], "cached": True, "expired": True}
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.error(f"❌ Error fetching clients: {e}")
        # Fallback a cache expirado
        if clients_cache["data"] is not None:
            logger.info("⚠️ Using expired cache due to exception")
            return {"success": True, "data": clients_cache["data"], "cached": True, "expired": True}
        return {"success": False, "error": str(e)}

def get_unavailable_clients_from_redash():
    """Obtener clientes no disponibles desde Redash con cache optimizado"""
    current_time = time.time()
    
    # Verificar cache
    if (unavailable_clients_cache["data"] is not None and 
        current_time - unavailable_clients_cache["timestamp"] < unavailable_clients_cache["ttl"]):
        logger.info("✅ Using cached unavailable clients data")
        return {"success": True, "data": unavailable_clients_cache["data"], "cached": True}
    
    # Fetch fresh data
    try:
        url = f"{REDASH_BASE_URL}/api/queries/{REDASH_UNAVAILABLE_QUERY_ID}/results.json"
        params = {'api_key': REDASH_UNAVAILABLE_API_KEY}
        
        logger.info(f"🔄 Fetching unavailable clients from Redash Query {REDASH_UNAVAILABLE_QUERY_ID}")
        response = requests.get(url, params=params, timeout=REDASH_TIMEOUT)
        
        logger.info(f"📡 Redash Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Extraer datos de la estructura de Redash
            query_result = data.get('query_result', {})
            clients = query_result.get('data', {}).get('rows', [])
            columns = query_result.get('data', {}).get('columns', [])
            
            logger.info(f"📊 Unavailable clients: {len(clients)} records with {len(columns)} columns")
            
            # Actualizar cache
            unavailable_clients_cache["data"] = {
                "clients": clients,
                "columns": columns,
                "metadata": {
                    "total_rows": len(clients),
                    "columns_count": len(columns),
                    "last_updated": current_time
                }
            }
            unavailable_clients_cache["timestamp"] = current_time
            
            return {
                "success": True, 
                "data": unavailable_clients_cache["data"], 
                "cached": False
            }
        else:
            logger.error(f"❌ Redash HTTP {response.status_code}: {response.text}")
            # Fallback a cache expirado si existe
            if unavailable_clients_cache["data"] is not None:
                logger.info("⚠️ Using expired unavailable clients cache due to API error")
                return {"success": True, "data": unavailable_clients_cache["data"], "cached": True, "expired": True}
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.error(f"❌ Error fetching unavailable clients: {e}")
        # Fallback a cache expirado
        if unavailable_clients_cache["data"] is not None:
            logger.info("⚠️ Using expired unavailable clients cache due to exception")
            return {"success": True, "data": unavailable_clients_cache["data"], "cached": True, "expired": True}
        return {"success": False, "error": str(e)}

def check_if_client_unavailable(doc_type, doc_number):
    """Verificar si un cliente está en la lista de no disponibles"""
    try:
        logger.info(f"🚫 Checking if client is unavailable: {doc_type} {doc_number}")
        
        # Obtener data de clientes no disponibles
        data_result = get_unavailable_clients_from_redash()
        
        if not data_result.get("success"):
            logger.error(f"❌ Failed to get unavailable clients data: {data_result.get('error')}")
            # Si no podemos verificar, asumimos que está disponible
            return {"success": True, "unavailable": False, "error": "No se pudo verificar disponibilidad"}
        
        data = data_result.get("data", {})
        clients = data.get("clients", [])
        columns = data.get("columns", [])
        
        if not clients:
            logger.info("ℹ️ No unavailable clients data - client is available")
            return {"success": True, "unavailable": False}
        
        # Identificar columnas de documento
        doc_columns = []
        potential_doc_fields = [
            'nit', 'cedula', 'documento', 'doc_number', 'identification', 
            'tax_id', 'client_id', 'customer_id', 'id_number', 'cc'
        ]
        
        for col in columns:
            col_name = col.get('name', '').lower()
            if any(field in col_name for field in potential_doc_fields):
                doc_columns.append(col.get('name'))
        
        # Si no hay columnas específicas, usar todas
        if not doc_columns:
            doc_columns = [col.get('name') for col in columns]
        
        # Limpiar número de documento
        clean_doc_number = str(doc_number).strip().replace('-', '').replace('.', '').replace(' ', '')
        
        # Buscar en clientes no disponibles
        for client in clients:
            if not isinstance(client, dict):
                continue
                
            for col_name in doc_columns:
                if col_name in client and client[col_name]:
                    client_doc = str(client[col_name]).strip().replace('-', '').replace('.', '').replace(' ', '')
                    
                    if clean_doc_number == client_doc:
                        logger.info(f"🚫 Client found in unavailable list: {doc_type} {doc_number}")
                        return {
                            "success": True, 
                            "unavailable": True,
                            "client_data": client,
                            "matched_field": col_name
                        }
        
        logger.info(f"✅ Client is available: {doc_type} {doc_number}")
        return {"success": True, "unavailable": False}
        
    except Exception as e:
        logger.error(f"❌ Error checking client availability: {e}")
        # En caso de error, asumir que está disponible para no bloquear
        return {"success": True, "unavailable": False, "error": str(e)}
    """Buscar cliente por tipo y número de documento"""
    try:
        logger.info(f"🔍 Starting search for {doc_type}: {doc_number}")
        
        # Obtener data de clientes
        data_result = get_clients_from_redash()
        
        if not data_result.get("success"):
            logger.error(f"❌ Failed to get clients data: {data_result.get('error')}")
            return {"success": False, "error": data_result.get("error"), "found": False}
        
        data = data_result.get("data", {})
        clients = data.get("clients", [])
        columns = data.get("columns", [])
        
        logger.info(f"📊 Got {len(clients)} clients and {len(columns)} columns")
        
        if not clients:
            logger.warning("⚠️ No clients data available")
            return {"success": True, "found": False, "message": "No hay datos de clientes disponibles"}
        
        # Identificar columnas relevantes para búsqueda de documentos
        doc_columns = []
        potential_doc_fields = [
            'nit', 'cedula', 'documento', 'doc_number', 'identification', 
            'tax_id', 'client_id', 'customer_id', 'id_number', 'cc'
        ]
        
        for col in columns:
            col_name = col.get('name', '').lower()
            if any(field in col_name for field in potential_doc_fields):
                doc_columns.append(col.get('name'))
        
        logger.info(f"🔍 Found potential document columns: {doc_columns}")
        
        # Si no se encuentran columnas específicas, buscar en todas las columnas
        if not doc_columns:
            doc_columns = [col.get('name') for col in columns]
            logger.info(f"🔍 Using all columns as fallback: {len(doc_columns)} columns")
        
        # Limpiar número de documento para comparación
        clean_doc_number = str(doc_number).strip().replace('-', '').replace('.', '').replace(' ', '')
        logger.info(f"🔍 Cleaned document number: {clean_doc_number}")
        
        matching_clients = []
        
        # Buscar en todos los registros
        for i, client in enumerate(clients):
            if not isinstance(client, dict):
                continue
                
            # Buscar en columnas de documento
            for col_name in doc_columns:
                if col_name in client and client[col_name]:
                    client_doc = str(client[col_name]).strip().replace('-', '').replace('.', '').replace(' ', '')
                    
                    # Comparación exacta
                    if clean_doc_number == client_doc:
                        logger.info(f"✅ Match found in client {i+1}, column {col_name}: {client_doc}")
                        matching_clients.append({
                            "client_data": client,
                            "matched_field": col_name,
                            "matched_value": client[col_name],
                            "search_type": f"{doc_type}_{clean_doc_number}"
                        })
                        break
        
        logger.info(f"🔍 Search completed: {len(matching_clients)} matches found")
        
        if matching_clients:
            logger.info(f"✅ Found {len(matching_clients)} matching clients for {doc_type}: {doc_number}")
            return {
                "success": True,
                "found": True,
                "matches": matching_clients,
                "total_matches": len(matching_clients),
                "search_criteria": {
                    "doc_type": doc_type,
                    "doc_number": doc_number,
                    "cleaned_number": clean_doc_number
                }
            }
        else:
            logger.info(f"❌ No matches found for {doc_type}: {doc_number}")
            return {
                "success": True,
                "found": False,
                "message": f"No se encontró cliente con {doc_type}: {doc_number}",
                "search_criteria": {
                    "doc_type": doc_type,
                    "doc_number": doc_number,
                    "cleaned_number": clean_doc_number
                },
                "total_clients_searched": len(clients)
            }
            
    except Exception as e:
        logger.error(f"❌ Error searching client: {e}")
def search_client_by_document_with_availability(doc_type, doc_number):
    """Buscar cliente implementando flujo de disponibilidad comercial"""
    try:
        logger.info(f"🔍 Starting commercial search flow for {doc_type}: {doc_number}")
        
        # PASO 1: Verificar si el cliente está en la lista de no disponibles
        logger.info("🚫 PASO 1: Verificando disponibilidad del cliente...")
        availability_check = check_if_client_unavailable(doc_type, doc_number)
        
        if not availability_check.get("success"):
            return {
                "success": False, 
                "error": f"Error verificando disponibilidad: {availability_check.get('error')}", 
                "found": False
            }
        
        if availability_check.get("unavailable"):
            # Cliente encontrado en lista de no disponibles
            logger.info(f"🚫 Client is UNAVAILABLE: {doc_type} {doc_number}")
            return {
                "success": True,
                "found": True,
                "unavailable": True,
                "client_data": availability_check.get("client_data"),
                "matched_field": availability_check.get("matched_field"),
                "message": "Cliente existente pero no disponible para crear órdenes"
            }
        
        # PASO 2: Cliente disponible, buscar en base de datos principal
        logger.info("✅ PASO 2: Cliente disponible, buscando información completa...")
        return search_client_by_document(doc_type, doc_number)
        
    except Exception as e:
        logger.error(f"❌ Error in commercial search flow: {e}")
        return {"success": False, "error": str(e), "found": False}

def search_client_by_document(doc_type, doc_number):
    """Buscar cliente por tipo y número de documento - FUNCIÓN ORIGINAL PARA COMPATIBILIDAD"""
    try:
        logger.info(f"🔍 Starting search for {doc_type}: {doc_number}")
        
        # Obtener data de clientes
        data_result = get_clients_from_redash()
        
        if not data_result.get("success"):
            logger.error(f"❌ Failed to get clients data: {data_result.get('error')}")
            return {"success": False, "error": data_result.get("error"), "found": False}
        
        data = data_result.get("data", {})
        clients = data.get("clients", [])
        columns = data.get("columns", [])
        
        logger.info(f"📊 Got {len(clients)} clients and {len(columns)} columns")
        
        if not clients:
            logger.warning("⚠️ No clients data available")
            return {"success": True, "found": False, "message": "No hay datos de clientes disponibles"}
        
        # Identificar columnas relevantes para búsqueda de documentos
        doc_columns = []
        potential_doc_fields = [
            'nit', 'cedula', 'documento', 'doc_number', 'identification', 
            'tax_id', 'client_id', 'customer_id', 'id_number', 'cc'
        ]
        
        for col in columns:
            col_name = col.get('name', '').lower()
            if any(field in col_name for field in potential_doc_fields):
                doc_columns.append(col.get('name'))
        
        logger.info(f"🔍 Found potential document columns: {doc_columns}")
        
        # Si no se encuentran columnas específicas, buscar en todas las columnas
        if not doc_columns:
            doc_columns = [col.get('name') for col in columns]
            logger.info(f"🔍 Using all columns as fallback: {len(doc_columns)} columns")
        
        # Limpiar número de documento para comparación
        clean_doc_number = str(doc_number).strip().replace('-', '').replace('.', '').replace(' ', '')
        logger.info(f"🔍 Cleaned document number: {clean_doc_number}")
        
        matching_clients = []
        
        # Buscar en todos los registros
        for i, client in enumerate(clients):
            if not isinstance(client, dict):
                continue
                
            # Buscar en columnas de documento
            for col_name in doc_columns:
                if col_name in client and client[col_name]:
                    client_doc = str(client[col_name]).strip().replace('-', '').replace('.', '').replace(' ', '')
                    
                    # Comparación exacta
                    if clean_doc_number == client_doc:
                        logger.info(f"✅ Match found in client {i+1}, column {col_name}: {client_doc}")
                        matching_clients.append({
                            "client_data": client,
                            "matched_field": col_name,
                            "matched_value": client[col_name],
                            "search_type": f"{doc_type}_{clean_doc_number}"
                        })
                        break
        
        logger.info(f"🔍 Search completed: {len(matching_clients)} matches found")
        
        if matching_clients:
            logger.info(f"✅ Found {len(matching_clients)} matching clients for {doc_type}: {doc_number}")
            return {
                "success": True,
                "found": True,
                "matches": matching_clients,
                "total_matches": len(matching_clients),
                "search_criteria": {
                    "doc_type": doc_type,
                    "doc_number": doc_number,
                    "cleaned_number": clean_doc_number
                }
            }
        else:
            logger.info(f"❌ No matches found for {doc_type}: {doc_number}")
            return {
                "success": True,
                "found": False,
                "message": f"No se encontró cliente con {doc_type}: {doc_number}",
                "search_criteria": {
                    "doc_type": doc_type,
                    "doc_number": doc_number,
                    "cleaned_number": clean_doc_number
                },
                "total_clients_searched": len(clients)
            }
            
    except Exception as e:
        logger.error(f"❌ Error searching client: {e}")
        return {"success": False, "error": str(e), "found": False}
        
        if matching_clients:
            logger.info(f"✅ Found {len(matching_clients)} matching clients for {doc_type}: {doc_number}")
            return {
                "success": True,
                "found": True,
                "matches": matching_clients,
                "total_matches": len(matching_clients),
                "search_criteria": {
                    "doc_type": doc_type,
                    "doc_number": doc_number,
                    "cleaned_number": clean_doc_number
                }
            }
        else:
            logger.info(f"❌ No matches found for {doc_type}: {doc_number}")
            return {
                "success": True,
                "found": False,
                "message": f"No se encontró cliente con {doc_type}: {doc_number}",
                "search_criteria": {
                    "doc_type": doc_type,
                    "doc_number": doc_number,
                    "cleaned_number": clean_doc_number
                },
                "total_clients_searched": len(clients)
            }
            
    except Exception as e:
        logger.error(f"❌ Error searching client: {e}")
        return {"success": False, "error": str(e), "found": False}

def get_clients_summary():
    """Obtener resumen de clientes disponibles"""
    try:
        data_result = get_clients_from_redash()
        
        if not data_result.get("success"):
            return {"success": False, "error": data_result.get("error")}
        
        data = data_result.get("data", {})
        clients = data.get("clients", [])
        columns = data.get("columns", [])
        metadata = data.get("metadata", {})
        
        # Resumen de columnas
        column_summary = []
        for col in columns:
            column_summary.append({
                "name": col.get("name"),
                "type": col.get("type"),
                "friendly_name": col.get("friendly_name", col.get("name"))
            })
        
        # Estadísticas básicas
        stats = {
            "total_clients": len(clients),
            "total_columns": len(columns),
            "last_updated": metadata.get("last_updated"),
            "cached": data_result.get("cached", False)
        }
        
        # Muestra de datos (primeros 3 registros)
        sample_clients = clients[:3] if clients else []
        
        return {
            "success": True,
            "stats": stats,
            "columns": column_summary,
            "sample_data": sample_clients
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting clients summary: {e}")
        return {"success": False, "error": str(e)}

def validate_document_number(doc_type, doc_number):
    """Validar formato de documento según tipo"""
    try:
        # Limpiar número
        clean_number = str(doc_number).strip().replace('-', '').replace('.', '').replace(' ', '')
        
        # Validar que solo contenga números
        if not clean_number.isdigit():
            return {"valid": False, "error": "El documento debe contener solo números"}
        
        # Validar longitud según tipo
        if doc_type == "NIT":
            if len(clean_number) < MIN_DOC_LENGTH or len(clean_number) > MAX_NIT_LENGTH:
                return {"valid": False, "error": f"NIT debe tener entre {MIN_DOC_LENGTH} y {MAX_NIT_LENGTH} dígitos"}
        elif doc_type == "CC":
            if len(clean_number) < MIN_DOC_LENGTH or len(clean_number) > MAX_CC_LENGTH:
                return {"valid": False, "error": f"Cédula debe tener entre {MIN_DOC_LENGTH} y {MAX_CC_LENGTH} dígitos"}
        
        return {"valid": True, "cleaned_number": clean_number}
        
    except Exception as e:
        return {"valid": False, "error": f"Error validando documento: {str(e)}"}

def format_client_info(client_data, matched_field=None):
    """Formatear información del cliente para mostrar - LIMPIO Y PROFESIONAL"""
    try:
        if not isinstance(client_data, dict):
            return "❌ Formato de cliente inválido"
        
        logger.info(f"🔍 Formatting client data with {len(client_data)} fields")
        
        formatted_info = []
        
        # Información de coincidencia (documento)
        if matched_field and matched_field in client_data:
            formatted_info.append(f"🔍 Documento: {client_data[matched_field]}")
        
        # 1. NOMBRE/RAZÓN SOCIAL - Prioridad alta
        name_found = False
        for name_field in ['nombre', 'name', 'client_name', 'razon_social', 'business_name', 'company_name', 'customer_name']:
            if name_field in client_data and client_data[name_field]:
                formatted_info.append(f"🏢 Nombre: {client_data[name_field]}")
                name_found = True
                break
        
        # 2. REPRESENTANTE LEGAL - Campo específico solicitado
        legal_found = False
        for legal_field in ['legal_name', 'representante_legal', 'rep_legal', 'legal_representative']:
            if legal_field in client_data and client_data[legal_field]:
                formatted_info.append(f"👤 Representante Legal: {client_data[legal_field]}")
                legal_found = True
                break
        
        # 3. TELÉFONO - Campo específico solicitado
        phone_found = False
        for phone_field in ['phone_number', 'telefono', 'phone', 'celular', 'movil', 'contact_phone']:
            if phone_field in client_data and client_data[phone_field]:
                formatted_info.append(f"📞 Teléfono: {client_data[phone_field]}")
                phone_found = True
                break
        
        # 4. EMAIL
        email_found = False
        for email_field in ['email', 'correo', 'mail', 'contact_email']:
            if email_field in client_data and client_data[email_field]:
                formatted_info.append(f"📧 Email: {client_data[email_field]}")
                email_found = True
                break
        
        # 5. DIRECCIÓN - Campo específico solicitado con enlace a Google Maps
        address_found = False
        for address_field in ['address', 'direccion', 'domicilio', 'ubicacion', 'street_address']:
            if address_field in client_data and client_data[address_field]:
                address_value = str(client_data[address_field])
                
                # Obtener ciudad y departamento para mejorar la búsqueda
                city_info = ""
                for city_field in ['ciudad', 'city', 'municipio', 'locality']:
                    if city_field in client_data and client_data[city_field]:
                        city_info = str(client_data[city_field])
                        break
                
                state_info = ""
                for state_field in ['departamento', 'estado', 'state', 'region']:
                    if state_field in client_data and client_data[state_field]:
                        state_info = str(client_data[state_field])
                        break
                
                # Construir dirección completa para Google Maps
                full_address = address_value
                if city_info:
                    full_address += f", {city_info}"
                if state_info:
                    full_address += f", {state_info}"
                full_address += ", Colombia"
                
                # Crear enlace de Google Maps
                import urllib.parse
                encoded_address = urllib.parse.quote_plus(full_address)
                google_maps_url = f"https://maps.google.com/maps?q={encoded_address}"
                
                # Truncar dirección si es muy larga para mostrar
                display_address = address_value
                if len(display_address) > 80:
                    display_address = display_address[:80] + "..."
                
                # Formato: [texto](enlace) para Markdown
                formatted_info.append(f"📍 Dirección: [{display_address}]({google_maps_url})")
                address_found = True
                break
        
        # 6. CIUDAD/UBICACIÓN
        city_found = False
        for city_field in ['ciudad', 'city', 'municipio', 'locality']:
            if city_field in client_data and client_data[city_field]:
                formatted_info.append(f"🌆 Ciudad: {client_data[city_field]}")
                city_found = True
                break
        
        # 7. DEPARTAMENTO/ESTADO (si existe)
        state_found = False
        for state_field in ['departamento', 'estado', 'state', 'region']:
            if state_field in client_data and client_data[state_field]:
                formatted_info.append(f"🗺️ Departamento: {client_data[state_field]}")
                state_found = True
                break
        
        # Si no encontramos los campos principales, mostrar campos disponibles
        if len(formatted_info) <= 1:  # Solo el documento
            logger.info(f"⚠️ Main fields not found, showing available fields")
            count = 0
            excluded_fields = ['id', 'created_at', 'updated_at', 'status', 'active']  # Campos técnicos a omitir
            
            for key, value in client_data.items():
                if (value and 
                    str(value).strip() != "" and 
                    key.lower() not in excluded_fields and 
                    count < 8):  # Máximo 8 campos
                    formatted_info.append(f"• {key}: {value}")
                    count += 1
        
        # Agregar resumen de completitud sin asteriscos
        fields_found = []
        if name_found: fields_found.append("Nombre")
        if legal_found: fields_found.append("Rep. Legal")
        if phone_found: fields_found.append("Teléfono")
        if email_found: fields_found.append("Email")
        if address_found: fields_found.append("Dirección")
        if city_found: fields_found.append("Ciudad")
        
        if fields_found:
            formatted_info.append(f"\n✅ Datos disponibles: {', '.join(fields_found)}")
        
        result = "\n".join(formatted_info) if formatted_info else "ℹ️ Cliente encontrado (información limitada)"
        logger.info(f"✅ Client info formatted successfully: {len(result)} characters, {len(fields_found)} main fields")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error formatting client info: {e}")
        return f"ℹ️ Cliente encontrado\n⚠️ Error mostrando detalles: {str(e)}"
