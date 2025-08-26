# bot_handlers.py - Manejadores del Bot Telegram v1.2 - CLEAN VERSION
import logging
from flask import request
from config import *
from redash_service import search_client_by_document_with_availability, get_clients_summary, validate_document_number, format_client_info
from utils import send_telegram_message

logger = logging.getLogger(__name__)

# Variables globales para estados de usuario
user_states = {}

def setup_telegram_routes(app):
    """Configurar rutas del bot de Telegram"""
    
    @app.route('/telegram-webhook', methods=['POST'])
    def telegram_webhook():
        """Webhook para recibir mensajes de Telegram"""
        try:
            update_data = request.get_json()
            
            if not update_data or 'message' not in update_data:
                return "OK", 200
            
            message = update_data['message']
            chat_id = message['chat']['id']
            user_id = message['from']['id']
            
            if 'text' not in message:
                return "OK", 200
            
            text = message['text'].strip()
            text_lower = text.lower()
            
            # Router de comandos
            if text in ['/start', 'start', 'inicio', 'hola']:
                handle_start_command(chat_id)
            elif text in ['/help', 'help', 'ayuda']:
                handle_help_command(chat_id)
            elif text_lower in ['/cliente', 'cliente', 'buscar', 'search']:
                handle_client_search_start(chat_id, user_id)
            elif text_lower in ['/resumen', 'resumen', 'estadisticas', 'stats']:
                handle_stats_command(chat_id)
            elif text_lower in ['/info', 'info', 'detalle', 'detalles']:
                handle_info_command(chat_id)
            elif text_lower in ['nit', 'cc'] and user_id in user_states:
                handle_document_type_selection(chat_id, user_id, text.upper())
            else:
                # Manejar estados de conversación
                if user_id in user_states:
                    handle_conversation_state(chat_id, user_id, text)
                else:
                    handle_unknown_command(chat_id, text)
            
            return "OK", 200
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return "Handled with error", 200

def handle_info_command(chat_id):
    """Comando /info - Información detallada"""
    text = """ℹ️ **INFORMACIÓN DETALLADA**

Para obtener información completa de un cliente:
1. Usa 'cliente' para buscar
2. El sistema mostrará automáticamente:

**Datos principales:**
• 🔍 Documento de identidad
• 🏢 Nombre/Razón social  
• 👤 Representante legal
• 📞 Teléfono de contacto
• 📧 Email corporativo
• 📍 Dirección completa
• 🌆 Ciudad y departamento

**💡 Tip:** Toda la información disponible se muestra automáticamente en cada búsqueda.

🔍 **Para buscar:** Escribe 'cliente'"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_start_command(chat_id):
    """Comando /start - Bienvenida"""
    logger.info(f"Start command from chat {chat_id}")
    
    text = """🎯 **BUSCADOR DE CLIENTES COMERCIALES** ⚡

🔹 Te ayudo a buscar clientes y verificar su **disponibilidad comercial** para crear órdenes.

**📋 ¿Qué puedo hacer?**
• cliente - Buscar cliente y verificar disponibilidad
• resumen - Ver información del sistema
• info - Ver qué datos obtienes
• help - Ver todos los comandos

**🔍 Puedo buscar por:**
• NIT - Número de Identificación Tributaria  
• CC - Cédula de Ciudadanía

**🚦 Estados de cliente:**
• 🟢 **DISPONIBLE** - Puede crear órdenes
• 🚫 **NO DISPONIBLE** - Existe pero no puede crear órdenes
• ❌ **NO ENCONTRADO** - Necesita pre-registro

**📊 Información que obtienes:**
• 🏢 Nombre/Razón social
• 👤 Representante legal
• 📞 Teléfono de contacto
• 📧 Email corporativo
• 📍 Dirección completa
• 🌆 Ciudad y departamento

**💡 ¿Cómo funciona?**
1. Escribe: cliente
2. Selecciona: NIT o CC  
3. Escribe el número del documento
4. ¡Te muestro el estado y la información!

