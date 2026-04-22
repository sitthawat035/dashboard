# ╔═══════════════════════════════════════════════════════╗
# ║  api/socket_events.py — Socket.IO event handlers      ║
# ║  log_tail_worker + @socketio.on handlers              ║
# ║  Refactored from server.py (Phase 2)                  ║
# ╚═══════════════════════════════════════════════════════╝

import os
import time
import threading
import subprocess
from flask import request

from api.config import AGENTS, ROOT_DIR
from api.helpers import resolve_active_log_file, read_file_tail, shorten_ts

# ─── Shared State (imported by gateway.py via set_cleanup_callback) ───────────
active_log_watchers: dict = {}    # agent_id -> count
log_watchers_lock = threading.Lock()
log_watcher_threads: dict = {}    # agent_id -> thread
log_watcher_stop_events: dict = {}  # agent_id -> threading.Event
client_subscriptions: dict = {}   # sid -> set of agent_keys

terminal_processes: dict = {}     # sid -> subprocess.Popen

# Module-level socketio reference (set during init_socketio)
_socketio = None


# ─── Init (called from server.py) ────────────────────────────────────────────

def init_socketio(socketio_instance):
    """Inject socketio instance and register all event handlers."""
    global _socketio
    _socketio = socketio_instance

    # Inject cleanup callback into gateway module to avoid circular import
    from api.gateway import set_cleanup_callback
    set_cleanup_callback(cleanup_log_watchers_for_agent)

    # Register Socket.IO event handlers
    socketio_instance.on_event("join_log_stream", handle_join_log_stream)
    socketio_instance.on_event("leave_log_stream", handle_leave_log_stream)
    socketio_instance.on_event("disconnect", handle_disconnect)
    socketio_instance.on_event("terminal_create", handle_terminal_create)
    socketio_instance.on_event("terminal_specific_create", handle_specific_terminal)
    socketio_instance.on_event("terminal_input", handle_terminal_input)


# ─── Log Tail Worker ──────────────────────────────────────────────────────────

def log_tail_worker(agent_key):
    """Enhanced log tailing worker with proper cleanup and gateway health monitoring."""
    agent = AGENTS.get(agent_key)
    if not agent:
        return

    log_path = resolve_active_log_file(agent_key)
    if not log_path:
        return

    room_name = f"log_{agent_key}"
    print(f"[LogStream] Thread started for {agent_key}")

    stop_event = log_watcher_stop_events.get(agent_key)
    if not stop_event:
        stop_event = threading.Event()
        log_watcher_stop_events[agent_key] = stop_event

    try:
        for _ in range(10):
            if os.path.exists(log_path):
                break
            time.sleep(0.5)

        if not os.path.exists(log_path):
            print(f"[LogStream] File not found: {log_path}")
            return

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0, 2)

            batch: list[str] = []
            batch_deadline = 0.0
            BATCH_SIZE = 10
            BATCH_TIMEOUT = 0.1

            while not stop_event.is_set():
                with log_watchers_lock:
                    if active_log_watchers.get(agent_key, 0) <= 0:
                        break

                line = f.readline()
                if not line:
                    cur_pos = f.tell()
                    if os.path.getsize(log_path) > cur_pos:
                        f.seek(cur_pos)
                    else:
                        time.sleep(0.05)
                        if batch:
                            now = time.time()
                            if now >= batch_deadline:
                                _emit_batch(agent_key, batch, room_name)
                                batch.clear()
                                batch_deadline = 0.0
                    continue

                line = line.rstrip("\r\n")
                line = shorten_ts(line)
                batch.append(line)

                now = time.time()
                if batch_deadline == 0.0:
                    batch_deadline = now + BATCH_TIMEOUT

                if len(batch) >= BATCH_SIZE or now >= batch_deadline:
                    _emit_batch(agent_key, batch, room_name)
                    batch.clear()
                    batch_deadline = 0.0

            if batch:
                _emit_batch(agent_key, batch, room_name)

    except Exception as e:
        print(f"[LogStream] Error for {agent_key}: {e}")
    finally:
        with log_watchers_lock:
            active_log_watchers[agent_key] = 0
            log_watcher_threads.pop(agent_key, None)
            log_watcher_stop_events.pop(agent_key, None)
        print(f"[LogStream] Thread stopped for {agent_key}")


def _emit_batch(agent_key, batch, room_name):
    if not _socketio:
        return
    if len(batch) == 1:
        _socketio.emit(
            "gateway_log_line",
            {"agent_id": agent_key, "line": batch[0]},
            room=room_name,
        )
    else:
        _socketio.emit(
            "gateway_log_lines",
            {"agent_id": agent_key, "lines": list(batch)},
            room=room_name,
        )


# ─── Cleanup Helpers ──────────────────────────────────────────────────────────

def stop_log_watcher(agent_key):
    stop_event = log_watcher_stop_events.get(agent_key)
    if stop_event:
        stop_event.set()
    thread = log_watcher_threads.get(agent_key)
    if thread and thread.is_alive():
        thread.join(timeout=2.0)


def cleanup_log_watchers_for_client(sid):
    with log_watchers_lock:
        if sid not in client_subscriptions:
            return
        agent_keys = list(client_subscriptions[sid])
        for agent_key in agent_keys:
            count = active_log_watchers.get(agent_key, 0)
            if count > 0:
                active_log_watchers[agent_key] = count - 1
                if active_log_watchers[agent_key] <= 0:
                    stop_log_watcher(agent_key)
        client_subscriptions.pop(sid, None)


