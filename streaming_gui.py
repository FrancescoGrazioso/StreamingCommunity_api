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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QLabel,
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
    """Redirect script output to GUI"""

    newText = pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))

    def flush(self):
        pass


class StreamingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.process = None
        self.current_context = None  # 'seasons', 'episodes', or None
        self.selected_season = None
        self.init_ui()

        # output redirect
        self.stdout_stream = Stream()
        self.stdout_stream.newText.connect(self.update_output)
        sys.stdout = self.stdout_stream

    def init_ui(self):
        self.setWindowTitle("StreamingCommunity GUI")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        main_layout = QVBoxLayout()

        tab_widget = QTabWidget()
        run_tab = QWidget()
        run_layout = QVBoxLayout()

        # search parameters group
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

        search_layout.addRow("Seleziona sito:", self.site_combo)
        search_group.setLayout(search_layout)
        run_layout.addWidget(search_group)

        # control buttons
        control_layout = QHBoxLayout()

        self.run_button = QPushButton("Esegui Script")
        self.run_button.clicked.connect(self.run_script)
        control_layout.addWidget(self.run_button)

        self.stop_button = QPushButton("Ferma Script")
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        # Console visibility checkbox
        self.console_checkbox = QCheckBox("Mostra Console")
        self.console_checkbox.setChecked(False)
        self.console_checkbox.stateChanged.connect(self.toggle_console)
        control_layout.addWidget(self.console_checkbox)

        run_layout.addLayout(control_layout)

        # Status label (replacing loader)
        self.status_label = QLabel("Richiesta in corso...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.hide()
        run_layout.addWidget(self.status_label)

        # output area
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()

        # Table widget
        self.results_table = QTableWidget()
        self.results_table.setVisible(False)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        self.results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        output_layout.addWidget(self.results_table)

        # Console output
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.hide()
        output_layout.addWidget(self.output_text)

        # Input controls
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Inserisci l'indice del media...")
        self.input_field.returnPressed.connect(self.send_input)
        self.send_button = QPushButton("Invia")
        self.send_button.clicked.connect(self.send_input)

        self.input_field.hide()
        self.send_button.hide()

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        output_layout.addLayout(input_layout)

        output_group.setLayout(output_layout)
        run_layout.addWidget(output_group)

        run_tab.setLayout(run_layout)
        tab_widget.addTab(run_tab, "Esecuzione")

        main_layout.addWidget(tab_widget)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def toggle_console(self, state):
        self.output_text.setVisible(state == Qt.Checked)

    def parse_and_show_results(self, text):
        # Handle seasons list
        if "Seasons found:" in text:
            self.status_label.hide()
            num_seasons = int(text.split("Seasons found:")[1].split()[0])

            # Setup table for seasons
            self.results_table.clear()
            self.results_table.setColumnCount(2)
            self.results_table.setHorizontalHeaderLabels(["Index", "Season"])

            # Populate table with seasons
            self.results_table.setRowCount(num_seasons)
            for i in range(num_seasons):
                index_item = QTableWidgetItem(str(i + 1))
                season_item = QTableWidgetItem(f"Stagione {i + 1}")
                self.results_table.setItem(i, 0, index_item)
                self.results_table.setItem(i, 1, season_item)

            # Adjust columns and show table
            self.results_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents
            )
            self.results_table.setVisible(True)
            self.results_table.itemSelectionChanged.connect(self.handle_selection)
            return

        # Handle regular table output (episodes or search results)
        if "┏━━━━━━━┳" in text and "└───────┴" in text:
            self.status_label.hide()

            # Extract table content
            table_lines = text[text.find("┏") : text.find("└")].split("\n")

            # Parse headers
            headers = table_lines[1].split("┃")[1:-1]
            headers = [h.strip() for h in headers]

            # Setup table
            self.results_table.clear()
            self.results_table.setColumnCount(len(headers))
            self.results_table.setHorizontalHeaderLabels(headers)

            # Parse rows
            rows = []
            for line in table_lines[3:]:
                if line.strip() and "│" in line:
                    cells = line.split("│")[1:-1]
                    cells = [cell.strip() for cell in cells]
                    rows.append(cells)

            # Populate table
            self.results_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, cell in enumerate(row):
                    item = QTableWidgetItem(cell)
                    self.results_table.setItem(i, j, item)

            # Adjust columns
            self.results_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeToContents
            )

            # Show table and connect selection
            self.results_table.setVisible(True)
            self.results_table.itemSelectionChanged.connect(self.handle_selection)

    def handle_selection(self):
        if self.results_table.selectedItems():
            selected_row = self.results_table.currentRow()
            if self.input_field.isVisible():
                if self.current_context == "seasons":
                    # For seasons, we add 1 because seasons are 1-based
                    self.input_field.setText(str(selected_row + 1))
                else:
                    # For episodes and search results, use the row number directly
                    self.input_field.setText(str(selected_row))

    def run_script(self):
        if self.process is not None and self.process.state() == QProcess.Running:
            print("Script già in esecuzione.")
            return

        self.current_context = None
        self.selected_season = None
        self.results_table.setVisible(False)
        self.status_label.setText("Richiesta in corso...")
        self.status_label.show()

        # build command line args
        args = []
        search_terms = self.search_terms.text()
        if search_terms:
            args.extend(["-s", search_terms])

        site_index = self.site_combo.currentIndex()
        if site_index >= 0:
            site_text = sites[site_index]["flag"]
            site_name = site_text.split()[0].upper()
            args.append(f"-{site_name}")

        self.output_text.clear()
        print(f"Avvio script con argomenti: {' '.join(args)}")

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)

        python_executable = sys.executable
        script_path = "run_streaming.py"

        self.process.start(python_executable, [script_path] + args)
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8", errors="replace")
        self.update_output(stdout)

        # Detect context
        if "Seasons found:" in stdout:
            self.current_context = "seasons"
            self.input_field.setPlaceholderText(
                "Inserisci il numero della stagione (es: 1, *, 1-2, 3-*)"
            )
        elif "Episodes find:" in stdout:
            self.current_context = "episodes"
            self.input_field.setPlaceholderText(
                "Inserisci l'indice dell'episodio (es: 1, *, 1-2, 3-*)"
            )

        # Parse and show results if available
        if "┏━━━━━━━┳" in stdout or "Seasons found:" in stdout:
            self.parse_and_show_results(stdout)
        elif "Episodes find:" in stdout:
            self.results_table.hide()
            self.status_label.setText(stdout)
            self.status_label.show()

        # Show input controls when needed
        if "Insert" in stdout:
            self.input_field.show()
            self.send_button.show()
            self.input_field.setFocus()
            self.output_text.verticalScrollBar().setValue(
                self.output_text.verticalScrollBar().maximum()
            )

    def send_input(self):
        if not self.process or self.process.state() != QProcess.Running:
            return

        user_input = self.input_field.text().strip()

        # Handle season selection
        if self.current_context == "seasons":
            if "-" in user_input or user_input == "*":
                # Multiple seasons selected, hide table
                self.results_table.hide()
            else:
                # Single season selected, table will update with episodes
                self.selected_season = user_input

        # Handle episode selection
        elif self.current_context == "episodes":
            if "-" in user_input or user_input == "*":
                # Multiple episodes selected, hide table
                self.results_table.hide()

        # Send input to process
        self.process.write(f"{user_input}\n".encode())
        self.input_field.clear()
        self.input_field.hide()
        self.send_button.hide()

        # Show status label for next step
        if self.current_context == "seasons" and not (
            "-" in user_input or user_input == "*"
        ):
            self.status_label.setText("Caricamento episodi...")
            self.status_label.show()

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8", errors="replace")
        self.update_output(stderr)

    def process_finished(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.input_field.hide()
        self.send_button.hide()
        self.status_label.hide()
        print("Script terminato.")

    def update_output(self, text):
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(text)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()

    def stop_script(self):
        if self.process is not None and self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(3000):
                self.process.kill()
            print("Script terminato.")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        if self.process is not None and self.process.state() == QProcess.Running:
            self.process.terminate()
            if not self.process.waitForFinished(1000):
                self.process.kill()
        sys.stdout = sys.__stdout__
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = StreamingGUI()
    gui.show()
    sys.exit(app.exec_())
