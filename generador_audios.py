import os
import csv
import argparse
import torch
from TTS.api import TTS
from pydub import AudioSegment

OUTPUT_DIR = "resources/audio"
TEXT_DIR = "resources/texto"


def generate_audio_from_csv(nicho: str, output_folder: str, lang: str = "en"):
    """Genera un archivo de audio a partir de un archivo CSV para un nicho específico."""
    csv_filename = os.path.join(TEXT_DIR, f"idea_{nicho}.csv")

    try:
        # Verifica que el archivo CSV existe
        if not os.path.exists(csv_filename):
            raise FileNotFoundError(f"No se encontró el archivo CSV: {csv_filename}")

        # Inicializa TTS antes de abrir el archivo
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"Usando dispositivo: {device}")

            # Inicializa el modelo TTS
            tts = TTS(
                model_name="tts_models/en/ljspeech/tacotron2-DDC",  # Modelo específico para inglés
                progress_bar=True,
            ).to(device)

            print("Modelo TTS cargado correctamente")

        except Exception as e:
            print(f"Error al inicializar TTS: {str(e)}")
            return

        # Procesa el archivo CSV
        with open(csv_filename, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            row = next(reader)

            try:
                # Genera el audio en WAV
                wav_output_path = os.path.join(
                    output_folder, f"temp_audio_{row['Nicho']}.wav"
                )
                mp3_output_path = os.path.join(
                    output_folder, f"audio_{row['Nicho']}.mp3"
                )
                print(f"Generando audio para: {row['Idea'][:50]}...")

                # Generamos el audio WAV
                tts.tts_to_file(text=row["Idea"], file_path=wav_output_path)

                # Convertimos WAV a MP3
                audio = AudioSegment.from_wav(wav_output_path)
                audio.export(mp3_output_path, format="mp3", bitrate="192k")

                # Eliminamos el archivo WAV temporal
                os.remove(wav_output_path)

                print(f"Audio MP3 generado exitosamente en: {mp3_output_path}")

            except Exception as e:
                print(f"Error generando audio para idea de {row['Nicho']}: {str(e)}")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    except FileNotFoundError as e:
        print(str(e))
    except StopIteration:
        print(f"El archivo CSV está vacío: {csv_filename}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
    finally:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def main():
    parser = argparse.ArgumentParser(description="Generador de audios desde CSV")
    parser.add_argument("--nicho", required=True, help="Nicho o tema de las historias")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_audio_from_csv(args.nicho, OUTPUT_DIR, lang="en")


if __name__ == "__main__":
    main()
