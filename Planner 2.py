import hashlib
import html
import json
import io
import re
import urllib.parse
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Wedding Planner", page_icon="💍", layout="wide")

DB = Path(__file__).with_name("wedding_data.json")
SIDES = ["Bride", "Groom"]
RSVP = ["Pending", "Confirmed", "Declined"]
TASK_COLS = ["task", "accountable", "vendor", "contact", "due", "remarks", "done"]
BUD_COLS = ["item", "estimated", "actual", "advance", "remaining"]
DEFAULT_TASKS = ["Book venue", "Book hotels for guests", "Finalise guest list", "Print & send invitations",
                 "Book catering", "Book photographer", "Arrange transport for guests"]
COUPLE = {"groom": "Ajay", "groom_family": "Narayanan", "bride": "Pooja", "bride_family": "Sivakumar"}

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
:root{--navy:#0B2447;--royal:#1D4ED8;--azure:#2F80ED;--sky:#5BC0F8;--ice:#EAF4FF;--mist:#F5F9FF;--line:#CFE0F7;--ink:#14284B}
html,body,.stApp,.stApp p,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp li,.stApp td,.stApp th,.stApp summary{font-family:'Plus Jakarta Sans',sans-serif}
/* keep Streamlit's icon font so arrows/icons don't show as raw text */
[data-testid="stIconMaterial"],span[class*="material"],.material-icons,.material-symbols-rounded{font-family:'Material Symbols Rounded','Material Symbols Outlined','Material Icons'!important;font-weight:normal!important;letter-spacing:normal!important;text-transform:none!important}
.stApp .hero h1,.stApp .sec,.stApp [data-testid="stMetricValue"],.stApp .card b{font-family:'Fraunces',serif!important}
.stApp{background:radial-gradient(1200px 500px at 90% -10%,#DCEBFF 0%,transparent 60%),linear-gradient(180deg,#F5F9FF 0%,#EAF2FD 100%);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:2rem;max-width:1200px}

/* hero */
.hero{position:relative;overflow:hidden;border-radius:26px;padding:34px 36px 28px;margin-bottom:18px;color:#fff;
  background:linear-gradient(120deg,#0B2447 0%,#14459E 55%,#2F80ED 100%);box-shadow:0 18px 40px rgba(20,69,158,.28)}
.hero:before,.hero:after{content:"";position:absolute;border-radius:50%;pointer-events:none}
.hero:before{width:320px;height:320px;right:-80px;top:-140px;background:radial-gradient(circle,rgba(91,192,248,.55),transparent 70%)}
.hero:after{width:260px;height:260px;left:35%;bottom:-170px;background:radial-gradient(circle,rgba(255,196,120,.35),transparent 70%)}
.hero .rings{font-size:2.1rem;line-height:1}
.hero h1{font-family:'Fraunces',serif;font-weight:800;font-size:clamp(1.7rem,4.2vw,3rem);line-height:1.12;margin:.35rem 0 .5rem;padding:0;letter-spacing:.01em;
  background:linear-gradient(90deg,#FFFFFF 0%,#BDE6FF 30%,#8FD3FF 52%,#FFD9A0 78%,#FFB8CF 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{margin:0;font-size:.95rem;color:#D6E8FF}
.hero b{color:#fff}

/* section headings */
.sec{font-family:'Fraunces',serif;font-weight:800;font-size:1.45rem;margin:.6rem 0 .7rem;display:flex;align-items:center;gap:10px}
.sec i{width:10px;height:26px;border-radius:6px;display:inline-block}
.sec span{-webkit-background-clip:text;background-clip:text;color:transparent}
.s0 i{background:linear-gradient(#2F80ED,#5BC0F8)}.s0 span{background-image:linear-gradient(90deg,#1D4ED8,#2FA4E7)}
.s1 i{background:linear-gradient(#7C3AED,#2F80ED)}.s1 span{background-image:linear-gradient(90deg,#6D28D9,#2F80ED)}
.s2 i{background:linear-gradient(#0EA5A4,#5BC0F8)}.s2 span{background-image:linear-gradient(90deg,#0B8F9E,#1D4ED8)}
.s3 i{background:linear-gradient(#F59E0B,#EF6A8A)}.s3 span{background-image:linear-gradient(90deg,#E07B00,#D6336C)}

/* tabs */
[data-baseweb="tab-list"]{gap:6px;background:#fff;padding:6px;border-radius:16px;border:1px solid var(--line);box-shadow:0 6px 18px rgba(29,78,216,.08)}
button[data-baseweb="tab"]{border-radius:12px;padding:8px 16px;font-weight:600;color:#47608C;background:transparent}
button[data-baseweb="tab"][aria-selected="true"]{color:#fff;background:linear-gradient(135deg,#1D4ED8,#2F80ED);box-shadow:0 6px 14px rgba(29,78,216,.35)}
[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}

/* buttons */
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:12px;border:0;font-weight:600;color:#fff!important;
  background:linear-gradient(135deg,#1D4ED8,#2F80ED);box-shadow:0 6px 14px rgba(29,78,216,.28);transition:transform .15s,box-shadow .15s}
.stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover,.stLinkButton>a:hover{transform:translateY(-1px);box-shadow:0 10px 20px rgba(29,78,216,.38);color:#fff!important}
.stButton>button:focus-visible,.stLinkButton>a:focus-visible{outline:3px solid #9CCBFF;outline-offset:2px}
.stDownloadButton>button:disabled{background:#B9C9E4;box-shadow:none}

/* make sure button text/background stay visible in every state (incl. download button hover) */
.stApp .stButton>button,.stApp .stFormSubmitButton>button,.stApp .stDownloadButton>button,.stApp .stLinkButton>a,
.stApp [data-testid^="stBaseButton"]{background:linear-gradient(135deg,#1D4ED8,#2F80ED)!important;color:#fff!important;border:0!important}
.stApp .stButton>button:hover,.stApp .stFormSubmitButton>button:hover,.stApp .stDownloadButton>button:hover,.stApp .stLinkButton>a:hover,
.stApp [data-testid^="stBaseButton"]:hover,.stApp [data-testid^="stBaseButton"]:active,.stApp [data-testid^="stBaseButton"]:focus{
  background:linear-gradient(135deg,#0F3FB8,#1F6FE0)!important;color:#fff!important;border:0!important}
.stApp .stButton>button *,.stApp .stFormSubmitButton>button *,.stApp .stDownloadButton>button *,.stApp .stLinkButton>a *,
.stApp [data-testid^="stBaseButton"] *{color:#fff!important}
.stApp .stDownloadButton>button:disabled,.stApp .stDownloadButton>button:disabled:hover{background:#B9C9E4!important;color:#fff!important}
/* inputs, expanders, metrics, forms */
[data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{border-radius:12px!important;background:#fff!important;border-color:var(--line)!important}
[data-testid="stExpander"],[data-testid="stForm"]{background:#fff;border:1px solid var(--line)!important;border-radius:18px;box-shadow:0 6px 18px rgba(29,78,216,.06)}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-left:6px solid var(--azure);border-radius:16px;padding:14px 18px;box-shadow:0 6px 18px rgba(29,78,216,.08)}
[data-testid="stMetricValue"]{font-family:'Fraunces',serif;color:var(--royal)}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border-radius:14px;overflow:hidden;border:1px solid var(--line)}
[data-testid="stProgress"]>div>div>div{background:linear-gradient(90deg,#2F80ED,#5BC0F8)}
hr{border-color:var(--line)!important}

/* dashboard cards */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:8px 0 18px}
.card{border-radius:18px;padding:16px 18px;color:#fff;box-shadow:0 10px 22px rgba(20,69,158,.22)}
.card small{opacity:.92;letter-spacing:.04em;font-size:.78rem;font-weight:600}
.card b{display:block;font-family:'Fraunces',serif;font-size:1.65rem;margin-top:4px}
.c1{background:linear-gradient(135deg,#1D4ED8,#2F80ED)}.c2{background:linear-gradient(135deg,#6D28D9,#3B82F6)}
.c3{background:linear-gradient(135deg,#0E8FA8,#38BDF8)}.c4{background:linear-gradient(135deg,#F59E0B,#EF6A8A)}

/* budget items */
.item{background:#fff;border:1px solid var(--line);border-radius:16px;padding:13px 16px;margin-bottom:10px;box-shadow:0 4px 12px rgba(29,78,216,.06)}
.item .top{display:flex;justify-content:space-between;gap:8px;font-weight:700;color:var(--navy)}
.item .top span:last-child{color:var(--royal)}
.item .row{display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px;font-size:.8rem;color:#5B6F94;margin:6px 0 8px}
.bar{height:9px;border-radius:9px;background:#DCE9FB;overflow:hidden}
.bar>div{height:100%;border-radius:9px;background:linear-gradient(90deg,#2F80ED,#5BC0F8)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>""", unsafe_allow_html=True)


# ---------- storage ----------
def load():
    d = {"guests": [], "hotels": [], "tasks": [], "budget": [], "couple": dict(COUPLE)}
    if DB.exists():
        try:
            d.update(json.loads(DB.read_text(encoding="utf-8")))
        except Exception:
            pass
    d["couple"] = {**COUPLE, **d.get("couple", {})}
    for t in d["tasks"]:  # migrate older files
        t.setdefault("accountable", t.pop("owner", ""))
        for k in ("vendor", "contact", "remarks"):
            t.setdefault(k, "")
    for b in d["budget"]:
        b.setdefault("advance", b.pop("paid", 0))
        b.setdefault("actual", 0)
        b.pop("side", None)
    if not d["tasks"]:
        d["tasks"] = [{"task": t, "accountable": "", "vendor": "", "contact": "", "due": "", "remarks": "",
                       "done": False} for t in DEFAULT_TASKS]
    return d


def save():
    DB.write_text(json.dumps(st.session_state.data, ensure_ascii=False, indent=1), encoding="utf-8")


def calc(rows):
    for r in rows:
        e, a, v = (float(r.get(k) or 0) for k in ("estimated", "actual", "advance"))
        r.update(estimated=e, actual=a, advance=v, remaining=(a if a > 0 else e) - v)
    return rows


def sync_budget():
    """Copy any task not yet in the budget into it (once, so deleted budget rows stay deleted)."""
    names = {b["item"] for b in D["budget"]}
    for t in D["tasks"]:
        if t.get("task") and not t.get("budgeted"):
            if t["task"] not in names:
                D["budget"].append({"item": t["task"], "estimated": 0, "actual": 0, "advance": 0, "remaining": 0})
            t["budgeted"] = True
    save()


if "data" not in st.session_state:
    st.session_state.data = load()
D = st.session_state.data
sync_budget()
CP = D["couple"]
TITLE = f"{CP['groom']} ({CP['groom_family']}) & {CP['bride']} ({CP['bride_family']}) Wedding"


_sec = [0]


def H(t):
    """Section heading with a rotating colour accent."""
    st.markdown(f'<div class="sec s{_sec[0] % 4}"><i></i><span>{html.escape(t)}</span></div>', unsafe_allow_html=True)
    _sec[0] += 1


def new_guest(name, side, headcount=1, phone="", relation="", rsvp="Pending"):
    return {"id": uuid.uuid4().hex[:8], "name": name.strip(), "side": side, "headcount": int(headcount),
            "phone": phone.strip(), "relation": relation.strip(), "rsvp": rsvp,
            "hotel": "", "room": "", "checkin": "", "checkout": ""}


# ---------- OCR (Tamil / English) ----------
TAMIL_DIGITS = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")
OCR_LANGS = {"Tamil + English": "tam+eng", "Tamil only": "tam", "English only": "eng"}


def run_ocr(file, lang):
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except ImportError:
        return None, "Install OCR support: pip install pytesseract pillow"
    try:
        img = ImageOps.autocontrast(ImageOps.grayscale(Image.open(file)))
        w, h = img.size
        if w < 1600:
            img = img.resize((w * 2, h * 2))
        return pytesseract.image_to_string(img, lang=lang, config="--psm 6"), None
    except Exception as e:
        return None, f"OCR failed: {e}. Install Tesseract with the Tamil pack (tesseract-ocr-tam)."


def parse_lines(text, side):
    out = []
    for line in text.translate(TAMIL_DIGITS).splitlines():
        line = re.sub(r"^\s*\d+[.)\-:]\s+", "", line).strip(" \t|•*-_")
        if len(line) < 2:
            continue
        m = re.match(r"^(.*?)[\s,:\-–=(]+(\d{1,2})\)?$", line)
        name, count = (m.group(1).strip(), int(m.group(2))) if m else (line, 1)
        if name:
            out.append(new_guest(name, side, max(count, 1)))
    return out


# ---------- helpers ----------
def wa_number(p):
    d = re.sub(r"\D", "", p or "")
    return ("91" + d) if len(d) == 10 else d


LBL = {
    "English": ("Accommodation Details", "Dear {n},", "We're delighted to host you. Your stay details:", "Hotel",
                "Address", "Location", "Room", "Check-in", "Check-out", "Hotel contact",
                "See you at the celebration!", "To be confirmed"),
    "தமிழ்": ("தங்குமிட விவரங்கள்", "அன்பிற்குரிய {n},",
             "உங்களை வரவேற்கக் காத்திருக்கிறோம். உங்கள் தங்குமிட விவரங்கள்:", "ஹோட்டல்", "முகவரி",
             "இருப்பிடம்", "அறை எண்", "செக்-இன்", "செக்-அவுட்", "ஹோட்டல் தொடர்பு",
             "கொண்டாட்டத்தில் சந்திப்போம்!", "விரைவில் தெரிவிக்கப்படும்"),
}


def room_message(g, lang):
    if lang == "Both":
        return room_message(g, "English") + "\n\n━━━━━━━━━━\n\n" + room_message(g, "தமிழ்")
    h = next((x for x in D["hotels"] if x["name"] == g["hotel"]), None)
    if not h:
        return ""
    t, hi, intro, lh, la, ll, lr, lci, lco, lc, bye, tbc = LBL[lang]
    L = [f"🎉 *{TITLE} – {t}*", "", hi.format(n=g["name"]), intro, "", f"🏨 {lh}: {h['name']}",
         f"📍 {la}: {h['address']}"]
    if h.get("link"):
        L.append(f"🗺️ {ll}: {h['link']}")
    L.append(f"🚪 {lr}: {g['room'] or tbc}")
    if g["checkin"]:
        L.append(f"🕑 {lci}: {g['checkin']}")
    if g["checkout"]:
        L.append(f"🕚 {lco}: {g['checkout']}")
    if h.get("contact"):
        L.append(f"☎️ {lc}: {h['contact']}")
    return "\n".join(L + ["", f"{bye} 💐"])


def guests_df(view):
    df = pd.DataFrame(D["guests"], columns=["id", "name", "side", "headcount", "phone", "relation", "rsvp",
                                            "hotel", "room", "checkin", "checkout"])
    return df if view == "All" else df[df.side == view]


def merge_edits(edited, cols):
    by_id = {g["id"]: g for g in D["guests"]}
    for _, r in edited.iterrows():
        g = by_id.get(r["id"])
        if g is not None:
            for c in cols:
                v = r[c]
                g[c] = int(v) if c == "headcount" and pd.notna(v) else ("" if pd.isna(v) else v)
    save()


def cards(items):
    st.markdown('<div class="grid">' + "".join(
        f'<div class="card {c}"><small>{html.escape(l.upper())}</small><b>{v}</b></div>'
        for l, v, c in items) + "</div>", unsafe_allow_html=True)


money = lambda x: f"₹{x:,.0f}"

# ---------- header ----------
st.markdown(
    f'<div class="hero"><div class="rings">💍</div><h1>{html.escape(TITLE)}</h1>'
    f'</div>',
    unsafe_allow_html=True)
with st.expander("👰🤵 COUPLE & FAMILY DETAILS"):
    a, b, c, d = st.columns(4)
    CP["groom"] = a.text_input("Groom", CP["groom"])
    CP["groom_family"] = b.text_input("Groom's family", CP["groom_family"])
    CP["bride"] = c.text_input("Bride", CP["bride"])
    CP["bride_family"] = d.text_input("Bride's family", CP["bride_family"])
    if st.button("Save details"):
        save()
        st.rerun()
view = st.radio("VIEW", ["All", "Bride", "Groom"], horizontal=True, key="view")

tabs = st.tabs(["📊 DASHBOARD", "👥 GUEST LIST", "🏨 ROOMS & SHARING", "✅ TASKS", "💰 BUDGET"])

# ---------- Dashboard ----------
with tabs[0]:
    df = pd.DataFrame(D["guests"], columns=guests_df("All").columns)
    if df.empty:
        st.info("No guests yet. Add some in the Guest list tab.")
    else:
        cols = st.columns(3)
        for col, side in zip(cols, SIDES + ["Total"]):
            s = df if side == "Total" else df[df.side == side]
            col.metric(f"{side.upper()} – HEADCOUNT", int(s.headcount.sum()), f"{len(s)} invitations")
        a, b = st.columns(2)
        with a:
            H("RSVP (headcount)")
            st.bar_chart(df.pivot_table(index="rsvp", columns="side", values="headcount", aggfunc="sum").fillna(0))
        with b:
            H("Accommodation")
            assigned = df[df.hotel != ""]
            st.metric("GUESTS WITH ROOMS", f"{len(assigned)} / {len(df)}")
            if not assigned.empty:
                st.bar_chart(assigned.groupby("hotel").headcount.sum())
    def guests_xlsx():
        buf = io.BytesIO()
        gdf_x = pd.DataFrame(D["guests"]).drop(columns=["id"], errors="ignore")
        gdf_x.columns = [c.title() for c in gdf_x.columns]
        with pd.ExcelWriter(buf, engine="openpyxl") as xw:
            gdf_x.to_excel(xw, index=False, sheet_name="Guests")
            ws = xw.sheets["Guests"]
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(
                    40, max(len(str(c.value or "")) for c in col) + 3)
        return buf.getvalue()

    st.download_button("⬇️ Download full guest list (Excel)", guests_xlsx() if D["guests"] else b"",
                       "guests.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       disabled=not D["guests"])

# ---------- Guest list ----------
with tabs[1]:
    H("Add guests")
    m1, m2, m3 = st.tabs(["✍️ ADD ONE", "📝 PASTE / TYPE LIST", "📷 SCAN LIST (TAMIL / ENGLISH)"])
    with m1:
        with st.form("add_guest", clear_on_submit=True):
            a, b, c = st.columns(3)
            name = a.text_input("Name (Tamil or English)")
            side = b.selectbox("Side", SIDES, index=0 if view != "Groom" else 1)
            hc = c.number_input("Headcount", 1, 50, 1)
            d, e, f = st.columns(3)
            phone = d.text_input("Phone / WhatsApp")
            rel = e.text_input("Relation (e.g. Uncle, Friend)")
            rsvp = f.selectbox("RSVP", RSVP)
            if st.form_submit_button("➕ Add guest") and name.strip():
                D["guests"].append(new_guest(name, side, hc, phone, rel, rsvp))
                save()
                st.rerun()
    with m2:
        st.caption("One guest per line, headcount at the end, e.g. `முருகன் குடும்பம், 4` or `Ravi Kumar 2`")
        txt = st.text_area("Guests", height=150, key="bulk_txt")
        bs = st.radio("Side", SIDES, horizontal=True, key="bulk_side")
        if st.button("Add all lines") and txt.strip():
            D["guests"] += parse_lines(txt, bs)
            save()
            st.session_state.pop("bulk_txt", None)
            st.rerun()
    with m3:
        st.caption("Upload photos of the list (Tamil, English or mixed). Review the text before adding.")
        ups = st.file_uploader("Images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
        lang_name = st.radio("Language in the paper", list(OCR_LANGS), horizontal=True)
        os_side = st.radio("These names belong to", SIDES, horizontal=True, key="ocr_side")
        if ups and st.button("🔍 Read text"):
            texts = []
            for u in ups:
                t, err = run_ocr(u, OCR_LANGS[lang_name])
                if err:
                    st.error(err)
                    break
                texts.append(t)
            else:
                st.session_state.ocr_text = "\n".join(texts)
        if "ocr_text" in st.session_state:
            edited_txt = st.text_area("Extracted text (fix mistakes here)", st.session_state.ocr_text, height=200)
            prev = parse_lines(edited_txt, os_side)
            st.write(f"**{len(prev)} guests detected**")
            if prev:
                st.dataframe(pd.DataFrame(prev)[["name", "headcount", "side"]], hide_index=True)
            if st.button("✅ Add these guests") and prev:
                D["guests"] += prev
                save()
                del st.session_state["ocr_text"]
                st.rerun()

    st.divider()
    H(f"Guest list – {view}")
    q = st.text_input("🔎 Search", "")
    gdf = guests_df(view)
    if q:
        gdf = gdf[gdf.name.str.contains(q, case=False, na=False) | gdf.relation.str.contains(q, case=False, na=False)]
    gdf = gdf[["id", "name", "side", "headcount", "phone", "relation", "rsvp"]].copy()
    gdf["delete"] = False
    st.caption(f"Total headcount shown: **{int(gdf.headcount.sum())}** across {len(gdf)} invitations")
    ed = st.data_editor(
        gdf, hide_index=True, use_container_width=True, key=f"ge_{view}_{q}",
        column_config={"id": None, "side": st.column_config.SelectboxColumn("Side", options=SIDES),
                       "rsvp": st.column_config.SelectboxColumn("RSVP", options=RSVP),
                       "headcount": st.column_config.NumberColumn("Headcount", min_value=1, max_value=50),
                       "delete": st.column_config.CheckboxColumn("🗑️")})
    if st.button("💾 Save changes"):
        gone = set(ed[ed["delete"]]["id"])
        merge_edits(ed[~ed["id"].isin(gone)], ["name", "side", "headcount", "phone", "relation", "rsvp"])
        D["guests"] = [g for g in D["guests"] if g["id"] not in gone]
        save()
        st.rerun()

# ---------- Rooms & sharing ----------
with tabs[2]:
    H("1. Hotels")
    with st.form("add_hotel", clear_on_submit=True):
        a, b = st.columns(2)
        hn = a.text_input("Hotel name")
        hc_ = b.text_input("Hotel contact number")
        ha = st.text_area("Address", height=70)
        hl = st.text_input("Google Maps link")
        if st.form_submit_button("➕ Add hotel") and hn.strip():
            D["hotels"].append({"name": hn.strip(), "address": ha.strip(), "link": hl.strip(), "contact": hc_.strip()})
            save()
            st.rerun()
    if D["hotels"]:
        hdf = st.data_editor(pd.DataFrame(D["hotels"]), num_rows="dynamic", use_container_width=True,
                             hide_index=True, key="hotel_ed")
        if st.button("💾 Save hotels"):
            D["hotels"] = [r for r in hdf.fillna("").to_dict("records") if r["name"]]
            save()
            st.rerun()

    st.divider()
    H("2. Allot rooms")
    show = st.radio("SHOW GUESTS", ["All", "With rooms", "Without rooms"], horizontal=True)
    rdf = guests_df(view)[["id", "name", "side", "headcount", "hotel", "room", "checkin", "checkout"]]
    if show == "With rooms":
        rdf = rdf[rdf.hotel != ""]
    elif show == "Without rooms":
        rdf = rdf[rdf.hotel == ""]
    st.caption(f"{len(rdf)} guests shown")
    red = st.data_editor(
        rdf, hide_index=True, use_container_width=True, key=f"re_{view}_{show}",
        disabled=["name", "side", "headcount"],
        column_config={"id": None, "hotel": st.column_config.SelectboxColumn("Hotel", options=[""] + [h["name"] for h in D["hotels"]]),
                       "room": "Room no.", "checkin": "Check-in (date/time)", "checkout": "Check-out"})
    if st.button("💾 Save room allotments"):
        merge_edits(red, ["hotel", "room", "checkin", "checkout"])
        st.rerun()

    st.divider()
    H("3. Share room details")
    ass = [g for g in D["guests"] if g["hotel"] and (view == "All" or g["side"] == view)]
    if not ass:
        st.info("Allot a hotel to a guest to enable sharing.")
    else:
        lang = st.radio("MESSAGE LANGUAGE", ["English", "தமிழ்", "Both"], horizontal=True)
        pick = st.selectbox("Guest", ass, format_func=lambda g: f"{g['name']} ({g['side']})")
        default = room_message(pick, lang)
        msg = st.text_area("✏️ Edit the message before sending", default, height=280,
                           key=f"msg_{pick['id']}_{lang}_{hashlib.md5(default.encode()).hexdigest()[:8]}")
        num = wa_number(pick["phone"])
        st.link_button("📲 Send on WhatsApp" + ("" if num else " (pick a contact)"),
                       f"https://wa.me/{num}?text={urllib.parse.quote(msg)}")
        with st.expander("Quick-send links for all guests with rooms (uses the selected language, unedited)"):
            rows = [{"Guest": g["name"], "Side": g["side"], "Hotel": g["hotel"], "Room": g["room"],
                     "WhatsApp": f"https://wa.me/{wa_number(g['phone'])}?text={urllib.parse.quote(room_message(g, lang))}"
                     if g["phone"] else None} for g in ass]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                         column_config={"WhatsApp": st.column_config.LinkColumn("Send", display_text="📲 WhatsApp")})

# ---------- Tasks ----------
with tabs[3]:
    H("Wedding checklist")
    st.caption("New tasks are copied to the Budget tab automatically when you save.")
    tdf = st.data_editor(
        pd.DataFrame(D["tasks"], columns=TASK_COLS + ["budgeted"]), num_rows="dynamic",
        use_container_width=True, hide_index=True, key="task_ed",
        column_config={"budgeted": None, "done": st.column_config.CheckboxColumn("Done"),
                       "accountable": "Accountable", "vendor": "Vendor", "contact": "Contact number",
                       "due": "Due date", "remarks": "Remarks"})
    if st.button("💾 Save tasks"):
        D["tasks"] = [r for r in tdf.fillna("").to_dict("records") if r["task"]]
        sync_budget()
        st.rerun()
    done = sum(bool(t["done"]) for t in D["tasks"])
    st.progress(done / max(len(D["tasks"]), 1), f"{done}/{len(D['tasks'])} done")

# ---------- Budget ----------
with tabs[4]:
    H("Budget tracker")
    B = calc(D["budget"])
    if not B:
        st.info("Add tasks in the Tasks tab and they appear here, or add items below.")
    for r in B:
        total = r["actual"] if r["actual"] > 0 else r["estimated"]
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

  
# import hashlib
# import html
# import json
# import io
# import re
# import urllib.parse
# import uuid
# from pathlib import Path

# import pandas as pd
# import streamlit as st

# st.set_page_config(page_title="Wedding Planner", page_icon="💍", layout="wide")

# DB = Path(__file__).with_name("wedding_data.json")
# SIDES = ["Bride", "Groom"]
# RSVP = ["Pending", "Confirmed", "Declined"]
# TASK_COLS = ["task", "accountable", "vendor", "contact", "due", "remarks", "done"]
# BUD_COLS = ["item", "estimated", "actual", "advance", "remaining"]
# DEFAULT_TASKS = ["Book venue", "Book hotels for guests", "Finalise guest list", "Print & send invitations",
#                  "Book catering", "Book photographer", "Arrange transport for guests"]
# COUPLE = {"groom": "Ajay", "groom_family": "Narayanan", "bride": "Pooja", "bride_family": "Sivakumar"}

# st.markdown("""<style>
# @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
# :root{--navy:#0B2447;--royal:#1D4ED8;--azure:#2F80ED;--sky:#5BC0F8;--ice:#EAF4FF;--mist:#F5F9FF;--line:#CFE0F7;--ink:#14284B}
# html,body,.stApp,.stApp p,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp li,.stApp td,.stApp th,.stApp summary{font-family:'Plus Jakarta Sans',sans-serif}
# /* keep Streamlit's icon font so arrows/icons don't show as raw text */
# [data-testid="stIconMaterial"],span[class*="material"],.material-icons,.material-symbols-rounded{font-family:'Material Symbols Rounded','Material Symbols Outlined','Material Icons'!important;font-weight:normal!important;letter-spacing:normal!important;text-transform:none!important}
# .stApp .hero h1,.stApp .sec,.stApp [data-testid="stMetricValue"],.stApp .card b{font-family:'Fraunces',serif!important}
# .stApp{background:radial-gradient(1200px 500px at 90% -10%,#DCEBFF 0%,transparent 60%),linear-gradient(180deg,#F5F9FF 0%,#EAF2FD 100%);color:var(--ink)}
# [data-testid="stHeader"]{background:transparent}
# .block-container{padding-top:2rem;max-width:1200px}

# /* hero */
# .hero{position:relative;overflow:hidden;border-radius:26px;padding:34px 36px 28px;margin-bottom:18px;color:#fff;
#   background:linear-gradient(120deg,#0B2447 0%,#14459E 55%,#2F80ED 100%);box-shadow:0 18px 40px rgba(20,69,158,.28)}
# .hero:before,.hero:after{content:"";position:absolute;border-radius:50%;pointer-events:none}
# .hero:before{width:320px;height:320px;right:-80px;top:-140px;background:radial-gradient(circle,rgba(91,192,248,.55),transparent 70%)}
# .hero:after{width:260px;height:260px;left:35%;bottom:-170px;background:radial-gradient(circle,rgba(255,196,120,.35),transparent 70%)}
# .hero .rings{font-size:2.1rem;line-height:1}
# .hero h1{font-family:'Fraunces',serif;font-weight:800;font-size:clamp(1.7rem,4.2vw,3rem);line-height:1.12;margin:.35rem 0 .5rem;padding:0;letter-spacing:.01em;
#   background:linear-gradient(90deg,#FFFFFF 0%,#BDE6FF 30%,#8FD3FF 52%,#FFD9A0 78%,#FFB8CF 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
# .hero p{margin:0;font-size:.95rem;color:#D6E8FF}
# .hero b{color:#fff}

# /* section headings */
# .sec{font-family:'Fraunces',serif;font-weight:800;font-size:1.45rem;margin:.6rem 0 .7rem;display:flex;align-items:center;gap:10px}
# .sec i{width:10px;height:26px;border-radius:6px;display:inline-block}
# .sec span{-webkit-background-clip:text;background-clip:text;color:transparent}
# .s0 i{background:linear-gradient(#2F80ED,#5BC0F8)}.s0 span{background-image:linear-gradient(90deg,#1D4ED8,#2FA4E7)}
# .s1 i{background:linear-gradient(#7C3AED,#2F80ED)}.s1 span{background-image:linear-gradient(90deg,#6D28D9,#2F80ED)}
# .s2 i{background:linear-gradient(#0EA5A4,#5BC0F8)}.s2 span{background-image:linear-gradient(90deg,#0B8F9E,#1D4ED8)}
# .s3 i{background:linear-gradient(#F59E0B,#EF6A8A)}.s3 span{background-image:linear-gradient(90deg,#E07B00,#D6336C)}

# /* tabs */
# [data-baseweb="tab-list"]{gap:6px;background:#fff;padding:6px;border-radius:16px;border:1px solid var(--line);box-shadow:0 6px 18px rgba(29,78,216,.08)}
# button[data-baseweb="tab"]{border-radius:12px;padding:8px 16px;font-weight:600;color:#47608C;background:transparent}
# button[data-baseweb="tab"][aria-selected="true"]{color:#fff;background:linear-gradient(135deg,#1D4ED8,#2F80ED);box-shadow:0 6px 14px rgba(29,78,216,.35)}
# [data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}

# /* buttons */
# .stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:12px;border:0;font-weight:600;color:#fff!important;
#   background:linear-gradient(135deg,#1D4ED8,#2F80ED);box-shadow:0 6px 14px rgba(29,78,216,.28);transition:transform .15s,box-shadow .15s}
# .stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover,.stLinkButton>a:hover{transform:translateY(-1px);box-shadow:0 10px 20px rgba(29,78,216,.38);color:#fff!important}
# .stButton>button:focus-visible,.stLinkButton>a:focus-visible{outline:3px solid #9CCBFF;outline-offset:2px}
# .stDownloadButton>button:disabled{background:#B9C9E4;box-shadow:none}

# /* inputs, expanders, metrics, forms */
# [data-baseweb="input"],[data-baseweb="select"]>div,[data-baseweb="textarea"]{border-radius:12px!important;background:#fff!important;border-color:var(--line)!important}
# [data-testid="stExpander"],[data-testid="stForm"]{background:#fff;border:1px solid var(--line)!important;border-radius:18px;box-shadow:0 6px 18px rgba(29,78,216,.06)}
# [data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-left:6px solid var(--azure);border-radius:16px;padding:14px 18px;box-shadow:0 6px 18px rgba(29,78,216,.08)}
# [data-testid="stMetricValue"]{font-family:'Fraunces',serif;color:var(--royal)}
# [data-testid="stDataFrame"],[data-testid="stDataEditor"]{border-radius:14px;overflow:hidden;border:1px solid var(--line)}
# [data-testid="stProgress"]>div>div>div{background:linear-gradient(90deg,#2F80ED,#5BC0F8)}
# hr{border-color:var(--line)!important}

# /* dashboard cards */
# .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:8px 0 18px}
# .card{border-radius:18px;padding:16px 18px;color:#fff;box-shadow:0 10px 22px rgba(20,69,158,.22)}
# .card small{opacity:.92;letter-spacing:.04em;font-size:.78rem;font-weight:600}
# .card b{display:block;font-family:'Fraunces',serif;font-size:1.65rem;margin-top:4px}
# .c1{background:linear-gradient(135deg,#1D4ED8,#2F80ED)}.c2{background:linear-gradient(135deg,#6D28D9,#3B82F6)}
# .c3{background:linear-gradient(135deg,#0E8FA8,#38BDF8)}.c4{background:linear-gradient(135deg,#F59E0B,#EF6A8A)}

# /* budget items */
# .item{background:#fff;border:1px solid var(--line);border-radius:16px;padding:13px 16px;margin-bottom:10px;box-shadow:0 4px 12px rgba(29,78,216,.06)}
# .item .top{display:flex;justify-content:space-between;gap:8px;font-weight:700;color:var(--navy)}
# .item .top span:last-child{color:var(--royal)}
# .item .row{display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px;font-size:.8rem;color:#5B6F94;margin:6px 0 8px}
# .bar{height:9px;border-radius:9px;background:#DCE9FB;overflow:hidden}
# .bar>div{height:100%;border-radius:9px;background:linear-gradient(90deg,#2F80ED,#5BC0F8)}
# @media (prefers-reduced-motion:reduce){*{transition:none!important}}
# </style>""", unsafe_allow_html=True)


# # ---------- storage ----------
# def load():
#     d = {"guests": [], "hotels": [], "tasks": [], "budget": [], "couple": dict(COUPLE)}
#     if DB.exists():
#         try:
#             d.update(json.loads(DB.read_text(encoding="utf-8")))
#         except Exception:
#             pass
#     d["couple"] = {**COUPLE, **d.get("couple", {})}
#     for t in d["tasks"]:  # migrate older files
#         t.setdefault("accountable", t.pop("owner", ""))
#         for k in ("vendor", "contact", "remarks"):
#             t.setdefault(k, "")
#     for b in d["budget"]:
#         b.setdefault("advance", b.pop("paid", 0))
#         b.setdefault("actual", 0)
#         b.pop("side", None)
#     if not d["tasks"]:
#         d["tasks"] = [{"task": t, "accountable": "", "vendor": "", "contact": "", "due": "", "remarks": "",
#                        "done": False} for t in DEFAULT_TASKS]
#     return d


# def save():
#     DB.write_text(json.dumps(st.session_state.data, ensure_ascii=False, indent=1), encoding="utf-8")


# def calc(rows):
#     for r in rows:
#         e, a, v = (float(r.get(k) or 0) for k in ("estimated", "actual", "advance"))
#         r.update(estimated=e, actual=a, advance=v, remaining=(a if a > 0 else e) - v)
#     return rows


# def sync_budget():
#     """Copy any task not yet in the budget into it (once, so deleted budget rows stay deleted)."""
#     names = {b["item"] for b in D["budget"]}
#     for t in D["tasks"]:
#         if t.get("task") and not t.get("budgeted"):
#             if t["task"] not in names:
#                 D["budget"].append({"item": t["task"], "estimated": 0, "actual": 0, "advance": 0, "remaining": 0})
#             t["budgeted"] = True
#     save()


# if "data" not in st.session_state:
#     st.session_state.data = load()
# D = st.session_state.data
# sync_budget()
# CP = D["couple"]
# TITLE = f"{CP['groom']} ({CP['groom_family']}) & {CP['bride']} ({CP['bride_family']}) Wedding"


# _sec = [0]


# def H(t):
#     """Section heading with a rotating colour accent."""
#     st.markdown(f'<div class="sec s{_sec[0] % 4}"><i></i><span>{html.escape(t)}</span></div>', unsafe_allow_html=True)
#     _sec[0] += 1


# def new_guest(name, side, headcount=1, phone="", relation="", rsvp="Pending"):
#     return {"id": uuid.uuid4().hex[:8], "name": name.strip(), "side": side, "headcount": int(headcount),
#             "phone": phone.strip(), "relation": relation.strip(), "rsvp": rsvp,
#             "hotel": "", "room": "", "checkin": "", "checkout": ""}


# # ---------- OCR (Tamil / English) ----------
# TAMIL_DIGITS = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")
# OCR_LANGS = {"Tamil + English": "tam+eng", "Tamil only": "tam", "English only": "eng"}


# def run_ocr(file, lang):
#     try:
#         import pytesseract
#         from PIL import Image, ImageOps
#     except ImportError:
#         return None, "Install OCR support: pip install pytesseract pillow"
#     try:
#         img = ImageOps.autocontrast(ImageOps.grayscale(Image.open(file)))
#         w, h = img.size
#         if w < 1600:
#             img = img.resize((w * 2, h * 2))
#         return pytesseract.image_to_string(img, lang=lang, config="--psm 6"), None
#     except Exception as e:
#         return None, f"OCR failed: {e}. Install Tesseract with the Tamil pack (tesseract-ocr-tam)."


# def parse_lines(text, side):
#     out = []
#     for line in text.translate(TAMIL_DIGITS).splitlines():
#         line = re.sub(r"^\s*\d+[.)\-:]\s+", "", line).strip(" \t|•*-_")
#         if len(line) < 2:
#             continue
#         m = re.match(r"^(.*?)[\s,:\-–=(]+(\d{1,2})\)?$", line)
#         name, count = (m.group(1).strip(), int(m.group(2))) if m else (line, 1)
#         if name:
#             out.append(new_guest(name, side, max(count, 1)))
#     return out


# # ---------- helpers ----------
# def wa_number(p):
#     d = re.sub(r"\D", "", p or "")
#     return ("91" + d) if len(d) == 10 else d


# LBL = {
#     "English": ("Accommodation Details", "Dear {n},", "We're delighted to host you. Your stay details:", "Hotel",
#                 "Address", "Location", "Room", "Check-in", "Check-out", "Hotel contact",
#                 "See you at the celebration!", "To be confirmed"),
#     "தமிழ்": ("தங்குமிட விவரங்கள்", "அன்பிற்குரிய {n},",
#              "உங்களை வரவேற்கக் காத்திருக்கிறோம். உங்கள் தங்குமிட விவரங்கள்:", "ஹோட்டல்", "முகவரி",
#              "இருப்பிடம்", "அறை எண்", "செக்-இன்", "செக்-அவுட்", "ஹோட்டல் தொடர்பு",
#              "கொண்டாட்டத்தில் சந்திப்போம்!", "விரைவில் தெரிவிக்கப்படும்"),
# }


# def room_message(g, lang):
#     if lang == "Both":
#         return room_message(g, "English") + "\n\n━━━━━━━━━━\n\n" + room_message(g, "தமிழ்")
#     h = next((x for x in D["hotels"] if x["name"] == g["hotel"]), None)
#     if not h:
#         return ""
#     t, hi, intro, lh, la, ll, lr, lci, lco, lc, bye, tbc = LBL[lang]
#     L = [f"🎉 *{TITLE} – {t}*", "", hi.format(n=g["name"]), intro, "", f"🏨 {lh}: {h['name']}",
#          f"📍 {la}: {h['address']}"]
#     if h.get("link"):
#         L.append(f"🗺️ {ll}: {h['link']}")
#     L.append(f"🚪 {lr}: {g['room'] or tbc}")
#     if g["checkin"]:
#         L.append(f"🕑 {lci}: {g['checkin']}")
#     if g["checkout"]:
#         L.append(f"🕚 {lco}: {g['checkout']}")
#     if h.get("contact"):
#         L.append(f"☎️ {lc}: {h['contact']}")
#     return "\n".join(L + ["", f"{bye} 💐"])


# def guests_df(view):
#     df = pd.DataFrame(D["guests"], columns=["id", "name", "side", "headcount", "phone", "relation", "rsvp",
#                                             "hotel", "room", "checkin", "checkout"])
#     return df if view == "All" else df[df.side == view]


# def merge_edits(edited, cols):
#     by_id = {g["id"]: g for g in D["guests"]}
#     for _, r in edited.iterrows():
#         g = by_id.get(r["id"])
#         if g is not None:
#             for c in cols:
#                 v = r[c]
#                 g[c] = int(v) if c == "headcount" and pd.notna(v) else ("" if pd.isna(v) else v)
#     save()


# def cards(items):
#     st.markdown('<div class="grid">' + "".join(
#         f'<div class="card {c}"><small>{html.escape(l.upper())}</small><b>{v}</b></div>'
#         for l, v, c in items) + "</div>", unsafe_allow_html=True)


# money = lambda x: f"₹{x:,.0f}"

# # ---------- header ----------
# st.markdown(
#     f'<div class="hero"><div class="rings">💍</div><h1>{html.escape(TITLE)}</h1>'
#     f'</div>',
#     unsafe_allow_html=True)
# with st.expander("👰🤵 COUPLE & FAMILY DETAILS"):
#     a, b, c, d = st.columns(4)
#     CP["groom"] = a.text_input("Groom", CP["groom"])
#     CP["groom_family"] = b.text_input("Groom's family", CP["groom_family"])
#     CP["bride"] = c.text_input("Bride", CP["bride"])
#     CP["bride_family"] = d.text_input("Bride's family", CP["bride_family"])
#     if st.button("Save details"):
#         save()
#         st.rerun()
# view = st.radio("VIEW", ["All", "Bride", "Groom"], horizontal=True, key="view")

# tabs = st.tabs(["📊 DASHBOARD", "👥 GUEST LIST", "🏨 ROOMS & SHARING", "✅ TASKS", "💰 BUDGET"])

# # ---------- Dashboard ----------
# with tabs[0]:
#     df = pd.DataFrame(D["guests"], columns=guests_df("All").columns)
#     if df.empty:
#         st.info("No guests yet. Add some in the Guest list tab.")
#     else:
#         cols = st.columns(3)
#         for col, side in zip(cols, SIDES + ["Total"]):
#             s = df if side == "Total" else df[df.side == side]
#             col.metric(f"{side.upper()} – HEADCOUNT", int(s.headcount.sum()), f"{len(s)} invitations")
#         a, b = st.columns(2)
#         with a:
#             H("RSVP (headcount)")
#             st.bar_chart(df.pivot_table(index="rsvp", columns="side", values="headcount", aggfunc="sum").fillna(0))
#         with b:
#             H("Accommodation")
#             assigned = df[df.hotel != ""]
#             st.metric("GUESTS WITH ROOMS", f"{len(assigned)} / {len(df)}")
#             if not assigned.empty:
#                 st.bar_chart(assigned.groupby("hotel").headcount.sum())
#     def guests_xlsx():
#         buf = io.BytesIO()
#         gdf_x = pd.DataFrame(D["guests"]).drop(columns=["id"], errors="ignore")
#         gdf_x.columns = [c.title() for c in gdf_x.columns]
#         with pd.ExcelWriter(buf, engine="openpyxl") as xw:
#             gdf_x.to_excel(xw, index=False, sheet_name="Guests")
#             ws = xw.sheets["Guests"]
#             for col in ws.columns:
#                 ws.column_dimensions[col[0].column_letter].width = min(
#                     40, max(len(str(c.value or "")) for c in col) + 3)
#         return buf.getvalue()

#     st.download_button("⬇️ Download full guest list (Excel)", guests_xlsx() if D["guests"] else b"",
#                        "guests.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#                        disabled=not D["guests"])

# # ---------- Guest list ----------
# with tabs[1]:
#     H("Add guests")
#     m1, m2, m3 = st.tabs(["✍️ ADD ONE", "📝 PASTE / TYPE LIST", "📷 SCAN LIST (TAMIL / ENGLISH)"])
#     with m1:
#         with st.form("add_guest", clear_on_submit=True):
#             a, b, c = st.columns(3)
#             name = a.text_input("Name (Tamil or English)")
#             side = b.selectbox("Side", SIDES, index=0 if view != "Groom" else 1)
#             hc = c.number_input("Headcount", 1, 50, 1)
#             d, e, f = st.columns(3)
#             phone = d.text_input("Phone / WhatsApp")
#             rel = e.text_input("Relation (e.g. Uncle, Friend)")
#             rsvp = f.selectbox("RSVP", RSVP)
#             if st.form_submit_button("➕ Add guest") and name.strip():
#                 D["guests"].append(new_guest(name, side, hc, phone, rel, rsvp))
#                 save()
#                 st.rerun()
#     with m2:
#         st.caption("One guest per line, headcount at the end, e.g. `முருகன் குடும்பம், 4` or `Ravi Kumar 2`")
#         txt = st.text_area("Guests", height=150, key="bulk_txt")
#         bs = st.radio("Side", SIDES, horizontal=True, key="bulk_side")
#         if st.button("Add all lines") and txt.strip():
#             D["guests"] += parse_lines(txt, bs)
#             save()
#             st.session_state.pop("bulk_txt", None)
#             st.rerun()
#     with m3:
#         st.caption("Upload photos of the list (Tamil, English or mixed). Review the text before adding.")
#         ups = st.file_uploader("Images", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
#         lang_name = st.radio("Language in the paper", list(OCR_LANGS), horizontal=True)
#         os_side = st.radio("These names belong to", SIDES, horizontal=True, key="ocr_side")
#         if ups and st.button("🔍 Read text"):
#             texts = []
#             for u in ups:
#                 t, err = run_ocr(u, OCR_LANGS[lang_name])
#                 if err:
#                     st.error(err)
#                     break
#                 texts.append(t)
#             else:
#                 st.session_state.ocr_text = "\n".join(texts)
#         if "ocr_text" in st.session_state:
#             edited_txt = st.text_area("Extracted text (fix mistakes here)", st.session_state.ocr_text, height=200)
#             prev = parse_lines(edited_txt, os_side)
#             st.write(f"**{len(prev)} guests detected**")
#             if prev:
#                 st.dataframe(pd.DataFrame(prev)[["name", "headcount", "side"]], hide_index=True)
#             if st.button("✅ Add these guests") and prev:
#                 D["guests"] += prev
#                 save()
#                 del st.session_state["ocr_text"]
#                 st.rerun()

#     st.divider()
#     H(f"Guest list – {view}")
#     q = st.text_input("🔎 Search", "")
#     gdf = guests_df(view)
#     if q:
#         gdf = gdf[gdf.name.str.contains(q, case=False, na=False) | gdf.relation.str.contains(q, case=False, na=False)]
#     gdf = gdf[["id", "name", "side", "headcount", "phone", "relation", "rsvp"]].copy()
#     gdf["delete"] = False
#     st.caption(f"Total headcount shown: **{int(gdf.headcount.sum())}** across {len(gdf)} invitations")
#     ed = st.data_editor(
#         gdf, hide_index=True, use_container_width=True, key=f"ge_{view}_{q}",
#         column_config={"id": None, "side": st.column_config.SelectboxColumn("Side", options=SIDES),
#                        "rsvp": st.column_config.SelectboxColumn("RSVP", options=RSVP),
#                        "headcount": st.column_config.NumberColumn("Headcount", min_value=1, max_value=50),
#                        "delete": st.column_config.CheckboxColumn("🗑️")})
#     if st.button("💾 Save changes"):
#         gone = set(ed[ed["delete"]]["id"])
#         merge_edits(ed[~ed["id"].isin(gone)], ["name", "side", "headcount", "phone", "relation", "rsvp"])
#         D["guests"] = [g for g in D["guests"] if g["id"] not in gone]
#         save()
#         st.rerun()

# # ---------- Rooms & sharing ----------
# with tabs[2]:
#     H("1. Hotels")
#     with st.form("add_hotel", clear_on_submit=True):
#         a, b = st.columns(2)
#         hn = a.text_input("Hotel name")
#         hc_ = b.text_input("Hotel contact number")
#         ha = st.text_area("Address", height=70)
#         hl = st.text_input("Google Maps link")
#         if st.form_submit_button("➕ Add hotel") and hn.strip():
#             D["hotels"].append({"name": hn.strip(), "address": ha.strip(), "link": hl.strip(), "contact": hc_.strip()})
#             save()
#             st.rerun()
#     if D["hotels"]:
#         hdf = st.data_editor(pd.DataFrame(D["hotels"]), num_rows="dynamic", use_container_width=True,
#                              hide_index=True, key="hotel_ed")
#         if st.button("💾 Save hotels"):
#             D["hotels"] = [r for r in hdf.fillna("").to_dict("records") if r["name"]]
#             save()
#             st.rerun()

#     st.divider()
#     H("2. Allot rooms")
#     show = st.radio("SHOW GUESTS", ["All", "With rooms", "Without rooms"], horizontal=True)
#     rdf = guests_df(view)[["id", "name", "side", "headcount", "hotel", "room", "checkin", "checkout"]]
#     if show == "With rooms":
#         rdf = rdf[rdf.hotel != ""]
#     elif show == "Without rooms":
#         rdf = rdf[rdf.hotel == ""]
#     st.caption(f"{len(rdf)} guests shown")
#     red = st.data_editor(
#         rdf, hide_index=True, use_container_width=True, key=f"re_{view}_{show}",
#         disabled=["name", "side", "headcount"],
#         column_config={"id": None, "hotel": st.column_config.SelectboxColumn("Hotel", options=[""] + [h["name"] for h in D["hotels"]]),
#                        "room": "Room no.", "checkin": "Check-in (date/time)", "checkout": "Check-out"})
#     if st.button("💾 Save room allotments"):
#         merge_edits(red, ["hotel", "room", "checkin", "checkout"])
#         st.rerun()

#     st.divider()
#     H("3. Share room details")
#     ass = [g for g in D["guests"] if g["hotel"] and (view == "All" or g["side"] == view)]
#     if not ass:
#         st.info("Allot a hotel to a guest to enable sharing.")
#     else:
#         lang = st.radio("MESSAGE LANGUAGE", ["English", "தமிழ்", "Both"], horizontal=True)
#         pick = st.selectbox("Guest", ass, format_func=lambda g: f"{g['name']} ({g['side']})")
#         default = room_message(pick, lang)
#         msg = st.text_area("✏️ Edit the message before sending", default, height=280,
#                            key=f"msg_{pick['id']}_{lang}_{hashlib.md5(default.encode()).hexdigest()[:8]}")
#         num = wa_number(pick["phone"])
#         st.link_button("📲 Send on WhatsApp" + ("" if num else " (pick a contact)"),
#                        f"https://wa.me/{num}?text={urllib.parse.quote(msg)}")
#         with st.expander("Quick-send links for all guests with rooms (uses the selected language, unedited)"):
#             rows = [{"Guest": g["name"], "Side": g["side"], "Hotel": g["hotel"], "Room": g["room"],
#                      "WhatsApp": f"https://wa.me/{wa_number(g['phone'])}?text={urllib.parse.quote(room_message(g, lang))}"
#                      if g["phone"] else None} for g in ass]
#             st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
#                          column_config={"WhatsApp": st.column_config.LinkColumn("Send", display_text="📲 WhatsApp")})

# # ---------- Tasks ----------
# with tabs[3]:
#     H("Wedding checklist")
#     st.caption("New tasks are copied to the Budget tab automatically when you save.")
#     tdf = st.data_editor(
#         pd.DataFrame(D["tasks"], columns=TASK_COLS + ["budgeted"]), num_rows="dynamic",
#         use_container_width=True, hide_index=True, key="task_ed",
#         column_config={"budgeted": None, "done": st.column_config.CheckboxColumn("Done"),
#                        "accountable": "Accountable", "vendor": "Vendor", "contact": "Contact number",
#                        "due": "Due date", "remarks": "Remarks"})
#     if st.button("💾 Save tasks"):
#         D["tasks"] = [r for r in tdf.fillna("").to_dict("records") if r["task"]]
#         sync_budget()
#         st.rerun()
#     done = sum(bool(t["done"]) for t in D["tasks"])
#     st.progress(done / max(len(D["tasks"]), 1), f"{done}/{len(D['tasks'])} done")

# # ---------- Budget ----------
# with tabs[4]:
#     H("Budget tracker")
#     B = calc(D["budget"])
#     if not B:
#         st.info("Add tasks in the Tasks tab and they appear here, or add items below.")
#     for r in B:
#         total = r["actual"] if r["actual"] > 0 else r["estimated"]
#         pct = min(100, int(r["advance"] / total * 100)) if total else 0
#         st.markdown(
#             f'<div class="item"><div class="top"><span>{html.escape(str(r["item"]))}</span>'
#             f'<span>{money(r["remaining"])} left</span></div>'
#             f'<div class="row"><span>Est {money(r["estimated"])}</span><span>Actual {money(r["actual"])}</span>'
#             f'<span>Advance {money(r["advance"])}</span></div>'
#             f'<div class="bar"><div style="width:{pct}%"></div></div></div>', unsafe_allow_html=True)

#     with st.expander("✏️ EDIT / ADD / DELETE ITEMS", expanded=not B):
#         st.caption("Edit cells directly. To delete, tick the row's left checkbox and press the Delete key / bin icon. "
#                    "Remaining = (actual, or estimate if actual is blank) − advance.")
#         bdf = st.data_editor(
#             pd.DataFrame(B, columns=BUD_COLS), num_rows="dynamic", use_container_width=True, hide_index=True,
#             disabled=["remaining"], key="bud_ed",
#             column_config={"item": "Item", **{k: st.column_config.NumberColumn(k.title() + " (₹)", min_value=0, step=500)
#                                               for k in ("estimated", "actual", "advance")},
#                            "remaining": st.column_config.NumberColumn("Remaining (₹)")})
#         bdf = bdf.fillna({"item": "", "estimated": 0, "actual": 0, "advance": 0, "remaining": 0})
#         if st.button("💾 Save budget"):
#             D["budget"] = calc([r for r in bdf.to_dict("records") if str(r["item"]).strip()])
#             save()
#             st.rerun()

#     live = calc(bdf.to_dict("records")) if "bdf" in dir() else B
#     H("Totals")
#     cards([("Estimated", money(sum(r["estimated"] for r in live)), "c1"),
#            ("Actual", money(sum(r["actual"] for r in live)), "c2"),
#            ("Advance paid", money(sum(r["advance"] for r in live)), "c3"),
#            ("Remaining", money(sum(r["remaining"] for r in live)), "c4")])
