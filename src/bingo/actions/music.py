"""
Ação para automação de reprodução de música no YouTube Music e transmissão para Chromecast via Vivaldi.
Suporta conexões seguras localhost via Chrome DevTools Protocol (CDP) e validação real do dispositivo.
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.request
from typing import Any, Optional

from bingo.logger import error, info, success, warning
from bingo.protocol import MessageType, create_dict
from bingo.state import state

DEFAULT_PLAYLIST_URL = os.getenv("BINGO_PLAYLIST_URL", "")
DEFAULT_DEVICE_NAME = "TutuLola"
DEFAULT_CDP_PORT = 9222
DEFAULT_CDP_HOST = "127.0.0.1"

# App IDs do Google Cast para identificação e validação estrita de sessão
YTM_APP_IDS = {"2DB7CC49", "233637DE"}  # 2DB7CC49: YouTube Music, 233637DE: YouTube
MIRRORING_APP_ID = "0F5096E8"  # Chrome Mirroring (espelhamento de aba)
BACKDROP_APP_ID = "E8C28D3C"   # Backdrop / Tela de descanso
NETFLIX_APP_ID = "CA5E8412"    # Netflix


def build_ytm_url(playlist_url: str = DEFAULT_PLAYLIST_URL, shuffle: bool = True) -> str:
    """
    Converte uma URL de playlist do YouTube Music no formato direto de reprodução /watch
    com o parâmetro shuffle=1 para iniciar imediatamente no modo aleatório.
    """
    if not playlist_url:
        return ""

    match = re.search(r"list=([a-zA-Z0-9_-]+)", playlist_url)
    if not match:
        return playlist_url

    playlist_id = match.group(1)
    if shuffle:
        return f"https://music.youtube.com/watch?list={playlist_id}&shuffle=1"
    return f"https://music.youtube.com/watch?list={playlist_id}"


def is_vivaldi_running() -> bool:
    """Verifica se há algum processo do Vivaldi em execução no sistema."""
    try:
        output = subprocess.check_output(["pgrep", "-f", "vivaldi-bin"], stderr=subprocess.DEVNULL)
        return bool(output.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def is_cdp_available(host: str = DEFAULT_CDP_HOST, port: int = DEFAULT_CDP_PORT) -> bool:
    """Verifica se a porta de depuração remota do Chromium (CDP) está respondendo em localhost."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except OSError:
        return False
    finally:
        sock.close()


def find_chromecast_device(
    target_name: Optional[str] = None, timeout: float = 3.5
) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
    """
    Descobre dispositivos Chromecast na rede local usando pychromecast.
    Retorna (dispositivo_alvo, lista_todos_dispositivos).
    """
    try:
        import pychromecast

        chromecasts, browser = pychromecast.get_chromecasts(timeout=timeout)
        devices = []
        target = None

        for cc in chromecasts:
            device_info = {
                "name": cc.name,
                "host": cc.cast_info.host,
                "port": cc.cast_info.port,
                "model": cc.model_name,
                "cast_type": cc.cast_type,
            }
            devices.append(device_info)

            if target_name and target_name.lower() in cc.name.lower():
                target = device_info
            elif target is None:
                target = device_info

        pychromecast.discovery.stop_discovery(browser)
        return target, devices
    except Exception as e:
        warning(f"Erro ao buscar Chromecasts via PyChromecast: {e}")
        return None, []


