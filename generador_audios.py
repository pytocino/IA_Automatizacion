import os
import csv
import argparse
from gtts import gTTS


OUTPUT_DIR = "resources/audio"
TEXT_DIR = "resources/texto"


def generate_audio_from_csv(nicho: str, output_folder: str, lang: str = "en"):
    """Genera un archivo de audio a partir de un archivo CSV para un nicho específico."""
    csv_filename = os.path.join(TEXT_DIR, f"idea_{nicho}.csv")

    try:
        with open(csv_filename, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            row = next(reader)
            try:
                tts = gTTS(
                    text=row["Idea"],
                    lang=lang,
                    tld="us",
                )
                output_path = os.path.join(output_folder, f"audio_{row['Nicho']}.mp3")
                tts.save(output_path)
            except Exception as e:
                print(f"Error generando audio para idea de {row['Nicho']}: {str(e)}")
    except FileNotFoundError:
        print(f"No se encontró el archivo CSV: {csv_filename}")
    except StopIteration:
        print(f"El archivo CSV está vacío: {csv_filename}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Generador de audios desde CSV")
    parser.add_argument("--nicho", required=True, help="Nicho o tema de las historias")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_audio_from_csv(args.nicho, OUTPUT_DIR, lang="en")


if __name__ == "__main__":
    main()
