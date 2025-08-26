# 🚀 mcpComercialExt v1.3 - Bot Comercial Externo + Gestión de Comerciales

## 🎯 Descripción General

**mcpComercialExt v1.3** es un sistema especializado que combina:
- **Búsqueda de clientes** con verificación de disponibilidad comercial
- **Registro de comerciales externos** con validación automática 
- **Bot de Telegram interactivo** para ambas funcionalidades

### 🏢 Contexto de Negocio
- **Búsqueda:** Facilitar a los comerciales la búsqueda y verificación de disponibilidad de clientes
- **Registro:** Permitir el registro seguro de nuevos comerciales externos
- **Validación:** Verificación automática de duplicados y formatos
- **Fuentes:** APIs de Redash (clientes) + NocoDB (comerciales)

---

## 🆕 Nuevas Funcionalidades v1.3

### **👤 Gestión de Comerciales Externos**
- ✅ **Registro paso a paso** via Telegram
- ✅ **Validación de duplicados** automática
- ✅ **Formatos validados** (email, teléfono, cédula)
- ✅ **Integración con NocoDB** para almacenamiento

### **🔍 Proceso de Registro:**
1. **Comando:** `crear` 
2. **Verificación:** Cédula única en el sistema
3. **Datos:** Email, nombre, teléfono (con validación)
4. **Confirmación:** Resumen antes de crear
5. **Resultado:** Comercial registrado y activo

---

## 📱 Comandos del Bot Actualizados

### **Comandos Principales**
```bash
/start      # Bienvenida con todas las funcionalidades
/help       # Lista completa de comandos
cliente     # Buscar cliente con verificación comercial  
crear       # Registrar nuevo comercial externo
resumen     # Estadísticas del sistema
info        # Información sobre datos mostrados
```

### **🔍 Proceso de Búsqueda de Cliente (Sin cambios)**
```
1. cliente → 2. NIT/CC → 3. número → 4. resultado
```

### **👤 Proceso de Registro de Comercial (NUEVO)**
```
1. crear → 2. cédula → 3. email → 4. nombre → 5. teléfono → 6. confirmar
```

---

## 🗂️ Estructura del Proyecto Actualizada

```
mcpComercialExt/
├── app.py                 # Aplicación principal Flask + endpoints NocoDB
├── config.py              # Configuración + variables NocoDB
├── redash_service.py      # Servicio Redash (clientes)
├── nocodb_service.py      # Servicio NocoDB (comerciales) [NUEVO]
├── bot_handlers.py        # Manejadores con flujo de registro
├── utils.py               # Utilidades y helpers
├── requirements.txt       # Dependencias Python
├── .env.example           # Variables de entorno [ACTUALIZADO]
├── .gitignore            # Archivos a ignorar
└── README.md             # Esta documentación
```

---

## 🔧 Configuración y Variables de Entorno

### 🌍 Variables de Entorno Nuevas

#### **NocoDB API (Comerciales)**
```bash
NOCODB_BASE_URL=https://nocodb.farmuhub.co/api/v2
NOCODB_TOKEN=-kgNP5Q5G54nlDXPei7IO9PMMyE4pIgxYCi6o17Y  
NOCODB_TABLE_ID=mbtfip114qi1u4o
```

#### **Variables Existentes (Sin cambios)**
```bash
# Telegram Bot
TELEGRAM_TOKEN=7337079580:AAFxBDY4B1Muc6sUpV0uNxYa6DgVQh3LE_8
WEBHOOK_URL=https://mcpcomercialext.onrender.com

# Redash APIs
REDASH_BASE_URL=https://redash-mcp.farmuhub.co
REDASH_API_KEY=MJAgj9yCdpVsWFdinPPfqBkQuvTBKmhCOD9JEmNZ
REDASH_QUERY_ID=100
REDASH_UNAVAILABLE_API_KEY=nQmXGYBuKdck7VBTrqvOZ45ypmp5idTlZpVEumbz
REDASH_UNAVAILABLE_QUERY_ID=133

# Pre-registro
PREREGISTER_URL=https://saludia.me/pre-register
```

---

## 🏗️ Integración con NocoDB

### **🔗 API de Comerciales**

#### **Verificar Existencia:**
```bash
curl -X 'GET' \
'https://nocodb.farmuhub.co/api/v2/tables/mbtfip114qi1u4o/records?where=(cedula,eq,123456)&limit=1' \
-H 'xc-token: -kgNP5Q5G54nlDXPei7IO9PMMyE4pIgxYCi6o17Y'
```