🚀 **¡Empecemos a buscar clientes!**"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_help_command(chat_id):
    """Comando /help - Ayuda"""
    text = """COMO USAR EL BUSCADOR COMERCIAL

Buscar Clientes:
• cliente - Empezar busqueda con verificacion comercial
• NIT - Para empresas
• CC - Para personas

Informacion:
• resumen - Ver datos del sistema
• info - Detalles sobre que informacion se muestra
• help - Mostrar esta ayuda
• start - Volver al inicio

Proceso paso a paso:
1. Empezar: Escribe 'cliente'
2. Tipo: Selecciona 'NIT' o 'CC'
3. Numero: Escribe el documento (solo numeros)
4. Resultado: Te muestro el estado comercial e informacion

Estados de cliente:
• DISPONIBLE - Cliente puede crear ordenes
• NO DISPONIBLE - Cliente existe pero no puede crear ordenes
• NO ENCONTRADO - Necesita pre-registro

Informacion completa que obtienes:
• Documento de identidad
• Nombre/Razon social
• Representante legal
• Telefono de contacto
• Email corporativo
• Direccion completa
• Ciudad y departamento
• Estado comercial (disponible/no disponible)

Formatos que acepto:
• NIT: Entre 6 y 15 numeros
• CC: Entre 6 y 10 numeros

Ejemplos:
• NIT: 901234567
• CC: 12345678

Para clientes nuevos:
Si no encuentras un cliente, te dare el enlace de pre-registro para crearlo.

Caracteristicas comerciales:
• Verificacion de disponibilidad para ordenes
• Informacion completa del cliente
• Enlaces de pre-registro automaticos
• Estados comerciales claros
• Disponible 24/7"""
    
    send_telegram_message(chat_id, text)

def handle_client_search_start(chat_id, user_id):
    """Iniciar proceso de búsqueda de cliente"""
    logger.info(f"Client search start from chat {chat_id}")
    
    # Establecer estado de usuario
    user_states[user_id] = {
        'step': 'document_type',
        'chat_id': chat_id
    }
    
    text = """🔍 **BÚSQUEDA DE CLIENTE** ⚡

**Paso 1/2:** Selecciona el tipo de documento

**Opciones disponibles:**
• **NIT** - Número de Identificación Tributaria
• **CC** - Cédula de Ciudadanía

📝 **Instrucciones:**
• Escribe exactamente: `NIT` o `CC`
• No uses símbolos adicionales

💡 **Ejemplo:**
Si quieres buscar por NIT, escribe: `NIT`
Si quieres buscar por cédula, escribe: `CC`"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_document_type_selection(chat_id, user_id, doc_type):
    """Manejar selección de tipo de documento"""
    logger.info(f"Document type selection: {doc_type} from chat {chat_id}")
    
    if user_id not in user_states:
        handle_client_search_start(chat_id, user_id)
        return
    
    if doc_type not in VALID_DOC_TYPES:
        send_telegram_message(chat_id, f"❌ **Tipo inválido:** {doc_type}\n\n**Opciones válidas:** NIT, CC", parse_mode='Markdown')
        return
    
    # Actualizar estado
    user_states[user_id]['step'] = 'document_number'
    user_states[user_id]['doc_type'] = doc_type
    
    doc_name = "NIT" if doc_type == "NIT" else "Cédula de Ciudadanía"
    min_length = MIN_DOC_LENGTH
    max_length = MAX_NIT_LENGTH if doc_type == "NIT" else MAX_CC_LENGTH
    
    text = f"""📄 **TIPO SELECCIONADO:** {doc_type} ({doc_name}) ✅

**Paso 2/2:** Ingresa el número de documento

**Formato requerido:**
• Solo números (sin puntos, guiones ni espacios)
• Entre {min_length} y {max_length} dígitos
• Ejemplo: 901234567

💡 **Instrucciones:**
• Copia y pega el número si es necesario
• Verifica que no tenga espacios al inicio o final

