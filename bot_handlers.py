# bot_handlers.py - Manejadores del Bot Telegram v1.4 - CLEAN VERSION + CREAR COMERCIAL + ÓRDENES
import logging
from flask import request
from config import *
from redash_service import search_client_by_document_with_availability, get_clients_summary, validate_document_number, format_client_info
from nocodb_service import (check_comercial_exists, create_comercial, validate_email_format, 
                          validate_cedula_format, validate_name_format, validate_phone_format, 
                          format_comercial_info, validate_order_number_format, get_comercial_by_cedula,
                          check_order_exists, process_order_assignment)
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
            elif text_lower in ['/crear', 'crear', 'nuevo', 'registrar']:
                handle_create_comercial_start(chat_id, user_id)
            elif text_lower in ['/orden', 'orden', 'asignar', 'assignment']:
                handle_order_assignment_start(chat_id, user_id)
            elif text_lower in ['/resumen', 'resumen', 'estadisticas', 'stats']:
                handle_stats_command(chat_id)
            elif text_lower in ['/info', 'info', 'detalle', 'detalles']:
                handle_info_command(chat_id)
            elif text_lower in ['nit', 'cc'] and user_id in user_states and user_states[user_id].get('process') == 'client_search':
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

**🔍 Para obtener información completa de un cliente:**
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

**👤 Para registrar comerciales nuevos:**
1. Usa 'crear' para empezar
2. El sistema solicitará:

**Datos requeridos:**
• 🆔 Cédula (única en el sistema)
• 📧 Email (formato válido)
• 👤 Nombre completo
• 📞 Teléfono de contacto

**📦 Para asignar órdenes:**
1. Usa 'orden' para empezar
2. El sistema verificará:

**Proceso de asignación:**
• 🔍 Comercial existe (por cédula)
• 📦 Orden existe (formato MP-XXXXX)
• 🎯 Asignación automática

**💡 Tip:** Toda la información disponible se muestra automáticamente en cada búsqueda, registro y asignación.

🔍 **Para buscar:** Escribe 'cliente'
👤 **Para registrar:** Escribe 'crear'  
📦 **Para asignar:** Escribe 'orden'"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_start_command(chat_id):
    """Comando /start - Bienvenida"""
    logger.info(f"Start command from chat {chat_id}")
    
    text = """🎯 **BUSCADOR DE CLIENTES COMERCIALES** ⚡

🔹 Te ayudo a buscar clientes y verificar su **disponibilidad comercial** para crear órdenes.
🔹 También puedo **registrar nuevos comerciales** en el sistema.
🔹 Y puedo **asignar órdenes** a comerciales externos.

**📋 ¿Qué puedo hacer?**
• cliente - Buscar cliente y verificar disponibilidad
• crear - Registrar nuevo comercial externo
• orden - Asignar orden a comercial externo
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

**👤 Para comerciales nuevos:**
• crear - Registrar comercial con cédula, email, nombre y teléfono
• Validación automática de duplicados
• Formatos de email y teléfono validados

**📦 Para asignación de órdenes:**
• orden - Asignar orden a comercial existente
• Verificación de comercial y orden
• Formato automático MP-XXXXX

**📊 Información que obtienes:**
• 🏢 Nombre/Razón social
• 👤 Representante legal
• 📞 Teléfono de contacto
• 📧 Email corporativo
• 📍 Dirección completa
• 🌆 Ciudad y departamento

**💡 ¿Cómo funciona?**
1. Escribe: cliente (buscar) | crear (registrar) | orden (asignar)
2. Sigue las instrucciones paso a paso
3. ¡Te muestro el resultado!

🚀 **¡Empecemos a trabajar!**"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_help_command(chat_id):
    """Comando /help - Ayuda"""
    text = """📋 COMANDOS DISPONIBLES

**🔍 Buscar Clientes:**
• cliente - Empezar búsqueda con verificación comercial
• NIT - Para empresas
• CC - Para personas

**👤 Gestión de Comerciales:**
• crear - Registrar nuevo comercial externo
• Proceso guiado paso a paso
• Validación automática de datos