#### **Crear Comercial:**
```bash
curl -X 'POST' \
'https://nocodb.farmuhub.co/api/v2/tables/mbtfip114qi1u4o/records' \
-H 'xc-token: -kgNP5Q5G54nlDXPei7IO9PMMyE4pIgxYCi6o17Y' \
-H 'Content-Type: application/json' \
-d '{
  "cedula": "123456",
  "email": "comercial@empresa.com", 
  "name": "Juan Pérez",
  "phone": "+57 300 123 4567"
}'
```

### **📊 Sistema de Validaciones**

#### **Validación de Campos:**
```python
VALIDACIONES = {
    "cedula": "6-12 dígitos únicos",
    "email": "Formato válido con @ y dominio (.com, .co, etc)",
    "name": "2-100 caracteres, solo letras y espacios",
    "phone": "7-20 dígitos, permite +, -, (), espacios"
}
```

---

## 🚦 Flujos de Usuario Actualizados

### **🟢 Cliente Disponible (Sin cambios)**
```
✅ ¡CLIENTE DISPONIBLE! 🎯
🔍 Documento: 901234567
🏢 Nombre: EMPRESA EJEMPLO S.A.S
[...información completa...]
🟢 Estado: Cliente DISPONIBLE para crear órdenes
```

### **👤 Comercial Creado Exitosamente (NUEVO)**
```
✅ ¡COMERCIAL CREADO EXITOSAMENTE! 🎉

Información registrada:
🆔 Cédula: 12345678
👤 Nombre: Juan Pérez  
📧 Email: juan.perez@empresa.com
📞 Teléfono: +57 300 123 4567

✅ Estado: Comercial registrado y activo en el sistema
```

### **🚫 Comercial Ya Registrado (NUEVO)**
```
🚫 COMERCIAL YA REGISTRADO

👤 Nombre: María García
🆔 Cédula: 12345678
📧 Email: maria@empresa.com
📞 Teléfono: 300 987 6543

⚠️ Estado: Este comercial ya existe en el sistema
```

---

## 📌 API REST Endpoints Nuevos

### **👤 Comerciales**

#### **Verificar Comercial**
```http
GET /api/comerciales/check?cedula=12345678
```
**Respuesta:**
```json
{
  "success": true,
  "exists": false,
  "message": "La cédula 12345678 está disponible para registro"
}
```

#### **Crear Comercial**
```http
POST /api/comerciales/create
Content-Type: application/json

{
  "cedula": "12345678",
  "email": "comercial@empresa.com",
  "name": "Juan Pérez", 
  "phone": "3001234567"
}
```

#### **Información de Comercial**
```http
GET /api/comerciales/info?cedula=12345678
```

### **🔍 Clientes (Sin cambios)**
- `GET /api/clients` - Lista de clientes
- `GET /api/clients/search` - Búsqueda por documento
- `GET /api/clients/summary` - Resumen y estadísticas

---

## ⚡ Características Técnicas v1.3

### **🆕 Nuevas Optimizaciones**

#### **Validación Robusta**
- **Email:** Regex + dominios válidos
- **Teléfono:** Formatos flexibles con validación de longitud
- **Nombres:** Caracteres especiales permitidos (acentos, ñ, apostrofes)
- **Cédula:** Limpieza automática y rango configurable

#### **Sistema de Estados Mejorado**
- **Procesos separados:** `client_search` vs `create_comercial`  
- **Validación por pasos:** Cada entrada validada individualmente
- **Confirmación requerida:** Resumen antes de crear
- **Manejo de errores:** Mensajes específicos por tipo de error

### **📊 Cache y Performance**
- **Cache dual:** Redash (1h) + NocoDB (sin cache, datos en tiempo real)
- **Timeouts diferenciados:** 30s Redash, 15s NocoDB, 8s Telegram
- **Fallbacks inteligentes:** En caso de error, opciones de recuperación

---

## 🚀 Deployment en Render v1.3

### **1. Variables de Entorno en Dashboard:**
```bash
# Existing variables + New NocoDB variables
NOCODB_BASE_URL=https://nocodb.farmuhub.co/api/v2
NOCODB_TOKEN=-kgNP5Q5G54nlDXPei7IO9PMMyE4pIgxYCi6o17Y
NOCODB_TABLE_ID=mbtfip114qi1u4o
```

### **2. Health Check Actualizado:**
```bash
curl https://mcpcomercialext.onrender.com/health
```
**Respuesta incluye:**
```json
{
  "services": {
    "nocodb_api": "ok",
    "redash_api": "ok", 
    "telegram_bot": "configured"
  },
  "data_status": {
    "nocodb_connection": "ok"
  }
}
```

---

## 🛠️ Testing de Funcionalidades

### **🧪 Test Manual del Bot**

#### **Registro de Comercial:**
```
1. Abrir chat con el bot
2. Escribir: crear
3. Seguir el flujo paso a paso:
   - Cédula: 87654321
   - Email: test@empresa.com
   - Nombre: Pedro Prueba
   - Teléfono: 300 999 8888
   - Confirmar: SI
4. Verificar creación exitosa
```

