# 🤖 bot_handlers.py - Manejadores del Bot Telegram v1.0
import logging
from flask import request
from config import *
from redash_service import search_client_by_document, get_clients_summary, validate_document_number, format_client_info
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
            logger.error(f"❌ Webhook error: {e}")
            return "Handled with error", 200

def handle_start_command(chat_id):
    """Comando /start - Bienvenida"""
    logger.info(f"📱 /start from chat {chat_id}")
    
    text = """🎯 **Buscador de Clientes** ⚡

🔹 Te ayudo a buscar información de clientes de forma rápida y fácil.

**📋 ¿Qué puedo hacer?**
• cliente - Buscar un cliente
• resumen - Ver información general
• help - Ver todos los comandos

**🔍 Puedo buscar por:**
• NIT - Número de Identificación Tributaria  
• CC - Cédula de Ciudadanía

**💡 ¿Cómo funciona?**
1. Escribe: cliente
2. Selecciona: NIT o CC  
3. Escribe el número del documento
4. ¡Listo! Te muestro la información

🚀 **¡Empecemos a buscar clientes!**"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_help_command(chat_id):
    """Comando /help - Ayuda"""
    text = """📚 **¿Cómo usar el buscador?** ⚡

**🔍 Buscar Clientes:**
• cliente - Empezar búsqueda
• NIT - Para empresas
• CC - Para personas

**📊 Información:**
• resumen - Ver datos disponibles
• help - Mostrar esta ayuda
• start - Volver al inicio

**📝 Proceso paso a paso:**
1. **Empezar:** Escribe `cliente`
2. **Tipo:** Selecciona `NIT` o `CC`
3. **Número:** Escribe el documento (solo números)
4. **Resultado:** Te muestro la información

**📄 Formatos que acepto:**
• NIT: Entre 6 y 15 números
• CC: Entre 6 y 10 números

**💡 Ejemplos:**
• NIT: 901234567
• CC: 12345678

**✨ Características:**
✅ Búsqueda instantánea
✅ Información completa del cliente
✅ Fácil de usar
✅ Disponible 24/7"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_client_search_start(chat_id, user_id):
    """Iniciar proceso de búsqueda de cliente"""
    logger.info(f"📱 Client search start from chat {chat_id}")
    
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
    logger.info(f"📱 Document type selection: {doc_type} from chat {chat_id}")
    
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
            send_telegram_message(chat_id, "❌ **Estado de conversación inválido.** Usa `/cliente` para reiniciar.", parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"❌ Conversation state error: {e}")
        if user_id in user_states:
            del user_states[user_id]
        send_telegram_message(chat_id, "❌ **Error procesando solicitud.** Usa `/cliente` para reiniciar.", parse_mode='Markdown')

def handle_document_number_input(chat_id, user_id, doc_number):
    """Manejar entrada del número de documento"""
    logger.info(f"📱 Document number input from chat {chat_id}")
    
    state = user_states[user_id]
    doc_type = state.get('doc_type')
    
    # Enviar mensaje de búsqueda en proceso
    send_telegram_message(chat_id, f"🔍 **Buscando {doc_type}: {doc_number}...**\n⏳ *Un momento por favor*")
    
    try:
        # Validar documento
        validation = validate_document_number(doc_type, doc_number)
        if not validation["valid"]:
            send_telegram_message(chat_id, f"❌ **Formato incorrecto:**\n{validation['error']}\n\n💡 Intenta nuevamente con solo números.", parse_mode='Markdown')
            return
        
        # Buscar cliente
        search_result = search_client_by_document(doc_type, doc_number)
        
        if not search_result["success"]:
            send_telegram_message(chat_id, f"❌ **Error al buscar:**\nNo pude consultar los datos en este momento.\n\n🔄 Por favor intenta en unos minutos.", parse_mode='Markdown')
            return
        
        if search_result["found"]:
            # Cliente encontrado
            matches = search_result["matches"]
            total_matches = search_result["total_matches"]
            
            if total_matches == 1:
                # Un solo cliente encontrado
                client_match = matches[0]
                client_info = format_client_info(
                    client_match["client_data"], 
                    client_match["matched_field"]
                )
                
                response = f"""✅ **¡CLIENTE ENCONTRADO!** 🎯

{client_info}

📋 **Búsqueda realizada:**
• Tipo: {doc_type}
• Número: {doc_number}

💡 **Nueva búsqueda:** Escribe `cliente`"""
                
            else:
                # Múltiples clientes encontrados
                response = f"✅ **¡ENCONTRÉ VARIOS CLIENTES!** ({total_matches}) 🔍\n\n"
                
                for i, match in enumerate(matches[:MAX_RESULTS_SHOW], 1):
                    client_info = format_client_info(match["client_data"], match["matched_field"])
                    response += f"**Cliente #{i}:**\n{client_info}\n\n"
                
                if total_matches > MAX_RESULTS_SHOW:
                    response += f"📌 **Mostrando {MAX_RESULTS_SHOW} de {total_matches} clientes encontrados**\n\n"
                
                response += f"💡 **Nueva búsqueda:** Escribe `cliente`"
            
            send_telegram_message(chat_id, response, parse_mode='Markdown')
            
        else:
            # Cliente no encontrado
            total_searched = search_result.get("total_clients_searched", 0)
            
            response = f"""❌ **NO ENCONTRÉ ESTE CLIENTE** 🔍

**Lo que busqué:**
• Tipo de documento: {doc_type}
• Número: {doc_number}
• Clientes consultados: {total_searched:,}

**¿Qué puede haber pasado?**
• El documento no está en la base de datos
• Puede estar registrado de forma diferente
• Verifica si escribiste bien el número

💡 **Sugerencias:**
• Revisa el número del documento
• Intenta con el otro tipo (NIT/CC si corresponde)
• Escribe `cliente` para buscar otro"""
            
            send_telegram_message(chat_id, response, parse_mode='Markdown')
        
        # Limpiar estado
        del user_states[user_id]
        
    except Exception as e:
        logger.error(f"❌ Document search error: {e}")
        send_telegram_message(chat_id, f"❌ **Hubo un problema:**\nNo pude completar la búsqueda en este momento.\n\n🔄 Usa `cliente` para intentar nuevamente.", parse_mode='Markdown')
        if user_id in user_states:
            del user_states[user_id]

def handle_stats_command(chat_id):
    """Manejar comando de estadísticas"""
    logger.info(f"📱 Stats command from chat {chat_id}")
    
    send_telegram_message(chat_id, "📊 **Cargando información...**\n⏳ *Un momento por favor*")
    
    try:
        summary_result = get_clients_summary()
        
        if not summary_result["success"]:
            send_telegram_message(chat_id, f"❌ **No pude obtener la información en este momento.**\nIntenta nuevamente en unos minutos.", parse_mode='Markdown')
            return
        
        stats = summary_result["stats"]
        columns = summary_result["columns"]
        
        response = f"""📊 **INFORMACIÓN DEL SISTEMA** ⚡

**📈 Resumen:**
• Total de clientes: {stats['total_clients']:,}
• Información actualizada: {'✅ Sí' if not stats['cached'] else '📋 Desde memoria'}

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
        logger.error(f"❌ Stats error: {e}")
        send_telegram_message(chat_id, f"❌ **Hubo un problema al obtener la información.**\nPor favor intenta en unos minutos.", parse_mode='Markdown')
        
        response +=