def verify_chromecast_playback(
    target_name: str = DEFAULT_DEVICE_NAME,
    host: Optional[str] = None,
    port: int = 8009,
    timeout: float = 10.0,
    stability_interval: float = 3.0,
    require_native: bool = True,
    expected_app_ids: Optional[set[str]] = None,
) -> dict[str, Any]:
    """
    Verifica o estado real do Chromecast na rede usando PyChromecast com validação rigorosa.
    Não simula sucesso nem considera PlaybackStatus local como prova.

    Critérios de validação:
    1. Rejeição de aplicativos alheios: Aplicativos como Netflix ('CA5E8412'), Spotify, etc.,
       nunca são reportados como sucesso de transmissão de música.
    2. Rejeição de espelhamento: '0F5096E8' (Chrome Mirroring) é rejeitado se require_native for True.
    3. Receptor correto: O app_id deve corresponder ao YouTube Music ('2DB7CC49' ou '233637DE').
    4. Persistência real: A sessão deve permanecer ativa após um intervalo de estabilidade (~3s),
       rejeitando sessões efêmeras que caem imediatamente após a desconexão do socket CDP.
    5. Standby: Se o dispositivo permanecer na tela de descanso (Backdrop: 'E8C28D3C'), retorna confirmed=False.
    """
    try:
        import pychromecast

        valid_apps = expected_app_ids or YTM_APP_IDS
        start_time = time.time()
        effective_stability = min(stability_interval, max(0.05, timeout * 0.3))

        while time.time() - start_time < timeout:
            app_id = None
            display_name = "Desconhecido"
            is_stand_by = True
            device_actual_name = target_name
            device_actual_host = host
            device_actual_port = port

            try:
                if host:
                    cc = pychromecast.get_chromecast_from_host((host, port, None, "Chromecast", target_name))
                    cc.wait()
                    app_id = cc.app_id
                    display_name = cc.status.display_name if cc.status else "Desconhecido"
                    is_stand_by = cc.status.is_stand_by if cc.status else True
                    cc.disconnect()
                else:
                    chromecasts, browser = pychromecast.get_chromecasts(timeout=1.5)
                    cc = next((c for c in chromecasts if target_name.lower() in c.name.lower()), None)
                    if cc:
                        cc.wait()
                        app_id = cc.app_id
                        display_name = cc.status.display_name if cc.status else "Desconhecido"
                        is_stand_by = cc.status.is_stand_by if cc.status else True
                        device_actual_name = cc.name
                        device_actual_host = cc.cast_info.host
                        device_actual_port = cc.cast_info.port
                        cc.disconnect()
                    pychromecast.discovery.stop_discovery(browser)
            except Exception:
                time.sleep(1.0)
                continue

            # Se ainda estiver em standby / Backdrop, aguarda o próximo ciclo
            if not app_id or app_id == BACKDROP_APP_ID:
                time.sleep(1.0)
                continue

            # Se for espelhamento de aba/tela (Chrome Mirroring)
            if app_id == MIRRORING_APP_ID:
                if require_native:
                    return {
                        "confirmed": False,
                        "is_mirroring": True,
                        "is_unrelated_app": False,
                        "app_id": app_id,
                        "display_name": display_name,
                        "device": device_actual_name,
                        "host": device_actual_host,
                        "port": device_actual_port,
                        "session_type": "mirroring",
                        "reason": "mirroring_rejected",
                        "message": (
                            f"Espelhamento de tela/aba detectado ({app_id} - {display_name}). "
                            "A transmissão nativa do YouTube Music foi solicitada e o espelhamento foi rejeitado "
                            "para evitar falso positivo."
                        ),
                    }

            # Se for um aplicativo alheio (ex: Netflix 'CA5E8412', Spotify, etc.)
            if app_id not in valid_apps:
                return {
                    "confirmed": False,
                    "is_mirroring": False,
                    "is_unrelated_app": True,
                    "app_id": app_id,
                    "display_name": display_name,
                    "device": device_actual_name,
                    "host": device_actual_host,
                    "port": device_actual_port,
                    "session_type": "unrelated_app",
                    "reason": "unrelated_app_busy",
                    "message": (
                        f"O Chromecast '{device_actual_name}' está atualmente executando outro aplicativo "
                        f"({display_name} [{app_id}]). A transmissão do YouTube Music não foi aceita nem "
                        "iniciada no dispositivo para evitar interromper a sessão ativa."
                    ),
                }

            # Sessão correta detectada (app_id in valid_apps, ex: '2DB7CC49' YouTube Music).
            # Verifica persistência após intervalo de estabilidade para evitar falso positivo efêmero.
            if effective_stability > 0:
                time.sleep(effective_stability)
                try:
                    if device_actual_host:
                        cc2 = pychromecast.get_chromecast_from_host(
                            (device_actual_host, device_actual_port, None, "Chromecast", device_actual_name)
                        )
                        cc2.wait()
                        app_id_after = cc2.app_id
                        display_name_after = cc2.status.display_name if cc2.status else "Desconhecido"
                        is_stand_by_after = cc2.status.is_stand_by if cc2.status else True
                        cc2.disconnect()
                    else:
                        chromecasts2, browser2 = pychromecast.get_chromecasts(timeout=1.5)
                        cc2 = next((c for c in chromecasts2 if device_actual_name.lower() in c.name.lower()), None)
                        if cc2:
                            cc2.wait()
                            app_id_after = cc2.app_id
                            display_name_after = cc2.status.display_name if cc2.status else "Desconhecido"
                            is_stand_by_after = cc2.status.is_stand_by if cc2.status else True
                            cc2.disconnect()
                        else:
                            app_id_after = None
                        pychromecast.discovery.stop_discovery(browser2)

                    if app_id_after != app_id or app_id_after in {BACKDROP_APP_ID, None}:
                        return {
                            "confirmed": False,
                            "is_mirroring": False,
                            "is_unrelated_app": False,
                            "app_id": app_id_after,
                            "display_name": display_name_after,
                            "device": device_actual_name,
                            "host": device_actual_host,
                            "port": device_actual_port,
                            "session_type": "unknown",
                            "reason": "session_dropped_immediately",
                            "message": (
                                f"A sessão Cast '{app_id}' ({display_name}) foi iniciada, mas encerrou "
                                f"imediatamente após {effective_stability:.1f}s e retornou para '{app_id_after}'. "
                                "Falso positivo evitado."
                            ),
                        }

                    app_id = app_id_after
                    display_name = display_name_after
                    is_stand_by = is_stand_by_after
                except Exception:
                    pass

            return {
                "confirmed": True,
                "is_mirroring": False,
                "is_unrelated_app": False,
                "app_id": app_id,
                "display_name": display_name,
                "session_type": "native_ytm" if app_id in YTM_APP_IDS else "native_cast",
                "is_stand_by": is_stand_by,
                "device": device_actual_name,
                "host": device_actual_host,
                "port": device_actual_port,
                "persistent": True,
                "reason": "ytm_confirmed",
            }

        return {
            "confirmed": False,
            "is_mirroring": False,
            "is_unrelated_app": False,
            "app_id": BACKDROP_APP_ID,
            "display_name": "Backdrop",
            "is_stand_by": True,
            "device": target_name,
            "host": host,
            "port": port,
            "reason": "standby_timeout",
            "message": (
                f"O Chromecast '{target_name}' permaneceu na tela de descanso (Backdrop). "
                "A transmissão não foi estabelecida na TV."
            ),
        }
    except Exception as e:
        return {
            "confirmed": False,
            "is_mirroring": False,
            "is_unrelated_app": False,
            "error": str(e),
            "device": target_name,
            "reason": "exception",
            "message": f"Falha ao validar status no Chromecast: {e}",
        }




