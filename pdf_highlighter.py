import sys
import os
import time
import pymupdf
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QLabel,
    QComboBox, QTextEdit, QWidget, QProgressBar, QMessageBox,
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon

COLORS = {
    "Yellow": (1, 1, 0),
    "Red": (1, 0, 0),
    "Green": (0, 1, 0),
    "Blue": (0, 0, 1),
    "Purple": (0.5, 0, 0.5),
    "Orange": (1, 0.647, 0),
    "Pink": (1, 0.75, 0.8),
    "Cyan": (0, 1, 1),
    "Light Green": (0.5, 1, 0),
    "Light Blue": (0.678, 0.847, 0.902),
    "Gray": (0.5, 0.5, 0.5),
    "Dark Blue": (0, 0, 0.5),
    "Dark Green": (0, 0.5, 0),
}
DEFAULT_COLOR = "Yellow"
OUTPUT_DIR = os.path.abspath('Result')


class HighlighterWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)

    def __init__(self, input_pdfs, output_pdfs, search_terms, color_name):
        super().__init__()
        self.input_pdfs = input_pdfs
        self.output_pdfs = output_pdfs
        self.search_terms = search_terms
        self.color = COLORS.get(color_name, COLORS[DEFAULT_COLOR])

    def run(self):
        try:
            total = len(self.search_terms) * sum(pymupdf.open(p).page_count for p in self.input_pdfs)
            done = 0

            for input_pdf, output_pdf in zip(self.input_pdfs, self.output_pdfs):
                doc = pymupdf.open(input_pdf)
                fname = os.path.basename(input_pdf)
                for idx, term in enumerate(self.search_terms, 1):
                    self.status.emit(f"[{idx}/{len(self.search_terms)}] Searching '{term}' in {fname}")
                    for page_num in range(doc.page_count):
                        page = doc.load_page(page_num)
                        for inst in page.search_for(term):
                            hl = page.add_highlight_annot(inst)
                            hl.set_colors(stroke=self.color)
                            hl.update()
                        done += 1
                        self.progress.emit(int(done / total * 100))

                os.makedirs(OUTPUT_DIR, exist_ok=True)
                doc.save(output_pdf)
                self.status.emit(f"Saved: {output_pdf}")

            self.finished.emit("All PDFs processed successfully.")
        except Exception as e:
            self.status.emit(f"Error: {e}")
            self.finished.emit("")


class PDFHighlighterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Highlighter")
        icon_path = os.path.join(getattr(sys, '_MEIPASS', ''), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(300, 300, 600, 600)
        self.pdf1_path = None
        self.pdf2_path = None
        self.txt_path = None
        self.highlight_color = DEFAULT_COLOR
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        self.label_pdf1 = QLabel("First PDF: Not Selected")
        self.label_pdf2 = QLabel("Second PDF: Not Selected (optional)")
        self.label_txt = QLabel("Search Terms File: Not Selected")
        for lbl in [self.label_pdf1, self.label_pdf2, self.label_txt]:
            layout.addWidget(lbl)

        for text, slot in [
            ("Select First PDF", self.select_pdf1),
            ("Select Second PDF (optional)", self.select_pdf2),
            ("Select Search Terms File (.txt)", self.select_txt),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        self.color_preview = QLabel("Highlight Color:")
        layout.addWidget(self.color_preview)

        self.color_selector = QComboBox()
        self.color_selector.addItems(COLORS.keys())
        self.color_selector.setCurrentText(DEFAULT_COLOR)
        self.color_selector.currentTextChanged.connect(self._on_color_changed)
        layout.addWidget(self.color_selector)
        self._update_color_preview(DEFAULT_COLOR)

        btn_process = QPushButton("Highlight PDFs")
        btn_process.clicked.connect(self.start_processing)
        layout.addWidget(btn_process)

        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _update_color_preview(self, name):
        r, g, b = (int(v * 255) for v in COLORS[name])
        self.color_preview.setStyleSheet(f"background-color: rgb({r},{g},{b}); padding: 4px;")

    def _on_color_changed(self, name):
        self.highlight_color = name
        self._update_color_preview(name)

    def select_pdf1(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select First PDF", "", "PDF Files (*.pdf)")
        if path:
            self.pdf1_path = path
            self.label_pdf1.setText(f"First PDF: {os.path.basename(path)}")

    def select_pdf2(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Second PDF", "", "PDF Files (*.pdf)")
        if path:
            self.pdf2_path = path
            self.label_pdf2.setText(f"Second PDF: {os.path.basename(path)}")

    def select_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Search Terms", "", "Text Files (*.txt)")
        if path:
            self.txt_path = path
            self.label_txt.setText(f"Search Terms: {os.path.basename(path)}")

    def _handle_existing(self, output_path):
        if not os.path.exists(output_path):
            return output_path
        box = QMessageBox(self)
        box.setWindowTitle("File Already Exists")
        box.setText(f"'{os.path.basename(output_path)}' already exists.")
        btn_ow = box.addButton("Overwrite", QMessageBox.AcceptRole)
        btn_rn = box.addButton("Rename", QMessageBox.ActionRole)
        btn_cl = box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec_()
        clicked = box.clickedButton()
        if clicked == btn_ow:
            return output_path
        if clicked == btn_rn:
            ts = time.strftime("%d.%m.%y_%H%M")
            base = os.path.basename(output_path).replace('.pdf', '')
            return os.path.join(OUTPUT_DIR, f'{base}_{ts}.pdf')
        return None

    def start_processing(self):
        if not self.pdf1_path or not self.txt_path:
            QMessageBox.warning(self, "Missing Input", "Select at least one PDF and a search terms file.")
            return

        with open(self.txt_path) as f:
            terms = f.read().splitlines()

        input_pdfs = [self.pdf1_path]
        output_pdfs = [os.path.join(OUTPUT_DIR, os.path.basename(self.pdf1_path).replace('.pdf', '_highlighted.pdf'))]

        if self.pdf2_path:
            input_pdfs.append(self.pdf2_path)
            output_pdfs.append(os.path.join(OUTPUT_DIR, os.path.basename(self.pdf2_path).replace('.pdf', '_highlighted.pdf')))

        resolved = []
        for out in output_pdfs:
            path = self._handle_existing(out)
            if path is None:
                return
            resolved.append(path)

        self.centralWidget().setEnabled(False)
        self.worker = HighlighterWorker(input_pdfs, resolved, terms, self.highlight_color)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.log.append)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, message):
        self.centralWidget().setEnabled(True)
        self.log.append(message)
        if message:
            QMessageBox.information(self, "Done", message)


def main():
    app = QApplication(sys.argv)
    window = PDFHighlighterApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