**📦 Asignación de Órdenes:**
• orden - Asignar orden a comercial externo
• Verificación de comercial existente
• Verificación de orden válida
• Formato automático MP-XXXXX

**📊 Información:**
• resumen - Ver datos del sistema
• info - Detalles sobre qué información se muestra
• help - Mostrar esta ayuda
• start - Volver al inicio

**🔍 Proceso de búsqueda:**
1. Empezar: Escribe 'cliente'
2. Tipo: Selecciona 'NIT' o 'CC'
3. Número: Escribe el documento (solo números)
4. Resultado: Te muestro el estado comercial e información

**👤 Proceso de registro:**
1. Empezar: Escribe 'crear'
2. Cédula: Ingresa cédula del comercial
3. Email: Proporciona email válido
4. Nombre: Ingresa nombre completo
5. Teléfono: Proporciona número de contacto
6. Confirmación: Te confirmo el registro

**📦 Proceso de asignación de órdenes:**
1. Empezar: Escribe 'orden'
2. Cédula: Ingresa cédula del comercial
3. Orden: Proporciona número de orden
4. Confirmación: Te confirmo la asignación

**🚦 Estados de cliente:**
• 🟢 DISPONIBLE - Cliente puede crear órdenes
• 🚫 NO DISPONIBLE - Cliente existe pero no puede crear órdenes
• ❌ NO ENCONTRADO - Necesita pre-registro

**📋 Datos del comercial requeridos:**
• Cédula: 6-12 dígitos únicos
• Email: Formato válido (@dominio.com/co/etc)
• Nombre: 2-100 caracteres
• Teléfono: 7-20 dígitos

**📦 Formatos de orden aceptados:**
• mp-0003 → MP-0003
• MP-0003 → MP-0003
• Mp-003 → MP-003
• 0003 → MP-0003

**✅ Validaciones automáticas:**
• Verificación de comercial existente
• Verificación de orden válida
• Formato de email válido
• Normalización de números de orden
• Longitud de campos apropiada

**📞 Para clientes nuevos:**
Si no encuentras un cliente, te daré el enlace de pre-registro para crearlo.

**⚡ Características comerciales:**
• Verificación de disponibilidad para órdenes
• Información completa del cliente
• Enlaces de pre-registro automáticos
• Estados comerciales claros
• Registro de comerciales seguros
• Asignación de órdenes automatizada
• Disponible 24/7"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_create_comercial_start(chat_id, user_id):
    """Iniciar proceso de creación de comercial"""
    logger.info(f"Create comercial start from chat {chat_id}")
    
    # Establecer estado de usuario
    user_states[user_id] = {
        'step': 'cedula',
        'process': 'create_comercial',
        'chat_id': chat_id,
        'data': {}
    }
    
    text = """👤 **REGISTRAR NUEVO COMERCIAL** ⚡

**¡Vamos a registrar un nuevo comercial externo!**

**Paso 1/4:** Ingresa la cédula del comercial

**🔍 Formato requerido:**
• Solo números (sin puntos, guiones ni espacios)
• Entre 6 y 12 dígitos
• Ejemplo: 12345678

**💡 Instrucciones:**
• El sistema verificará que no esté registrado
• Si ya existe, te mostraré la información
• Si está disponible, continuaremos con el registro

📝 **Ingresa la cédula:**"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_order_assignment_start(chat_id, user_id):
    """Iniciar proceso de asignación de orden"""
    logger.info(f"Order assignment start from chat {chat_id}")
    
    # Establecer estado de usuario
    user_states[user_id] = {
        'step': 'comercial_cedula',
        'process': 'order_assignment',
        'chat_id': chat_id,
        'data': {}
    }
    
    text = """📦 **ASIGNAR ORDEN A COMERCIAL** ⚡

**¡Vamos a asignar una orden a un comercial externo!**

**Paso 1/3:** Ingresa la cédula del comercial

**🔍 Formato requerido:**
• Solo números (sin puntos, guiones ni espacios)
• Entre 6 y 12 dígitos
• Debe ser un comercial ya registrado
• Ejemplo: 12345678

**💡 Instrucciones:**
• El sistema verificará que el comercial exista
• Si no existe, deberás registrarlo primero con 'crear'
• Si existe, continuaremos con la orden

