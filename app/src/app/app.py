import asyncio
import logging
import sys
import time

from qtpy.QtCore import Qt, QThread, Signal, QObject
from qtpy.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from classcadconnector import AbstractClient, SocketIOClient
from classcadconnector.httpclient import _HttpClient
from classcadpyvista import ScgPyVistaConverter

from app.models.examplemodels import get_all_models, PARAM_SLIDER, PARAM_CHECKBOX, PARAM_DROPDOWN, PARAM_NUMBER

logging.basicConfig(level=logging.INFO, format="[%(levelname)s]: %(message)s")
logger = logging.getLogger(__name__)


def _create_client(use_socket_io: bool) -> AbstractClient:
    if use_socket_io:
        return SocketIOClient(url="ws://localhost:9091")
    return _HttpClient(url="http://localhost:9094")


# ── Background worker for async model generation ──

class _ModelWorker(QObject):
    """Runs the async ClassCAD API calls on a background thread.
    Emits *scene_ready(scg, label)* so the main thread can update the viewport."""
    scene_ready = Signal(object, str)   # (scg_dict, label)
    finished = Signal()
    error = Signal(str)

    def __init__(self, model, params, use_socket_io: bool):
        super().__init__()
        self._model = model
        self._params = params
        self._use_socket_io = use_socket_io

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._do_work())
            finally:
                loop.close()
            self.finished.emit()
        except Exception as exc:
            logger.exception("Model generation failed")
            self.error.emit(str(exc))

    async def _save_and_emit_scg(self, client: AbstractClient, model, product_id):
        scg = await client.getScg()
        self.scene_ready.emit(scg, model["label"])

    async def _do_work(self):
        model = self._model
        client = _create_client(self._use_socket_io)
        try:
            success = await client.connect()
            if not success:
                raise RuntimeError("Could not connect to ClassCAD server")

            api = client.getApiU()
            await api.v1.common.clear(dict())

            start = time.perf_counter()
            product_id = await model["create_func"](api, self._params)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"{model['label']}: {elapsed:.0f} ms")

            if product_id is not None:
                await self._save_and_emit_scg(client, model, product_id)
        finally:
            await client.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClassCAD Examples")
        self.resize(1280, 720)

        self.all_models = get_all_models()
        self._param_widgets: dict = {}
        self._current_model = None
        self._worker: _ModelWorker | None = None
        self._worker_thread: QThread | None = None

        # ── Central widget with splitter ──
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Left: embedded 3D viewport
        self._plotter = QtInteractor(splitter)
        self._plotter.show_grid(color="lightgray")
        self._plotter.add_axes(viewport=(0.8, 0.8, 1.0, 1.0))
        self._plotter.view_isometric()
        self._plotter.enable_custom_trackball_style(
            left="rotate",
            right="pan",
            middle="dolly",
        )
        splitter.addWidget(self._plotter.interactor)

        # Right: controls panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(4, 4, 4, 4)
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 3)  # viewport gets more space
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([900, 380])

        # ── Connection controls ──
        conn_group = QGroupBox("Connection")
        conn_layout = QHBoxLayout(conn_group)
        self._radio_socketio = QRadioButton("SocketIO")
        self._radio_socketio.setChecked(True)
        self._radio_http = QRadioButton("HTTP")
        conn_layout.addWidget(self._radio_socketio)
        conn_layout.addWidget(self._radio_http)
        right_layout.addWidget(conn_group)

        # ── Tabs for model categories ──
        self._tabs = QTabWidget()
        self._list_widgets: dict[str, tuple[QListWidget, list]] = {}

        for category in ("Solid", "Part", "Assembly"):
            lw = QListWidget()
            models = [m for m in self.all_models if m["category"] == category]
            for m in models:
                lw.addItem(m["label"])
            lw.currentRowChanged.connect(lambda row, cat=category: self._on_select(row, cat))
            self._tabs.addTab(lw, category)
            self._list_widgets[category] = (lw, models)

        right_layout.addWidget(self._tabs, stretch=1)

        # ── Parameters panel ──
        self._params_group = QGroupBox("Parameters")
        self._params_layout = QFormLayout(self._params_group)
        right_layout.addWidget(self._params_group)

        # ── Apply button ──
        self._apply_btn = QPushButton("Apply / Run")
        self._apply_btn.clicked.connect(self._on_apply)
        right_layout.addWidget(self._apply_btn)

        # ── Status bar ──
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready — select a model to run")

    # ── Viewport helpers ──

    def _clear_viewport(self):
        self._plotter.clear()
        self._plotter.show_grid(color="lightgray")
        self._plotter.add_axes(viewport=(0.8, 0.8, 1.0, 1.0))

    def _load_scene_into_viewport(self, scg: dict, title: str):
        scene = ScgPyVistaConverter.convert_scg(scg, include_edges=True)

        logger.info(f"SCG2PyVista blocks: {scene.multiblock.n_blocks}")

        self._clear_viewport()
        scene.add_to_plotter(self._plotter)
        self._plotter.add_text(title, font_size=12)
        self._plotter.view_isometric()
        self._plotter.reset_camera()
        self._plotter.update()

    # ── Callbacks ──

    def _on_select(self, row: int, category: str):
        if row < 0:
            return
        _, models = self._list_widgets[category]
        model = models[row]
        self._current_model = model
        self._build_param_widgets(model)

    def _build_param_widgets(self, model):
        # Clear old widgets
        while self._params_layout.rowCount() > 0:
            self._params_layout.removeRow(0)
        self._param_widgets.clear()

        params = model.get("params", [])
        if not params:
            self._params_layout.addRow(QLabel("(no parameters)"))
            return

        for p in params:
            name = p["name"]
            ptype = p.get("type", PARAM_NUMBER)

            if ptype == PARAM_SLIDER:
                slider = QSlider(Qt.Orientation.Horizontal)
                pmin = p.get("min", 0)
                pmax = p.get("max", 100)
                step = p.get("step", 1)
                default = p.get("default", pmin)
                # QSlider works with ints; scale by 1/step
                scale_factor = 1.0 / step if step else 1.0
                slider.setMinimum(int(pmin * scale_factor))
                slider.setMaximum(int(pmax * scale_factor))
                slider.setValue(int(default * scale_factor))
                slider.setSingleStep(1)
                # Display current value
                value_label = QLabel(str(default))
                value_label.setMinimumWidth(40)
                slider.valueChanged.connect(
                    lambda v, lbl=value_label, sf=scale_factor: lbl.setText(str(v / sf))
                )
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.addWidget(slider, stretch=1)
                row_layout.addWidget(value_label)
                self._params_layout.addRow(name, row_widget)
                self._param_widgets[name] = ("slider", slider, step)

            elif ptype == PARAM_CHECKBOX:
                cb = QCheckBox()
                cb.setChecked(bool(p.get("default", 0)))
                self._params_layout.addRow(name, cb)
                self._param_widgets[name] = ("checkbox", cb)

            elif ptype == PARAM_DROPDOWN:
                combo = QComboBox()
                options = p.get("options", [])
                combo.addItems(options)
                combo.setCurrentIndex(int(p.get("default", 0)))
                self._params_layout.addRow(name, combo)
                self._param_widgets[name] = ("dropdown", combo, options)

            else:  # number
                spin = QDoubleSpinBox()
                spin.setDecimals(2)
                spin.setRange(-1e9, 1e9)
                spin.setValue(p.get("default", 0))
                self._params_layout.addRow(name, spin)
                self._param_widgets[name] = ("number", spin)

    def _collect_params(self) -> dict:
        result = {}
        model = self._current_model
        if not model:
            return result

        for p in model.get("params", []):
            name = p["name"]
            entry = self._param_widgets.get(name)
            if entry is None:
                continue

            kind = entry[0]
            if kind == "slider":
                _, slider, step = entry
                result[name] = slider.value() * step
            elif kind == "checkbox":
                _, cb = entry
                result[name] = 1 if cb.isChecked() else 0
            elif kind == "dropdown":
                _, combo, options = entry
                result[name] = combo.currentIndex()
            else:  # number
                _, spin = entry
                result[name] = spin.value()

        return result

    def _stop_worker(self):
        """Wait for any running worker thread to finish."""
        if self._worker_thread is not None and self._worker_thread.isRunning():
            self._worker_thread.quit()
            self._worker_thread.wait()
            self._worker_thread = None
            self._worker = None

    def _on_apply(self):
        if self._current_model is None:
            QMessageBox.information(self, "Info", "Select a model first.")
            return

        # Stop any running worker before starting new work
        self._stop_worker()

        # Prevent double-clicks while running
        if self._worker_thread is not None and self._worker_thread.isRunning():
            return

        model = self._current_model
        params = self._collect_params()

        self._status_bar.showMessage(f"Building {model['label']}...")
        self._apply_btn.setEnabled(False)

        worker = _ModelWorker(model, params, self._radio_socketio.isChecked())
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.scene_ready.connect(self._load_scene_into_viewport)
        worker.finished.connect(lambda: self._on_worker_done(model["label"]))
        worker.error.connect(self._on_worker_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(self._on_thread_finished)

        self._worker = worker  # prevent GC
        self._worker_thread = thread
        thread.start()

    def _on_thread_finished(self):
        self._worker_thread = None
        self._worker = None

    def _on_worker_done(self, label: str):
        self._apply_btn.setEnabled(True)
        self._status_bar.showMessage(f"{label} — done", 5000)

    def _on_worker_error(self, msg: str):
        self._apply_btn.setEnabled(True)
        self._status_bar.showMessage("Error")
        QMessageBox.critical(self, "Error", msg)

    def closeEvent(self, event):
        self._stop_worker()
        self._plotter.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
