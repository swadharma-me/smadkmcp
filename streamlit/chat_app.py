import streamlit as st
import requests
import websocket
import threading
import json
import queue
import time

# ======================= Page & Layout =======================
st.set_page_config(page_title="WS Chat", layout="wide")

# ======================= Safe rerun helper =======================
def safe_rerun():
    try:
        return st.experimental_rerun()
    except Exception:
        pass
    try:
        return st.rerun()
    except Exception:
        pass
    try:
        from streamlit.runtime.scriptrunner import RerunException
        raise RerunException()
    except Exception:
        pass
    st.session_state["_needs_rerun"] = True
    try:
        st.warning("Please refresh manually (auto rerun not supported).")
    except Exception:
        pass
    return None

# --- CONFIGURATION VARIABLES ---
FIREBASE_API_KEY = "AIzaSyAPO5FbHwxwKuTvJINZkyJAEDvukHuxNwM"
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=" + FIREBASE_API_KEY
WEBSOCKET_CHAT_URL = "wss://devsmwschat.smaraami.com/chat/{sessionId}"
##

# Keep the connection alive ~10 minutes idle (send a ping every 9 minutes)
WS_PING_INTERVAL_SEC = 540  # 9 minutes
WS_PING_TIMEOUT_SEC  = 60   # wait up to 30s for pong
WS_RECONNECT_BACKOFF_SEC = 3

# ======================= Session State =======================
if "incoming_q" not in st.session_state:
    st.session_state["incoming_q"] = queue.Queue()  # server -> UI
if "outgoing_q" not in st.session_state:
    st.session_state["outgoing_q"] = queue.Queue()  # UI -> server

incoming_q = st.session_state["incoming_q"]
outgoing_q = st.session_state["outgoing_q"]