⚡ **El sistema buscará automáticamente** en la base de datos una vez reciba el número."""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_conversation_state(chat_id, user_id, text):
    """Manejar estados de conversación activa"""
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    step = state['step']
    
    try:
        if step == 'document_number':
            handle_document_number_input(chat_id, user_id, text)
        else:
            # Estado no reconocido, reiniciar
            del user_states[user_id]
            send_telegram_message(chat_id, "Estado de conversacion invalido. Usa 'cliente' para reiniciar.")
    
    except Exception as e:
        logger.error(f"Conversation state error: {e}")
        if user_id in user_states:
            del user_states[user_id]
        send_telegram_message(chat_id, "Error procesando solicitud. Usa 'cliente' para reiniciar.")

def handle_document_number_input(chat_id, user_id, doc_number):
    """Manejar entrada del número de documento"""
    logger.info(f"Document number input: {doc_number} from chat {chat_id}")
    
    state = user_states[user_id]
    doc_type = state.get('doc_type')
    
    # Enviar mensaje de búsqueda en proceso
    send_telegram_message(chat_id, f"Buscando {doc_type}: {doc_number}...\nUn momento por favor")
    
    try:
        # Validar documento
        logger.info(f"Validating document: {doc_type} {doc_number}")
        validation = validate_document_number(doc_type, doc_number)
        if not validation["valid"]:
            logger.warning(f"Validation failed: {validation['error']}")
            send_telegram_message(chat_id, f"Formato incorrecto:\n{validation['error']}\n\nIntenta nuevamente con solo numeros.")
            return
        
        # Buscar cliente con nuevo flujo comercial
        logger.info(f"Starting commercial search for {doc_type}: {doc_number}")
        search_result = search_client_by_document_with_availability(doc_type, doc_number)
        logger.info(f"Search result: success={search_result.get('success')}, found={search_result.get('found')}, unavailable={search_result.get('unavailable', False)}")
        
        if not search_result["success"]:
            logger.error(f"Search failed: {search_result.get('error')}")
            send_telegram_message(chat_id, f"Error al buscar:\nNo pude consultar los datos en este momento.\n\nPor favor intenta en unos minutos.")
            return
        
        if search_result["found"]:
            # Verificar si es cliente no disponible
            if search_result.get("unavailable"):
                logger.info(f"Client is unavailable for orders")
                response = f"""CLIENTE EXISTENTE - NO DISPONIBLE

Documento: {doc_type} {doc_number}

Estado: Este cliente EXISTE en el sistema pero NO esta disponible para crear nuevas ordenes en este momento.

Recomendacion: Contacta a tu supervisor o al area comercial para mas informacion sobre este cliente.

Nueva busqueda: Escribe 'cliente'"""
                
                send_telegram_message(chat_id, response)
                
            else:
                # Cliente encontrado y disponible
                matches = search_result["matches"]
                total_matches = search_result["total_matches"]
                logger.info(f"Found {total_matches} available matches")
                
                if total_matches == 1:
                    # Un solo cliente encontrado
                    client_match = matches[0]
                    logger.info(f"Formatting single available client info...")
                    
                    try:
                        client_info = format_client_info(
                            client_match["client_data"], 
                            client_match["matched_field"]
                        )
                        logger.info(f"Client info formatted: {len(client_info)} chars")
                        
                        response = f"""CLIENTE DISPONIBLE!

{client_info}

Estado: Cliente DISPONIBLE para crear ordenes

Busqueda realizada:
• Tipo: {doc_type}
• Numero: {doc_number}

Nueva busqueda: Escribe 'cliente'"""
                        
                        logger.info(f"Sending response: {len(response)} characters")
                        success = send_telegram_message(chat_id, response)
                        logger.info(f"Message sent: {success}")
                        
                    except Exception as format_error:
                        logger.error(f"Format error: {format_error}")
                        # Respuesta de fallback más simple
                        simple_response = f"""CLIENTE DISPONIBLE!

Documento: {doc_type} {doc_number}
Estado: Cliente disponible para crear ordenes

Nueva busqueda: Escribe 'cliente'"""
                        send_telegram_message(chat_id, simple_response)
                    
                else:
                    # Múltiples clientes encontrados
                    logger.info(f"Formatting multiple available clients: {total_matches}")
                    response = f"""VARIOS CLIENTES DISPONIBLES! ({total_matches})

