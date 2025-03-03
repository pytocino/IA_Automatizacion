import os
import csv
import argparse
import gtts

OUTPUT_DIR = "resources/audio"
TEXT_DIR = "resources/texto"


def generate_audio_from_csv(nicho: str, output_folder: str, lang: str = "en"):
    """Genera un archivo de audio a partir de un archivo CSV para un nicho específico."""
    csv_filename = os.path.join(TEXT_DIR, f"idea_{nicho}.csv")

    try:
        # Verifica que el archivo CSV existe
        if not os.path.exists(csv_filename):
            raise FileNotFoundError(f"No se encontró el archivo CSV: {csv_filename}")

        # Procesa el archivo CSV
        with open(csv_filename, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            row = next(reader)

            try:
                # Definimos la ruta de salida
                mp3_output_path = os.path.join(
                    output_folder, f"audio_{row['Nicho']}.mp3"
                )

                # Generamos el audio MP3 directamente usando Google TTS
                tts = gtts.gTTS(text=row["Idea"], lang=lang, slow=False)
                tts.save(mp3_output_path)

                print(f"Audio generado correctamente: {mp3_output_path}")

            except Exception as e:
                print(f"Error generando audio para idea de {row['Nicho']}: {str(e)}")

    except FileNotFoundError as e:
        print(str(e))
    except StopIteration:
        print(f"El archivo CSV está vacío: {csv_filename}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Generador de audios desde CSV")
    parser.add_argument("--nicho", required=True, help="Nicho o tema de las historias")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_audio_from_csv(args.nicho, OUTPUT_DIR)


if __name__ == "__main__":
    main()
