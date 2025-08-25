# 🚀 mcpComercialExt v1.0 - Bot Comercial Externo

## 🎯 Descripción General

**mcpComercialExt** es un sistema especializado de búsqueda de clientes para comerciales externos, que permite consultar la base de datos de clientes a través de un bot de Telegram interactivo.

### 🏢 Contexto de Negocio
- **Objetivo:** Facilitar a los comerciales externos la búsqueda de información de clientes
- **Funcionalidad Principal:** Búsqueda por NIT y Cédula de Ciudadanía
- **Fuente de Datos:** API de Redash con más de 5,000 registros de clientes

---

## 🗂️ Estructura del Proyecto

```
mcpComercialExt/
├── app.py              # Aplicación principal Flask
├── config.py           # Configuración central
├── redash_service.py   # Servicio de integración con Redash
├── bot_handlers.py     # Manejadores del bot de Telegram
├── utils.py            # Utilidades y helpers
├── requirements.txt    # Dependencias Python
└── README.md           # Documentación
```

---

## 🔧 Configuración y Deployment

### 📦 Dependencias
```txt
Flask==3.0.0
Flask-CORS==4.0.0
requests==2.31.0
gunicorn==21.2.0
```

### 🌍 Variables de Entorno

#### Para Render (Producción):
```bash
WEBHOOK_URL=https://your-app-name.onrender.com
```

#### Configuración Hardcoded (No cambiar):
```python
# Token del bot de Telegram
TELEGRAM_TOKEN = "7337079580:AAFxBDY4B1Muc6sUpV0uNxYa6DgVQh3LE_8"

# API de Redash
REDASH_BASE_URL = "https://redash-mcp.farmuhub.co"
REDASH_API_KEY = "MJAgj9yCdpVsWFdinPPfqBkQuvTBKmhCOD9JEmNZ"
REDASH_QUERY_ID = "100"
```

### 🚀 Deployment en Render

1. **Configuración del Servicio:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Puerto: Automático

2. **Variable de Entorno:**
   ```bash
   WEBHOOK_URL=https://your-app-name.onrender.com
   ```

3. **URLs del Sistema:**
   - Producción: `https://your-app-name.onrender.com`
   - API Base: `https://your-app-name.onrender.com/api`
   - Webhook: `https://your-app-name.onrender.com/telegram-webhook`

---

## 🤖 Bot de Telegram

### 📱 Comandos Principales

#### Comandos Básicos
```bash
/start      # Bienvenida e introducción
/help       # Lista completa de comandos
cliente     # Iniciar búsqueda de cliente
resumen     # Ver estadísticas de la base de datos
```

### 🔍 Proceso de Búsqueda (3 Pasos)

#### Paso 1: Comando Inicial
```
Usuario: cliente
Bot: "Selecciona el tipo de documento: NIT o CC"
```

#### Paso 2: Tipo de Documento
```
Usuario: NIT
Bot: "Ingresa el número de NIT (solo números, sin puntos ni guiones)"
```

#### Paso 3: Número de Documento
```
Usuario: 901234567
Bot: [Resultado de la búsqueda]
```

### 📋 Tipos de Documento Soportados

#### NIT (Número de Identificación Tributaria)
- **Formato:** Solo números
- **Longitud:** Entre 6 y 15 dígitos
- **Ejemplo:** `901234567`

#### CC (Cédula de Ciudadanía)
- **Formato:** Solo números
- **Longitud:** Entre 6 y 10 dígitos
- **Ejemplo:** `12345678`

### 💬 Ejemplos de Conversación

#### Búsqueda Exitosa
```
👤 Usuario: cliente
🤖 Bot: 🔍 BÚSQUEDA DE CLIENTE ⚡
        Paso 1/2: Selecciona el tipo de documento
        Opciones: NIT o CC

👤 Usuario: NIT
🤖 Bot: 📄 TIPO SELECCIONADO: NIT ✅
        Paso 2/2: Ingresa el número de documento
        Formato: Solo números (sin puntos, guiones ni espacios)

👤 Usuario: 901234567
🤖 Bot: 🔍 Buscando NIT: 901234567...
        ⏳ Consultando base de datos

🤖 Bot: ✅ CLIENTE ENCONTRADO 🎯
        🔍 Encontrado por: nit = 901234567
        • Nombre: EMPRESA EJEMPLO S.A.S
        • Email: contacto@ejemplo.com
        • Teléfono: 300 123 4567
        • Ciudad: Bogotá - Cundinamarca
```

