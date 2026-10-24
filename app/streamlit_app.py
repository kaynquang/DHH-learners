"""Fricative practice: feedback on /s/, /ʃ/ and /f/.

Run: streamlit run app/streamlit_app.py
"""
import streamlit as st

st.set_page_config(page_title="Fricative practice", page_icon=":material/graphic_eq:", layout="wide")

page = st.navigation(
    [
        st.Page("app_pages/practice.py", title="Practice", icon=":material/graphic_eq:", default=True),
        st.Page("app_pages/calibrate.py", title="Calibrate", icon=":material/tune:"),
        st.Page("app_pages/how_it_works.py", title="How it works", icon=":material/menu_book:"),
    ],
    position="top",
)
page.run()