defaults = {
    "token": None,
    "sessionId": None,
    "ws_thread": None,             # Thread handle
    "stop_event": None,            # threading.Event()
    "messages": [],                # transcript
    "show_debug": False,           # hidden by default
    "clear_chat_input_on_rerun": False,
    "ws_connected": False,         # purely UI (derived from events)
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ======================= Input clear (run BEFORE text_input) =======================
def _apply_clear_if_requested():
    if st.session_state.get("clear_chat_input_on_rerun"):
        st.session_state["chat_input"] = ""  # safe: widget not created yet this run
        st.session_state["clear_chat_input_on_rerun"] = False

# ======================= Message parser =======================
def _extract_messages(payload):
    out = []

    def _coerce_to_str(v):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            for k in ("text", "content", "data", "payload", "msg", "message"):
                if k in v and isinstance(v[k], str):
                    return v[k]
            return json.dumps(v, ensure_ascii=False)
        if isinstance(v, (list, tuple)):
            flat = []
            for item in v:
                s = _coerce_to_str(item)
                if s:
                    flat.append(s)
            return "\n".join(flat) if flat else None
        return str(v)

    if isinstance(payload, dict):
        if "message" in payload:
            s = _coerce_to_str(payload["message"])
            if s:
                out.append(s)
        elif "messages" in payload:
            s = _coerce_to_str(payload["messages"])
            if s:
                out.append(s)
        else:
            for k in ("text", "content", "data", "payload", "msg", "status"):
                if k in payload:
                    s = _coerce_to_str(payload[k])
                    if s:
                        out.append(s)
                        break
            if not out:
                out.append(json.dumps(payload, ensure_ascii=False))
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            out.extend(_extract_messages(item))
    else:
        out.append(str(payload))
    return out

# ======================= WebSocket Thread (no Streamlit APIs here) =======================
def ws_worker(ws_url: str, auth_header: str, incoming: queue.Queue, outgoing: queue.Queue, stop_event: threading.Event):
    """
    Runs in a background thread.
    - Owns the WebSocket connection (websocket-client)
    - Pushes incoming server messages into `incoming`
    - Consumes outbound messages from `outgoing` and sends them when connected
    - Never touches Streamlit APIs or st.session_state
    """

    def _on_message(ws, message):
        try:
            data = json.loads(message)
            for s in _extract_messages(data):
                incoming.put(("server", s))
        except json.JSONDecodeError:
            incoming.put(("server", message))

    def _on_error(ws, error):
        incoming.put(("error", str(error)))

    def _on_close(ws, code, reason):
        incoming.put(("info", "WebSocket closed."))
        incoming.put(("_conn_state_", False))

    def _sender_loop(ws):
        """Pump messages from outgoing queue to the socket while connected."""
        try:
            while ws.sock and ws.sock.connected and not stop_event.is_set():
                try:
                    msg = outgoing.get(timeout=0.2)
                except queue.Empty:
                    continue
                try:
                    ws.send(msg)
                except Exception as e:
                    incoming.put(("error", f"Send failed: {e}"))
        except Exception as e:
            incoming.put(("error", f"Sender loop exception: {e}"))

    def _on_open(ws):
        incoming.put(("info", "WebSocket connection opened."))
        incoming.put(("_conn_state_", True))
        # Start a small sender thread that drains outgoing_q while connected
        threading.Thread(target=_sender_loop, args=(ws,), daemon=True).start()

    while not stop_event.is_set():
        try:
            ws_app = websocket.WebSocketApp(
                ws_url,
                header=[auth_header],
                on_message=_on_message,
                on_error=_on_error,
                on_close=_on_close,
                on_open=_on_open,
            )

            # This blocks until socket closes or an exception occurs
            ws_app.run_forever(
                ping_interval=WS_PING_INTERVAL_SEC,
                ping_timeout=WS_PING_TIMEOUT_SEC,
            )
        except Exception as e:
            incoming.put(("error", f"WS worker exception: {e}"))

        # If asked to stop, break; else brief backoff then reconnect
        if stop_event.is_set():
            break
        time.sleep(WS_RECONNECT_BACKOFF_SEC)

# ======================= UI =======================
st.title("Streamlit WebSocket Chat")
_apply_clear_if_requested()

# Toggle debug rail
st.session_state["show_debug"] = st.toggle("Show debug panel", value=False, help="Toggle the left debug rail")

# ---- Login flow ----
if st.session_state["token"] is None:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_clicked = st.button("Login")

    if login_clicked:
        payload = {"email": username, "password": password, "returnSecureToken": True}
        resp = requests.post(FIREBASE_AUTH_URL, json=payload)
        if resp.status_code == 200:
            st.session_state["token"] = resp.json()["idToken"]
            import uuid
            st.session_state["sessionId"] = str(uuid.uuid4())
            st.success("Login successful! Redirecting to chat...")
            safe_rerun()
        else:
            st.error("Login failed. Check credentials.")

# ---- Chat flow ----
else:
    # Ensure background WS thread started once
    if st.session_state["ws_thread"] is None:
        ws_url = WEBSOCKET_CHAT_URL.format(sessionId=st.session_state["sessionId"])
        auth_header = f"Authorization: Bearer {st.session_state['token']}"
        stop_event = threading.Event()
        st.session_state["stop_event"] = stop_event

        t = threading.Thread(
            target=ws_worker,
            args=(ws_url, auth_header, incoming_q, outgoing_q, stop_event),
            daemon=True,
        )
        t.start()
        st.session_state["ws_thread"] = t

    # Drain incoming queue -> session messages; handle connection state pings
    flushed = False
    while True:
        try:
            sender, payload = incoming_q.get_nowait()
        except queue.Empty:
            break
        if sender == "_conn_state_":
            st.session_state["ws_connected"] = bool(payload)
        else:
            st.session_state["messages"].append((sender, payload))
            flushed = True

    if flushed:
        st.session_state["clear_chat_input_on_rerun"] = True
        safe_rerun()

    # ----- Left debug rail (hidden by default) -----
    if st.session_state["show_debug"]:
        with st.sidebar:
            st.header("Debug")
            st.write(f"IncomingQ size: {incoming_q.qsize()}")
            st.write(f"OutgoingQ size: {outgoing_q.qsize()}")
            st.write(f"WS connected: {st.session_state.get('ws_connected', False)}")

            last_server = None
            for s, m in reversed(st.session_state["messages"]):
                if s == "server":
                    last_server = m
                    break
            st.write("Last parsed server message:")
            st.code(last_server or "<none>")

    # ----- Chat UI -----
    st.subheader("Chat")
    st.caption("Server messages appear on the left; your messages appear on the right.")

    # Optional auto-refresh
    try:
        from streamlit_autorefresh import st_autorefresh
        auto_refresh = st.checkbox("Enable auto-refresh", value=True)
        if auto_refresh:
            st_autorefresh(interval=1500, key="auto_refresh_counter")
    except Exception:
        st.warning("`streamlit-autorefresh` not installed. Install with: pip install streamlit-autorefresh")

    # Transcript bubbles
    for sender, msg in st.session_state["messages"]:
        if sender == "server":
            left, right = st.columns([7, 5], vertical_alignment="top")
            with left:
                with st.chat_message("assistant"):
                    st.write(msg)
        elif sender == "you":
            left, right = st.columns([5, 7], vertical_alignment="top")
            with right:
                with st.chat_message("user"):
                    st.write(msg)
        elif sender == "error":
            st.error(msg)
        elif sender == "info":
            st.info(msg)
        else:
            st.write(f"**{sender}:** {msg}")

    # Input & controls
    user_msg = st.text_input("Type your message", key="chat_input")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        send_clicked = st.button("Send")
    with c2:
        refresh_clicked = st.button("Refresh")
    with c3:
        disconnect_clicked = st.button("Disconnect")

    if refresh_clicked:
        st.session_state["clear_chat_input_on_rerun"] = True
        safe_rerun()

    if disconnect_clicked:
        ev = st.session_state.get("stop_event")
        if ev and isinstance(ev, threading.Event):
            ev.set()
        st.session_state["ws_thread"] = None
        st.session_state["stop_event"] = None
        st.session_state["ws_connected"] = False
        st.info("WebSocket disconnect requested.")

    if send_clicked and user_msg:
        # Add to transcript immediately
        st.session_state["messages"].append(("you", user_msg))
        # Enqueue to server (thread will actually send)
        try:
            outgoing_q.put_nowait(user_msg)
        except Exception as e:
            st.session_state["messages"].append(("error", f"Enqueue failed: {e}"))

        st.session_state["clear_chat_input_on_rerun"] = True
        safe_rerun()