#### Cliente No Encontrado
```
👤 Usuario: 999888777
🤖 Bot: ❌ CLIENTE NO ENCONTRADO 🔍
        Búsqueda realizada:
        • Tipo: NIT
        • Número: 999888777
        • Registros consultados: 5,247
        
        Posibles causas:
        • El documento no está registrado
        • Formato diferente en la base de datos
        • Error de digitación
```

---

## 📊 Integración con Redash

### 🔗 Configuración de API

#### Endpoint Principal
```
https://redash-mcp.farmuhub.co/api/queries/100/results.json?api_key=MJAgj9yCdpVsWFdinPPfqBkQuvTBKmhCOD9JEmNZ
```

#### Estructura de Datos
```json
{
  "query_result": {
    "data": {
      "rows": [
        {
          "campo1": "valor1",
          "campo2": "valor2",
          "nit": "901234567",
          "nombre": "EMPRESA EJEMPLO"
        }
      ],
      "columns": [
        {"name": "campo1", "type": "string"},
        {"name": "nit", "type": "string"}
      ]
    }
  }
}
```

### ⚡ Sistema de Cache

#### Características
- **TTL:** 1 hora (3600 segundos)
- **Propósito:** Reducir latencia en consultas repetidas
- **Invalidación:** Automática por tiempo
- **Fallback:** Cache expirado en caso de error de API

#### Beneficios
- ✅ Respuestas instantáneas para consultas recientes
- ✅ Menor carga sobre la API de Redash
- ✅ Mayor disponibilidad del servicio
- ✅ Mejor experiencia de usuario

---

## 🔍 Sistema de Búsqueda

### 🎯 Algoritmo de Búsqueda

#### Detección Automática de Campos
1. **Campos Específicos:** `nit`, `cedula`, `documento`, `doc_number`, `identification`
2. **Campos Generales:** Todos los campos de texto como fallback
3. **Limpieza de Datos:** Eliminación de puntos, guiones y espacios
4. **Comparación Exacta:** Coincidencia precisa del documento

#### Procesamiento de Documentos
```python
# Ejemplo de limpieza
Input:  "90.123.456-7"
Clean:  "901234567"

Input:  "12.345.678"
Clean:  "12345678"
```

### 📈 Estadísticas de Búsqueda

#### Métricas Disponibles
- **Total de clientes:** +5,000 registros
- **Campos detectados:** Automático según estructura
- **Tiempo de respuesta:** ~500ms (cached) / ~2s (fresh)
- **Tasa de éxito:** Depende de la calidad de datos

---

## 📌 API REST

### 🏠 Endpoints Principales

#### Información del Sistema
```http
GET /
```
**Respuesta:** Información completa del sistema, configuración y estado

#### Health Check
```http
GET /health
```
**Respuesta:** Estado detallado de servicios y conexiones

#### Listar Clientes
```http
GET /api/clients?limit=10&include_sample=true
```
**Parámetros:**
- `limit` (opcional): Número máximo de clientes
- `include_sample` (opcional): Incluir muestra de datos

#### Buscar Cliente
```http
GET /api/clients/search?type=NIT&number=901234567
```
**Parámetros:**
- `type`: Tipo de documento (NIT/CC)
- `number`: Número de documento

**Respuesta exitosa:**
```json
{
  "success": true,
  "found": true,
  "matches": [
    {
      "client_data": {
        "nit": "901234567",
        "nombre": "EMPRESA EJEMPLO S.A.S"
      },
      "matched_field": "nit",
      "matched_value": "901234567"
    }
  ],
  "total_matches": 1
}
```

#### Resumen de Clientes
```http
GET /api/clients/summary
```
**Respuesta:** Estadísticas y metadatos de la base de datos

#### Configurar Webhook
```http
POST /setup-webhook
```
**Función:** Configurar webhook de Telegram automáticamente

---

## 🛠️ Características Técnicas

### ⚡ Optimizaciones

#### Performance
- **Cache en Memoria:** TTL de 1 hora para consultas Redash
- **Conexiones Reutilizables:** Pool de conexiones HTTP
- **Timeouts Configurables:** 30s para Redash, 8s para Telegram
- **Respuestas Chunked:** División automática de mensajes largos

