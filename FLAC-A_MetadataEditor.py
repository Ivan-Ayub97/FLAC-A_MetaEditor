import os
import shutil
import traceback

from mutagen.flac import FLAC, Picture
from PIL import Image
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QFileDialog,
                             QGridLayout, QHBoxLayout, QLabel, QListWidget,
                             QMessageBox, QPushButton, QSplitter, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)


class FlacMetadataEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FLAC-Album Metadata Editor - v1.0")
        self.setWindowIcon(QIcon("icon.png"))
        self.setGeometry(100, 100, 1200, 750)
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #ffa500; font-family: Consolas; font-size: 12px; }
            QPushButton { background-color: #333; color: #ffa500; padding: 6px 12px; font-weight: bold; border-radius: 6px; }
            QPushButton:hover { background-color: #444; }
            QHeaderView::section { background-color: #444; color: #ffa500; }
            QTableWidget { background-color: #000000; color: #ffa500; }
            QTextEdit { background-color: #000; color: white; border: 1px solid #ffa500; }
        """)

        self.selected_files = []
        self.cover_image_path = None
        self.output_folder = ""

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        toolbar_layout = QHBoxLayout()
        self.select_files_btn = QPushButton("📂 FLAC Files")
        self.select_files_btn.clicked.connect(self.select_files)

        self.cover_btn = QPushButton("🖼 Cover")
        self.cover_btn.clicked.connect(self.select_cover)

        self.output_btn = QPushButton("📁 Output Folder")
        self.output_btn.clicked.connect(self.select_output_folder)

        self.clear_btn = QPushButton("🧹 Clear")
        self.clear_btn.clicked.connect(self.clear_all)

        self.bulk_edit_btn = QPushButton("📋 Bulk Edit")
        self.bulk_edit_btn.clicked.connect(self.bulk_edit)

        for btn in [self.select_files_btn, self.cover_btn, self.output_btn, self.clear_btn, self.bulk_edit_btn]:
            toolbar_layout.addWidget(btn)

        main_layout.addLayout(toolbar_layout)

        splitter = QSplitter(Qt.Horizontal)

        # Metadata Table (main area)
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(["File", "Title", "Track", "Album", "Composer", "Genre", "Date", "Producer", "Album Artist", "License"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(24)
        splitter.addWidget(self.table)

        # Right side panel (narrow)
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        self.cover_preview = QLabel("No Cover")
        self.cover_preview.setFixedSize(150, 150)
        self.cover_preview.setAlignment(Qt.AlignCenter)
        self.cover_preview.setStyleSheet("border: 2px solid #ffa500;")
        right_layout.addWidget(self.cover_preview, alignment=Qt.AlignTop)

        self.export_btn = QPushButton("💾 Save & Export")
        self.export_btn.clicked.connect(self.export_files)
        self.export_btn.setStyleSheet("background-color: #ff6600; color: #fff; font-weight: bold; padding: 8px;")
        right_layout.addWidget(self.export_btn)

        right_layout.addWidget(QLabel("Log:"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(140)
        right_layout.addWidget(self.log_box)

        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 4)  # Main metadata area takes more space
        splitter.setStretchFactor(1, 1)  # Right panel thinner

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select FLAC Files", "", "FLAC Files (*.flac)")
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
                    self.load_file(f)

    def load_file(self, f):
        try:
            audio = FLAC(f)
            row = self.table.rowCount()
            self.table.insertRow(row)
            item = QTableWidgetItem(os.path.basename(f))
            item.setToolTip(f)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(audio.get("title", [""])[0]))
            self.table.setItem(row, 2, QTableWidgetItem(audio.get("tracknumber", [""])[0]))
            self.table.setItem(row, 3, QTableWidgetItem(audio.get("album", [""])[0]))
            self.table.setItem(row, 4, QTableWidgetItem(audio.get("composer", [""])[0]))
            self.table.setItem(row, 5, QTableWidgetItem(audio.get("genre", [""])[0]))
            self.table.setItem(row, 6, QTableWidgetItem(audio.get("date", [""])[0]))
            self.table.setItem(row, 7, QTableWidgetItem(audio.get("producer", [""])[0]))
            self.table.setItem(row, 8, QTableWidgetItem(audio.get("album artist", [""])[0]))
            self.table.setItem(row, 9, QTableWidgetItem(audio.get("license", [""])[0]))
        except Exception as e:
            self.log(f"❌ Failed to load: {f} -> {e}")

    def bulk_edit(self):
        rows_data = []
        for i in range(self.table.rowCount()):
            row_data = {
                'file': self.table.item(i, 0).text(),
                'title': self.table.item(i, 1).text(),
                'track': self.table.item(i, 2).text(),
                'album': self.table.item(i, 3).text(),
                'composer': self.table.item(i, 4).text(),
                'genre': self.table.item(i, 5).text(),
                'date': self.table.item(i, 6).text(),
                'producer': self.table.item(i, 7).text(),
                'album artist': self.table.item(i, 8).text(),
            }

            rows_data.append(row_data)

        rows_data = [row for row in rows_data if row['track'].isdigit()]
        rows_data.sort(key=lambda x: int(x['track']))

        for index, row_data in enumerate(rows_data):
            new_filename = f"{index + 1}. {row_data['title']}.flac"

            self.table.item(index, 0).setText(new_filename)
            self.table.item(index, 2).setText(row_data['track'])
            self.table.item(index, 3).setText(row_data['album'])
            self.table.item(index, 4).setText(row_data['composer'])
            self.table.item(index, 5).setText(row_data['genre'])
            self.table.item(index, 6).setText(row_data['date'])
            self.table.item(index, 7).setText(row_data['producer'])
            self.table.item(index, 8).setText(row_data['album artist'])

        self.log("✔ Bulk edit completed!")

    def select_cover(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Cover Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if file:
            self.cover_image_path = file
            pixmap = QPixmap(file).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.cover_preview.setPixmap(pixmap)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.log("✔ Output folder set to: " + folder)

    def clear_all(self):
        self.table.setRowCount(0)
        self.selected_files = []
        self.cover_image_path = None
        self.cover_preview.clear()
        self.cover_preview.setText("No Cover")
        self.output_folder = ""
        self.log_box.clear()

    def export_files(self):
        if not self.selected_files:
            self.warn("No FLAC files selected.")
            return
        if not self.output_folder:
            self.warn("No output folder selected.")
            return

        self.log("🚀 Starting export process...")

        for i, file_path in enumerate(self.selected_files):
            try:
                row = i
                title = self.table.item(row, 1).text() if self.table.item(row, 1) else os.path.basename(file_path)
                output_filename = f"{title}.flac"
                output_path = os.path.join(self.output_folder, output_filename)

                if os.path.exists(output_path):
                    reply = QMessageBox.question(self, "Overwrite?", f"{output_path} exists. Overwrite?", QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.No:
                        continue

                shutil.copy(file_path, output_path)
                audio = FLAC(output_path)
                tags = [self.table.item(row, col).text() if self.table.item(row, col) else "" for col in range(1, 10)]
                keys = ["TITLE", "TRACKNUMBER", "ALBUM", "COMPOSER", "GENRE", "DATE", "PRODUCER", "ALBUMARTIST", "LICENSE"]

                # Clear existing tags to avoid duplication
                audio.delete()
                for key, value in zip(keys, tags):
                    if value:
                        audio[key] = value

                # Add embedded cover image (front cover)
                if self.cover_image_path:
                    image_data = open(self.cover_image_path, 'rb').read()

                    picture = Picture()
                    picture.data = image_data
                    picture.type = 3  # front cover
                    picture.mime = "image/jpeg" if self.cover_image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

                    img = Image.open(self.cover_image_path)
                    picture.width = img.width
                    picture.height = img.height
                    picture.depth = 24  # bits-per-pixel
                    picture.colors = 0

                    # Remove previous pictures and add the new one
                    audio.clear_pictures()
                    audio.add_picture(picture)

                audio.save()
                self.log(f"✅ Exported: {output_filename}")

            except Exception as e:
                self.log(f"❌ Error exporting {file_path}: {e}\n{traceback.format_exc()}")


    def log(self, message):
        self.log_box.append(message)

    def warn(self, message):
        QMessageBox.warning(self, "Warning", message)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = FlacMetadataEditor()
    window.show()
    sys.exit(app.exec_())