📝 **Ingresa la cédula del comercial:**"""
    
    send_telegram_message(chat_id, text, parse_mode='Markdown')

def handle_client_search_start(chat_id, user_id):
    """Iniciar proceso de búsqueda de cliente"""
    logger.info(f"Client search start from chat {chat_id}")
    
    # Establecer estado de usuario
    user_states[user_id] = {
        'step': 'document_type',
        'process': 'client_search',
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
    process = state.get('process', '')
    step = state['step']
    
    try:
        if process == 'client_search':
            if step == 'document_number':
                handle_document_number_input(chat_id, user_id, text)
        elif process == 'create_comercial':
            if step == 'cedula':
                handle_cedula_input(chat_id, user_id, text)
            elif step == 'email':
                handle_email_input(chat_id, user_id, text)
            elif step == 'name':
                handle_name_input(chat_id, user_id, text)
            elif step == 'phone':
                handle_phone_input(chat_id, user_id, text)
            elif step == 'confirm':
                handle_create_confirmation(chat_id, user_id, text)
        elif process == 'order_assignment':
            if step == 'comercial_cedula':
                handle_comercial_cedula_input(chat_id, user_id, text)
            elif step == 'order_number':
                handle_order_number_input(chat_id, user_id, text)
            elif step == 'assignment_confirm':
                handle_assignment_confirmation(chat_id, user_id, text)
        else:
            # Estado no reconocido, reiniciar
            del user_states[user_id]
            send_telegram_message(chat_id, "Estado de conversación inválido. Usa 'cliente' o 'crear' para reiniciar.")
    
    except Exception as e:
        logger.error(f"Conversation state error: {e}")
        if user_id in user_states:
            del user_states[user_id]
        send_telegram_message(chat_id, "Error procesando solicitud. Usa 'cliente' o 'crear' para reiniciar.")

def handle_cedula_input(chat_id, user_id, cedula):
    """Manejar entrada de cédula para comercial"""
    logger.info(f"Cedula input: {cedula} from chat {chat_id}")
    
    state = user_states[user_id]
    
    # Enviar mensaje de verificación
    send_telegram_message(chat_id, f"🔍 Verificando cédula: {cedula}...\n⏳ Un momento por favor")
    
    try:
        # Validar formato de cédula
        validation = validate_cedula_format(cedula)
        if not validation["valid"]:
            send_telegram_message(chat_id, f"❌ **Formato incorrecto:**\n{validation['error']}\n\n📝 **Intenta nuevamente:**", parse_mode='Markdown')
            return
        
        clean_cedula = validation["cleaned_cedula"]
        
        # Verificar si el comercial ya existe
        exists_check = check_comercial_exists(clean_cedula)
        
        if not exists_check["success"]:
            send_telegram_message(chat_id, f"❌ **Error verificando cédula:**\n{exists_check['error']}\n\n📝 **Intenta nuevamente:**")
            return
        
        if exists_check["exists"]:
            # Comercial ya existe
            comercial_data = exists_check["comercial_data"]
            formatted_info = format_comercial_info(comercial_data)
            
            response = f"""🚫 **COMERCIAL YA REGISTRADO**

{formatted_info}

⚠️ **Estado:** Este comercial ya existe en el sistema.

💡 **¿Qué hacer?**
• Contacta al administrador si necesitas actualizar datos
• Usa otra cédula para registrar un comercial diferente

🔄 **Nueva acción:** Escribe 'crear' para intentar con otra cédula"""
            
            send_telegram_message(chat_id, response, parse_mode='Markdown')
            
            # Limpiar estado
            del user_states[user_id]
            return
        
        # Cédula disponible, continuar con email
        state['data']['cedula'] = clean_cedula
        state['step'] = 'email'
        
        text = f"""✅ **CÉDULA DISPONIBLE:** {clean_cedula}

**Paso 2/4:** Ingresa el email del comercial

**📧 Formato requerido:**
• Debe contener @ y un dominio válido
• Ejemplos válidos:
  - juan.perez@empresa.com
  - maria@tienda.co
  - carlos123@negocio.net

