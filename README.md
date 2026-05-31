# TUI Tools

Colección de herramientas **TUI** (*Terminal User Interface*) para macOS, desarrolladas en Python con el framework [Textual](https://github.com/Textualize/textual).

---

## ¿Qué es una TUI?

Una **TUI** (*Terminal User Interface*) es una interfaz gráfica que funciona directamente dentro del terminal, sin necesidad de ventanas del sistema operativo ni entornos de escritorio. A diferencia de una CLI (línea de comandos pura), una TUI ofrece paneles, menús, tablas, formularios y navegación interactiva — todo renderizado en texto dentro de la propia consola.

Son especialmente útiles para tareas técnicas donde se quiere la potencia del terminal con la comodidad de una interfaz visual: administración de sistemas, monitorización, configuración de dispositivos, gestión de archivos, etc.

---

## Herramientas disponibles

### [SerialTUI](./SerialTUI/)

Terminal UI para conexiones seriales en macOS. Diseñada para trabajar con equipos de red (Cisco, HP, Juniper, Aruba) y cualquier dispositivo con puerto serie USB.

**Características principales:**
- Auto-detección de dispositivos `/dev/cu.*` con refresco en tiempo real
- Configuración visual de baud rate, data bits, paridad, stop bits y flow control
- Sesión serial integrada dentro de la propia TUI (sin saltar a otra ventana)
- Gestión de perfiles por dispositivo con carga automática al reconectar
- Control de Hardware Flow Control y Software Flow Control por perfil

```
cd SerialTUI
bash install.sh
python3 serial_tui.py
```

---

## Próximamente

Este repositorio irá creciendo con nuevas herramientas TUI orientadas a administración de sistemas, redes y automatización. Cada herramienta tendrá su propio directorio con instalador y documentación independiente.

---

## Requisitos generales

- macOS 12 Monterey o superior
- Python 3.10+
- [Homebrew](https://brew.sh)

---

## Licencia

Apache 2.0 — ver [LICENSE](./LICENSE)
