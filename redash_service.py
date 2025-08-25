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

def search_client_by_document(doc_type, doc_number):
    """Buscar cliente por tipo y número de documento"""
    try:
        # Obtener data de clientes
        data_result = get_clients_from_redash()
        
        if not data_result.get("success"):
            return {"success": False, "error": data_result.get("error"), "found": False}
        
        data = data_result.get("data", {})
        clients = data.get("clients", [])
        columns = data.get("columns", [])
        
        if not clients:
            return {"success": True, "found": False, "message": "No hay datos de clientes disponibles"}
        
        # Identificar columnas relevantes para búsqueda de documentos
        # Buscar columnas que puedan contener información de documento
        doc_columns = []
        potential_doc_fields = [
            'nit', 'cedula', 'documento', 'doc_number', 'identification', 
            'tax_id', 'client_id', 'customer_id', 'id_number'
        ]
        
        for col in columns:
            col_name = col.get('name', '').lower()
            if any(field in col_name for field in potential_doc_fields):
                doc_columns.append(col.get('name'))
        
        logger.info(f"🔍 Searching in potential document columns: {doc_columns}")
        
        # Si no se encuentran columnas específicas, buscar en todas las columnas de texto
        if not doc_columns:
            doc_columns = [col.get('name') for col in columns if col.get('type') in ['string', 'text']]
            logger.info(f"🔍 Fallback: searching in all text columns: {doc_columns}")
        
        # Limpiar número de documento para comparación
        clean_doc_number = str(doc_number).strip().replace('-', '').replace('.', '').replace(' ', '')
        
        matching_clients = []
        
        # Buscar en todos los registros
        for client in clients:
            if not isinstance(client, dict):
                continue
                
            # Buscar en columnas de documento
            for col_name in doc_columns:
                if col_name in client and client[col_name]:
                    client_doc = str(client[col_name]).strip().replace('-', '').replace('.', '').replace(' ', '')
                    
                    # Comparación exacta
                    if clean_doc_number == client_doc:
                        matching_clients.append({
                            "client_data": client,
                            "matched_field": col_name,
                            "matched_value": client[col_name],
                            "search_type": f"{doc_type}_{clean_doc_number}"
                        })
                        break
        
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
    """Formatear información del cliente para mostrar"""
    try:
        if not isinstance(client_data, dict):
            return "Formato de cliente inválido"
        
        # Campos comunes que suelen existir
        common_fields = [
            'nombre', 'name', 'client_name', 'customer_name',
            'razon_social', 'business_name', 'company_name',
            'email', 'correo', 'telefono', 'phone', 'celular',
            'ciudad', 'city', 'municipio', 'departamento', 'state',
            'direccion', 'address', 'barrio', 'neighborhood'
        ]
        
        formatted_info = []
        
        # Información principal
        if matched_field:
            formatted_info.append(f"🔍 **Encontrado por:** {matched_field} = {client_data.get(matched_field)}")
        
        # Buscar y mostrar campos relevantes
        for field in common_fields:
            for key, value in client_data.items():
                if field.lower() in key.lower() and value:
                    formatted_info.append(f"• **{key}:** {value}")
                    break
        
        # Si no se encontraron campos comunes, mostrar algunos campos disponibles
        if len(formatted_info) <= 1:  # Solo el matched_field
            count = 0
            for key, value in client_data.items():
                if value and count < 5:  # Mostrar máximo 5 campos
                    formatted_info.append(f"• **{key}:** {value}")
                    count += 1
        
        return "\n".join(formatted_info) if formatted_info else "No se pudo formatear la información del cliente"
        
    except Exception as e:
        logger.error(f"❌ Error formatting client info: {e}")
        return f"Error formateando información: {str(e)}"
