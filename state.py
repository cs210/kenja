"""
Way to track page views in Streamlit.
From one of the creators: https://gist.github.com/ash2shukla/ff180d7fbe8ec3a0240f19f4452acde7
"""
from streamlit.runtime import get_instance
from streamlit.runtime.scriptrunner import get_script_run_ctx as get_report_ctx
from streamlit.runtime.legacy_caching.hashing import _CodeHasher
from metrics import VISIT_COUNT
from streamlit_extras.prometheus import streamlit_registry
registry = streamlit_registry()

class _SessionState:
    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "hasher": _CodeHasher(hash_funcs),
            "is_rerun": False,
            "session": session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state["data"]:
                self._state["data"][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def clear(self):
        """Clear session state and request a rerun."""
        self._state["data"].clear()
        self._state["session"].request_rerun()

    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state["is_rerun"]:
            self._state["is_rerun"] = False

        elif self._state["hash"] is not None:
            if self._state["hash"] != self._state["hasher"].to_bytes(
                self._state["data"], None
            ):
                self._state["is_rerun"] = True
                self._state["session"].request_rerun()

        self._state["hash"] = self._state["hasher"].to_bytes(self._state["data"], None)


def _get_session():
    runtime = get_instance()
    session_id = get_report_ctx().session_id
    session_info = runtime._session_mgr.get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")

    return session_info.session

def get_state(hash_funcs=None):
    session = _get_session()

    if not hasattr(session, "_custom_session_state"):
        session._custom_session_state = _SessionState(session, hash_funcs)
    return session._custom_session_state


def provide_state(func):
    def wrapper(*args, **kwargs):
        state = get_state(hash_funcs={})
        count_sessions()
        return_value = func(state=state, *args, **kwargs)
        state.sync()
        return return_value

    return wrapper

def count_sessions():
    state = get_state(hash_funcs={})

    if not state._is_session_reused:
        VISIT_COUNT.inc()
        state._is_session_reused = True