**💡 Instrucciones:**
• Escribe el email completo
• Verifica que esté bien escrito
• El sistema validará el formato automáticamente

📝 **Ingresa el email:**"""
        
        send_telegram_message(chat_id, text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Cedula input error: {e}")
        send_telegram_message(chat_id, f"❌ **Error procesando cédula:**\nNo pude verificar la cédula en este momento.\n\n📝 **Intenta nuevamente:**")

def handle_email_input(chat_id, user_id, email):
    """Manejar entrada de email para comercial"""
    logger.info(f"Email input from chat {chat_id}")
    
    state = user_states[user_id]
    
    try:
        # Validar formato de email
        validation = validate_email_format(email)
        if not validation["valid"]:
            send_telegram_message(chat_id, f"❌ **Formato de email incorrecto:**\n{validation['error']}\n\n📧 **Ejemplos válidos:**\n• juan@empresa.com\n• maria@tienda.co\n\n📝 **Intenta nuevamente:**", parse_mode='Markdown')
            return
        
        clean_email = validation["cleaned_email"]
        
        # Guardar email y continuar con nombre
        state['data']['email'] = clean_email
        state['step'] = 'name'
        
        text = f"""✅ **EMAIL VÁLIDO:** {clean_email}

**Paso 3/4:** Ingresa el nombre del comercial

**👤 Formato requerido:**
• Mínimo 2 caracteres, máximo 100
• Solo letras, espacios, puntos, guiones y apostrofes
• Ejemplos válidos:
  - Juan Pérez
  - María José Rodríguez
  - Carlos O'Connor
  - Ana-Sofía Martínez

**💡 Instrucciones:**
• Escribe el nombre completo
• Puede incluir nombres y apellidos
• El sistema capitalizará automáticamente

📝 **Ingresa el nombre:**"""
        
        send_telegram_message(chat_id, text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Email input error: {e}")
        send_telegram_message(chat_id, f"❌ **Error procesando email:**\nNo pude validar el email en este momento.\n\n📝 **Intenta nuevamente:**")

def handle_name_input(chat_id, user_id, name):
    """Manejar entrada de nombre para comercial"""
    logger.info(f"Name input from chat {chat_id}")
    
    state = user_states[user_id]
    
    try:
        # Validar formato de nombre
        validation = validate_name_format(name)
        if not validation["valid"]:
            send_telegram_message(chat_id, f"❌ **Formato de nombre incorrecto:**\n{validation['error']}\n\n👤 **Ejemplos válidos:**\n• Juan Pérez\n• María José\n• Carlos O'Connor\n\n📝 **Intenta nuevamente:**", parse_mode='Markdown')
            return
        
        clean_name = validation["cleaned_name"]
        
        # Guardar nombre y continuar con teléfono
        state['data']['name'] = clean_name
        state['step'] = 'phone'
        
        text = f"""✅ **NOMBRE VÁLIDO:** {clean_name}

**Paso 4/4:** Ingresa el teléfono del comercial

**📞 Formato requerido:**
• Entre 7 y 20 dígitos
• Puede incluir espacios, guiones, paréntesis y signo +
• Ejemplos válidos:
  - 3001234567
  - +57 300 123 4567
  - (1) 234-5678
  - 300-123-4567

**💡 Instrucciones:**
• Escribe el número completo
• Incluye código de país si es internacional
• El sistema validará la longitud automáticamente

📝 **Ingresa el teléfono:**"""
        
        send_telegram_message(chat_id, text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Name input error: {e}")
        send_telegram_message(chat_id, f"❌ **Error procesando nombre:**\nNo pude validar el nombre en este momento.\n\n📝 **Intenta nuevamente:**")

def handle_phone_input(chat_id, user_id, phone):
    """Manejar entrada de teléfono para comercial"""
    logger.info(f"Phone input from chat {chat_id}")
    
    state = user_states[user_id]
    
    try:
        # Validar formato de teléfono
        validation = validate_phone_format(phone)
        if not validation["valid"]:
            send_telegram_message(chat_id, f"❌ **Formato de teléfono incorrecto:**\n{validation['error']}\n\n📞 **Ejemplos válidos:**\n• 3001234567\n• +57 300 123 4567\n• (1) 234-5678\n\n📝 **Intenta nuevamente:**", parse_mode='Markdown')
            return
        
        clean_phone = validation["cleaned_phone"]
        
        # Guardar teléfono y mostrar resumen para confirmación
        state['data']['phone'] = clean_phone
        state['step'] = 'confirm'
        
        data = state['data']
        
        text = f"""📋 **RESUMEN DEL COMERCIAL A CREAR**

