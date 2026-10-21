        pct = min(100, int(r["advance"] / total * 100)) if total else 0
        st.markdown(
            f'<div class="item"><div class="top"><span>{html.escape(str(r["item"]))}</span>'
            f'<span>{money(r["remaining"])} left</span></div>'
            f'<div class="row"><span>Est {money(r["estimated"])}</span><span>Actual {money(r["actual"])}</span>'
            f'<span>Advance {money(r["advance"])}</span></div>'
            f'<div class="bar"><div style="width:{pct}%"></div></div></div>', unsafe_allow_html=True)

    with st.expander("✏️ EDIT / ADD / DELETE ITEMS", expanded=not B):
        st.caption("Edit cells directly. To delete, tick the row's left checkbox and press the Delete key / bin icon. "
                   "Remaining = (actual, or estimate if actual is blank) − advance.")
        bdf = st.data_editor(
            pd.DataFrame(B, columns=BUD_COLS), num_rows="dynamic", use_container_width=True, hide_index=True,
            disabled=["remaining"], key="bud_ed",
            column_config={"item": "Item", **{k: st.column_config.NumberColumn(k.title() + " (₹)", min_value=0, step=500)
                                              for k in ("estimated", "actual", "advance")},
                           "remaining": st.column_config.NumberColumn("Remaining (₹)")})
        bdf = bdf.fillna({"item": "", "estimated": 0, "actual": 0, "advance": 0, "remaining": 0})
        if st.button("💾 Save budget"):
            D["budget"] = calc([r for r in bdf.to_dict("records") if str(r["item"]).strip()])
            save()
            st.rerun()

    live = calc(bdf.to_dict("records")) if "bdf" in dir() else B
    H("Totals")
    cards([("Estimated", money(sum(r["estimated"] for r in live)), "c1"),
           ("Actual", money(sum(r["actual"] for r in live)), "c2"),
           ("Advance paid", money(sum(r["advance"] for r in live)), "c3"),
           ("Remaining", money(sum(r["remaining"] for r in live)), "c4")])
