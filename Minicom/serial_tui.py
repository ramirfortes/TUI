#!/usr/bin/env python3
"""Serial TUI — terminal serial integrado con auto-detección de /dev/cu.*"""

import glob
import json
import subprocess
import threading
from pathlib import Path

import serial
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Select,
    Static,
)

# ── Constantes ────────────────────────────────────────────────────────────────

PROFILES_PATH = Path.home() / ".config" / "serial-tui" / "profiles.json"
IGNORED_DEVICES = ["Bluetooth", "debug-console", "wlan-debug"]

BAUD_RATES = [
    ("300", "300"), ("1200", "1200"), ("2400", "2400"), ("4800", "4800"),
    ("9600", "9600"), ("19200", "19200"), ("38400", "38400"), ("57600", "57600"),
    ("115200", "115200 ✦"), ("230400", "230400"), ("460800", "460800"), ("921600", "921600"),
]
PARITY_OPTIONS = [("N", "None"), ("E", "Even"), ("O", "Odd")]
DATA_BITS      = [("7", "7"), ("8", "8")]
STOP_BITS      = [("1", "1"), ("2", "2")]

PARITY_MAP = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN, "O": serial.PARITY_ODD}
BITS_MAP   = {"7": serial.SEVENBITS,   "8": serial.EIGHTBITS}
STOP_MAP   = {"1": serial.STOPBITS_ONE, "2": serial.STOPBITS_TWO}


# ── Helpers ───────────────────────────────────────────────────────────────────

def detect_devices() -> list[tuple[str, str]]:
    all_devs = sorted(glob.glob("/dev/cu.*"))
    devs = [d for d in all_devs if not any(x in d for x in IGNORED_DEVICES)]
    usb_info = _get_usb_info()
    return [(d, f"{d}  {usb_info.get(Path(d).name, '')}".strip()) for d in devs]


def _get_usb_info() -> dict[str, str]:
    try:
        raw = subprocess.check_output(
            ["system_profiler", "SPUSBDataType", "-json"], timeout=3,
            stderr=subprocess.DEVNULL,
        )
        data = json.loads(raw)
    except Exception:
        return {}
    out: dict[str, str] = {}
    _walk_usb(data, out)
    return out


def _walk_usb(node, out: dict):
    if isinstance(node, list):
        for item in node:
            _walk_usb(item, out)
    elif isinstance(node, dict):
        bsd  = node.get("bsd_name", "")
        prod = node.get("_name", "") or node.get("manufacturer", "")
        if bsd and prod:
            out[bsd] = prod
        for v in node.values():
            if isinstance(v, (dict, list)):
                _walk_usb(v, out)


def load_profiles() -> dict:
    if PROFILES_PATH.exists():
        try:
            return json.loads(PROFILES_PATH.read_text())
        except Exception:
            pass
    return {}


def save_profiles(profiles: dict):
    PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILES_PATH.write_text(json.dumps(profiles, indent=2))


# ── Widget personalizado ──────────────────────────────────────────────────────

class DeviceList(ListView):
    pass


# ── App principal ─────────────────────────────────────────────────────────────