**Datos ingresados:**
🆔 **Cédula:** {data['cedula']}
📧 **Email:** {data['email']}
👤 **Nombre:** {data['name']}
📞 **Teléfono:** {data['phone']}

**¿Los datos son correctos?**

**✅ Para CONFIRMAR:** Escribe `SI` o `CONFIRMAR`
**❌ Para CANCELAR:** Escribe `NO` o `CANCELAR`

💡 **Nota:** Una vez confirmado, se creará el comercial en el sistema."""
        
        send_telegram_message(chat_id, text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Phone input error: {e}")
        send_telegram_message(chat_id, f"❌ **Error procesando teléfono:**\nNo pude validar el teléfono en este momento.\n\n📝 **Intenta nuevamente:**")

def handle_comercial_cedula_input(chat_id, user_id, cedula):
    """Manejar entrada de cédula para asignación de orden"""
    logger.info(f"Comercial cedula input: {cedula} from chat {chat_id}")
    
    state = user_states[user_id]
    
    # Enviar mensaje de verificación
    send_telegram_message(chat_id, f"🔍 Verificando comercial con cédula: {cedula}...\n⏳ Un momento por favor")
    
    try:
        # Verificar si el comercial existe y obtener ID
        result = get_comercial_by_cedula(cedula)
        
        if not result.get("success"):
            send_telegram_message(chat_id, f"❌ **Error verificando comercial:**\n{result.get('error')}\n\n📝 **Intenta nuevamente:**")
            return
        
        if not result.get("found"):
            # Comercial no existe
            response = f"""❌ **COMERCIAL NO ENCONTRADO**

La cédula **{cedula}** no está registrada en el sistema.

**¿Qué hacer?**
• Verifica que la cédula sea correcta
• Registra primero el comercial con el comando `crear`
• Una vez registrado, podrás asignar órdenes

**🔄 Opciones:**
• Escribe `crear` para registrar el comercial
• Escribe `orden` para intentar con otra cédula

📝 **¿Quieres intentar con otra cédula?** Ingresa la cédula:"""
            
            send_telegram_message(chat_id, response, parse_mode='Markdown')
            return
        
        # Comercial encontrado, guardar datos y continuar
        comercial_id = result.get("comercial_id")
        comercial_data = result.get("comercial_data")
        
        state['data']['comercial_cedula'] = cedula
        state['data']['comercial_id'] = comercial_id
        state['data']['comercial_data'] = comercial_data
        state['step'] = 'order_number'
        
        formatted_info = format_comercial_info(comercial_data)
        
        text = f"""✅ **COMERCIAL ENCONTRADO** 

{formatted_info}

**Paso 2/3:** Ingresa el número de orden

**📦 Formato de orden:**
• Ejemplos aceptados:
  - MP-0003
  - mp-0003  
  - Mp-003
  - 0003 (se convertirá a MP-0003)

**💡 Instrucciones:**
• El sistema normalizará el formato automáticamente
• Verificará que la orden exista en el sistema
• Formato final será: MP-XXXXX

📝 **Ingresa el número de orden:**"""
        
        send_telegram_message(chat_id, text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Comercial cedula input error: {e}")
        send_telegram_message(chat_id, f"❌ **Error procesando cédula:**\nNo pude verificar el comercial en este momento.\n\n📝 **Intenta nuevamente:**")

def handle_order_number_input(chat_id, user_id, order_number):
    """Manejar entrada de número de orden"""
    logger.info(f"Order number input: {order_number} from chat {chat_id}")
    
    state = user_states[user_id]
    
    # Enviar mensaje de verificación
    send_telegram_message(chat_id, f"📦 Verificando orden: {order_number}...\n⏳ Un momento por favor")
    
    try:
        # Verificar que la orden existe
        result = check_order_exists(order_number)
        
        if not result.get("success"):
            send_telegram_message(chat_id, f"❌ **Error verificando orden:**\n{result.get('error')}\n\n📝 **Intenta nuevamente:**")
            return
        
        if not result.get("exists"):
            normalized_order = result.get("normalized_order", order_number)
            
            response = f"""❌ **ORDEN NO ENCONTRADA**

