# Bot de Telegram para facturas HELISA - Iglesia MANMIN

## Requisitos previos

1. **Python 3.10+** instalado
2. **Telegram Bot Token** (crear con @BotFather en Telegram)
3. **Google Cloud Vision API Key** (obtener en console.cloud.google.com)

## Instalacion

### 1. Crear el Bot de Telegram

1. Abre Telegram y busca **@BotFather**
2. Envia `/newbot`
3. ponle nombre: `Facturas MANMIN Bot`
4. ponle username: `manmin_facturas_bot`
5. BotFather te dara un **token** (algo como `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)
6. Copia ese token

### 2. Configurar Google Cloud Vision

1. Ve a https://console.cloud.google.com
2. Crea un proyecto nuevo (o usa uno existente)
3. Busca **Cloud Vision API** y habilitala
4. Ve a **Credenciales** > **Crear credencial** > **Clave de API**
5. Descarga el archivo JSON de la clave
6. Renombra el archivo a `service_account.json` y guardalo en `C:\Dashboard facturas 2026\config\`

### 3. Instalar el sistema

Abre PowerShell y ejecuta:

```powershell
cd "C:\Dashboard facturas 2026"
pip install -r requirements.txt
```

### 4. Configurar el archivo .env

Abre el archivo `.env` y pon tu token de Telegram:

```
TELEGRAM_BOT_TOKEN=aqui_tu_token_de_telegram
GOOGLE_VISION_API_KEY=aqui_tu_api_key
ADMIN_IDS=tu_id_de_telegram
```

Para saber tu ID de Telegram:
1. Abre Telegram y busca **@userinfobot**
2. Envia `/start`
3. Te dara tu ID (un numero como `123456789`)

### 5. Iniciar el Bot

```powershell
cd "C:\Dashboard facturas 2026\bot"
python main.py
```

### 6. Iniciar el Dashboard

En otra ventana de PowerShell:

```powershell
cd "C:\Dashboard facturas 2026"
streamlit run dashboard/app.py
```

El dashboard se abrira en http://localhost:8501

## Uso

### Enviar facturas por Telegram

1. Abre Telegram y busca tu bot (`@manmin_facturas_bot`)
2. Envia `/start`
3. Envia una **foto** o **PDF** de la factura
4. El bot extraera los datos con OCR
5. Confirma si los datos son correctos
6. Selecciona la cuenta contable
7. La factura se guardara en la base de datos

### Administrar usuarios (solo admin)

1. Envia `/admin` al bot
2. Para agregar usuario: `/agregar_usuario 123456789 Nombre Apellido`
3. Para ver usuarios: `/listar_usuarios`
4. Para eliminar: `/eliminar_usuario 123456789`

### Generar archivo para HELISA

1. Abre el dashboard en http://localhost:8501
2. Ve a la pestana **Generar Archivo HELISA**
3. Haz clic en **Generar archivo Excel para HELISA**
4. Descarga el archivo
5. En HELISA ve a **Herramientas > Importar datos**
6. Selecciona el archivo generado

## Cuentas contables configuradas

| Cuenta | Nombre |
|--------|--------|
| 51201001 | Arrendamiento edificio |
| 51352501 | Acueducto y alcantarillado |
| 51353001 | Energia electrica |
| 51353501 | Internet y telefono |
| 51355501 | Gas |
| 51952501 | Panaderia, onces y refrigerios |
| 51952502 | Bebidas y gaseosas |
| 51953001 | Utiles, papeleria y fotocopias |
| 51953501 | Gasolina y combustible |
| 51956001 | Restaurantes y casinos |
| 51956501 | Parqueaderos |
| 51959501 | Ferreteria |
| 51959502 | Premiaciones |
| 51959503 | Gastos para confecciones |
| 51959504 | Gastos para decoracion |
| 51959505 | Equipo de audio |
| 51454001 | Reparacion y mantenimiento vehiculos |
| 51401501 | Softwares |
| 51109501 | Honorarios otros |

## Estructura de archivos

```
C:\Dashboard facturas 2026\
├── bot/                    # Bot de Telegram
│   ├── main.py             # Punto de entrada
│   ├── handlers/           # Manejadores de comandos
│   ├── ocr/                # Modulo OCR (Google Vision)
│   ├── helisa/             # Generador de archivos HELISA
│   └── database/           # Base de datos SQLite
├── dashboard/              # Dashboard web (Streamlit)
├── data/                   # Base de datos
├── config/                 # Configuracion y API keys
├── exports/                # Archivos generados
├── requirements.txt        # Dependencias
├── .env                    # Variables de entorno
└── README.md               # Este archivo
```

## Solucion de problemas

**El bot no inicia:**
- Verifica que el token de Telegram este correcto en `.env`
- Verifica que tengas internet

**OCR no funciona:**
- Verifica que la API key de Google Vision este en `.env`
- Verifica que el archivo `service_account.json` este en `config/`

**Dashboard no carga:**
- Verifica que Streamlit este instalado: `pip install streamlit`
- Verifica que la base de datos exista en `data/`
