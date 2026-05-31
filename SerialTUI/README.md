# SerialTUI

Terminal UI para conexiones seriales en macOS. Auto-detecta dispositivos `/dev/cu.*`, permite configurar parámetros de conexión, gestiona perfiles guardados y muestra la sesión serial integrada dentro de la misma ventana de terminal.

Pensado especialmente para equipos de red (Cisco, HP, Juniper) y cualquier dispositivo con puerto serie USB.

---

## Captura

```
┌─────────────────────────────────────────────────────────────────┐
│  SerialTUI                                          12:34:56    │
├──────────────────────┬──────────────────────────────────────────┤
│ Dispositivos         │ Configuración                            │
│                      │ /dev/cu.usbserial-1234                   │
│ /dev/cu.usbserial-   │ Baud rate   [ 9600              ▼ ]     │
│   1234  CP2102       │ Data bits   [ 8                 ▼ ]     │
│                      │ Paridad     [ None              ▼ ]     │
│                      │ Stop bits   [ 1                 ▼ ]     │
│                      │ Nombre      [ Cisco Console        ]     │
│                      │ ⚠ Flow Control                          │
│                      │ ☐ HW Flow Control (RTS/CTS)             │
│                      │ ☐ SW Flow Control (XON/XOFF)            │
│                      │ [ ⚡ Conectar ] [ 💾 Guardar perfil ]   │
├──────────────────────┴──────────────────────────────────────────┤
│ Perfiles guardados                                              │
│ Nombre          Dispositivo           Baud   Frame  HFC  SFC   │
│ Cisco Console   /dev/cu.usbserial-..  9600   8N1    ✗    ✗    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Requisitos

| Herramienta | Versión mínima |
|-------------|---------------|
| macOS       | 12 Monterey+  |
| Python      | 3.10+         |
| Homebrew    | cualquiera    |

---

## Instalación rápida

Clona el repositorio y ejecuta el instalador:

```bash
git clone https://github.com/ramirfortes/TUI.git
cd TUI/SerialTUI
bash install.sh
```

El script `install.sh` realiza automáticamente los siguientes pasos:

1. Comprueba si **Homebrew** está instalado; si no, lo instala.
2. Comprueba si **minicom** está instalado; si no, lo instala via `brew install minicom`.
3. Comprueba si **Python 3** está disponible; si no, lo instala via `brew install python3`.
4. Instala las dependencias Python (`textual`, `pyserial`) con `pip`.

### Instalación manual (opcional)

Si prefieres instalar las dependencias tú mismo:

```bash
# Dependencias del sistema
brew install minicom

# Dependencias Python
pip3 install -r requirements.txt
```

---

## Uso

```bash
python3 serial_tui.py
```

### Flujo de trabajo

1. **Conecta** el cable de consola al Mac (USB-Serial, RJ45-Serial, etc.)
2. El dispositivo aparece automáticamente en la lista izquierda (refresco cada 2 s)
3. Selecciona el dispositivo con el ratón o teclado
4. Ajusta los parámetros de conexión en el panel derecho
5. Pulsa **⚡ Conectar** — la sesión serial se abre dentro de la misma ventana
6. Escribe comandos en la barra inferior y pulsa `Enter` para enviarlos
7. Pulsa **✕ Desconectar** o `Ctrl+D` para cerrar la sesión
8. Pulsa **💾 Guardar perfil** para recordar la configuración del dispositivo

### Teclado

| Tecla     | Acción                         |
|-----------|-------------------------------|
| `R`       | Forzar refresco de dispositivos |
| `Ctrl+D`  | Desconectar sesión activa      |
| `Ctrl+Q`  | Salir de la aplicación         |
| `Enter`   | Enviar texto (en barra de envío) |

---

## Flow Control — nota importante para equipos de red

La mayoría de equipos de red (Cisco, HP, Juniper, Aruba…) requieren **Hardware Flow Control desactivado** para que la entrada de texto funcione. SerialTUI lo deja desactivado por defecto.

| Opción                        | Por defecto | Cuándo activar                              |
|-------------------------------|-------------|---------------------------------------------|
| HW Flow Control (RTS/CTS)     | ☐ OFF       | Solo si el dispositivo lo requiere          |
| SW Flow Control (XON/XOFF)    | ☐ OFF       | Solo si el dispositivo lo requiere          |

El estado de cada opción se guarda por perfil.

---

## Perfiles

Los perfiles se guardan en `~/.config/serial-tui/profiles.json`:

```json
{
  "/dev/cu.usbserial-1234": {
    "name": "Cisco Console",
    "baud": "9600",
    "bits": "8",
    "parity": "N",
    "stop": "1",
    "hw_flow": false,
    "sw_flow": false
  },
  "last_used": "/dev/cu.usbserial-1234"
}
```

Al arrancar la app, el último dispositivo usado se selecciona y carga automáticamente.

---

## Estructura del proyecto

```
SerialTUI/
├── serial_tui.py      # Aplicación principal
├── requirements.txt   # Dependencias Python
├── install.sh         # Instalador automático
└── README.md          # Este archivo
```

---

## Dependencias

| Paquete    | Uso                                      |
|------------|------------------------------------------|
| `textual`  | Framework TUI (interfaz de terminal)     |
| `pyserial` | Comunicación con el puerto serie         |

---

## Licencia

Apache 2.0 — ver [LICENSE](../LICENSE)