def launch_vivaldi_with_cdp(
    url: Optional[str] = None,
    port: int = DEFAULT_CDP_PORT,
    host: str = DEFAULT_CDP_HOST,
) -> bool:
    """
    Inicia uma nova instância do Vivaldi com a porta de depuração remota restrita a localhost (127.0.0.1).
    Preserva cookies, perfil existente e sessão autenticada do usuário.
    """
    v_bin = shutil.which("vivaldi") or shutil.which("vivaldi-stable") or "vivaldi"
    args = [
        v_bin,
        f"--remote-debugging-port={port}",
        f"--remote-debugging-address={host}",
    ]
    if url:
        args.append(url)

    subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Aguarda até 5 segundos para a porta responder
    for _ in range(10):
        time.sleep(0.5)
        if is_cdp_available(host=host, port=port):
            return True
    return False


def restart_vivaldi_with_cdp(
    port: int = DEFAULT_CDP_PORT,
    host: str = DEFAULT_CDP_HOST,
) -> bool:
    """
    Encerra graciosamente a instância em execução do Vivaldi e a reabre com suporte a CDP.
    Exige ação explícita do usuário para evitar fechamentos inesperados.
    """
    info("Encerrando graciosamente o Vivaldi para habilitar a porta CDP...")
    try:
        subprocess.run(["pkill", "-TERM", "-f", "vivaldi-bin"], check=False)
        for _ in range(8):
            time.sleep(0.5)
            if not is_vivaldi_running():
                break
        if is_vivaldi_running():
            subprocess.run(["pkill", "-KILL", "-f", "vivaldi-bin"], check=False)
            time.sleep(1.0)
    except Exception as e:
        warning(f"Aviso ao encerrar Vivaldi: {e}")

    return launch_vivaldi_with_cdp(port=port, host=host)


def validate_prerequisites(
    target_device: Optional[str] = None, timeout: float = 3.5
) -> dict[str, Any]:
    """
    Valida os pré-requisitos necessários para a automação:
    - Vivaldi instalado
    - Instância do Vivaldi em execução
    - Porta CDP aberta
    - Chromecast na rede local
    """
    v_path = shutil.which("vivaldi") or shutil.which("vivaldi-stable")
    v_installed = v_path is not None
    v_running = is_vivaldi_running()
    cdp_open = is_cdp_available()

    target, all_devices = find_chromecast_device(target_device or DEFAULT_DEVICE_NAME, timeout=timeout)

    ok = v_installed and (target is not None)

    messages = []
    if not v_installed:
        messages.append("Vivaldi não encontrado no PATH.")
    if not target:
        messages.append(
            f"Chromecast '{target_device or DEFAULT_DEVICE_NAME}' não encontrado na rede local. "
            "Verifique se o dispositivo está ligado e na mesma rede Wi-Fi."
        )

    return {
        "ok": ok,
        "vivaldi_installed": v_installed,
        "vivaldi_path": v_path,
        "vivaldi_running": v_running,
        "cdp_available": cdp_open,
        "chromecast_found": target is not None,
        "target_device": target,
        "all_devices": all_devices,
        "issues": messages,
    }