#### **Verificación de Duplicado:**
```
1. Escribir: crear
2. Usar la misma cédula: 87654321  
3. Verificar mensaje de "ya registrado"
```

### **🧪 Test API Endpoints:**

#### **Verificar Comercial:**
```bash
curl "https://mcpcomercialext.onrender.com/api/comerciales/check?cedula=87654321"
```

#### **Crear via API:**
```bash
curl -X POST "https://mcpcomercialext.onrender.com/api/comerciales/create" \
-H "Content-Type: application/json" \
-d '{
  "cedula": "11223344",
  "email": "api@test.com",
  "name": "API Test",
  "phone": "300 111 2233"
}'
```

---

## 🚨 Troubleshooting v1.3

### **❌ Problemas Específicos de NocoDB**

#### **Error "NocoDB connection failed"**
**Síntomas:** Bot responde con error al usar `crear`
**Solución:**
- Verificar NOCODB_TOKEN en variables de entorno
- Confirmar que https://nocodb.farmuhub.co esté accesible
- Revisar logs: `/health` endpoint

#### **Comercial no se crea pero no hay error**
**Síntomas:** Proceso completo pero sin registro
**Solución:**
- Verificar NOCODB_TABLE_ID correcto
- Confirmar permisos del token
- Revisar estructura de tabla en NocoDB

#### **Validación de email muy estricta**
**Síntomas:** Emails válidos rechazados
**Solución:**
- Verificar extensión del dominio (.com, .co, etc)
- Revisar regex en `nocodb_service.py`
- Ajustar `valid_extensions` si necesario

### **⚠️ Problemas de Estados de Usuario**

#### **Bot "se olvida" en medio del registro**
**Síntomas:** Usuario en paso 3/4, bot responde como comando nuevo
**Solución:**
- Estados se limpian por timeout o error
- Usar `crear` para reiniciar proceso
- Verificar que no hay caracteres especiales en inputs

---

## 📋 Próximas Mejoras v1.4

### **🎯 Funcionalidades Planeadas**

#### **v1.4 - Gestión Avanzada de Comerciales**
- [ ] Editar datos de comerciales existentes
- [ ] Listar comerciales registrados con filtros
- [ ] Desactivar/activar comerciales
- [ ] Histórico de cambios en comerciales
- [ ] Búsqueda de comerciales por email/nombre

#### **v1.5 - Reportes y Analytics**
- [ ] Dashboard de comerciales activos
- [ ] Estadísticas de uso del bot por comercial
- [ ] Reportes de clientes más buscados
- [ ] Métricas de conversión (búsquedas → órdenes)

#### **v1.6 - Integración Completa**
- [ ] Crear órdenes directamente desde el bot
- [ ] Asignación automática de clientes a comerciales
- [ ] Notificaciones push para comerciales
- [ ] Sincronización bidireccional con CRM

---

## 🔄 Changelog v1.3

### **✨ Nuevas Características:**
- ✅ **Comando `crear` para registrar comerciales**
- ✅ **Integración completa con NocoDB API**
- ✅ **Validación de duplicados automática**
- ✅ **Validación robusta de email, teléfono, nombre**
- ✅ **Proceso paso a paso con confirmación**
- ✅ **Estados de usuario separados por proceso**
- ✅ **Nuevos endpoints API para comerciales**

### **🔧 Mejoras Técnicas:**
- ✅ **Nuevo módulo `nocodb_service.py`**
- ✅ **Sistema de validaciones modular**
- ✅ **Manejo de errores específico por validación**
- ✅ **Health check incluyendo NocoDB**
- ✅ **Timeouts configurables por servicio**
- ✅ **Logging detallado para debugging**

### **📱 Experiencia del Usuario:**
- ✅ **Flujo de registro intuitivo y guiado**
- ✅ **Mensajes de error descriptivos y útiles**
- ✅ **Confirmación con resumen antes de crear**
- ✅ **Respuestas diferenciadas por estado**
- ✅ **Comandos help actualizados con nueva funcionalidad**

### **🛡️ Seguridad:**
- ✅ **Variables sensibles en entorno**
- ✅ **Validación estricta de todos los campos**
- ✅ **Prevención de inyección en queries**
- ✅ **Limpieza de datos de entrada**

---

## 📊 Métricas y KPIs v1.3

### **📈 Métricas de Uso**
- **Búsquedas de clientes:** Tracking existente
- **Registros de comerciales:** Nuevas métricas
- **Tasa de éxito:** Validaciones pasadas vs fallidas
- **Tiempo de respuesta:** Separado por funcionalidad

