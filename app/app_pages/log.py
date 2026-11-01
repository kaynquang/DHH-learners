"""Log page: every scored recording, with the ones flagged as "said right, scored wrong" first, for debugging."""
import pandas as pd
import streamlit as st

from fricative import config as C
from fricative import reclog

st.title("Log")
st.caption(f"Every recording that gets a result is saved here with what the app measured and decided. Flag the ones you said correctly "
           f"that the app judged wrong, then use them to find out why. Files are in `{reclog.LOG_DIR}`.")

entries = reclog.list_entries()
if not entries:
    st.info("Nothing logged yet. Record a word on the Practice page.", icon=":material/history:")
    st.stop()

flagged = [e for e in entries if e.get("flagged")]
unflagged = len(entries) - len(flagged)
with st.popover("Delete logs", icon=":material/delete_sweep:"):
    st.caption("This removes the recordings and their notes from this computer. It cannot be undone.")
    if st.button(f"Delete the {unflagged} not flagged", disabled=not unflagged, icon=":material/delete:", key="log_del_unflagged"):
        n = reclog.delete_many(keep_flagged=True)
        st.toast(f"Deleted {n} recordings. Flagged ones were kept.", icon=":material/check:")
        st.rerun()
    sure = st.checkbox("I am sure I want to delete everything", key="log_del_sure")
    if st.button(f"Delete all {len(entries)}", disabled=not sure, type="primary", icon=":material/delete_forever:", key="log_del_all"):
        n = reclog.delete_many()
        st.toast(f"Deleted {n} recordings.", icon=":material/check:")
        st.rerun()
with st.container(horizontal=True, gap="large"):
    st.metric("Recordings", len(entries))
    st.metric("Flagged as wrong", len(flagged))
only_flagged = st.toggle("Only flagged", value=bool(flagged), key="log_only_flagged")
sounds = sorted({e.get("target", "") for e in entries})
pick = st.segmented_control("Sound", ["All", *sounds], default="All", required=True, key="log_sound",
                            format_func=lambda s: s if s == "All" else C.PHONE_LABEL.get(s, s))
shown = [e for e in entries if (e.get("flagged") or not only_flagged) and (pick == "All" or e.get("target") == pick)]

st.dataframe(pd.DataFrame([{
    "Time": e["time"].replace("T", " "), "Flagged": "⚑" if e.get("flagged") else "", "Word": e["word"],
    "Target": C.PHONE_LABEL.get(e.get("target"), e.get("target")), "Result": e["verdict"]["label"],
    "App heard": C.PHONE_LABEL.get(e["verdict"].get("heard"), "–"), "Profile": e.get("profile"), "Source": e.get("source"),
    "Note": e.get("note", ""),
} for e in shown]), hide_index=True, width="stretch", alt="Table of logged recordings")

st.subheader("Details")
for e in shown:
    v = e["verdict"]
    head = f"{'⚑ ' if e.get('flagged') else ''}{e['time'].replace('T', ' ')} · {e['word']} {C.PHONE_LABEL.get(e.get('target'), '')} · {v['label']}"
    with st.expander(head):
        path = reclog.audio_path(e)
        if path.exists():
            st.audio(path.read_bytes())
        st.markdown(f"**{v['label']}** · {v['message']}")
        if e.get("flagged"):
            st.warning(e.get("note") or "(no note)", icon=":material/flag:")
        note = st.text_area("Note", value=e.get("note", ""), key=f"lognote_{e['id']}")
        with st.container(horizontal=True):
            if st.button("Save note and flag", key=f"logflag_{e['id']}", icon=":material/flag:"):
                reclog.flag(e["id"], note)
                st.rerun()
            if e.get("flagged") and st.button("Remove flag", key=f"logunflag_{e['id']}"):
                reclog.unflag(e["id"])
                st.rerun()
            if st.button("Delete", key=f"logdel_{e['id']}", icon=":material/delete:"):
                reclog.delete(e["id"])
                st.rerun()
        st.caption("What the app measured and the settings used:")
        st.json({k: e.get(k) for k in ("id", "source", "profile", "details", "settings", "verdict")}, expanded=False)
