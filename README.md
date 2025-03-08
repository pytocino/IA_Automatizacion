# 🎬 Generador Automático de Videos con IA 🚀

[![Project Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/yourusername/IA_Automatizacion) <!-- Replace with your project status badge if applicable -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) <!-- Replace with your license badge if applicable -->
[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/) <!-- Example Python version badge -->

**Crea videos automáticamente combinando el poder de la Inteligencia Artificial: texto generado por IA, voz sintética e imágenes impresionantes. ¡Ideal para contenido atractivo y automatizado!**

## ✨ Características Asombrosas

- **🧠 Generación de Texto Inteligente:** Utiliza **Llama 3.2** (a través de Ollama) para crear narrativas cautivadoras y originales.
- **🗣️ Voz Sintética Realista:** Convierte el texto en audio natural con **gTTS**, dándole vida a tus historias.
- **🖼️ Imágenes Impactantes:** Genera visuales únicas y relevantes con **Stable Diffusion 3.5**, optimizadas para la narrativa.
- **🎬 Creación de Videos Automatizada:** Ensambla imágenes, audio y subtítulos en un video MP4 profesional usando **FFmpeg**.
- **📝 Subtítulos Sincronizados:** Incluye subtítulos SRT sincronizados automáticamente para mejorar la accesibilidad y el alcance.
- **📊 Barra de Progreso Visual:** Monitorea el avance de la generación del video en tiempo real.
- **🪵 Sistema de Logging Detallado:** Registra cada paso del proceso en `automation.log` para un seguimiento y depuración fácil.

## ⚙️ Requisitos Previos Esenciales

Asegúrate de tener instalado y configurado lo siguiente en tu sistema:

- **Python 🐍:** **Python 3.12** es requerido. Se recomienda usar la versión específica para asegurar compatibilidad. [Descargar Python](https://www.python.org/downloads/)
- **GPU NVIDIA con CUDA 🚀:**
  - Tarjeta gráfica **NVIDIA GeForce RTX 3060 o superior** recomendada para un rendimiento óptimo.
  - **NVIDIA CUDA Toolkit 2.16:** [Descargar CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
  - **NVIDIA cuDNN 9.7.1:** [Descargar cuDNN](https://developer.nvidia.com/cudnn) (requiere cuenta de desarrollador NVIDIA) - Asegúrate de que la versión de cuDNN sea compatible con tu versión de CUDA.
- **FFmpeg 🎬:** **FFmpeg 7.1-essentials_build** o superior. Necesario para la manipulación de video y audio. [Descargar FFmpeg](https://ffmpeg.org/download.html) - Asegúrate de añadir FFmpeg a tu PATH del sistema.
- **Ollama 🦙:** **Ollama instalado y configurado** para ejecutar modelos de lenguaje localmente. [Descargar Ollama](https://ollama.com/download)
- **Modelo Llama 3.2 en Ollama:** Asegúrate de haber descargado el modelo **Llama 3.2** en Ollama. Ejecuta en tu terminal: `ollama pull llama2`

## 🛠️ Instalación Paso a Paso

1.  **Clona el Repositorio:**

    ```bash
    git clone <url-del-repositorio>
    cd IA_Automatizacion
    ```

    _(Reemplaza `<url-del-repositorio>` con la URL real de tu repositorio)_

2.  **Crea y Activa un Entorno Virtual (Recomendado):**

    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Windows
    source venv/bin/activate # Linux/macOS
    ```

    _Usar un entorno virtual aísla las dependencias del proyecto del resto de tu sistema._

3.  **Instala las Dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

    _Este comando instalará todas las bibliotecas Python necesarias listadas en `requirements.txt`._

4.  **Descarga el Modelo Llama 3.2 en Ollama:**

    ```bash
    ollama pull llama2
    ```

    _Este comando descarga el modelo Llama 3.2 a través de Ollama, si aún no lo tienes._

## 💻 Cómo Utilizar el Generador de Videos

1.  **Configura `config.json`:**

    Abre el archivo `config.json` y personaliza los nichos, eras, ubicaciones y tonos para la generación de contenido.

    ```json
    {
      "nichos": [
        {
          "name": "Ancient Technology",
          "eras": ["Bronze Age", "Iron Age"],
          "locations": ["Greece", "Egypt"],
          "tones": ["fascinating", "curious"]
        },
        {
          "name": "Lost Civilizations",
          "eras": ["Neolithic", "Pre-Columbian"],
          "locations": ["South America", "Southeast Asia"],
          "tones": ["mysterious", "awe-inspiring"]
        }
      ],
      "num_ideas": 1 // Number of video ideas to generate (currently not used in `main.py` but present in README example)
    }
    ```

    _Edita este archivo para definir los temas y estilos de video que deseas generar._

2.  **Ejecuta el Programa:**

    Puedes ejecutar el script `main.py` de dos maneras:

    - **Opción A: Desde la Terminal (Recomendado para ver logs en tiempo real):**

      ```bash
      python main.py --config config.json
      ```

      _Este comando ejecuta el script `main.py` usando el archivo de configuración `config.json`._

    - **Opción B: Usando el Acceso Directo (Para ejecución rápida):**

      - Haz doble clic en el archivo `GenerarContenido.bat` que se encuentra en el escritorio (si lo has creado).
      - _Asegúrate de que el archivo `.bat` esté correctamente configurado para ejecutar `main.py` en tu entorno virtual._

## 📊 Monitoreo y Seguimiento

- **Barra de Progreso Visual:** Observa la barra de progreso en la consola para ver el estado actual de la generación del video.
- **Logs Detallados:** Revisa el archivo `automation.log` para mensajes detallados de cada etapa del proceso, incluyendo posibles errores.
- **Salida en Tiempo Real:** La consola mostrará información relevante durante la ejecución del script.

## 📁 Estructura del Proyecto

```
IA_Automatizacion/
├── main.py # 🚀 Script principal que coordina la automatización
├── generador_textos.py # 📝 Genera el texto/idea del video usando Llama 3.2
├── generador_audios.py # 🔊 Sintetiza la voz a partir del texto con gTTS
├── generador_imagenes.py # 🖼️ Genera imágenes basadas en prompts con Stable Diffusion 3.5
├── generador_prompts.py # 💡 Crea prompts de imágenes a partir del texto generado
├── generador_videos_subtitulados.py # 🎬 Ensambla video, audio y subtítulos con FFmpeg
├── config.json # ⚙️ Archivo de configuración para nichos y parámetros
├── requirements.txt # 📦 Lista de dependencias de Python
├── .env # 🔑 (Opcional) Variables de entorno (ej: Token de Telegram)
├── automation.log # 🪵 Archivo de logs para seguimiento y depuración
└── README.md # 📖 Este archivo de documentación
```

## 🛠️ Componentes Clave en Detalle

1.  **Generador de Textos (`generador_textos.py`)**

    - Utiliza el modelo **Llama 3.2** a través de la API local de **Ollama**.
    - Genera historias cortas y concisas optimizadas para videos cortos.
    - Personalizable en tono, época y ubicación a través de `config.json`.

2.  **Generador de Imágenes (`generador_imagenes.py`)**

    - Emplea **Stable Diffusion 3.5** para crear imágenes visualmente atractivas.
    - Optimizado para eficiencia de memoria en GPUs con **cuantización y slicing de atención**.
    - Guarda imágenes en formato **WebP** de alta calidad y bajo peso.

3.  **Sistema de Automatización (`automation.py` y `main.py`)**
    - Ejecución secuencial y coordinada de todos los componentes del pipeline.
    - Manejo robusto de errores con logging detallado.
    - Diseñado para ser extensible y adaptable a diferentes necesidades.

## 📝 Notas Importantes

- **Formato WebP:** Las imágenes se guardan en formato WebP para optimizar el espacio de almacenamiento sin sacrificar la calidad visual.
- **Videos MP4:** Los videos resultantes se generan en formato MP4 con códec H.264, compatible con la mayoría de plataformas.
- **Creación Automática de Directorios:** El sistema crea automáticamente todos los directorios necesarios (`resources/texto`, `resources/audio`, etc.) si no existen.
- **Logging Centralizado:** Todos los logs se registran en el archivo `automation.log` para facilitar el seguimiento y la depuración.

## 🔍 Solución de Problemas Comunes

- **Revisa `automation.log`:** En caso de errores, el archivo `automation.log` es el primer lugar para buscar mensajes detallados y pistas sobre la causa del problema.
- **Barra de Progreso:** Observa la barra de progreso en la consola para identificar en qué etapa del proceso se detuvo o falló la generación.
- **Errores con Timestamp:** Los errores en el log incluyen marcas de tiempo para facilitar la correlación con eventos específicos durante la ejecución.
- **Problemas con Ollama/Modelos:** Asegúrate de que Ollama esté correctamente instalado y ejecutándose, y que el modelo Llama 3.2 se haya descargado correctamente (`ollama pull llama2`).
- **Dependencias Faltantes:** Si encuentras errores relacionados con "ModuleNotFoundError", verifica que hayas instalado correctamente todas las dependencias con `pip install -r requirements.txt` en tu entorno virtual.
- **FFmpeg no encontrado:** Asegúrate de que FFmpeg esté instalado y correctamente añadido a las variables de entorno de tu sistema (PATH).

## 📄 Licencia

Este proyecto está distribuido bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

**¡Disfruta automatizando la creación de videos con IA!** 🚀

_(Recuerda personalizar las URLs, credenciales, nombres de usuario, y otros detalles específicos de tu implementación en este README)_