Documento buscado: {doc_type} {doc_number}
Estado: Clientes DISPONIBLES para crear ordenes
Resultado: Se encontraron {total_matches} clientes con este documento

Nueva busqueda: Escribe 'cliente'"""
                    
                    send_telegram_message(chat_id, response)
            
        else:
            # Cliente no encontrado - mostrar opción de pre-registro
            total_searched = search_result.get("total_clients_searched", 0)
            logger.info(f"No matches found in {total_searched} clients - showing pre-register option")
            
            response = f"""CLIENTE NO ENCONTRADO

Lo que busque:
• Tipo de documento: {doc_type}
• Numero: {doc_number}
• Clientes consultados: {total_searched:,}

Que hacer ahora?

CREAR NUEVO CLIENTE:
Para registrar este cliente usa el siguiente enlace:

{PREREGISTER_URL}

Pasos:
1. Hacer clic en el enlace de arriba
2. Completar el formulario de pre-registro
3. Una vez registrado, podras crear ordenes

Nueva busqueda: Escribe 'cliente'"""
            
            send_telegram_message(chat_id, response)
        
        # Limpiar estado
        del user_states[user_id]
        logger.info(f"Search process completed, user state cleaned")
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        send_telegram_message(chat_id, f"Hubo un problema:\nNo pude completar la busqueda en este momento.\n\nUsa 'cliente' para intentar nuevamente.")
        if user_id in user_states:
            del user_states[user_id]

def handle_stats_command(chat_id):
    """Manejar comando de estadísticas"""
    logger.info(f"Stats command from chat {chat_id}")
    
    send_telegram_message(chat_id, "📊 **Cargando información...**\n⏳ *Un momento por favor*")
    
    try:
        summary_result = get_clients_summary()
        
        if not summary_result["success"]:
            send_telegram_message(chat_id, f"❌ **No pude obtener la información en este momento.**\nIntenta nuevamente en unos minutos.", parse_mode='Markdown')
            return
        
        stats = summary_result["stats"]
        
        cached_status = "✅ Sí" if not stats['cached'] else "📋 Desde memoria"
        
        response = f"""📊 **INFORMACIÓN DEL SISTEMA** ⚡

**📈 Resumen:**
• Total de clientes: {stats['total_clients']:,}
• Información actualizada: {cached_status}

**🔍 ¿Qué puedo buscar?**
• Clientes por NIT (empresas)
• Clientes por Cédula (personas)
• Información completa de contacto
• Datos de ubicación

**⚡ Características:**
✅ Búsqueda rápida e inteligente
✅ Más de {stats['total_clients']:,} clientes disponibles
✅ Información siempre actualizada
✅ Disponible las 24 horas

💡 **Para buscar un cliente:** Escribe `cliente`"""
        
        send_telegram_message(chat_id, response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        send_telegram_message(chat_id, f"❌ **Hubo un problema al obtener la información.**\nPor favor intenta en unos minutos.", parse_mode='Markdown')

def handle_unknown_command(chat_id, text):
    """Manejar comandos no reconocidos"""
    text_lower = text.lower()
    
    # Sugerencias inteligentes
    if any(word in text_lower for word in ['cliente', 'buscar', 'encontrar', 'search']):
        suggestion = "💡 **Sugerencia:** Escribe `cliente` para buscar un cliente"
    elif any(word in text_lower for word in ['nit', 'cedula', 'documento']):
        suggestion = "💡 **Sugerencia:** Escribe `cliente` primero, luego elige el tipo de documento"
    elif any(word in text_lower for word in ['estadistica', 'resumen', 'info']):
        suggestion = "💡 **Sugerencia:** Escribe `resumen` para ver información del sistema"
    else:
        suggestion = "💡 **Sugerencia:** Escribe `help` para ver qué puedo hacer"
    
    response = f"""❓ **No entendí:** `{text}`

{suggestion}

**📋 Lo que puedo hacer:**
• `cliente` - Buscar un cliente
• `resumen` - Ver información general  
• `help` - Ver todos los comandos

**🔍 ¿Quieres buscar un cliente?** Escribe: `cliente`"""
    
    send_telegram_message(chat_id, response, parse_mode='Markdown')