def send_mpris_play() -> bool:
    """Envia sinal MPRIS Play para o Vivaldi via DBus."""
    try:
        out = subprocess.check_output(
            [
                "dbus-send",
                "--session",
                "--dest=org.freedesktop.DBus",
                "--type=method_call",
                "--print-reply",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus.ListNames",
            ],
            stderr=subprocess.DEVNULL,
        ).decode()

        services = [
            line.split('"')[1]
            for line in out.splitlines()
            if "org.mpris.MediaPlayer2.vivaldi" in line
        ]

        if not services:
            return False

        for s in services:
            subprocess.run(
                [
                    "dbus-send",
                    "--session",
                    f"--dest={s}",
                    "--type=method_call",
                    "/org/mpris/MediaPlayer2",
                    "org.mpris.MediaPlayer2.Player.Play",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        return True
    except Exception:
        return False


def open_in_vivaldi(url: str) -> bool:
    """
    Abre ou reutiliza a instância do Vivaldi de forma segura via IPC nativo do Chromium.
    Preserva cookies, perfil existente e sessão autenticada.
    """
    v_bin = shutil.which("vivaldi") or shutil.which("vivaldi-stable") or "vivaldi"
    subprocess.Popen(
        [v_bin, url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return True


class CDPClient:
    """
    Cliente WebSocket assíncrono leve para comunicação direta com o Chrome DevTools Protocol (CDP).
    Permite controle de abas individuais sem interferência nas janelas de extensão interna do Vivaldi.
    """

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._msg_id = 0

    async def __aenter__(self):
        import websockets

        self.ws = await websockets.connect(self.ws_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.ws:
            await self.ws.close()

    async def send(self, method: str, params: Optional[dict[str, Any]] = None, timeout: float = 3.0) -> dict[str, Any]:
        """Envia um comando CDP e aguarda a resposta correspondente pelo ID da mensagem."""
        self._msg_id += 1
        req_id = self._msg_id
        await self.ws.send(json.dumps({"id": req_id, "method": method, "params": params or {}}))

        start = time.time()
        while time.time() - start < timeout:
            try:
                raw = await asyncio.wait_for(self.ws.recv(), timeout=0.8)
                data = json.loads(raw)
                if data.get("id") == req_id:
                    return data
            except asyncio.TimeoutError:
                pass
        return {}


async def _async_play_via_cdp(
    url: str,
    device_name: str,
    device_host: Optional[str] = None,
    device_port: int = 8009,
    cdp_port: int = DEFAULT_CDP_PORT,
    cdp_host: str = DEFAULT_CDP_HOST,
) -> dict[str, Any]:
    """Rotina assíncrona para orquestrar a sessão Cast nativa via CDP e validar a transmissão."""
    import websockets

    # 1. Abre a URL no Vivaldi via IPC nativo para garantir que a aba seja criada, focada e ativa com áudio
    open_in_vivaldi(url)
    await asyncio.sleep(2.0)

    # 2. Conecta ao endpoint CDP do Vivaldi
    try:
        req = urllib.request.Request(f"http://{cdp_host}:{cdp_port}/json/list")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            pages = json.loads(resp.read().decode())
    except Exception as e:
        return {
            "success": False,
            "mode": "cdp_failed",
            "message": f"Não foi possível conectar ao endpoint CDP ({cdp_host}:{cdp_port}): {e}",
            "local_playback": {"status": "error"},
            "cast_stream": {"status": "failed", "error": str(e)},
        }

    # Seleciona preferencialmente abas do YouTube Music ou a primeira aba de navegação
    yt_pages = [p for p in pages if p.get("type") == "page" and "music.youtube.com" in p.get("url", "")]
    if yt_pages:
        active_tab = yt_pages[0]
    else:
        normal_tabs = [p for p in pages if p.get("type") == "page"]
        active_tab = normal_tabs[0] if normal_tabs else None

    if not active_tab or not active_tab.get("webSocketDebuggerUrl"):
        return {
            "success": False,
            "mode": "cdp_failed",
            "message": "Nenhuma aba de navegação elegível encontrada no Vivaldi.",
            "local_playback": {"status": "error"},
            "cast_stream": {"status": "failed"},
        }

    # Ativa a aba
    try:
        urllib.request.urlopen(f"http://{cdp_host}:{cdp_port}/json/activate/{active_tab['id']}", timeout=2.0)
    except Exception:
        pass

    ws_url = active_tab["webSocketDebuggerUrl"]

    # 3. Conecta ao WebSocket da aba, aguarda descoberta de sinks e dispara Cast nativo via user gesture
    cast_log = []
    cast_issues = []
    dom_play_info = {}
    target_sink_name = device_name
    sink_found = False

    async with websockets.connect(ws_url) as ws:
        req_id = 0

        async def cdp_call(method: str, params: Optional[dict[str, Any]] = None, timeout: float = 4.0) -> dict[str, Any]:
            nonlocal req_id, target_sink_name, sink_found
            req_id += 1
            cid = req_id
            await ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
            start_c = time.time()
            while time.time() - start_c < timeout:
                try:
                    raw_msg = await asyncio.wait_for(ws.recv(), timeout=0.6)
                    data = json.loads(raw_msg)
                    ev_method = data.get("method")
                    if ev_method == "Cast.sinksUpdated":
                        sinks = data.get("params", {}).get("sinks", [])
                        for s in sinks:
                            if device_name.lower() in s.get("name", "").lower():
                                target_sink_name = s.get("name", device_name)
                                sink_found = True
                                cast_log.append(f"Sink '{target_sink_name}' localizado via CDP")
                                break
                    elif ev_method == "Cast.issueUpdated":
                        issue = data.get("params", {}).get("issueMessage", "")
                        if issue:
                            cast_issues.append(issue)
                            cast_log.append(f"Cast.issueUpdated: {issue}")

                    if data.get("id") == cid:
                        return data
                except asyncio.TimeoutError:
                    pass
            return {}

        # Habilita Cast para iniciar descoberta mDNS de sinks
        await cdp_call("Cast.enable")
        cast_log.append("Cast.enable ativado")

        # Aguarda eventos Cast.sinksUpdated até que o sink alvo apareça na rede
        start_wait = time.time()
        while time.time() - start_wait < 4.0 and not sink_found:
            try:
                raw_event = await asyncio.wait_for(ws.recv(), timeout=0.6)
                event_data = json.loads(raw_event)
                if event_data.get("method") == "Cast.sinksUpdated":
                    sinks = event_data.get("params", {}).get("sinks", [])
                    for s in sinks:
                        if device_name.lower() in s.get("name", "").lower():
                            target_sink_name = s.get("name", device_name)
                            sink_found = True
                            cast_log.append(f"Sink '{target_sink_name}' localizado via CDP")
                            break
                elif event_data.get("method") == "Cast.issueUpdated":
                    issue = event_data.get("params", {}).get("issueMessage", "")
                    if issue:
                        cast_issues.append(issue)
                        cast_log.append(f"Cast.issueUpdated: {issue}")
            except asyncio.TimeoutError:
                pass

        # Configura o sink alvo como destino pré-selecionado de apresentação
        await cdp_call("Cast.setSinkToUse", {"sinkName": target_sink_name})
        cast_log.append(f"Sink configurado para '{target_sink_name}'")
        await asyncio.sleep(0.5)

        # Localiza o botão Cast nativo visível no DOM do YouTube Music (com polling para renderização)
        eval_btn_script = r"""
        (() => {
            const btn = Array.from(document.querySelectorAll('ytmusic-cast-button')).find(b => !b.hidden && b.offsetParent);
            if (!btn) return null;
            const rect = btn.getBoundingClientRect();
            return {
                x: Math.round(rect.x + rect.width / 2),
                y: Math.round(rect.y + rect.height / 2),
                state: btn.getAttribute('cast-button-connection-state') || 'DISCONNECTED',
                text: (btn.innerText || '').trim()
            };
        })()
        """
        btn_info = None
        start_btn = time.time()
        while time.time() - start_btn < 5.0:
            resp_btn = await cdp_call("Runtime.evaluate", {"expression": eval_btn_script, "returnByValue": True})
            val = resp_btn.get("result", {}).get("result", {}).get("value")
            if val and isinstance(val, dict) and val.get("x") and val.get("x") > 0:
                btn_info = val
                break
            await asyncio.sleep(0.5)

        if btn_info and btn_info.get("x"):
            bx, by = btn_info["x"], btn_info["y"]
            btn_state = btn_info.get("state")
            cast_log.append(f"Botão Cast nativo encontrado no DOM em ({bx}, {by}) [Estado atual: {btn_state}]")

            # Se não estiver conectado, despacha evento confiável de clique do mouse (Trusted User Gesture)
            if btn_state != "CONNECTED":
                await cdp_call("Input.dispatchMouseEvent", {"type": "mousePressed", "x": bx, "y": by, "button": "left", "clickCount": 1})
                await cdp_call("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": bx, "y": by, "button": "left", "clickCount": 1})
                cast_log.append(f"Clique confiável (Input.dispatchMouseEvent) disparado no botão Cast nativo em ({bx}, {by})")

                # Aguarda até 6 segundos para confirmação no DOM (estado CONNECTED)
                start_dom = time.time()
                while time.time() - start_dom < 6.0:
                    await asyncio.sleep(0.6)
                    chk = await cdp_call("Runtime.evaluate", {"expression": eval_btn_script, "returnByValue": True})
                    v = chk.get("result", {}).get("result", {}).get("value")
                    if v and v.get("state") == "CONNECTED":
                        cast_log.append(f"Botão Cast conectado no DOM: {v.get('text', target_sink_name)}")
                        break
        else:
            cast_log.append("Aviso: Botão ytmusic-cast-button visível não encontrado no DOM")

        # Inicia reprodução nos controles do player se estiver pausado e captura metadados
        eval_play_script = r"""
        (() => {
            const playBtn = document.querySelector('ytmusic-wiz-player-controls button[title="Tocar"], ytmusic-wiz-player-controls button[aria-label="Tocar"], #play-pause-button');
            let playTriggered = false;
            if (playBtn) {
                playBtn.click();
                playTriggered = true;
            } else {
                const v = document.querySelector('video');
                if (v && v.paused) {
                    v.play();
                    playTriggered = true;
                }
            }
            const pauseBtn = document.querySelector('ytmusic-wiz-player-controls button[title="Pausar"], ytmusic-wiz-player-controls button[aria-label="Pausar"]');
            const trackInfoEl = document.querySelector('ytmusic-track-info') || document.querySelector('ytmusic-player-bar .title');
            const rawText = trackInfoEl ? trackInfoEl.innerText : null;
            const trackInfo = rawText ? rawText.split('\n').join(' - ').trim() : null;
            const castBtn = Array.from(document.querySelectorAll('ytmusic-cast-button')).find(b => !b.hidden && b.offsetParent);
            return {
                playTriggered: playTriggered,
                isPlaying: !!pauseBtn,
                trackInfo: trackInfo || null,
                castState: castBtn ? castBtn.getAttribute('cast-button-connection-state') : null,
                castReceiver: castBtn ? (castBtn.innerText || '').trim() : null
            };
        })()
        """
        # Aguarda metadados da faixa e confirmação de reprodução no DOM
        start_meta = time.time()
        while time.time() - start_meta < 4.0:
            resp_play = await cdp_call("Runtime.evaluate", {"expression": eval_play_script, "returnByValue": True})
            dom_play_info = resp_play.get("result", {}).get("result", {}).get("value") or {}
            if dom_play_info.get("trackInfo") and dom_play_info.get("isPlaying"):
                break
            await asyncio.sleep(0.8)

        if dom_play_info.get("trackInfo"):
            cast_log.append(f"Faixa identificada no DOM: {dom_play_info['trackInfo']}")
        await asyncio.sleep(1.0)

    # 4. Dispara comando MPRIS auxiliar
    send_mpris_play()

    # 5. Validação real no Chromecast físico via PyChromecast com teste de estabilidade
    cast_check = verify_chromecast_playback(
        target_name=device_name,
        host=device_host,
        port=device_port,
        timeout=10.0,
        stability_interval=3.0,
        require_native=True,
    )

    track_title = dom_play_info.get("trackInfo")
    dom_receiver = dom_play_info.get("castReceiver")

    # Caso 1: Dispositivo ocupado por aplicativo alheio (ex: Netflix, Spotify)
    if cast_check.get("is_unrelated_app"):
        msg = (
            f"O Chromecast '{device_name}' está ocupado executando outro aplicativo "
            f"({cast_check.get('display_name')} [{cast_check.get('app_id')}]). "
            "A transmissão do YouTube Music não foi iniciada para não interromper a reprodução ativa."
        )
        return {
            "success": False,
            "mode": "cdp_cast_busy_other_app",
            "message": msg,
            "local_playback": {"status": "playing", "track": track_title},
            "cast_stream": {
                "status": "busy_other_app",
                "confirmed": False,
                "app_id": cast_check.get("app_id"),
                "display_name": cast_check.get("display_name"),
                "device": device_name,
                "details": cast_check,
            },
            "cast_log": cast_log,
            "cast_issues": cast_issues,
        }

    # Caso 2: Espelhamento de tela/aba rejeitado
    if cast_check.get("is_mirroring"):
        msg = (
            f"O Chromecast '{device_name}' iniciou apenas espelhamento de tela/aba ({cast_check.get('app_id')}) "
            "em vez de transmissão nativa do YouTube Music, e foi rejeitado para evitar falso positivo."
        )
        return {
            "success": False,
            "mode": "cdp_cast_mirroring_rejected",
            "message": msg,
            "local_playback": {"status": "playing", "track": track_title},
            "cast_stream": {
                "status": "mirroring_rejected",
                "confirmed": False,
                "app_id": cast_check.get("app_id"),
                "display_name": cast_check.get("display_name"),
                "device": device_name,
                "details": cast_check,
            },
            "cast_log": cast_log,
            "cast_issues": cast_issues,
        }

    # Caso 3: Sessão caiu imediatamente após iniciar
    if cast_check.get("reason") == "session_dropped_immediately":
        msg = (
            f"A transmissão Cast para '{device_name}' foi iniciada momentaneamente, mas foi encerrada "
            "pelo dispositivo após alguns segundos (sessão efêmera não persistiu)."
        )
        return {
            "success": False,
            "mode": "cdp_cast_dropped",
            "message": msg,
            "local_playback": {"status": "playing", "track": track_title},
            "cast_stream": {
                "status": "dropped_immediately",
                "confirmed": False,
                "device": device_name,
                "details": cast_check,
            },
            "cast_log": cast_log,
            "cast_issues": cast_issues,
        }

    # Caso 4: Sessão nativa confirmada no Chromecast, valida evidência real de reprodução da mídia
    if cast_check.get("confirmed"):
        # Validação rigorosa: exige metadados da faixa confirmados para não declarar falso positivo
        if not track_title or track_title.lower() in {"desconhecido", "none", ""}:
            msg = (
                f"O aplicativo YouTube Music [{cast_check.get('app_id')}] foi iniciado no Chromecast '{device_name}', "
                "mas os metadados da faixa solicitada não puderam ser confirmados no player. "
                "Transmissão não declarada como sucesso para evitar falso positivo."
            )
            return {
                "success": False,
                "mode": "cdp_cast_unconfirmed_playback",
                "message": msg,
                "local_playback": {"status": "playing", "track": None},
                "cast_stream": {
                    "status": "unconfirmed_playback",
                    "confirmed": False,
                    "session_type": cast_check.get("session_type", "native_ytm"),
                    "app_id": cast_check.get("app_id"),
                    "display_name": cast_check.get("display_name"),
                    "device": device_name,
                    "details": cast_check,
                },
                "cast_log": cast_log,
                "cast_issues": cast_issues,
            }

        # Sucesso real: receptor correto, sessão persistente e metadados de reprodução confirmados
        msg = (
            f"Playlist iniciada no Vivaldi e transmissão Cast nativa CONFIRMADA para o Chromecast '{device_name}' "
            f"(App: {cast_check.get('display_name')} [{cast_check.get('app_id')}] - Faixa: '{track_title}' - Estável e persistente)."
        )
        return {
            "success": True,
            "mode": "cdp_cast_confirmed",
            "message": msg,
            "local_playback": {
                "status": "routed_to_cast",
                "track": track_title,
            },
            "cast_stream": {
                "status": "active",
                "confirmed": True,
                "session_type": cast_check.get("session_type", "native_ytm"),
                "app_id": cast_check.get("app_id"),
                "display_name": cast_check.get("display_name"),
                "device": device_name,
                "track": track_title,
                "cast_receiver": dom_receiver or device_name,
                "persistent": True,
            },
            "cast_log": cast_log,
            "cast_issues": cast_issues,
        }

    # Caso 5: Dispositivo em standby ou timeout
    msg = (
        f"A playlist está aberta e reproduzindo localmente no Vivaldi, mas a transmissão para o Chromecast "
        f"'{device_name}' NÃO foi confirmada pelo dispositivo (o Chromecast permaneceu em modo descanso/Backdrop). "
        "Verifique se o Vivaldi e o Chromecast estão na mesma rede e se não há isolamento de portas."
    )
    return {
        "success": False,
        "mode": "cdp_cast_unconfirmed",
        "message": msg,
        "local_playback": {"status": "playing", "track": track_title},
        "cast_stream": {
            "status": "unconfirmed",
            "confirmed": False,
            "details": cast_check,
            "device": device_name,
        },
        "cast_log": cast_log,
        "cast_issues": cast_issues,
    }


def play_via_cdp(
    url: str,
    device_name: Optional[str] = None,
    device_host: Optional[str] = None,
    device_port: int = 8009,
    cdp_port: int = DEFAULT_CDP_PORT,
    cdp_host: str = DEFAULT_CDP_HOST,
) -> dict[str, Any]:
    """
    Interface síncrona para automação via Chrome DevTools Protocol (CDP).
    Utiliza asyncio para executar a rotina de controle e validação de Cast.
    """
    target = device_name or DEFAULT_DEVICE_NAME
    try:
        return asyncio.run(
            _async_play_via_cdp(
                url=url,
                device_name=target,
                device_host=device_host,
                device_port=device_port,
                cdp_port=cdp_port,
                cdp_host=cdp_host,
            )
        )
    except Exception as e:
        warning(f"Erro ao executar automação CDP: {e}")
        return {
            "success": False,
            "mode": "cdp_failed",
            "message": f"Falha na automação CDP: {e}",
            "local_playback": {"status": "unknown"},
            "cast_stream": {"status": "failed", "error": str(e)},
        }


def play_playlist(
    playlist_url: str = DEFAULT_PLAYLIST_URL,
    shuffle: bool = True,
    device_name: Optional[str] = None,
    skip_discovery: bool = False,
    restart_vivaldi: bool = False,
) -> dict[str, Any]:
    """
    Função principal para automação da playlist no YouTube Music e transmissão para Chromecast:
    1. Valida pré-requisitos (Vivaldi e Chromecast).
    2. Constrói URL direta com modo aleatório (shuffle).
    3. Se solicitado ou se o Vivaldi estiver fechado, habilita a porta CDP em localhost.
    4. Se o CDP estiver ativo, executa a transmissão direta com validação real no Chromecast.
    5. Se o CDP não estiver ativo e o Vivaldi já estiver aberto, utiliza abertura nativa com aviso explícito.
    """
    target_device = device_name or DEFAULT_DEVICE_NAME

    if not playlist_url:
        return {
            "success": False,
            "mode": "no_playlist",
            "message": "Nenhuma playlist definida. Defina a variável BINGO_PLAYLIST_URL no ambiente ou informe a URL da playlist.",
            "prerequisites": validate_prerequisites(target_device=target_device, timeout=0.1),
            "local_playback": {"status": "idle"},
            "cast_stream": {"status": "not_attempted_no_playlist"},
        }

    # Validação de pré-requisitos
    prereqs = validate_prerequisites(target_device=target_device, timeout=3.5 if not skip_discovery else 0.5)

    if not prereqs["vivaldi_installed"]:
        return {
            "success": False,
            "message": "Vivaldi não está instalado no sistema.",
            "prerequisites": prereqs,
            "local_playback": {"status": "not_installed"},
            "cast_stream": {"status": "failed"},
        }

    chromecast_info = prereqs["target_device"]
    if not chromecast_info and not skip_discovery:
        return {
            "success": False,
            "message": (
                f"Chromecast '{target_device}' não foi localizado na rede local. "
                "Verifique se está na mesma rede e tente novamente."
            ),
            "prerequisites": prereqs,
            "local_playback": {"status": "idle"},
            "cast_stream": {"status": "not_found"},
        }

    # Se o usuário solicitou reiniciar o Vivaldi com CDP
    if restart_vivaldi:
        info("Opção explícita '--restart-vivaldi' detectada. Reiniciando Vivaldi com porta CDP...")
        restart_vivaldi_with_cdp()
        prereqs["cdp_available"] = is_cdp_available()
        prereqs["vivaldi_running"] = is_vivaldi_running()

    # Se o Vivaldi não estiver rodando, inicia-o diretamente com CDP habilitado
    elif not prereqs["vivaldi_running"]:
        info("Vivaldi não está em execução. Iniciando com porta CDP habilitada em 127.0.0.1...")
        launch_vivaldi_with_cdp()
        prereqs["cdp_available"] = is_cdp_available()
        prereqs["vivaldi_running"] = is_vivaldi_running()

    # Monta URL com shuffle
    watch_url = build_ytm_url(playlist_url, shuffle=shuffle)

    # Caminho 1: Porta CDP disponível (automação completa com transmissão e validação Cast)
    if prereqs["cdp_available"]:
        info(f"Porta CDP {DEFAULT_CDP_PORT} disponível. Executando automação e transmissão via CDP...")
        result = play_via_cdp(
            watch_url,
            device_name=chromecast_info["name"] if chromecast_info else target_device,
            device_host=chromecast_info["host"] if chromecast_info else None,
            device_port=chromecast_info.get("port", 8009) if chromecast_info else 8009,
        )
        state.running_programs.add("vivaldi")
        state.last_command = "play_music"
        result["prerequisites"] = prereqs
        result["url"] = watch_url
        result["target_device"] = chromecast_info
        return result

    # Caminho 2: Vivaldi em execução sem CDP e sem permissão explícita para reiniciar
    info(f"Reutilizando instância do Vivaldi via IPC nativo com URL: {watch_url}")
    open_in_vivaldi(watch_url)

    state.running_programs.add("vivaldi")
    state.last_command = "play_music"

    time.sleep(1.5)
    send_mpris_play()

    device_name_display = chromecast_info["name"] if chromecast_info else target_device
    device_ip_display = chromecast_info["host"] if chromecast_info else "IP desconhecido"

    msg = (
        f"Playlist aberta com modo aleatório no Vivaldi (sessão Premium preservada). "
        f"Chromecast '{device_name_display}' detectado em {device_ip_display}. "
        "A reprodução foi iniciada LOCALMENTE. Para transmissão automática sem clique manual, "
        "o Vivaldi precisa ser iniciado com suporte a depuração remota (use '--restart-vivaldi' ou inicie com "
        "'vivaldi --remote-debugging-port=9222 --remote-debugging-address=127.0.0.1')."
    )

    return {
        "success": True,
        "mode": "native_instance_reused",
        "message": msg,
        "url": watch_url,
        "target_device": chromecast_info,
        "prerequisites": prereqs,
        "local_playback": {"status": "playing"},
        "cast_stream": {
            "status": "not_attempted_no_cdp",
            "confirmed": False,
            "device": device_name_display,
        },
    }


def execute(message: dict[str, Any]) -> dict[str, Any]:
    """
    Ponto de entrada do Bingo handler para a ação de música.
    Recebe um dict de mensagem do protocolo e retorna a resposta de status.
    """
    playlist_url = message.get("playlist_url") or message.get("url") or DEFAULT_PLAYLIST_URL
    shuffle = message.get("shuffle", True)
    device_name = message.get("device") or message.get("target_device") or DEFAULT_DEVICE_NAME
    restart_vivaldi = message.get("restart_vivaldi", False)

    try:
        result = play_playlist(
            playlist_url=playlist_url,
            shuffle=shuffle,
            device_name=device_name,
            restart_vivaldi=restart_vivaldi,
        )

        res = create_dict(
            MessageType.STATUS,
            success=result["success"],
            message=result["message"],
            command="play_music",
            data=result,
        )
    except Exception as e:
        error(f"Exceção durante execução de play_playlist: {e}")
        res = create_dict(
            MessageType.STATUS,
            success=False,
            message=f"Erro interno na automação musical: {e}",
            command="play_music",
            data={"mode": "internal_error", "error": str(e)},
        )

    if "id" in message:
        res["id"] = message["id"]

    return res


def cli_main():
    """Interface de linha de comando para execução direta no terminal."""
    parser = argparse.ArgumentParser(
        description="Automação do YouTube Music no Vivaldi e transmissão para Chromecast (Bingo Core)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Apenas valida os pré-requisitos (Vivaldi, CDP e Chromecast) sem abrir a música",
    )
    parser.add_argument(
        "--playlist",
        default=DEFAULT_PLAYLIST_URL,
        help="URL da playlist do YouTube Music",
    )
    parser.add_argument(
        "--device",
        default=DEFAULT_DEVICE_NAME,
        help="Nome amigável do Chromecast (padrão: TutuLola)",
    )
    parser.add_argument(
        "--no-shuffle",
        action="store_true",
        help="Desativa o modo aleatório (shuffle)",
    )
    parser.add_argument(
        "--restart-vivaldi",
        action="store_true",
        help="Reinicia o Vivaldi com a porta CDP habilitada em localhost (127.0.0.1) preservando o perfil do usuário",
    )

    args = parser.parse_args()

    print("\n🎵 ==========================================")
    print("   Bingo - Automação de Música no Chromecast")
    print("==========================================\n")

    if args.check:
        print("🔍 Verificando pré-requisitos...")
        prereqs = validate_prerequisites(target_device=args.device)
        print(f" - Vivaldi instalado: {'✅ Sim' if prereqs['vivaldi_installed'] else '❌ Não'} ({prereqs['vivaldi_path']})")
        print(f" - Vivaldi em execução: {'✅ Sim' if prereqs['vivaldi_running'] else 'ℹ️ Não (será aberto com CDP)'}")
        print(f" - Porta CDP (9222): {'✅ Aberta' if prereqs['cdp_available'] else 'ℹ️ Fechada (use --restart-vivaldi para habilitar)'}")
        print(f" - Chromecast encontrado: {'✅ Sim' if prereqs['chromecast_found'] else '❌ Não'}")

        if prereqs["target_device"]:
            dev = prereqs["target_device"]
            print(f"   * Dispositivo alvo: {dev['name']} ({dev['host']}:{dev['port']}) [{dev['model']}]")

        if prereqs["all_devices"]:
            print(f"   * Total de Chromecasts na rede: {len(prereqs['all_devices'])}")

        if prereqs["issues"]:
            print("\n⚠️ Problemas detectados:")
            for issue in prereqs["issues"]:
                print(f"   - {issue}")
        else:
            print("\n✨ Todos os requisitos para reprodução estão atendidos!")
        print()
        return

    print(f"🎯 Dispositivo alvo: {args.device}")
    print(f"📋 Playlist: {args.playlist}")
    print(f"🔀 Modo Aleatório: {'Desativado' if args.no_shuffle else 'Ativado'}")
    if args.restart_vivaldi:
        print("🔄 Reinício do Vivaldi: Habilitado (--restart-vivaldi)\n")
    else:
        print()

    result = play_playlist(
        playlist_url=args.playlist,
        shuffle=not args.no_shuffle,
        device_name=args.device,
        restart_vivaldi=args.restart_vivaldi,
    )

    print("---------------------------------------------")
    if result["success"]:
        print(f"✅ SUCESSO: {result['message']}\n")
    else:
        print(f"⚠️ AVISO: {result['message']}\n")

    print(f"🔗 URL: {result.get('url')}")
    if result.get("target_device"):
        dev = result["target_device"]
        print(f"📺 Chromecast Alvo: {dev['name']} ({dev['host']}:{dev['port']})")

    # Informações separadas de reprodução local e Cast
    if "local_playback" in result:
        loc = result["local_playback"]
        loc_track = f" | Faixa: {loc.get('track')}" if loc.get("track") else ""
        print(f"💻 Reprodução Local: {loc.get('status')}{loc_track}")
    if "cast_stream" in result:
        cs = result["cast_stream"]
        c_status = cs.get("status")
        c_app = cs.get("display_name") or "Nenhum"
        c_id = cs.get("app_id") or ""
        c_type = cs.get("session_type", "unknown")
        c_conf = "✅ Confirmada na TV" if cs.get("confirmed") else "❌ Não confirmada na TV"
        track = cs.get("track")
        track_str = f" | Faixa: {track}" if track else ""
        app_str = f" [App: {c_app}{f' ({c_id})' if c_id else ''}]"
        print(f"📡 Transmissão Cast: {c_status} ({c_conf}){app_str} [Tipo: {c_type}]{track_str}")

    print(f"⚙️ Modo de execução: {result.get('mode')}\n")


if __name__ == "__main__":
    cli_main()