def cleanup_log_watchers_for_agent(agent_key):
    """Used when gateway stops/restarts."""
    with log_watchers_lock:
        if agent_key in active_log_watchers:
            active_log_watchers[agent_key] = 0
            stop_log_watcher(agent_key)
            print(f"[LogStream] Cleaned up log watchers for agent {agent_key} due to gateway state change")


def cleanup_zombie_threads():
    with log_watchers_lock:
        to_remove = []
        for agent_key, thread in log_watcher_threads.items():
            if not thread.is_alive():
                to_remove.append(agent_key)
                active_log_watchers.pop(agent_key, None)
                log_watcher_stop_events.pop(agent_key, None)

        for agent_key in to_remove:
            log_watcher_threads.pop(agent_key, None)
            print(f"[LogStream] Cleaned up zombie thread for agent {agent_key}")

        if to_remove:
            print(f"[LogStream] Cleaned up {len(to_remove)} zombie threads")


# ─── Socket.IO Event Handlers ─────────────────────────────────────────────────

def handle_join_log_stream(data):
    from flask_socketio import join_room, emit
    sid = getattr(request, "sid", None)
    agent_id = data.get("agent_id")
    if not agent_id or agent_id not in AGENTS:
        return
    room_name = f"log_{agent_id}"
    join_room(room_name)
    print(f"[LogStream] DEBUG: Client {sid} joined room {room_name}")

    with log_watchers_lock:
        if sid:
            if sid not in client_subscriptions:
                client_subscriptions[sid] = set()
            client_subscriptions[sid].add(agent_id)

        count = active_log_watchers.get(agent_id, 0)
        active_log_watchers[agent_id] = count + 1

        if count == 0:
            t = threading.Thread(target=log_tail_worker, args=(agent_id,), daemon=True)
            log_watcher_threads[agent_id] = t
            t.start()

    active_log = resolve_active_log_file(agent_id)
    lines, size = read_file_tail(active_log, 100)
    emit("gateway_log_init", {"agent_id": agent_id, "lines": lines})


def handle_leave_log_stream(data):
    from flask_socketio import leave_room
    sid = getattr(request, "sid", None)
    agent_id = data.get("agent_id")
    if not agent_id:
        return
    room_name = f"log_{agent_id}"
    leave_room(room_name)

    with log_watchers_lock:
        if sid and sid in client_subscriptions:
            client_subscriptions[sid].discard(agent_id)

        count = active_log_watchers.get(agent_id, 0)
        if count > 0:
            active_log_watchers[agent_id] = count - 1
            if active_log_watchers[agent_id] <= 0:
                stop_log_watcher(agent_id)


def handle_disconnect():
    sid = getattr(request, "sid", None)
    if sid:
        print(f"DEBUG: Client disconnected (sid: {sid}). Cleaning up resources...")

        # Cleanup terminal processes
        if sid in terminal_processes:
            p = terminal_processes.pop(sid, None)
            if p:
                try:
                    p.kill()
                except Exception as e:
                    print(f"DEBUG: Error killing process for sid {sid}: {e}")

        cleanup_log_watchers_for_client(sid)


def handle_terminal_create(data):
    sid = data.get("id")
    if not sid:
        return

    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        _si = si
    except Exception:
        _si = None

    p = subprocess.Popen(
        ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=0,
        startupinfo=_si,
        cwd=ROOT_DIR,
    )
    terminal_processes[sid] = p

    def reader():
        buffer = []
        last_emit = time.time()
        try:
            while True:
                char = p.stdout.read(1)
                if not char:
                    break
                buffer.append(char)
                now = time.time()
                if len(buffer) > 100 or (now - last_emit > 0.01 and buffer):
                    if _socketio:
                        _socketio.emit(f"terminal_output_{sid}", "".join(buffer))
                    buffer = []
                    last_emit = now
        except Exception as e:
            print(f"DEBUG: Reader error for sid {sid}: {e}")
        finally:
            if buffer and _socketio:
                _socketio.emit(f"terminal_output_{sid}", "".join(buffer))
            if _socketio:
                _socketio.emit(f"terminal_output_{sid}", "\r\n[Process terminated]\r\n")

    threading.Thread(target=reader, daemon=True).start()


def handle_specific_terminal(data):
    sid = data.get("id")
    agent_id = data.get("agent_id")
    if not sid:
        return

    agent_dir = ROOT_DIR
    if agent_id in AGENTS:
        agent_dir = AGENTS[agent_id].get("workspace", ROOT_DIR)

    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        _si = si
    except Exception:
        _si = None

    p = subprocess.Popen(
        ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=0,
        startupinfo=_si,
        cwd=agent_dir if os.path.exists(agent_dir) else ROOT_DIR,
    )
    terminal_processes[sid] = p

    def reader():
        buffer = []
        last_emit = time.time()
        try:
            while True:
                char = p.stdout.read(1)
                if not char:
                    break
                buffer.append(char)
                now = time.time()
                if len(buffer) > 100 or (now - last_emit > 0.01 and buffer):
                    if _socketio:
                        _socketio.emit(f"terminal_output_{sid}", "".join(buffer))
                    buffer = []
                    last_emit = now
        except Exception:
            pass
        finally:
            if buffer and _socketio:
                _socketio.emit(f"terminal_output_{sid}", "".join(buffer))
            if _socketio:
                _socketio.emit(f"terminal_output_{sid}", "\r\n[Process terminated]\r\n")

    threading.Thread(target=reader, daemon=True).start()


def handle_terminal_input(data):
    sid = data.get("id")
    input_data = data.get("data")
    if sid in terminal_processes and input_data:
        p = terminal_processes[sid]
        try:
            clean_data = input_data.replace("\r", "")
            p.stdin.write(clean_data)
            p.stdin.flush()
        except Exception:
            pass