class SerialTUI(App):

    CSS = """
    /* ── Estructura general ── */
    Screen {
        layout: vertical;
        background: $surface;
    }

    /* Zona superior: dispositivos + configuración */
    #top-split {
        height: 3fr;
        min-height: 20;
    }

    #left {
        width: 38%;
        min-width: 24;
        border: round $primary;
        padding: 0 1;
    }

    #right {
        width: 62%;
        border: round $accent;
        padding: 1 2;
        overflow-y: auto;
    }

    /* Zona inferior: perfiles o terminal */
    #bottom-area {
        height: 2fr;
        min-height: 10;
        margin-top: 1;
    }

    #profiles-panel {
        height: 1fr;
        border: round $warning;
        padding: 0 1;
    }

    #terminal-panel {
        height: 1fr;
        border: round $success;
        padding: 0 1;
        display: none;
    }

    #terminal-panel.connected {
        display: block;
    }

    /* Fila de envío (visible solo al conectar) */
    #send-row {
        height: 3;
        margin-top: 1;
        display: none;
    }

    #send-row.connected {
        display: block;
    }

    #send-input {
        width: 1fr;
        margin-right: 1;
    }

    #btn-disconnect {
        width: 20;
    }

    /* ── Secciones del panel derecho ── */
    .section-title {
        text-style: bold;
        color: $text-muted;
        margin-bottom: 1;
    }

    .field-row {
        height: 3;
        margin-bottom: 1;
    }

    .field-label {
        width: 14;
        padding-top: 1;
    }

    Select { width: 1fr; }
    Input  { width: 1fr; }

    DeviceList { height: 1fr; }

    #device-title { margin-bottom: 1; }

    #selected-device {
        color: $success;
        text-style: bold;
        height: 1;
        margin-bottom: 1;
    }

    /* Flow control */
    #flow-section {
        border: tall $warning 40%;
        padding: 0 1;
        margin-top: 1;
        margin-bottom: 1;
        height: auto;
    }

    .flow-title {
        color: $warning;
        text-style: bold;
        margin-bottom: 1;
    }

    .flow-row {
        height: 3;
    }

    .flow-hint {
        color: $text-muted;
        text-style: italic;
        padding-top: 1;
        margin-left: 1;
        width: 1fr;
    }

    /* Botones */
    #btn-row {
        height: 3;
        margin-top: 1;
    }

    #btn-connect { width: 1fr; margin-right: 1; }
    #btn-save    { width: 1fr; }

    /* Tabla de perfiles */
    #profiles-table { height: 1fr; }

    /* Terminal */
    #terminal-log {
        height: 1fr;
        background: $surface-darken-2;
    }

    /* Estado de conexión */
    #conn-status {
        height: 1;
        color: $success;
        text-style: bold;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit",            "Salir"),
        Binding("r",      "refresh_devices", "Actualizar"),
        Binding("ctrl+d", "disconnect",      "Desconectar", show=False),
    ]

    selected_device: reactive[str] = reactive("")

    def __init__(self):
        super().__init__()
        self._profiles  = load_profiles()
        self._devices:  list[tuple[str, str]] = []
        self._serial:   serial.Serial | None  = None
        self._reader:   threading.Thread | None = None
        self._stop_evt: threading.Event = threading.Event()

    # ── Composición ──────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical():
            # Zona superior
            with Horizontal(id="top-split"):

                # Panel izquierdo — dispositivos
                with Vertical(id="left"):
                    yield Static("Dispositivos seriales", classes="section-title", id="device-title")
                    yield DeviceList(id="device-list")

                # Panel derecho — configuración
                with Vertical(id="right"):
                    yield Static("Configuración", classes="section-title")
                    yield Static("Sin dispositivo seleccionado", id="selected-device")

                    with Horizontal(classes="field-row"):
                        yield Label("Baud rate",  classes="field-label")
                        yield Select([(label, val) for val, label in BAUD_RATES], value="115200", id="baud-select")

                    with Horizontal(classes="field-row"):
                        yield Label("Data bits",  classes="field-label")
                        yield Select([(label, val) for val, label in DATA_BITS],  value="8",      id="bits-select")

                    with Horizontal(classes="field-row"):
                        yield Label("Paridad",    classes="field-label")
                        yield Select([(label, val) for val, label in PARITY_OPTIONS], value="N", id="parity-select")

                    with Horizontal(classes="field-row"):
                        yield Label("Stop bits",  classes="field-label")
                        yield Select([(label, val) for val, label in STOP_BITS],  value="1",      id="stop-select")

                    with Horizontal(classes="field-row"):
                        yield Label("Nombre",     classes="field-label")
                        yield Input(placeholder="ej: Cisco Console", id="profile-name")

                    with Vertical(id="flow-section"):
                        yield Static("⚠ Flow Control", classes="flow-title")
                        with Horizontal(classes="flow-row"):
                            yield Checkbox("HW Flow Control (RTS/CTS)", value=False, id="hw-flow")
                            yield Static("Desactivar para Cisco / HP / Juniper", classes="flow-hint")
                        with Horizontal(classes="flow-row"):
                            yield Checkbox("SW Flow Control (XON/XOFF)", value=False, id="sw-flow")
                            yield Static("Activar solo si el equipo lo requiere",  classes="flow-hint")

                    with Horizontal(id="btn-row"):
                        yield Button("⚡ Conectar",      id="btn-connect", variant="success")
                        yield Button("💾 Guardar perfil", id="btn-save",    variant="primary")

            # Zona inferior
            with Vertical(id="bottom-area"):

                # Perfiles (visible cuando desconectado)
                with Vertical(id="profiles-panel"):
                    yield Static("Perfiles guardados  [dim](clic para cargar)[/dim]", classes="section-title")
                    yield DataTable(id="profiles-table", cursor_type="row")

                # Terminal (visible cuando conectado)
                with Vertical(id="terminal-panel"):
                    yield Static("", id="conn-status")
                    yield RichLog(id="terminal-log", highlight=False, markup=False, wrap=True)

            # Fila de envío
            with Horizontal(id="send-row"):
                yield Input(placeholder="Escribe y pulsa Enter para enviar…", id="send-input")
                yield Button("✕ Desconectar", id="btn-disconnect", variant="error")

        yield Footer()

    # ── Montaje ───────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._setup_profiles_table()
        self._load_device_list()
        self.set_interval(2.0, self._auto_refresh)

    # ── Dispositivos ──────────────────────────────────────────────────────────

    def _load_device_list(self):
        self._devices = detect_devices()
        lv = self.query_one("#device-list", DeviceList)
        lv.clear()
        if not self._devices:
            lv.append(ListItem(Label("  (sin dispositivos)")))
        else:
            for path, label in self._devices:
                lv.append(ListItem(Label(f"  {label}"), id=f"dev-{path.replace('/', '_')}"))
        last = self._profiles.get("last_used", "")
        if last and any(d[0] == last for d in self._devices):
            self.selected_device = last
            self._apply_profile(last)

    def _auto_refresh(self):
        if self._serial and self._serial.is_open:
            return
        new = detect_devices()
        if new != self._devices:
            self._load_device_list()

    def action_refresh_devices(self):
        self._load_device_list()
        self.notify("Dispositivos actualizados")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and idx < len(self._devices):
            self.selected_device = self._devices[idx][0]
            self.query_one("#selected-device", Static).update(
                f"[bold]{self.selected_device}[/bold]"
            )
            self._apply_profile(self.selected_device)

    # ── Perfiles ──────────────────────────────────────────────────────────────

    def _setup_profiles_table(self):
        table = self.query_one("#profiles-table", DataTable)
        table.add_columns("Nombre", "Dispositivo", "Baud", "Frame", "HFC", "SFC")
        self._refresh_profiles_table(table)

    def _refresh_profiles_table(self, table: DataTable | None = None):
        if table is None:
            table = self.query_one("#profiles-table", DataTable)
        table.clear()
        for dev, cfg in self._profiles.items():
            if dev == "last_used":
                continue
            table.add_row(
                cfg.get("name", dev),
                dev,
                str(cfg.get("baud", "115200")),
                f"{cfg.get('bits','8')}{cfg.get('parity','N')}{cfg.get('stop','1')}",
                "✓" if cfg.get("hw_flow") else "✗",
                "✓" if cfg.get("sw_flow") else "✗",
            )

    def _apply_profile(self, device: str):
        cfg = self._profiles.get(device, {})
        if not cfg:
            return
        try:
            self.query_one("#baud-select",    Select).value = str(cfg.get("baud",   "115200"))
            self.query_one("#bits-select",    Select).value = str(cfg.get("bits",   "8"))
            self.query_one("#parity-select",  Select).value = str(cfg.get("parity", "N"))
            self.query_one("#stop-select",    Select).value = str(cfg.get("stop",   "1"))
            self.query_one("#profile-name",   Input).value  = cfg.get("name", "")
            self.query_one("#hw-flow",     Checkbox).value  = cfg.get("hw_flow", False)
            self.query_one("#sw-flow",     Checkbox).value  = cfg.get("sw_flow", False)
        except Exception:
            pass

    def _get_current_config(self) -> dict:
        return {
            "baud":    str(self.query_one("#baud-select",   Select).value   or "115200"),
            "bits":    str(self.query_one("#bits-select",   Select).value   or "8"),
            "parity":  str(self.query_one("#parity-select", Select).value   or "N"),
            "stop":    str(self.query_one("#stop-select",   Select).value   or "1"),
            "name":    self.query_one("#profile-name", Input).value.strip(),
            "hw_flow": self.query_one("#hw-flow", Checkbox).value,
            "sw_flow": self.query_one("#sw-flow", Checkbox).value,
        }

    def _save_current_profile(self):
        if not self.selected_device:
            self.notify("Selecciona un dispositivo primero", severity="warning")
            return
        cfg = self._get_current_config()
        self._profiles[self.selected_device] = {
            **cfg,
            "name": cfg["name"] or Path(self.selected_device).name,
        }
        save_profiles(self._profiles)
        self._refresh_profiles_table()
        self.notify(f"Perfil guardado: {cfg['name'] or self.selected_device}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table    = self.query_one("#profiles-table", DataTable)
        row_data = table.get_row(event.row_key)
        if not row_data:
            return
        device = str(row_data[1])
        if device in self._profiles:
            self.selected_device = device
            self.query_one("#selected-device", Static).update(f"[bold]{device}[/bold]")
            self._apply_profile(device)
            self.notify(f"Perfil cargado: {row_data[0]}")

    # ── Botones ───────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-connect":    self._do_connect()
            case "btn-save":       self._save_current_profile()
            case "btn-disconnect": self.action_disconnect()

    # ── Conexión serial ───────────────────────────────────────────────────────

    def _do_connect(self):
        if not self.selected_device:
            self.notify("Selecciona un dispositivo primero", severity="warning")
            return

        cfg = self._get_current_config()

        try:
            self._serial = serial.Serial(
                port     = self.selected_device,
                baudrate = int(cfg["baud"]),
                bytesize = BITS_MAP.get(cfg["bits"],   serial.EIGHTBITS),
                parity   = PARITY_MAP.get(cfg["parity"], serial.PARITY_NONE),
                stopbits = STOP_MAP.get(cfg["stop"],   serial.STOPBITS_ONE),
                xonxoff  = cfg["sw_flow"],
                rtscts   = cfg["hw_flow"],
                timeout  = 0.1,
            )
        except serial.SerialException as e:
            self.notify(f"Error al abrir puerto: {e}", severity="error", timeout=8)
            return

        # Guardar last_used
        self._profiles["last_used"] = self.selected_device
        save_profiles(self._profiles)

        # Cambiar vista a terminal
        self.query_one("#profiles-panel").display = False
        self.query_one("#terminal-panel").add_class("connected")
        self.query_one("#send-row").add_class("connected")
        self.query_one("#btn-connect", Button).disabled = True

        frame = f"{cfg['bits']}{cfg['parity']}{cfg['stop']}"
        hfc   = "HFC:ON" if cfg["hw_flow"] else "HFC:OFF"
        sfc   = "SFC:ON" if cfg["sw_flow"] else "SFC:OFF"
        self.query_one("#conn-status", Static).update(
            f"[bold green]● CONECTADO[/bold green]  "
            f"{self.selected_device}  {cfg['baud']} baud  {frame}  {hfc}  {sfc}"
        )

        log = self.query_one("#terminal-log", RichLog)
        log.clear()
        log.write(Text(
            f"─── Sesión iniciada: {self.selected_device} @ {cfg['baud']} baud ───\n",
            style="dim"
        ))

        self.query_one("#send-input", Input).focus()

        # Hilo lector
        self._stop_evt.clear()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _read_loop(self):
        log = self.query_one("#terminal-log", RichLog)
        buf = b""
        while not self._stop_evt.is_set():
            try:
                chunk = self._serial.read(256)
            except Exception:
                break
            if not chunk:
                continue
            buf += chunk
            # Procesar líneas completas; dejar resto en buffer
            text = buf.decode("utf-8", errors="replace")
            # Normalizar \r\n → \n
            text = text.replace("\r\n", "\n").replace("\r", "\n")
            if "\n" in text:
                lines = text.split("\n")
                buf = lines[-1].encode("utf-8")
                output = "\n".join(lines[:-1])
                self.call_from_thread(log.write, Text(output))
            elif len(buf) > 4096:
                self.call_from_thread(log.write, Text(buf.decode("utf-8", errors="replace")))
                buf = b""

    def action_disconnect(self):
        if not self._serial:
            return
        self._stop_evt.set()
        if self._reader:
            self._reader.join(timeout=1.0)
            self._reader = None
        try:
            self._serial.close()
        except Exception:
            pass
        self._serial = None

        log = self.query_one("#terminal-log", RichLog)
        log.write(Text("\n─── Sesión cerrada ───\n", style="dim"))

        self.query_one("#terminal-panel").remove_class("connected")
        self.query_one("#send-row").remove_class("connected")
        self.query_one("#profiles-panel").display = True
        self.query_one("#btn-connect", Button).disabled = False
        self.query_one("#conn-status", Static).update("")
        self.notify("Desconectado")

    # ── Envío de datos ────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "send-input":
            return
        text = event.value
        if self._serial and self._serial.is_open:
            try:
                # Equipos de red esperan \r como final de línea
                self._serial.write((text + "\r\n").encode("utf-8"))
                log = self.query_one("#terminal-log", RichLog)
                log.write(Text(f"» {text}", style="bold cyan"))
            except serial.SerialException as e:
                self.notify(f"Error al enviar: {e}", severity="error")
        event.input.value = ""

    # ── Salida limpia ─────────────────────────────────────────────────────────

    def action_quit(self):
        if self._serial:
            self.action_disconnect()
        self.exit()


if __name__ == "__main__":
    SerialTUI().run()
