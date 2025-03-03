import sys
import os
import json
import random
import subprocess
import threading
import time
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QListWidget,
    QProgressBar,
    QFrame,
    QFileDialog,
    QMessageBox,
    QTabWidget,
    QTextEdit,
    QSplitter,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont


class WorkerThread(QThread):
    update_progress = pyqtSignal(str, int)
    update_status = pyqtSignal(str)
    task_complete = pyqtSignal(bool, str)

    def __init__(self, task_name, script_path, args):
        super().__init__()
        self.task_name = task_name
        self.script_path = script_path
        self.args = args

    def run(self):
        try:
            self.update_status.emit(f"Ejecutando {self.task_name}...")

            cmd = ["python", self.script_path]
            if self.args:
                cmd.extend(self.args)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1,
            )

            # Simulation of progress for better UX
            for i in range(10):
                time.sleep(0.3)  # Simulating work
                self.update_progress.emit(self.task_name, (i + 1) * 10)

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.update_status.emit(f"✓ {self.task_name} completado")
                self.task_complete.emit(True, stdout)
            else:
                error_msg = f"Error en {self.task_name}:\n{stderr}"
                self.update_status.emit(f"❌ Error en {self.task_name}")
                self.task_complete.emit(False, error_msg)

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            self.update_status.emit(f"❌ Error en {self.task_name}: {str(e)}")
            self.task_complete.emit(False, f"{str(e)}\n\nDetalles:\n{error_details}")


class HistoryVideoGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Videos Históricos")
        self.setMinimumSize(900, 600)

        # Load configuration
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                self.config = json.load(f)
                self.nichos = self.config.get("nichos", [])
        except Exception as e:
            self.config = {}
            self.nichos = []
            QMessageBox.warning(
                self, "Error", f"No se pudo cargar la configuración: {str(e)}"
            )

        # Initialize variables
        self.current_nicho = None
        self.current_era = None
        self.current_location = None
        self.current_tone = None
        self.worker_threads = []
        self.tasks_completed = 0
        self.total_tasks = 6  # Number of generation steps

        # Setup UI
        self.setup_ui()
        self.populate_nicho_dropdown()

        # Create resources directories
        os.makedirs("resources/texto", exist_ok=True)
        os.makedirs("resources/audio", exist_ok=True)
        os.makedirs("resources/prompts", exist_ok=True)
        os.makedirs("resources/imagenes", exist_ok=True)
        os.makedirs("resources/subtitulos", exist_ok=True)
        os.makedirs("resources/video", exist_ok=True)
        os.makedirs("log", exist_ok=True)

    def setup_ui(self):
        # Main layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Header with title
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.StyledPanel)
        header_layout = QVBoxLayout(header_frame)

        title_label = QLabel("Generador de Videos Históricos")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        header_layout.addWidget(title_label)

        description = QLabel("Crea videos educativos sobre historia con IA")
        description.setAlignment(Qt.AlignCenter)
        description.setFont(QFont("Arial", 12))
        header_layout.addWidget(description)

        main_layout.addWidget(header_frame)

        # Content area - split into control panel and preview/log area
        content_splitter = QSplitter(Qt.Horizontal)

        # Control panel (left side)
        control_panel = QFrame()
        control_panel.setFrameShape(QFrame.StyledPanel)
        control_layout = QVBoxLayout(control_panel)

        # Nicho selection
        nicho_layout = QHBoxLayout()
        nicho_label = QLabel("Nicho:")
        nicho_label.setMinimumWidth(100)
        self.nicho_dropdown = QComboBox()
        self.nicho_dropdown.currentIndexChanged.connect(self.on_nicho_changed)
        nicho_layout.addWidget(nicho_label)
        nicho_layout.addWidget(self.nicho_dropdown)
        control_layout.addLayout(nicho_layout)

        # Era selection
        era_layout = QHBoxLayout()
        era_label = QLabel("Era:")
        era_label.setMinimumWidth(100)
        self.era_dropdown = QComboBox()
        era_layout.addWidget(era_label)
        era_layout.addWidget(self.era_dropdown)
        control_layout.addLayout(era_layout)

        # Location selection
        location_layout = QHBoxLayout()
        location_label = QLabel("Ubicación:")
        location_label.setMinimumWidth(100)
        self.location_dropdown = QComboBox()
        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_dropdown)
        control_layout.addLayout(location_layout)

        # Tone selection
        tone_layout = QHBoxLayout()
        tone_label = QLabel("Tono:")
        tone_label.setMinimumWidth(100)
        self.tone_dropdown = QComboBox()
        tone_layout.addWidget(tone_label)
        tone_layout.addWidget(self.tone_dropdown)
        control_layout.addLayout(tone_layout)

        # Random selection button
        random_button = QPushButton("Selección Aleatoria")
        random_button.clicked.connect(self.randomize_selections)
        control_layout.addWidget(random_button)

        # Add some spacing
        control_layout.addSpacing(20)

        # Generate button
        self.generate_button = QPushButton("GENERAR VIDEO")
        self.generate_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.generate_button.setMinimumHeight(50)
        self.generate_button.clicked.connect(self.start_generation)
        control_layout.addWidget(self.generate_button)

        # Overall progress
        progress_label = QLabel("Progreso Total:")
        control_layout.addWidget(progress_label)

        self.overall_progress = QProgressBar()
        control_layout.addWidget(self.overall_progress)

        # Current task progress
        task_label = QLabel("Tarea Actual:")
        control_layout.addWidget(task_label)

        self.current_task_label = QLabel("Ninguna")
        control_layout.addWidget(self.current_task_label)

        self.task_progress = QProgressBar()
        control_layout.addWidget(self.task_progress)

        # Stretch to push everything to the top
        control_layout.addStretch()

        # Preview/Log area (right side)
        preview_log_tabs = QTabWidget()

        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        preview_log_tabs.addTab(self.log_text, "Log")

        # Preview tab (to be implemented)
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)

        self.preview_label = QLabel("No hay preview disponible")
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)

        self.open_video_button = QPushButton("Abrir Último Video")
        self.open_video_button.clicked.connect(self.open_last_video)
        self.open_video_button.setEnabled(False)
        preview_layout.addWidget(self.open_video_button)

        preview_log_tabs.addTab(preview_widget, "Preview")

        # Add panels to splitter
        content_splitter.addWidget(control_panel)
        content_splitter.addWidget(preview_log_tabs)
        content_splitter.setSizes([300, 600])  # Initial sizes

        main_layout.addWidget(content_splitter)

        # Status bar
        self.statusBar().showMessage("Listo")

    def populate_nicho_dropdown(self):
        if not self.nichos:
            return

        self.nicho_dropdown.clear()
        for nicho in self.nichos:
            self.nicho_dropdown.addItem(nicho["name"])

    def on_nicho_changed(self, index):
        if index < 0 or index >= len(self.nichos):
            return

        nicho = self.nichos[index]
        self.current_nicho = nicho["name"]

        # Update era dropdown
        self.era_dropdown.clear()
        for era in nicho["eras"]:
            self.era_dropdown.addItem(era)

        # Update location dropdown
        self.location_dropdown.clear()
        for location in nicho["locations"]:
            self.location_dropdown.addItem(location)

        # Update tone dropdown
        self.tone_dropdown.clear()
        for tone in nicho["tones"]:
            self.tone_dropdown.addItem(tone)

    def randomize_selections(self):
        if not self.nichos:
            return

        # Randomly select a nicho
        nicho_index = random.randint(0, len(self.nichos) - 1)
        self.nicho_dropdown.setCurrentIndex(nicho_index)

        nicho = self.nichos[nicho_index]

        # Randomly select era, location, and tone
        if nicho["eras"]:
            self.era_dropdown.setCurrentIndex(random.randint(0, len(nicho["eras"]) - 1))

        if nicho["locations"]:
            self.location_dropdown.setCurrentIndex(
                random.randint(0, len(nicho["locations"]) - 1)
            )

        if nicho["tones"]:
            self.tone_dropdown.setCurrentIndex(
                random.randint(0, len(nicho["tones"]) - 1)
            )

        self.log_message("Selección aleatoria aplicada")

    def log_message(self, message):
        self.log_text.append(f"{time.strftime('%H:%M:%S')} - {message}")
        self.log_text.ensureCursorVisible()

    def start_generation(self):
        if not self.current_nicho:
            QMessageBox.warning(self, "Error", "Por favor selecciona un nicho")
            return

        # Get current selections
        self.current_nicho = self.nicho_dropdown.currentText()
        self.current_era = self.era_dropdown.currentText()
        self.current_location = self.location_dropdown.currentText()
        self.current_tone = self.tone_dropdown.currentText()

        # Reset progress
        self.overall_progress.setValue(0)
        self.task_progress.setValue(0)
        self.tasks_completed = 0

        # Disable generate button during processing
        self.generate_button.setEnabled(False)
        self.open_video_button.setEnabled(False)

        # Define tasks
        tasks = [
            (
                "Generando texto",
                "./generador_textos.py",
                [
                    "--nicho",
                    self.current_nicho,
                    "--era",
                    self.current_era,
                    "--location",
                    self.current_location,
                    "--tone",
                    self.current_tone,
                ],
            ),
            (
                "Generando audio",
                "./generador_audios.py",
                ["--nicho", self.current_nicho],
            ),
            (
                "Generando prompts",
                "./generador_prompts.py",
                ["--nicho", self.current_nicho],
            ),
            (
                "Generando imágenes",
                "./generador_imagenes.py",
                ["--nicho", self.current_nicho],
            ),
            (
                "Generando subtitulos",
                "./generador_subtitulos.py",
                ["--nicho", self.current_nicho],
            ),
            (
                "Generando videos",
                "./generador_videos_subtitulados.py",
                ["--nicho", self.current_nicho],
            ),
        ]

        # Start the first task
        self.log_message("Iniciando generación de video...")
        self.start_next_task(tasks)

    def start_next_task(self, tasks):
        if not tasks:
            # All tasks completed
            self.log_message("¡Generación de video completada!")
            self.generate_button.setEnabled(True)
            self.open_video_button.setEnabled(True)
            QMessageBox.information(
                self, "Completado", "¡El video se ha generado con éxito!"
            )
            return

        # Get the next task
        task_name, script_path, args = tasks[0]
        remaining_tasks = tasks[1:]

        # Update UI
        self.current_task_label.setText(task_name)
        self.task_progress.setValue(0)
        self.log_message(f"Iniciando: {task_name}")

        # Create and start worker thread
        worker = WorkerThread(task_name, script_path, args)
        worker.update_progress.connect(self.update_task_progress)
        worker.update_status.connect(self.update_status)
        worker.task_complete.connect(
            lambda success, output: self.on_task_complete(
                success, output, remaining_tasks
            )
        )

        self.worker_threads.append(worker)
        worker.start()

    def update_task_progress(self, task_name, progress):
        self.task_progress.setValue(progress)

    def update_status(self, status):
        self.statusBar().showMessage(status)

    def on_task_complete(self, success, output, remaining_tasks):
        if success:
            # Increment completed tasks
            self.tasks_completed += 1
            self.overall_progress.setValue(
                int(self.tasks_completed / self.total_tasks * 100)
            )

            # Log output
            if output:
                self.log_message(output)

            # Start next task
            self.start_next_task(remaining_tasks)
        else:
            # Handle error
            self.log_message(f"ERROR: {output}")
            self.generate_button.setEnabled(True)
            QMessageBox.critical(
                self, "Error", f"Error durante la generación: {output}"
            )

    def open_last_video(self):
        video_path = os.path.join(
            "resources", "video", f"video_{self.current_nicho}.mp4"
        )
        if os.path.exists(video_path):
            if sys.platform == "win32":
                os.startfile(video_path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, video_path])
        else:
            QMessageBox.warning(self, "Error", "No se encontró el video")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    window = HistoryVideoGenerator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