#### Robustez
- **Fallback a Cache Expirado:** En caso de error de API
- **Validación de Entrada:** Formato y longitud de documentos
- **Manejo de Errores:** Mensajes descriptivos para usuarios
- **Logging Completo:** Rastreo de todas las operaciones

### 🔒 Validaciones

#### Documentos
```python
# NIT: 6-15 dígitos
# CC: 6-10 dígitos
# Solo números (limpieza automática)

def validate_document_number(doc_type, doc_number):
    clean_number = str(doc_number).replace('-', '').replace('.', '')
    
    if doc_type == "NIT":
        return 6 <= len(clean_number) <= 15
    elif doc_type == "CC":
        return 6 <= len(clean_number) <= 10
```

#### Estados de Usuario
- **Gestión de Sesiones:** Estados temporales por usuario
- **Timeouts de Sesión:** Limpieza automática de estados antiguos
- **Validación de Flujo:** Verificación de pasos secuenciales

---

## 🚨 Troubleshooting

### ❌ Problemas Comunes

#### Bot No Responde
**Síntoma:** El bot no recibe mensajes
**Solución:**
1. Verificar token: `GET /health`
2. Configurar webhook: `POST /setup-webhook`
3. Verificar URL de webhook en variables de entorno

#### Error de API Redash
**Síntoma:** "Error consultando base de datos"
**Solución:**
1. Verificar conectividad a Redash
2. Validar API key en configuración
3. Revisar logs para detalles del error

#### Cliente No Encontrado (Falso Negativo)
**Síntoma:** Cliente existe pero no se encuentra
**Posibles Causas:**
1. Formato diferente en base de datos (ej: con puntos)
2. Campo de documento en columna no detectada
3. Tipo de documento incorrecto (NIT vs CC)

#### Timeout en Búsquedas
**Síntoma:** "Tiempo de espera agotado"
**Solución:**
1. La primera consulta puede tardar más (cache vacío)
2. Consultas subsecuentes serán más rápidas (cache activo)
3. Verificar estabilidad de red con Redash

### ✅ Verificación del Sistema

#### Health Check Completo
```bash
curl https://your-app-name.onrender.com/health
```

#### Test de API
```bash
curl "https://your-app-name.onrender.com/api/clients/search?type=NIT&number=901234567"
```

#### Configuración de Webhook
```bash
curl -X POST https://your-app-name.onrender.com/setup-webhook
```

---

## 📋 Próximas Mejoras

### 🎯 Funcionalidades Planeadas

#### v1.1 - Búsqueda Avanzada
- [ ] Búsqueda por nombre/razón social
- [ ] Búsqueda por ciudad/departamento
- [ ] Filtros combinados (ej: NIT + Ciudad)
- [ ] Búsqueda parcial (wildcards)

#### v1.2 - Información Enriquecida
- [ ] Historial de búsquedas por usuario
- [ ] Exportación de resultados
- [ ] Información de contacto expandida
- [ ] Links a sistemas externos

#### v1.3 - Analytics
- [ ] Dashboard de uso del bot
- [ ] Métricas de comerciales activos
- [ ] Reportes de búsquedas más frecuentes
- [ ] Optimización basada en patrones de uso

### 🔧 Mejoras Técnicas
- [ ] Base de datos local para cache persistente
- [ ] API GraphQL para consultas flexibles
- [ ] Autenticación por comercial
- [ ] Rate limiting por usuario
- [ ] Webhooks para actualizaciones de datos

---

## 📞 Soporte y Contacto

### 🔧 Mantenimiento
- **Desarrollador:** Equipo de Desarrollo FarmuHub
- **Monitoreo:** Logs automáticos en Render
- **Actualizaciones:** Deploy automático desde repositorio

### 📚 Recursos
- **Documentación Telegram Bot API:** [telegram.org](https://core.telegram.org/bots/api)
- **Flask Documentation:** [flask.palletsprojects.com](https://flask.palletsprojects.com/)
- **Redash API:** Documentación interna

### 🆘 Escalación
Para problemas críticos o mejoras del sistema, contactar al equipo de desarrollo de FarmuHub.

---

**📅 Última actualización:** Agosto 2025 - v1.0  
**🎯 Próximo release:** v1.1 con búsqueda avanzada
