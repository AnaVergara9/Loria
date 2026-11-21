"""Cliente MCP del bot: lanza herramientas_mcp/servidor_mcp.py y le pide ejecutar herramientas.

La librería MCP es asíncrona y el agente corre en hilos normales, así que el cliente vive en un
hilo propio con su propio bucle de eventos. Desde fuera se usa con funciones normales:

    cliente.iniciar()                       # lanza el servidor y espera a que esté listo
    cliente.herramientas_para_modelo()      # lista de herramientas, sin los parámetros de contexto
    cliente.llamar("consultar_perfil", {}, contexto={"user_id": 123})
"""
import os
import sys
import json
import asyncio
import logging
import threading

from mcp import Client, StdioServerParameters

log = logging.getLogger("cliente_mcp")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # carpeta del proyecto

# Estos parámetros los llena el bot, nunca el modelo: se quitan de lo que el modelo ve.
PARAMETROS_DE_CONTEXTO = {"user_id", "ruta_audio", "transcripcion", "tiempo_max", "evitar_modelos"}


class ClienteMCP:
    def __init__(self, modulo: str = "herramientas_mcp.servidor_mcp"):
        self._parametros = StdioServerParameters(
            command=sys.executable,                 # el mismo Python del entorno virtual
            args=["-m", modulo],                   # se ejecuta como módulo desde la raíz del proyecto
            cwd=RAIZ,
            env=dict(os.environ),                   # el servidor necesita las claves y la configuración
        )
        self._bucle = None
        self._cliente = None
        self._listo = threading.Event()
        self._error = None
        self._cerrar = None
        self.herramientas = []                      # tal como las describe el servidor

    # ------------------------------------------------------------ arranque y cierre
    def iniciar(self, espera_max: float = 300):
        """Lanza el servidor MCP y espera a que responda (la primera vez carga wav2vec2, puede tardar)."""
        threading.Thread(target=self._hilo, name="cliente-mcp", daemon=True).start()
        if not self._listo.wait(espera_max):
            raise TimeoutError("El servidor MCP no arrancó a tiempo.")
        if self._error:
            raise RuntimeError(f"No se pudo iniciar el servidor MCP: {self._error}") from self._error
        log.info("MCP | conectado al servidor, %s herramientas: %s",
                 len(self.herramientas), ", ".join(h.name for h in self.herramientas))

    def _hilo(self):
        self._bucle = asyncio.new_event_loop()
        self._bucle.run_until_complete(self._conexion())

    async def _conexion(self):
        self._cerrar = asyncio.Event()
        try:
            async with Client(self._parametros) as cliente:
                self._cliente = cliente
                self.herramientas = (await cliente.list_tools()).tools
                self._listo.set()
                await self._cerrar.wait()           # la conexión queda abierta hasta cerrar()
        except Exception as e:
            self._error = e
            log.exception("MCP | se perdió la conexión con el servidor")
        finally:
            self._cliente = None
            self._listo.set()

    def cerrar(self):
        if self._bucle and self._cerrar:
            self._bucle.call_soon_threadsafe(self._cerrar.set)

    # ------------------------------------------------------------ uso
    def herramientas_para_modelo(self) -> list:
        """Convierte las herramientas MCP al formato neutro del agente (sirve para Gemini y Groq)."""
        neutras = []
        for h in self.herramientas:
            esquema = json.loads(json.dumps(h.input_schema))  # copia
            props = {k: _limpiar(v) for k, v in esquema.get("properties", {}).items()
                     if k not in PARAMETROS_DE_CONTEXTO}
            requeridos = [k for k in esquema.get("required", []) if k not in PARAMETROS_DE_CONTEXTO]
            parametros = {"type": "object", "properties": props}
            if requeridos:
                parametros["required"] = requeridos
            neutras.append({"nombre": h.name, "descripcion": h.description or "", "parametros": parametros})
        return neutras

    def llamar(self, nombre: str, args: dict, contexto: dict, espera_max: float = 60) -> dict:
        """Pide al servidor ejecutar una herramienta. Siempre devuelve un dict (con "error" si falló)."""
        if self._cliente is None:
            return {"error": "El servidor de herramientas no está disponible."}
        herramienta = next((h for h in self.herramientas if h.name == nombre), None)
        if herramienta is None:
            return {"error": f"Herramienta desconocida: {nombre}"}

        # Del modelo solo se aceptan los parámetros que la herramienta declara (a veces inventa otros)
        # y nunca los de contexto; esos los agrega el bot.
        acepta = set(herramienta.input_schema.get("properties", {}))
        completos = {k: v for k, v in args.items() if k in acepta and k not in PARAMETROS_DE_CONTEXTO}
        completos.update({k: v for k, v in contexto.items() if k in acepta and v is not None})

        futuro = asyncio.run_coroutine_threadsafe(
            self._cliente.call_tool(nombre, completos, read_timeout_seconds=espera_max), self._bucle)
        try:
            r = futuro.result(timeout=espera_max + 5)
        except Exception as e:
            log.warning("MCP | %s falló: %s", nombre, e)
            return {"error": f"La herramienta {nombre} no respondió."}
        if r.is_error:
            texto = " ".join(getattr(c, "text", "") for c in r.content)
            return {"error": texto or f"La herramienta {nombre} falló."}
        if isinstance(r.structured_content, dict):
            return r.structured_content
        texto = " ".join(getattr(c, "text", "") for c in r.content)
        try:
            return json.loads(texto)
        except ValueError:
            return {"resultado": texto}


def _limpiar(esquema: dict) -> dict:
    """Quita los "title" que agrega pydantic (no aportan nada al modelo)."""
    return {k: v for k, v in esquema.items() if k != "title"}


cliente = ClienteMCP()
