# Generador Automático de Videos 🎥

Este proyecto automatiza la creación de videos combinando texto generado por IA, síntesis de voz y generación de imágenes.

**Requisitos de Hardware Recomendados:**

- RAM: 16GB mínimo (32GB recomendado)
- GPU: NVIDIA GeForce RTX 3060 o superior
- Almacenamiento: 512GB SSD (1TB recomendado)

## 🚀 Características

- Generación de texto usando Mistral AI
- Conversión de texto a voz con gTTS
- Generación de imágenes con Stable Diffusion 3
- Creación automática de videos con FFmpeg
- Subtítulos sincronizados
- Barra de progreso visual
- Sistema de logging integrado

## 📋 Requisitos Previos

- Python 3.12
- GPU compatible con CUDA
- NVIDIA CUDA 2.16
- NVIDIA cuDNN 9.7.1
- FFmpeg 7.1-essentials_build
- Cuenta en Hugging Face

## 🔧 Instalación

1. Clonar el repositorio y acceder al directorio:

```bash
git clone <url-del-repositorio>
cd IA_Automatizacion
```

2. Crear y activar entorno virtual:

```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
   Crear archivo `.env`:

```env
HUGGINGFACE_TOKEN=tu_token_aqui
```

## 💻 Uso

1. Configurar `config.json`:

```json
{
  "nichos": ["adventure", "mystery", "sci-fi", "fantasy"],
  "num_ideas": 1
}
```

2. Ejecutar el programa:
   - **Opción A**: Desde terminal
   ```bash
   python main.py --config config.json
   ```
   - **Opción B**: Usando el acceso directo
     - Doble clic en `GenerarContenido.bat` desde el escritorio

## 📊 Monitoreo y Logs

- Progreso visual con barras de progreso
- Logs detallados en `automation.log`
- Salida en tiempo real en consola

## 📁 Estructura del Proyecto

```
IA_Automatizacion/
├── main.py                        # Coordinador principal
├── generador_textos.py           # Generación de historias
├── generador_audios.py           # Síntesis de voz
├── generador_imagenes.py         # Generación de imágenes
├── generador_videos_subtitulados.py  # Creación de videos
├── config.json                   # Configuración
├── requirements.txt              # Dependencias
├── .env                         # Variables de entorno
└── automation.log               # Archivo de logs
```

## 🛠️ Componentes Principales

1. **Generador de Textos**

   - Usa Mistral AI 7B Instruct
   - Optimizado para historias cortas

2. **Generador de Imágenes**

   - Stable Diffusion 3.5
   - Optimización de memoria
   - Formato WebP

3. **Sistema de Automatización**
   - Ejecución secuencial optimizada
   - Manejo de errores robusto
   - Logging comprehensivo

## 📝 Notas Importantes

- Las imágenes se generan en formato WebP para optimizar espacio
- Videos en MP4 con codec H.264
- El sistema crea automáticamente los directorios necesarios
- Los logs se mantienen en `automation.log`

## 🔍 Solución de Problemas

- Revisar `automation.log` para mensajes detallados
- La barra de progreso muestra el estado actual
- Los errores se registran con timestamp para fácil debugging

## 📄 Licencia

Este proyecto está bajo la Licencia MIT

```
¡Recuerda personalizar las URLs, credenciales y otros detalles específicos de tu implementación!
```