La orden **{normalized_order}** no existe en el sistema.

**¿Qué verificar?**
• El número de orden sea correcto
• La orden esté creada en el sistema
• No haya errores de escritura

**💡 Formato normalizado:** {normalized_order}

📝 **¿Quieres intentar con otro número?** Ingresa la orden:"""
            
            send_telegram_message(chat_id, response, parse_mode='Markdown')
            return
        
        # Orden encontrada, preparar confirmación
        normalized_order = result.get("normalized_order")
        order_data = result.get("order_data")
        
        state['data']['order_number'] = normalized_order
        state['data']['order_data'] = order_data
        state['step'] = 'assignment_confirm'
        
        comercial_data = state['data']['comercial_data']
        
        text = f"""📋 **RESUMEN DE ASIGNACIÓN**

**Comercial:**
👤 **Nombre:** {comercial_data.get('name', 'Sin nombre')}
🆔 **Cédula:** {comercial_data.get('cedula')}
📧 **Email:** {comercial_data.get('email', 'No disponible')}

**Orden:**
📦 **Número:** {normalized_order}
✅ **Estado:** Orden válida en el sistema

**¿Confirmas la asignación?**

**✅ Para CONFIRMAR:** Escribe `SI` o `CONFIRMAR`
**❌ Para CANCELAR:** Escribe `NO` o `CANCELAR`

💡 **Nota:** Una vez confirmado, la orden será asignada al comercial."""
        
        send_telegram_message(chat_id, text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Order number input error: {e}")
        send_telegram_message(chat_id, f"❌ **Error procesando orden:**\nNo pude verificar la orden en este momento.\n\n📝 **Intenta nuevamente:**")

def handle_assignment_confirmation(chat_id, user_id, confirmation):
    """Manejar confirmación de asignación de orden"""
    logger.info(f"Assignment confirmation: {confirmation} from chat {chat_id}")
    
    state = user_states[user_id]
    confirmation_lower = confirmation.lower().strip()
    
    if confirmation_lower in ['si', 'sí', 'yes', 'confirmar', 'confirmo', 'ok', 'vale']:
        # Confirmar asignación
        send_telegram_message(chat_id, "🎯 **Asignando orden...**\n⏳ *Un momento por favor*")
        
        try:
            data = state['data']
            
            # Procesar asignación completa
            result = process_order_assignment(
                cedula=data['comercial_cedula'],
                order_number=data['order_number']
            )
            
            if result["success"]:
                # Éxito
                details = result["details"]
                
                response = f"""✅ **¡ORDEN ASIGNADA EXITOSAMENTE!** 🎉

**Información de la asignación:**
📦 **Orden:** {details['order_number']}
👤 **Comercial:** {details['comercial_name']}
🆔 **Cédula:** {details['comercial_cedula']}
🔗 **ID Comercial:** {details['comercial_id']}

**✅ Estado:** Orden asignada y activa en el sistema

🔄 **¿Qué hacer ahora?**
• El comercial ya tiene la orden asignada
• Para asignar otra orden: escribe 'orden'
• Para buscar clientes: escribe 'cliente'
• Para registrar comercial: escribe 'crear'

