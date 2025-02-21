````markdown
# filepath: /C:/Users/pedro/Documents/IA_Automatizacion/README.md

# Generador Automático de Videos 🎥

Este proyecto automatiza la creación de videos combinando texto generado por IA, síntesis de voz y generación de imágenes. 16GB RAM (necesita más) || NVIDIA GeForce RTX 3060 Laptop GPU (suficiente(creo)) || 512GB SSD (más no estaría mal)

## 🚀 Características

- Generación de texto usando Mistral AI
- Conversión de texto a voz con gTTS
- Generación de imágenes con Stable Diffusion
- Creación automática de videos con FFmpeg
- Subtítulos sincronizados

## 📋 Requisitos Previos

- Python 3.12
- GPU compatible con CUDA (recomendado) o muchísima RAM
- NVIDIA CUDA 2.16
- NVIDIA cuDNN 9.7.1
- FFmpeg 7.1-essentials_build-www.gyan.dev
- Cuenta en Hugging Face (para acceso a modelos)

## 🔧 Instalación

1. Clonar el repositorio:

```bash
git clone <url-del-repositorio>
cd IA_Automatizacion
```
````

2. Crear y activar entorno virtual:

```bash
python -3.12 -m venv venv
.\venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
   - Crear archivo `.env` con tus credenciales:

```env
HUGGINGFACE_TOKEN=tu_token_aqui
```

## 💻 Uso

1. Configurar parámetros en `config.json`:

```json
{
  "nichos": ["adventure", "love", "mystery", "sci-fi", "horror", "fantasy"], //modificar a placer
  "num_ideas": 1
}
```

2. Ejecutar la automatización:

```bash
python main.py
```

## 📁 Estructura del Proyecto

```
IA_Automatizacion/
├── main.py                 # Script principal
├── generador_textos.py     # Generación de texto
├── generador_audios.py     # Síntesis de voz
├── generador_videos.py     # Creación de videos
├── add_subtitles.py        # Añadir subtítulos
├── config.json             # Configuración
├── requirements.txt        # Dependencias
├── .env                    # Variables de entorno
├── .gitignore             # Exclusiones de Git
└── README.md              # Este archivo
```

## 🛠️ Componentes Principales

1. **Generador de Textos**

   - Utiliza Mistral AI para generar historias cortas
   - Formato optimizado para videos

2. **Generador de Audio**

   - Convierte texto a voz usando gTTS
   - Soporte multilenguaje

3. **Generador de Videos**
   - Genera imágenes con Stable Diffusion
   - Combina imágenes y audio con FFmpeg
   - Añade subtítulos sincronizados

## 📝 Notas

- Las imágenes generadas se guardan en formato WebP
- Los videos se generan en formato MP4 con codec H.264
- Se recomienda usar GPU para la generación de imágenes

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama para feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit de cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE.md para detalles

```

¡Recuerda personalizar las URLs, credenciales y otros detalles específicos de tu implementación!
```
