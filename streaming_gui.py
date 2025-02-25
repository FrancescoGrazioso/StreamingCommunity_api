import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTabWidget,
    QTextEdit,
    QGroupBox,
    QFormLayout,
)
from PyQt5.QtCore import Qt, QProcess, pyqtSignal, QObject

from StreamingCommunity.run import load_search_functions

search_functions = load_search_functions()
sites = []
for alias, (_, use_for) in search_functions.items():
    sites.append(
        {"index": len(sites), "name": alias.split("_")[0], "flag": alias[:3].upper()}
    )


class Stream(QObject):
    """Reindirizza l'output dello script alla GUI"""

    newText = pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))

    def flush(self):
        pass


class StreamingGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Processo per eseguire lo script
        self.process = None

        self.init_ui()

        # Reindirizzamento dell'output
        self.stdout_stream = Stream()
        self.stdout_stream.newText.connect(self.update_output)
        sys.stdout = self.stdout_stream

    def init_ui(self):
        self.setWindowTitle("StreamingCommunity GUI")
        self.setGeometry(100, 100, 1000, 700)

        # Widget e layout principale
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Crea un widget a schede
        tab_widget = QTabWidget()

        # Scheda 1: Esecuzione script
        run_tab = QWidget()
        run_layout = QVBoxLayout()

        # Gruppo per i parametri di ricerca
        search_group = QGroupBox("Parametri di Ricerca")
        search_layout = QFormLayout()

        self.search_terms = QLineEdit()
        search_layout.addRow("Termini di ricerca:", self.search_terms)

        self.site_combo = QComboBox()

        for site in sites:
            self.site_combo.addItem(f"{site['name']}", site["index"])
            self.site_combo.setItemData(site["index"], site["flag"], Qt.ToolTipRole)
        if self.site_combo.count() > 0:
            self.site_combo.setCurrentIndex(0)
        # Qui dovresti popolare il combobox con i siti disponibili
        # Per ora lo lascio vuoto, ma andrebbe riempito dinamicamente
        search_layout.addRow("Seleziona sito:", self.site_combo)

        search_group.setLayout(search_layout)
        run_layout.addWidget(search_group)

        # Bottoni di controllo
        control_layout = QHBoxLayout()

        self.run_button = QPushButton("Esegui Script")
        self.run_button.clicked.connect(self.run_script)
        control_layout.addWidget(self.run_button)

        self.stop_button = QPushButton("Ferma Script")
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        run_layout.addLayout(control_layout)

        # Area di output
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)

        output_group.setLayout(output_layout)
        run_layout.addWidget(output_group)

        run_tab.setLayout(run_layout)
        tab_widget.addTab(run_tab, "Esecuzione")

        main_layout.addWidget(tab_widget)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def run_script(self):
        if self.process is not None and self.process.state() == QProcess.Running:
            print("Script già in esecuzione.")
            return

        # Costruisci la command line con gli argomenti
        args = []

        # Aggiungi i termini di ricerca
        search_terms = self.search_terms.text()
        if search_terms:
            args.extend(["-s", search_terms])

        # Aggiungi il sito selezionato se presente
        site_index = self.site_combo.currentIndex()
        if site_index >= 0:
            site_text = sites[site_index]["flag"]
            # Assumo che il nome del sito sia il primo elemento del testo
            site_name = site_text.split()[0].upper()
            args.append(f"-{site_name}")

        self.output_text.clear()
        print(f"Avvio script con argomenti: {' '.join(args)}")

        # Creiamo e avviamo il processo
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        python_executable = sys.executable
        script_path = "run_streaming.py"

        self.process.start(python_executable, [script_path] + args)

        # Aggiorna lo stato dei pulsanti
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_script(self):
        if self.process is not None and self.process.state() == QProcess.Running:
            self.process.terminate()
            # Attendi che si chiuda (con timeout)
            if not self.process.waitForFinished(3000):
                self.process.kill()
            print("Script terminato.")

            # Aggiorna lo stato dei pulsanti
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8", errors="replace")
        self.update_output(stdout)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8", errors="replace")
        self.update_output(stderr)

    def process_finished(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        print("Script terminato.")

    def update_output(self, text):
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()

    def closeEvent(self, event):
        # Fermae qualsiasi processo in esecuzione prima di chiudere
        if self.process is not None and self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()

        # Ripristina stdout
        sys.stdout = sys.__stdout__

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = StreamingGUI()
    gui.show()
    sys.exit(app.exec_())