### **🎯 KPIs Objetivos**
- **Tiempo promedio de registro:** < 2 minutos
- **Tasa de error en validación:** < 5%
- **Disponibilidad de NocoDB:** > 99%
- **Satisfacción de usuario:** Medida por re-intentos

---

## 🔐 Consideraciones de Seguridad

### **🛡️ Protección de Datos**
- **Tokens API:** Nunca en código, solo en variables de entorno
- **Datos sensibles:** Validación sin almacenamiento temporal
- **Logs:** No incluyen datos personales completos
- **APIs:** Rate limiting implícito por bot de Telegram

### **✅ Cumplimiento**
- **GDPR:** Datos mínimos necesarios, no persistencia local
- **Consentimiento:** Implícito al usar el bot
- **Acceso:** Solo usuarios autorizados del bot
- **Auditoría:** Logs de todas las operaciones

---

## 📞 Soporte y Mantenimiento v1.3

### **🔧 Mantenimiento Rutinario**
- **Health checks:** Monitoring de ambas APIs
- **Cache invalidation:** Automática por TTL
- **Log rotation:** Gestionado por Render
- **Updates:** Deploy desde repositorio git

### **🆘 Escalación de Problemas**

#### **Nivel 1 - Problemas Menores**
- Validación de campo específica
- Error de formato de usuario
- **Acción:** Mensaje de ayuda, reintentar

#### **Nivel 2 - Problemas de API**
- NocoDB timeout o error 500
- Redash slow response
- **Acción:** Fallback, notificación en logs

#### **Nivel 3 - Problemas Críticos**
- APIs completamente down
- Bot no responde
- **Acción:** Escalación inmediata a desarrollo

### **📚 Documentación Técnica**
- **API Docs:** Swagger/OpenAPI pendiente v1.4
- **Code Comments:** Documentación inline completa
- **Architecture:** Diagrama de flujo actualizado
- **Deployment:** Guía paso a paso actualizada

---

## 🌟 Casos de Uso Reales

### **👤 Caso 1: Registro de Comercial Nuevo**
```
Comercial: María quiere registrarse
1. Abre chat con bot
2. Escribe: crear
3. Sigue flujo: 12345678 → maria@empresa.com → María García → 300123456
4. Confirma: SI
5. ✅ Registrada exitosamente
```

### **🚫 Caso 2: Comercial Duplicado**
```
Comercial: Pedro intenta usar cédula existente  
1. Escribe: crear
2. Ingresa: 12345678 (ya registrada)
3. ❌ Sistema informa que ya existe
4. Muestra datos del comercial existente
```

### **🔍 Caso 3: Búsqueda de Cliente (Flujo Original)**
```
Comercial: Juan busca empresa por NIT
1. Escribe: cliente
2. Selecciona: NIT
3. Ingresa: 901234567
4. ✅ Cliente disponible con información completa
```

### **📊 Caso 4: Monitoreo del Sistema**
```
Admin: Verificar estado general
1. GET /health
2. ✅ Todos los servicios operativos
3. Redash: 5,247 clientes
4. NocoDB: conexión OK
5. Cache: activo (23 min)
```

---

## 🔄 Migración desde v1.2

### **⚡ Compatibilidad**
- ✅ **Búsqueda de clientes:** Sin cambios
- ✅ **Comandos existentes:** Totalmente compatibles
- ✅ **API endpoints:** Retrocompatibles
- ✅ **Variables de entorno:** Nuevas opcionales

### **🆕 Cambios Requeridos**
1. **Agregar variables NocoDB** en Render dashboard
2. **No modificar** variables existentes
3. **Probar** comando `crear` después del deploy
4. **Verificar** endpoint `/health` incluya NocoDB

### **📋 Checklist de Migración**
- [ ] Variables de entorno configuradas
- [ ] Deploy exitoso en Render
- [ ] Health check pasando
- [ ] Test de comando `crear`
- [ ] Test de comando `cliente` (sin regresión)
- [ ] Logs sin errores críticos

---

**📅 Última actualización:** Agosto 2025 - v1.3  
**🎯 Próximo release:** v1.4 con gestión avanzada de comerciales
**🚀 Estado:** Producción - Completamente operativo**

---

## 🏁 Conclusión

mcpComercialExt v1.3 representa una evolución significativa del sistema, agregando capacidades completas de gestión de comerciales externos mientras mantiene toda la funcionalidad existente de búsqueda de clientes.

**🎯 Beneficios Clave:**
- **Doble funcionalidad:** Búsqueda + Registro en una sola herramienta
- **Validación robusta:** Prevención de errores y duplicados
- **Experiencia fluida:** Procesos paso a paso intuitivos
- **Escalabilidad:** Arquitectura preparada para futuras mejoras

El sistema está listo para producción y preparado para las próximas funcionalidades avanzadas de la hoja de ruta v1.4-v1.6.