🎯 **¡Asignación completada!**"""
                
                send_telegram_message(chat_id, response, parse_mode='Markdown')
                
            else:
                # Error en asignación
                send_telegram_message(chat_id, f"❌ **Error asignando orden:**\n{result['error']}\n\n🔄 **Intenta nuevamente:** Escribe 'orden'")
            
            # Limpiar estado
            del user_states[user_id]
            
        except Exception as e:
            logger.error(f"Assignment confirmation error: {e}")
            send_telegram_message(chat_id, f"❌ **Error procesando asignación:**\nNo pude completar la asignación en este momento.\n\n🔄 **Intenta nuevamente:** Escribe 'orden'")
            if user_id in user_states:
                del user_states[user_id]
    
    elif confirmation_lower in ['no', 'cancelar', 'cancel', 'salir', 'exit']:
        # Cancelar asignación
        send_telegram_message(chat_id, "❌ **Asignación cancelada**\n\n🔄 **Para intentar nuevamente:** Escribe 'orden'\n💡 **Para otras opciones:** Escribe 'help'")
        
        # Limpiar estado
        del user_states[user_id]
    
    else:
        # Respuesta no reconocida
        send_telegram_message(chat_id, "❓ **Respuesta no reconocida**\n\n**✅ Para CONFIRMAR:** Escribe `SI`\n**❌ Para CANCELAR:** Escribe `NO`", parse_mode='Markdown')

def handle_create_confirmation(chat_id, user_id, confirmation):
    """Manejar confirmación de creación de comercial"""
    logger.info(f"Create confirmation: {confirmation} from chat {chat_id}")
    
    state = user_states[user_id]
    confirmation_lower = confirmation.lower().strip()
    
    if confirmation_lower in ['si', 'sí', 'yes', 'confirmar', 'confirmo', 'ok', 'vale']:
        # Confirmar creación
        send_telegram_message(chat_id, "🏗️ **Creando comercial...**\n⏳ *Un momento por favor*")
        
        try:
            data = state['data']
            
            # Crear comercial
            result = create_comercial(
                cedula=data['cedula'],
                email=data['email'], 
                name=data['name'],
                phone=data['phone']
            )
            
            if result["success"]:
                # Éxito
                details = result["details"]
                
                response = f"""✅ **¡COMERCIAL CREADO EXITOSAMENTE!** 🎉

**Información registrada:**
🆔 **Cédula:** {details['cedula']}
👤 **Nombre:** {details['name']}
📧 **Email:** {details['email']}
📞 **Teléfono:** {details['phone']}

**✅ Estado:** Comercial registrado y activo en el sistema

🔄 **¿Qué hacer ahora?**
• El comercial ya puede usar el sistema
• Para registrar otro: escribe 'crear'
• Para buscar clientes: escribe 'cliente'

🎯 **¡Listo para trabajar!**"""
                
                send_telegram_message(chat_id, response, parse_mode='Markdown')
                
            else:
                # Error en creación
                send_telegram_message(chat_id, f"❌ **Error creando comercial:**\n{result['error']}\n\n🔄 **Intenta nuevamente:** Escribe 'crear'")
            
            # Limpiar estado
            del user_states[user_id]
            
        except Exception as e:
            logger.error(f"Create confirmation error: {e}")
            send_telegram_message(chat_id, f"❌ **Error procesando creación:**\nNo pude crear el comercial en este momento.\n\n🔄 **Intenta nuevamente:** Escribe 'crear'")
            if user_id in user_states:
                del user_states[user_id]
    
    elif confirmation_lower in ['no', 'cancelar', 'cancel', 'salir', 'exit']:
        # Cancelar creación
        send_telegram_message(chat_id, "❌ **Creación cancelada**\n\n🔄 **Para intentar nuevamente:** Escribe 'crear'\n💡 **Para otras opciones:** Escribe 'help'")
        
        # Limpiar estado
        del user_states[user_id]
    
    else:
        # Respuesta no reconocida
        send_telegram_message(chat_id, "❓ **Respuesta no reconocida**\n\n**✅ Para CONFIRMAR:** Escribe `SI`\n**❌ Para CANCELAR:** Escribe `NO`", parse_mode='Markdown')

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
            send_telegram_message(chat_id, f"Formato incorrecto:\n{validation['error']}\n\nIntenta nuevamente con solo números.")
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

Estado: Este cliente EXISTE en el sistema pero NO está disponible para crear nuevas órdenes en este momento.

Recomendación: Contacta a tu supervisor o al área comercial para más información sobre este cliente.

Nueva búsqueda: Escribe 'cliente'"""
                
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

