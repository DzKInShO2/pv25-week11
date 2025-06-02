from PyQt5.QtCore import Qt
from PyQt5.QtSql import (
    QSqlDatabase,
    QSqlQuery
)
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QMenu,
    QAction,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QMessageBox,
    QLineEdit,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QStatusBar,
    QScrollArea,
    QDockWidget,
    QFileDialog
)


class LibraryTable(QTableWidget):
    def __init__(self, database):
        super().__init__()

        self.searched = ""
        self.setupDatabase_(database)
        self.tableUpdateView_()

        self.itemChanged.connect(self.updateItem_)

    def setSearched(self, search):
        self.searched = search
        self.tableUpdateView_()

    def insertRecord(self, title, author, year):
        if title == "":
            QMessageBox.warning(None,
                                "",
                                "Judul buku belum terisi.")
            return False

        if author == "":
            QMessageBox.warning(None,
                                "",
                                "Pengarang buku belum terisi.")
            return False

        if year == "":
            QMessageBox.warning(None,
                                "",
                                "Tahun buku belum terisi.")
            return False

        if not year.isnumeric():
            QMessageBox.warning(None,
                                "",
                                "Tahun harus dalam bentuk angka.")
            return False

        sql_insert_book = QSqlQuery()
        sql_insert_book.prepare(
            """
            INSERT INTO Buku (Judul, Pengarang, Tahun) VALUES (?, ?, ?);
            """
        )

        sql_insert_book.addBindValue(title)
        sql_insert_book.addBindValue(author)
        sql_insert_book.addBindValue(year)
        sql_insert_book.exec()

        self.tableUpdateView_()

        return True

    def deleteRecord(self, idx):
        sql_delete_book = QSqlQuery()
        sql_delete_book.prepare(
            """
            DELETE FROM Buku WHERE ID = ?;
            """
        )

        sql_delete_book.addBindValue(idx)
        sql_delete_book.exec()

        self.tableUpdateView_()

    def exportToCSV(self, path):
        query = QSqlQuery()
        query.prepare("""
        SELECT * FROM Buku;
        """)

        if query.exec():
            with open(path, "w") as f:
                f.write("Judul,Pengarang,Tahun")
                while query.next():
                    f.write(f"{query.value(1)},{
                            query.value(2)},{query.value(3)}\n")

    def setupDatabase_(self, database):
        self.sql_conn = QSqlDatabase.addDatabase("QSQLITE")
        self.sql_conn.setDatabaseName(database)

        self.sql_conn.open()

        QSqlQuery().exec(
            """
            CREATE TABLE IF NOT EXISTS Buku (
                ID INTEGER PRIMARY KEY NOT NULL,
                Judul TEXT NOT NULL,
                Pengarang TEXT NOT NULL,
                Tahun INTEGER NOT NULL
            );
            """
        )

        query = QSqlQuery()
        query.prepare("""
        SELECT * FROM Buku;
        """)

        self.columns = []
        if query.exec():
            self.columns = [query.record().fieldName(i)
                            for i in range(query.record().count())]

    def updateItem_(self, item):
        sql_update_book = QSqlQuery()
        sql_update_book.prepare(f"""
        UPDATE Buku SET {self.columns[item.column()]} = ?
        WHERE ID = ?;
        """)

        sql_book_id = QSqlQuery()
        if sql_book_id.exec(f"""
        SELECT ID FROM Buku LIMIT 1 OFFSET {item.row()};
        """):
            sql_book_id.next()
            sql_update_book.addBindValue(item.text())
            sql_update_book.addBindValue(sql_book_id.value(0))
            sql_update_book.exec()

    def tableUpdateView_(self):
        sql_retrieve_books = QSqlQuery()

        if self.searched == "":
            sql_retrieve_books.prepare("""
            SELECT * FROM Buku;
            """)
        else:
            sql_retrieve_books.prepare("""
            SELECT * FROM Buku WHERE Judul LIKE ?;
            """)
            sql_retrieve_books.addBindValue(f"%{self.searched}%")

        if sql_retrieve_books.exec():
            self.setColumnCount(len(self.columns))
            self.setHorizontalHeaderLabels(self.columns)

            rows = []
            while sql_retrieve_books.next():
                row_data = [sql_retrieve_books.value(i) for i in range(
                    sql_retrieve_books.record().count())]
                rows.append(row_data)

            row_count = len(rows)
            self.setRowCount(row_count)

            for i in range(row_count):
                for j in range(4):
                    self.setItem(i, j, QTableWidgetItem(str(rows[i][j])))


class CRUDWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedSize(720, 480)
        self.setWindowTitle("Manajemen Buku")

        self.menubarInit_()
        self.menubarCallbacks_()

        self.statusbarInit_()
        self.dockInit_()

        self.widgetInit_()

    def menubarInit_(self):
        menubar = self.menuBar()

        # Buat aksi untuk menu file
        self.file_save_action_ = QAction("Simpan", self)
        self.file_export_action_ = QAction("Expor ke CSV", self)
        self.file_exit_action_ = QAction("Keluar", self)

        # Tambah aksi ke menu file
        file_menu = QMenu("File", self)
        file_menu.addAction(self.file_save_action_)
        file_menu.addAction(self.file_export_action_)
        file_menu.addAction(self.file_exit_action_)

        # Buat aksi untuk menu edit
        self.edit_search_action_ = QAction("Cari Judul", self)
        self.edit_delete_action_ = QAction("Hapus Data", self)

        # Tambah aksi ke menu edit
        edit_menu = QMenu("Edit", self)
        edit_menu.addAction(self.edit_search_action_)
        edit_menu.addAction(self.edit_delete_action_)

        # Tambah menu ke menubar
        menubar.addMenu(file_menu)
        menubar.addMenu(edit_menu)

    def menubarCallbacks_(self):
        # Callback/Signal untuk menu file
        self.file_save_action_.triggered.connect(self.fileSaved_)
        self.file_export_action_.triggered.connect(self.fileExported_)
        self.file_exit_action_.triggered.connect(self.fileExited_)

        # Callback/Signal untuk menu file
        self.edit_search_action_.triggered.connect(self.editSearched_)
        self.edit_delete_action_.triggered.connect(self.editDeleted_)

    def statusbarInit_(self):
        statusbar = QStatusBar()
        statusbar.addPermanentWidget(QLabel("Dzakanov Inshoofi (F1D02310110)"))

        self.setStatusBar(statusbar)

    def dockInit_(self):
        form_dock = QDockWidget()
        form_widget = QWidget()

        self.record_title = QLineEdit()
        self.record_author = QLineEdit()
        self.record_year = QLineEdit()

        save_button = QPushButton("Simpan")
        delete_button = QPushButton("Hapus Data")
        save_button.clicked.connect(self.fileSaved_)
        delete_button.clicked.connect(self.editDeleted_)

        save_delete_layout = QHBoxLayout()
        save_delete_layout.addWidget(save_button)
        save_delete_layout.addWidget(delete_button)

        self.search_line = QLineEdit()
        self.search_line.setPlaceholderText("Cari judul...")
        self.search_line.textChanged.connect(self.editSearched_)

        search_line_layout = QVBoxLayout()
        search_line_layout.addWidget(self.search_line)

        paste_full_from_clipboard = QPushButton("Paste CSV (3 Value) dari Clipboard")
        paste_full_from_clipboard.clicked.connect(self.pasteFull_)

        paste_layout = QVBoxLayout()
        paste_layout.addWidget(paste_full_from_clipboard)

        form = QFormLayout()
        form.setFormAlignment(Qt.AlignmentFlag.AlignHCenter)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        form.addRow(QLabel("Judul"), self.record_title)
        form.addRow(QLabel("Pengarang"), self.record_author)
        form.addRow(QLabel("Tahun"), self.record_year)
        form.addRow(paste_layout)
        form.addRow(save_delete_layout)
        form.addRow(search_line_layout)

        form_widget.setLayout(form)
        form_dock.setWidget(form_widget)

        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, form_dock)

    def widgetInit_(self):
        self.table = LibraryTable("perpustakaan.sql")

        scrollarea = QScrollArea()
        scrollarea.setWidgetResizable(True)
        scrollarea.setWidget(self.table)

        widget = QWidget()
        root = QVBoxLayout()

        root.addWidget(scrollarea)
        widget.setLayout(root)

        self.setCentralWidget(widget)

    def fileSaved_(self):
        title = self.record_title.text()
        author = self.record_author.text()
        year = self.record_year.text()

        if self.table.insertRecord(title, author, year):
            self.record_title.clear()
            self.record_author.clear()
            self.record_year.clear()

    def fileExported_(self):
        path, _ = QFileDialog.getSaveFileName(self, "Simpan CSV", "",
                                              "CSV Files (*.csv)")
        if len(path.split(".")) == 1:
            path += ".csv"

        self.table.exportToCSV(path)

    def fileExited_(self):
        self.close()

    def editSearched_(self):
        self.table.setSearched(self.search_line.text())

    def editDeleted_(self):
        if self.table.currentRow() > -1:
            row = self.table.currentRow()
            idx = int(self.table.item(row, 0).text())

            is_continue = QMessageBox.question(self, "",
                                               f"Hapus buku ID {idx}?",
                                               QMessageBox.Yes | QMessageBox.No)
            if is_continue == QMessageBox.Yes:
                self.table.deleteRecord(idx)
        else:
            QMessageBox.warning(None, "", "Tidak ada data yang dipilih.")

    def pasteFull_(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if text is None:
            return

        lines = text.split(",")
        for i in range(len(lines)):
            if i == 0:
                self.record_title.setText(lines[i].strip())
            elif i == 1:
                self.record_author.setText(lines[i].strip())
            elif i == 2:
                self.record_year.setText(lines[i].strip())


if __name__ == "__main__":
    app = QApplication([])
    win = CRUDWindow()

    win.show()
    app.exec()
