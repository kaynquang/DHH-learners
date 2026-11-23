"""Rate page: teachers listen to collected recordings and rate them (correct / almost / not yet) without seeing what the app decided.
Agreement between the app and each rater, and between raters, is computed on the Agreement tab, and everything can be exported as a zip."""
import hashlib

import pandas as pd
import streamlit as st

from fricative import collect
from fricative.collect import LABELS

st.title("Rate")
st.caption(f"Recordings come from the teacher-run sessions (learner app, ?page=collect). Files are in `{collect.root()}`. Only recordings whose participant "
           "consented to keeping audio can be rated. The app's verdict is hidden while you rate.  \n"
           "錄音來自老師進行的錄音（孩子端程式，?page=collect）。只有同意保存錄音的參與者才能被評分。評分時看不到程式的判定。")

tab_rate, tab_agree, tab_export = st.tabs(["Rate", "Agreement", "Export and delete"])

with tab_rate:
    rater = collect.clean_code(st.text_input("Your rater code (initials)", key="rt_code", max_chars=10))
    first_only = st.toggle("Rate only the first recording of each word (half the work; recommended for the pilot)", value=True, key="rt_first_only")
    takes = [t for t in collect.all_takes() if t.get("audio") and (t["take"] == 1 or not first_only)]
    if not rater:
        st.info("Enter your rater code to start.", icon=":material/badge:")
    elif not takes:
        st.info("No recordings with audio yet.", icon=":material/mic_off:")
    else:
        L = collect.labels()
        todo = [t for t in takes if (t["take_id"], rater) not in L]
        todo.sort(key=lambda t: hashlib.md5((rater + t["take_id"]).encode()).hexdigest())      # a fixed random order per rater, so order does not follow participant or word
        st.progress((len(takes) - len(todo)) / len(takes), text=f"{len(takes) - len(todo)} of {len(takes)} rated 已評 {len(takes) - len(todo)} / {len(takes)}")
        if not todo:
            st.success("You have rated every recording.", icon=":material/check_circle:")
        else:
            t = todo[0]
            st.subheader(f"Target word 目標字: {t['word']}  (/{t['phone']}/)")
            st.caption("Does the first sound of this word sound right for the word? Rate only the first consonant.")
            st.audio((collect.root() / t["code"] / t["audio"]).read_bytes())
            unsure = st.checkbox("I am not sure", key=f"rt_unsure_{t['take_id']}")
            note = st.text_input("Note (optional)", key=f"rt_note_{t['take_id']}", max_chars=200)
            cols = st.columns(3)
            for c, lab in zip(cols, LABELS):
                if c.button(lab.capitalize(), key=f"rt_{lab}_{t['take_id']}", type="primary" if lab == "correct" else "secondary", use_container_width=True):
                    collect.add_label(t["take_id"], rater, lab, unsure, note)
                    st.rerun()

with tab_agree:
    A = collect.agreement()
    st.caption("Exact agreement and kappa between the app's verdict (correct = green, almost = yellow, not yet = red) and each rater, over recordings the app scored; "
               "recordings the app did not score are counted separately and never dropped silently.  \n"
               "程式的判定（正確＝綠、差不多＝黃、還沒＝紅）與每位評分者的完全一致率與 kappa，只計算程式有評分的錄音；程式未評分的錄音另外計數，不會被默默排除。")
    if not A["raters"]:
        st.info("No ratings yet.", icon=":material/rate_review:")
    for r, d in A["app_vs_rater"].items():
        st.markdown(f"**App vs rater 程式對評分者 {r}**: {d['n']} rated 已評; app did not score 程式未評分 {d['not_scored']}")
        st.write({"exact agreement 完全一致率": None if d["exact"] is None else round(d["exact"], 3), "kappa": None if d["kappa"] is None else round(d["kappa"], 3),
                  "weighted kappa 加權 kappa": None if d["weighted_kappa"] is None else round(d["weighted_kappa"], 3)})
        st.dataframe(pd.DataFrame(d["confusion"]).T.rename_axis("app says 程式判定").rename(columns=lambda c: f"rater 評分者: {c}"), width="stretch")
    rows = collect.disagreements()
    if rows:
        with st.expander(f"Takes with a disagreement 有分歧的錄音 ({len(rows)}): for the analysis, not for the raters 供分析使用，不給評分者看"):
            st.caption("The app's verdict next to the raters' labels, so the cases that differ can be listened to and discussed after all ratings are in.  \n程式的判定與評分者的標記並列，待所有評分完成後，可聆聽並討論有分歧的錄音。")
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    for k, d in A["rater_vs_rater"].items():
        st.markdown(f"**{k}**: {d['n']} in common 共同評分")
        st.write({"exact agreement 完全一致率": None if d["exact"] is None else round(d["exact"], 3), "kappa": None if d["kappa"] is None else round(d["kappa"], 3),
                  "weighted kappa 加權 kappa": None if d["weighted_kappa"] is None else round(d["weighted_kappa"], 3)})

with tab_export:
    people = collect.participants()
    st.write(f"{len(people)} participants 位參與者: {', '.join(people) or '-'}")
    up = st.file_uploader("Import data exported from another computer (zip)", type="zip", key="rt_import")
    if up is not None and st.button("Import", key="rt_import_go", icon=":material/upload:"):
        res = collect.import_zip(up.getvalue())
        st.success(f"Added {len(res['added'])} participants ({', '.join(res['added']) or '-'}); skipped {len(res['skipped'])} whose code already exists here "
                   f"({', '.join(res['skipped']) or '-'}); {res['labels_added']} new ratings.  \n"
                   f"已加入 {len(res['added'])} 位參與者（{', '.join(res['added']) or '-'}）；略過 {len(res['skipped'])} 位（代碼已存在：{', '.join(res['skipped']) or '-'}）；新增 {res['labels_added']} 筆評分。")
    if people:
        st.download_button("Download all data (zip)", collect.export_zip(), file_name="seesound_collection.zip", mime="application/zip", icon=":material/download:")
        who = st.selectbox("Delete one participant (the right to have data deleted)", [""] + people, key="rt_del_who")
        sure = st.checkbox("I am sure; this removes their recordings, takes and ratings from this computer", key="rt_del_sure")
        if st.button("Delete", disabled=not (who and sure), icon=":material/delete:", key="rt_del"):
            collect.delete_participant(who)
            st.toast(f"Deleted 已刪除 {who}.")
            st.rerun()