Estado: Cliente DISPONIBLE para crear órdenes

Búsqueda realizada:
• Tipo: {doc_type}
• Número: {doc_number}

Nueva búsqueda: Escribe 'cliente'"""
                        
                        logger.info(f"Sending response: {len(response)} characters")
                        success = send_telegram_message(chat_id, response)
                        logger.info(f"Message sent: {success}")
                        
                    except Exception as format_error:
                        logger.error(f"Format error: {format_error}")
                        # Respuesta de fallback más simple
                        simple_response = f"""CLIENTE DISPONIBLE!

Documento: {doc_type} {doc_number}
Estado: Cliente disponible para crear órdenes

Nueva búsqueda: Escribe 'cliente'"""
                        send_telegram_message(chat_id, simple_response)
                    
                else:
                    # Múltiples clientes encontrados
                    logger.info(f"Formatting multiple available clients: {total_matches}")
                    response = f"""VARIOS CLIENTES DISPONIBLES! ({total_matches})

Documento buscado: {doc_type} {doc_number}
Estado: Clientes DISPONIBLES para crear órdenes
Resultado: Se encontraron {total_matches} clientes con este documento

Nueva búsqueda: Escribe 'cliente'"""
                    
                    send_telegram_message(chat_id, response)
            
        else:
            # Cliente no encontrado - mostrar opción de pre-registro
            total_searched = search_result.get("total_clients_searched", 0)
            logger.info(f"No matches found in {total_searched} clients - showing pre-register option")
            
            response = f"""CLIENTE NO ENCONTRADO

Lo que busqué:
• Tipo de documento: {doc_type}
• Número: {doc_number}
• Clientes consultados: {total_searched:,}

¿Qué hacer ahora?

CREAR NUEVO CLIENTE:
Para registrar este cliente usa el siguiente enlace:

{PREREGISTER_URL}

Pasos:
1. Hacer clic en el enlace de arriba
2. Completar el formulario de pre-registro
3. Una vez registrado, podrás crear órdenes

Nueva búsqueda: Escribe 'cliente'"""
            
            send_telegram_message(chat_id, response)
        
        # Limpiar estado
        del user_states[user_id]
        logger.info(f"Search process completed, user state cleaned")
        
    except Exception as e:
        logger.error(f"Document search error: {e}")
        send_telegram_message(chat_id, f"Hubo un problema:\nNo pude completar la búsqueda en este momento.\n\nUsa 'cliente' para intentar nuevamente.")
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

**👤 ¿Qué puedo registrar?**
• Comerciales externos nuevos
• Validación automática de duplicados
• Datos completos de contacto

**📦 ¿Qué puedo asignar?**
• Órdenes a comerciales existentes
• Verificación automática de comercial
• Verificación automática de orden
• Formato MP-XXXXX normalizado

**⚡ Características:**
✅ Búsqueda rápida e inteligente
✅ Más de {stats['total_clients']:,} clientes disponibles
✅ Registro seguro de comerciales
✅ Asignación automatizada de órdenes
✅ Información siempre actualizada
✅ Disponible las 24 horas

💡 **Para buscar un cliente:** Escribe `cliente`
👤 **Para registrar comercial:** Escribe `crear`
📦 **Para asignar orden:** Escribe `orden`"""
        
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
    elif any(word in text_lower for word in ['crear', 'nuevo', 'registrar', 'comercial']):
        suggestion = "💡 **Sugerencia:** Escribe `crear` para registrar un comercial"
    elif any(word in text_lower for word in ['orden', 'asignar', 'assignment', 'order']):
        suggestion = "💡 **Sugerencia:** Escribe `orden` para asignar una orden"
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
• `crear` - Registrar comercial nuevo
• `orden` - Asignar orden a comercial
• `resumen` - Ver información general  
• `help` - Ver todos los comandos

**🔍 ¿Quieres buscar un cliente?** Escribe: `cliente`
**👤 ¿Quieres crear un comercial?** Escribe: `crear`
**📦 ¿Quieres asignar una orden?** Escribe: `orden`"""
    
    send_telegram_message(chat_id, response, parse_mode='Markdown')
