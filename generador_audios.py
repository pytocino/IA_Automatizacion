import os
import csv
from gtts import gTTS


def generate_audio_from_csv(csv_filename: str, output_folder: str, lang: str = "en"):
    with open(csv_filename, mode="r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tts = gTTS(text=row["Idea"], lang=lang)
            output_path = os.path.join(
                output_folder, f"idea_{row['ID']}_{row['Nicho']}.mp3"
            )
            tts.save(output_path)


if __name__ == "__main__":
    generate_audio_from_csv("ideas_generadas.csv", "audios", lang="en")
