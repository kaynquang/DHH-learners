"""Fricative practice: feedback on /s/, /ʃ/ and /f/.

Run: streamlit run app/streamlit_app.py
"""
import streamlit as st

from fricative import warmup
from fricative.calibrated import create_profile, delete_profile, last_profile, list_profiles, load_profile, remember_profile

st.set_page_config(page_title="Fricative practice", page_icon=":material/graphic_eq:", layout="wide")


@st.cache_resource(show_spinner="Loading the models…")
def _ready() -> dict:
    return warmup.warm()


_ready()                                    # every model is loaded before the first page is used

NO_PROFILE = "No profile"


def apply_profile() -> None:
    """Switch to the chosen profile: bring back its calibration, or start with none."""
    name = st.session_state["profile_select"]
    st.session_state.pop("calibration", None)
    st.session_state["cal_tokens"] = []
    if name != NO_PROFILE:
        saved = load_profile(name)
        if saved is not None:
            st.session_state["calibration"], st.session_state["cal_tokens"] = saved
    remember_profile(None if name == NO_PROFILE else name)


def add_profile() -> None:
    name = create_profile(st.session_state.get("new_profile", ""))
    if name is None:
        st.session_state["profile_msg"] = "Type a name that is not already used."
        return
    st.session_state["profile_select"] = name
    st.session_state["new_profile"] = ""
    st.session_state.pop("profile_msg", None)
    apply_profile()


def remove_profile() -> None:
    delete_profile(st.session_state["profile_select"])
    st.session_state["profile_select"] = NO_PROFILE
    apply_profile()


if "profile_select" not in st.session_state:        # first run of this browser session: reopen the profile used last time
    st.session_state["profile_select"] = last_profile() or NO_PROFILE
    apply_profile()

with st.sidebar:
    st.selectbox("Profile", [NO_PROFILE, *list_profiles()], key="profile_select", on_change=apply_profile,
                 help="Each profile keeps its own voice calibration on this computer.")
    with st.popover("Add profile", icon=":material/person_add:", width="stretch"):
        st.text_input("Profile name", key="new_profile", max_chars=30)
        st.button("Create", on_click=add_profile, key="create_profile")
        if st.session_state.get("profile_msg"):
            st.caption(st.session_state["profile_msg"])
    if st.session_state["profile_select"] != NO_PROFILE:
        st.button("Delete this profile", icon=":material/delete:", on_click=remove_profile, key="delete_profile", type="tertiary")
    st.divider()

page = st.navigation(
    [
        st.Page("app_pages/practice.py", title="Practice", icon=":material/graphic_eq:", default=True),
        st.Page("app_pages/teacher.py", title="Teacher view", icon=":material/monitoring:"),
        st.Page("app_pages/calibrate.py", title="Calibrate", icon=":material/tune:"),
        st.Page("app_pages/log.py", title="Log", icon=":material/history:"),
        st.Page("app_pages/camera_log.py", title="Camera log", icon=":material/videocam:"),
        st.Page("app_pages/how_it_works.py", title="How it works", icon=":material/menu_book:"),
    ],
    position="top",
)
page.run()
