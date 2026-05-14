import streamlit as st
import pandas as pd
import math, re, json, datetime
from pathlib import Path
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                     Paragraph, Spacer)
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

st.set_page_config(page_title="Engineering Unit Converter Pro",
                   page_icon="🔄", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""<style>
div[data-testid="stMetric"]{background:#f8f9fa;border:1px solid #dee2e6;
border-radius:8px;padding:12px 16px;}
</style>""", unsafe_allow_html=True)

CATEGORIES = {
    "🌡️ Temperature": {"units": ["°C", "°F", "K", "°R"], "type": "temperature"},
    "📐 Length": {"units_to_base": {"m":1.0,"mm":1e-3,"cm":1e-2,"km":1e3,"in":0.0254,"ft":0.3048,"yd":0.9144,"mile":1609.344,"μm (micron)":1e-6}},
    "⚖️ Mass": {"units_to_base": {"kg":1.0,"g":1e-3,"mg":1e-6,"tonne (MT)":1e3,"lb":0.45359237,"oz":0.028349523125,"short ton (US)":907.18474,"long ton (UK)":1016.0469088}},
    "🔴 Pressure": {"units_to_base": {"Pa":1.0,"kPa":1e3,"MPa":1e6,"bar":1e5,"mbar":1e2,"psi (lbf/in²)":6894.757293168,"atm":101325.0,"mmHg (torr)":133.322387415,"inHg":3386.389,"mmH₂O":9.80665,"inH₂O":249.08891,"kg/cm²":98066.5}},
    "🌊 Vol. Flow Rate": {"units_to_base": {"m³/h":1.0,"m³/s":3600.0,"m³/min":60.0,"L/h":1e-3,"L/min (LPM)":0.06,"L/s":3.6,"USgal/min (GPM)":0.2271247,"USgal/h (GPH)":0.003785412,"ft³/h (CFH)":0.028316847,"ft³/min (CFM)":1.699011,"bbl/day (BOPD)":0.006624,"bbl/h":0.158987295}},
    "⚡ Mass Flow Rate": {"units_to_base": {"kg/h":1.0,"kg/s":3600.0,"kg/min":60.0,"g/s":3.6,"g/min":0.06,"lb/h":0.45359237,"lb/s":1632.9325,"lb/min":27.2155422,"tonne/h (MT/h)":1000.0,"short ton/h":907.18474}},
    "📦 Volume": {"units_to_base": {"m³":1.0,"L":1e-3,"mL":1e-6,"cm³ (cc)":1e-6,"ft³":0.028316846592,"in³":1.6387064e-5,"US gallon":0.003785411784,"UK gallon":0.00454609,"barrel (oil)":0.158987295}},
    "📏 Area": {"units_to_base": {"m²":1.0,"cm²":1e-4,"mm²":1e-6,"km²":1e6,"ft²":0.09290304,"in²":6.4516e-4,"yd²":0.83612736,"acre":4046.8564224,"hectare":1e4}},
    "🔥 Energy / Heat": {"units_to_base": {"J":1.0,"kJ":1e3,"MJ":1e6,"GJ":1e9,"cal":4.184,"kcal":4184.0,"BTU":1055.05585,"MMBTU":1.05505585e9,"kWh":3.6e6,"MWh":3.6e9,"therm":1.05505585e8,"hp·h":2684519.5}},
    "⚡ Power / Heat Rate": {"units_to_base": {"W":1.0,"kW":1e3,"MW":1e6,"hp":745.69987,"BTU/h":0.29307107,"MMBTU/h":293071.07,"kcal/h":1.163,"ton (refrig.)":3516.853,"GJ/h":277777.778}},
    "🧪 Density": {"units_to_base": {"kg/m³":1.0,"g/cm³":1000.0,"g/mL":1000.0,"kg/L":1000.0,"lb/ft³":16.01846337,"lb/gal (US)":119.826427,"lb/in³":27679.90471}},
    "💧 Dynamic Viscosity": {"units_to_base": {"Pa·s":1.0,"mPa·s (cP)":1e-3,"P (poise)":0.1,"cP (centipoise)":1e-3,"lb/(ft·s)":1.488164,"lb/(ft·h)":4.133789e-4}},
    "💨 Kinematic Viscosity": {"units_to_base": {"m²/s":1.0,"mm²/s (cSt)":1e-6,"cSt (centistokes)":1e-6,"St (stokes)":1e-4,"ft²/s":0.09290304,"ft²/h":2.58064e-5}},
    "🌬️ Velocity": {"units_to_base": {"m/s":1.0,"km/h":0.277778,"ft/s":0.3048,"ft/min":0.00508,"mph":0.44704,"knot":0.514444}},
    "🔄 Force": {"units_to_base": {"N":1.0,"kN":1e3,"lbf":4.448222,"kgf":9.80665,"dyne":1e-5}},
    "🔩 Torque": {"units_to_base": {"N·m":1.0,"kN·m":1e3,"lbf·ft":1.355818,"lbf·in":0.1129848,"kgf·m":9.80665,"kgf·cm":0.0980665}},
    "🔥 Heat Flux": {"units_to_base": {"W/m²":1.0,"kW/m²":1e3,"BTU/(h·ft²)":3.154591,"kcal/(h·m²)":1.163,"cal/(s·cm²)":41840.0}},
    "🌡️ Thermal Conductivity": {"units_to_base": {"W/(m·K)":1.0,"W/(m·°C)":1.0,"BTU/(h·ft·°F)":1.730735,"kcal/(h·m·°C)":1.163,"cal/(s·cm·°C)":418.4}},
    "♨️ Heat Transfer Coeff.": {"units_to_base": {"W/(m²·K)":1.0,"W/(m²·°C)":1.0,"BTU/(h·ft²·°F)":5.678263,"kcal/(h·m²·°C)":1.163}},
}

PIPE_SCHEDULE = {
    "1/2":{"od":0.840,10:0.083,40:0.109,80:0.147,160:None},
    "3/4":{"od":1.050,10:0.083,40:0.113,80:0.154,160:None},
    "1":{"od":1.315,10:0.109,40:0.133,80:0.179,160:0.250},
    "1-1/4":{"od":1.660,10:0.109,40:0.140,80:0.191,160:None},
    "1-1/2":{"od":1.900,10:0.109,40:0.145,80:0.200,160:None},
    "2":{"od":2.375,10:0.109,40:0.154,80:0.218,160:0.344},
    "2-1/2":{"od":2.875,10:0.120,40:0.203,80:0.276,160:None},
    "3":{"od":3.500,10:0.120,40:0.216,80:0.300,160:0.438},
    "3-1/2":{"od":4.000,10:0.120,40:0.226,80:0.318,160:None},
    "4":{"od":4.500,10:0.120,40:0.237,80:0.337,160:0.531},
    "5":{"od":5.563,10:0.134,40:0.258,80:0.375,160:0.625},
    "6":{"od":6.625,10:0.134,40:0.280,80:0.432,160:0.719},
    "8":{"od":8.625,10:0.148,40:0.322,80:0.500,160:0.906},
    "10":{"od":10.750,10:0.165,40:0.365,80:0.500,160:1.125},
    "12":{"od":12.750,10:0.180,40:0.406,80:0.500,160:1.312},
    "14":{"od":14.000,10:0.250,40:0.438,80:0.594,160:1.406},
    "16":{"od":16.000,10:0.250,40:0.500,80:0.656,160:1.594},
    "18":{"od":18.000,10:0.250,40:0.562,80:0.750,160:1.781},
    "20":{"od":20.000,10:0.250,40:0.594,80:0.812,160:1.969},
    "24":{"od":24.000,10:0.250,40:0.688,80:0.969,160:2.344},
}

MATERIALS = {
    "A106 Gr.B (CS)":{"S":20000,"note":"Carbon Steel, to 400°F"},
    "A333 Gr.6 (LT-CS)":{"S":20000,"note":"Low-Temp CS, to -50°F"},
    "A312 TP304 (SS)":{"S":20000,"note":"SS 304, to 600°F"},
    "A312 TP304L (SS)":{"S":16700,"note":"SS 304L, to 600°F"},
    "A312 TP316 (SS)":{"S":20000,"note":"SS 316, to 600°F"},
    "A312 TP316L (SS)":{"S":16700,"note":"SS 316L, to 600°F"},
    "A335 P11 (Alloy)":{"S":17100,"note":"1¼Cr-½Mo, to 1050°F"},
    "A335 P22 (Alloy)":{"S":15000,"note":"2¼Cr-1Mo, to 1050°F"},
    "API 5L Gr.B":{"S":20000,"note":"Line Pipe, to 400°F"},
    "API 5L X42":{"S":25200,"note":"Line Pipe X42"},
    "API 5L X52":{"S":31200,"note":"Line Pipe X52"},
    "API 5L X65":{"S":39000,"note":"Line Pipe X65"},
    "Custom":{"S":20000,"note":"User-defined"},
}

COMMON_GASES = {
    "Air":{"M":28.97,"k":1.40},"Nitrogen (N2)":{"M":28.01,"k":1.40},
    "Oxygen (O2)":{"M":32.00,"k":1.40},"Hydrogen (H2)":{"M":2.016,"k":1.41},
    "Methane (CH4)":{"M":16.04,"k":1.31},"Ethane (C2H6)":{"M":30.07,"k":1.19},
    "Ethylene (C2H4)":{"M":28.05,"k":1.24},"Propane (C3H8)":{"M":44.10,"k":1.13},
    "CO2":{"M":44.01,"k":1.29},"Steam (H2O)":{"M":18.015,"k":1.33},
    "Ammonia (NH3)":{"M":17.03,"k":1.31},"Natural Gas (typ)":{"M":18.0,"k":1.27},
    "Custom":{"M":28.97,"k":1.40},
}

UNIT_ALIASES = {
    "pa":("🔴 Pressure","Pa"),"kpa":("🔴 Pressure","kPa"),
    "mpa":("🔴 Pressure","MPa"),"bar":("🔴 Pressure","bar"),
    "mbar":("🔴 Pressure","mbar"),"psi":("🔴 Pressure","psi (lbf/in²)"),
    "atm":("🔴 Pressure","atm"),"mmhg":("🔴 Pressure","mmHg (torr)"),
    "torr":("🔴 Pressure","mmHg (torr)"),"inhg":("🔴 Pressure","inHg"),
    "inh2o":("🔴 Pressure","inH₂O"),"mmh2o":("🔴 Pressure","mmH₂O"),
    "kg/cm2":("🔴 Pressure","kg/cm²"),"ksc":("🔴 Pressure","kg/cm²"),
    "degc":("🌡️ Temperature","°C"),"celsius":("🌡️ Temperature","°C"),
    "degf":("🌡️ Temperature","°F"),"fahrenheit":("🌡️ Temperature","°F"),
    "kelvin":("🌡️ Temperature","K"),"rankine":("🌡️ Temperature","°R"),
    "mm":("📐 Length","mm"),"cm":("📐 Length","cm"),"km":("📐 Length","km"),
    "inch":("📐 Length","in"),"inches":("📐 Length","in"),
    "ft":("📐 Length","ft"),"feet":("📐 Length","ft"),
    "mile":("📐 Length","mile"),"micron":("📐 Length","μm (micron)"),
    "kg":("⚖️ Mass","kg"),"lb":("⚖️ Mass","lb"),"lbs":("⚖️ Mass","lb"),
    "oz":("⚖️ Mass","oz"),"tonne":("⚖️ Mass","tonne (MT)"),
    "gpm":("🌊 Vol. Flow Rate","USgal/min (GPM)"),
    "m3/h":("🌊 Vol. Flow Rate","m³/h"),
    "lpm":("🌊 Vol. Flow Rate","L/min (LPM)"),
    "cfm":("🌊 Vol. Flow Rate","ft³/min (CFM)"),
    "bpd":("🌊 Vol. Flow Rate","bbl/day (BOPD)"),
    "bbl/h":("🌊 Vol. Flow Rate","bbl/h"),
    "kg/h":("⚡ Mass Flow Rate","kg/h"),"kg/s":("⚡ Mass Flow Rate","kg/s"),
    "lb/h":("⚡ Mass Flow Rate","lb/h"),"lb/s":("⚡ Mass Flow Rate","lb/s"),
    "tonne/h":("⚡ Mass Flow Rate","tonne/h (MT/h)"),
    "liter":("📦 Volume","L"),"litre":("📦 Volume","L"),
    "gallon":("📦 Volume","US gallon"),"bbl":("📦 Volume","barrel (oil)"),
    "kj":("🔥 Energy / Heat","kJ"),"btu":("🔥 Energy / Heat","BTU"),
    "mmbtu":("🔥 Energy / Heat","MMBTU"),"kcal":("🔥 Energy / Heat","kcal"),
    "kwh":("🔥 Energy / Heat","kWh"),
    "kw":("⚡ Power / Heat Rate","kW"),"hp":("⚡ Power / Heat Rate","hp"),
    "btu/h":("⚡ Power / Heat Rate","BTU/h"),
    "mmbtu/h":("⚡ Power / Heat Rate","MMBTU/h"),
    "kg/m3":("🧪 Density","kg/m³"),"g/cm3":("🧪 Density","g/cm³"),
    "lb/ft3":("🧪 Density","lb/ft³"),
    "cp":("💧 Dynamic Viscosity","cP (centipoise)"),
    "pa.s":("💧 Dynamic Viscosity","Pa·s"),
    "cst":("💨 Kinematic Viscosity","cSt (centistokes)"),
    "m/s":("🌬️ Velocity","m/s"),"km/h":("🌬️ Velocity","km/h"),
    "ft/s":("🌬️ Velocity","ft/s"),"mph":("🌬️ Velocity","mph"),
    "lbf":("🔄 Force","lbf"),"kgf":("🔄 Force","kgf"),
    "m2":("📏 Area","m²"),"ft2":("📏 Area","ft²"),
    "acre":("📏 Area","acre"),"hectare":("📏 Area","hectare"),
}

# ═══════════ HELPER FUNCTIONS ═══════════

def temp_convert(val, fu, tu):
    if fu=="°C": c=val
    elif fu=="°F": c=(val-32)*5/9
    elif fu=="K": c=val-273.15
    elif fu=="°R": c=(val-491.67)*5/9
    else: return None
    if tu=="°C": return c
    elif tu=="°F": return c*9/5+32
    elif tu=="K": return c+273.15
    elif tu=="°R": return (c+273.15)*9/5
    return None

def linear_convert(val, ff, tf):
    return val * ff / tf

def do_convert(val, ck, fu, tu):
    cat = CATEGORIES[ck]
    if cat.get("type")=="temperature": return temp_convert(val, fu, tu)
    return linear_convert(val, cat["units_to_base"][fu], cat["units_to_base"][tu])

def get_unit_list(ck):
    cat = CATEGORIES[ck]
    return cat["units"] if cat.get("type")=="temperature" else list(cat["units_to_base"].keys())

def recommend_valve_size(cv):
    for mx, sz in [(10,"1\""),(30,"1½\""),(75,"2\""),(150,"3\""),(300,"4\""),
                    (500,"6\""),(1000,"8\""),(2000,"10\""),(3000,"12\"")]:
        if cv <= mx: return sz
    return "14\" or larger"

def parse_nl_query(text):
    text = text.strip()
    p1 = r"(?:convert\s+)?(-?\d+\.?\d*(?:e[+-]?\d+)?)\s+(.+?)\s+(?:to|in|into|->|=)\s+(.+)"
    m = re.match(p1, text, re.IGNORECASE)
    if m: return _resolve(float(m.group(1)), m.group(2).strip(), m.group(3).strip())
    p2 = r"how\s+many\s+(.+?)\s+(?:in|are\s+in)\s+(-?\d+\.?\d*(?:e[+-]?\d+)?)\s+(.+)"
    m = re.match(p2, text, re.IGNORECASE)
    if m: return _resolve(float(m.group(2)), m.group(3).strip(), m.group(1).strip())
    p3 = r"what\s+is\s+(-?\d+\.?\d*(?:e[+-]?\d+)?)\s+(.+?)\s+(?:in|to)\s+(.+)"
    m = re.match(p3, text, re.IGNORECASE)
    if m: return _resolve(float(m.group(1)), m.group(2).strip(), m.group(3).strip())
    return None

def _resolve(val, ft, tt):
    fi, ti = UNIT_ALIASES.get(ft.lower()), UNIT_ALIASES.get(tt.lower())
    if not fi or not ti: return {"error": f"Unrecognised unit(s): '{ft}' / '{tt}'"}
    if fi[0] != ti[0]: return {"error": f"Cannot convert between {fi[0]} and {ti[0]}"}
    result = do_convert(val, fi[0], fi[1], ti[1])
    return {"value":val,"from":fi[1],"to":ti[1],"category":fi[0],"result":result}

FAV_FILE = Path("favorites.json")
def load_favorites():
    if FAV_FILE.exists():
        try: return json.loads(FAV_FILE.read_text())
        except: return []
    return []
def save_favorites(favs):
    FAV_FILE.write_text(json.dumps(favs, indent=2))

def generate_pdf(title, sections):
    if not HAS_PDF: return None
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=15*mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    sty = getSampleStyleSheet()
    story = [Paragraph(title, sty["Title"]), Spacer(1,3*mm)]
    now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    story += [Paragraph(f"Generated: {now}", sty["Normal"]), Spacer(1,6*mm)]
    for sec in sections:
        if sec.get("heading"):
            story += [Paragraph(sec["heading"], sty["Heading2"]), Spacer(1,2*mm)]
        for ln in sec.get("lines", []):
            story += [Paragraph(str(ln), sty["Normal"]), Spacer(1,1*mm)]
        if sec.get("table_headers") and sec.get("table_rows"):
            data = [sec["table_headers"]] + sec["table_rows"]
            t = Table(data, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a5276")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),8),
                ("ALIGN",(0,0),(-1,-1),"CENTER"),
                ("GRID",(0,0),(-1,-1),0.5,colors.grey),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f0f4f8")]),
                ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ]))
            story.append(t)
        story.append(Spacer(1,4*mm))
    story += [Spacer(1,6*mm), Paragraph("Engineering Unit Converter Pro", sty["Italic"])]
    doc.build(story)
    return buf.getvalue()

# ═══════════ SESSION STATE ═══════════
for k, v in [("favorites",None),("from_unit_name",None),("to_unit_name",None),
             ("prev_category",None),("nl_query_text","")]:
    if k not in st.session_state:
        st.session_state[k] = load_favorites() if k=="favorites" and v is None else v

# ═══════════ SIDEBAR ═══════════
with st.sidebar:
    st.markdown("# 🔄"); st.header("Settings")
    category = st.selectbox("📂 Category", list(CATEGORIES.keys()), index=3, key="cat_sel")
    st.markdown("---")
    api_key = st.text_input("🔑 OpenAI API Key *(optional)*", type="password", key="api_key")
    st.markdown("---")
    st.markdown("### 📌 Quick Reference")
    st.markdown("- **1 atm** = 101.325 kPa\n- **1 bar** = 14.504 psi\n"
                "- **1 in** = 25.4 mm\n- **1 m³/h** = 4.403 GPM\n"
                "- **1 BTU** = 1.055 kJ\n- **1 cP** = 1 mPa·s\n- **1 hp** = 0.7457 kW")
    st.markdown("---"); st.caption("Built with ❤️ for Process Engineers")

unit_list = get_unit_list(category)
if category != st.session_state.prev_category:
    st.session_state.from_unit_name = unit_list[0]
    st.session_state.to_unit_name = unit_list[min(1,len(unit_list)-1)]
    st.session_state.prev_category = category

st.title("🔄 Engineering Unit Converter Pro")
st.markdown("**Comprehensive conversion suite — Cv Calculator, Pipe Rating, PDF Export & AI**")

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs(
    ["🔄 Converter","🔩 Pipe Schedule","🔧 Cv Calculator",
     "🧮 Pipe Rating","⭐ Favourites","🤖 AI Assistant"])

# ══════════ TAB 1 — CONVERTER ══════════
with tab1:
    st.subheader(f"{category}")
    def swap_units():
        st.session_state.from_unit_name, st.session_state.to_unit_name = (
            st.session_state.to_unit_name, st.session_state.from_unit_name)
    def safe_idx(n,lst,d=0): return lst.index(n) if n in lst else d
    fi = safe_idx(st.session_state.from_unit_name, unit_list, 0)
    ti = safe_idx(st.session_state.to_unit_name, unit_list, min(1,len(unit_list)-1))
    c1,cs,c2 = st.columns([5,1,5])
    with c1:
        from_unit = st.selectbox("**From**", unit_list, index=fi, key="from_sel")
        input_value = st.number_input("Enter value", value=1.0, format="%.6g", key="inp_val")
    with cs:
        st.markdown(""); st.markdown("")
        st.button("🔄 Swap", on_click=swap_units, use_container_width=True)
    with c2:
        to_unit = st.selectbox("**To**", unit_list, index=ti, key="to_sel")
        result = do_convert(input_value, category, from_unit, to_unit)
        st.text_input("Result", value=f"{result:.6g}", disabled=True, key="res_disp")
    st.session_state.from_unit_name = from_unit
    st.session_state.to_unit_name = to_unit
    st.success(f"### ✅  {input_value:.6g}  {from_unit}  =  **{result:.6g}  {to_unit}**")
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("⭐ Add to Favourites", key="add_fav"):
            entry = {"category":category,"from":from_unit,"to":to_unit}
            if entry not in st.session_state.favorites:
                st.session_state.favorites.append(entry)
                save_favorites(st.session_state.favorites); st.toast("Added! ⭐")
            else: st.toast("Already saved", icon="ℹ️")
    with bc2:
        pdf1 = generate_pdf("Unit Conversion Report",[{"heading":"Result",
            "lines":[f"{input_value:.6g} {from_unit} = {result:.6g} {to_unit}",
                     f"Category: {category}"]}])
        if pdf1:
            st.download_button("📄 Export PDF", pdf1, file_name="conversion.pdf",
                               mime="application/pdf", key="pdf_conv")
    with st.expander("📊 Full Conversion Table", expanded=False):
        rows = [{"Unit":u, f"1 {from_unit} =":f"{do_convert(1.0,category,from_unit,u):.6g}"}
                for u in unit_list]
        st.table(pd.DataFrame(rows))
    with st.expander("📋 Batch Conversion", expanded=False):
        bi = st.text_input("Values (comma-separated)", value="1, 10, 100, 1000", key="batch")
        if bi:
            try:
                vals=[float(v.strip()) for v in bi.split(",") if v.strip()]
                st.table(pd.DataFrame([{from_unit:f"{v:.6g}",
                    to_unit:f"{do_convert(v,category,from_unit,to_unit):.6g}"} for v in vals]))
            except: st.error("Enter valid numbers separated by commas.")

# ══════════ TAB 2 — PIPE SCHEDULE ══════════
with tab2:
    st.subheader("🔩 Pipe Schedule Lookup  (ASME B36.10M)")
    pc1,pc2 = st.columns(2)
    with pc1:
        sel_nps = st.selectbox("NPS (inches)", list(PIPE_SCHEDULE.keys()), index=11, key="nps_sel")
    with pc2:
        du = st.radio("Units", ["inches","mm"], horizontal=True, key="pipe_u")
    mul = 25.4 if du=="mm" else 1.0
    pipe = PIPE_SCHEDULE[sel_nps]; od = pipe["od"]
    st.markdown(f"#### NPS {sel_nps} in  —  OD = **{od*mul:.3f} {du}**")
    drows = []
    for sch in [10,40,80,160]:
        wt = pipe.get(sch)
        if wt:
            idv=od-2*wt; area=math.pi/4*idv**2; wpf=10.6906*(od-wt)*wt
            if du=="mm":
                drows.append({"Sch":f"{sch}",f"Wall({du})":f"{wt*mul:.2f}",
                    f"ID({du})":f"{idv*mul:.2f}","Area(mm²)":f"{area*645.16:.1f}",
                    "Wt(kg/m)":f"{wpf*1.488:.2f}"})
            else:
                drows.append({"Sch":f"{sch}",f"Wall({du})":f"{wt:.4f}",
                    f"ID({du})":f"{idv:.4f}","Area(in²)":f"{area:.4f}",
                    "Wt(lb/ft)":f"{wpf:.2f}"})
        else:
            drows.append({"Sch":f"{sch}",f"Wall({du})":"N/A",f"ID({du})":"N/A",
                "Area(mm²)" if du=="mm" else "Area(in²)":"N/A",
                "Wt(kg/m)" if du=="mm" else "Wt(lb/ft)":"N/A"})
    st.table(pd.DataFrame(drows))
    ps_pdf = generate_pdf("Pipe Schedule Report",[{"heading":f"NPS {sel_nps} in — OD {od*mul:.3f} {du}",
        "table_headers":list(drows[0].keys()),"table_rows":[list(r.values()) for r in drows]}])
    if ps_pdf:
        st.download_button("📄 Export PDF", ps_pdf, file_name="pipe_schedule.pdf",
                           mime="application/pdf", key="pdf_pipe")
    with st.expander("📊 Complete Reference Table", expanded=False):
        rr=[]
        for nps,data in PIPE_SCHEDULE.items():
            row={"NPS":nps,f"OD({du})":f"{data['od']*mul:.3f}"}
            for s in [10,40,80,160]:
                w=data.get(s)
                if w: row[f"S{s}Wall"]=f"{w*mul:.3f}"; row[f"S{s}ID"]=f"{(data['od']-2*w)*mul:.3f}"
                else: row[f"S{s}Wall"]="-"; row[f"S{s}ID"]="-"
            rr.append(row)
        st.dataframe(pd.DataFrame(rr), use_container_width=True, hide_index=True)


# ══════════ TAB 3 — Cv CALCULATOR ══════════
with tab3:
    st.subheader("🔧 Control Valve Cv Calculator")
    st.caption("ISA/IEC 60534 — Liquid & Gas/Vapor Service")

    svc = st.radio("Service Type", ["Liquid", "Gas / Vapor"], horizontal=True, key="cv_svc")

    if svc == "Liquid":
        st.markdown("**Formula:** &nbsp; Cv = Q × √(G_f / ΔP)")
        lc1, lc2 = st.columns(2)
        with lc1:
            st.markdown("##### 📥 Process Conditions")
            Q = st.number_input("Flow Rate, Q (US GPM)", value=500.0, min_value=0.0, step=10.0, key="cv_q")
            P1 = st.number_input("Upstream Pressure, P1 (psia)", value=150.0, min_value=0.01, step=5.0, key="cv_p1l")
            P2 = st.number_input("Downstream Pressure, P2 (psia)", value=100.0, min_value=0.0, step=5.0, key="cv_p2l")
            fluid = st.selectbox("Fluid", ["Water (1.0)", "Light HC (0.65)", "Heavy Oil (0.92)", "Custom"], key="cv_fl")
            if fluid == "Custom":
                Gf = st.number_input("Specific Gravity, Gf", value=1.0, min_value=0.01, step=0.01, key="cv_gf")
            else:
                Gf = {"Water (1.0)":1.0, "Light HC (0.65)":0.65, "Heavy Oil (0.92)":0.92}[fluid]
        with lc2:
            st.markdown("##### 📊 Results")
            dP = P1 - P2
            if dP <= 0:
                st.error("⚠️ P1 must be greater than P2!")
            else:
                Cv = Q * math.sqrt(Gf / dP)
                vsize = recommend_valve_size(Cv)
                st.metric("ΔP (psi)", f"{dP:.2f}")
                st.metric("Calculated Cv", f"{Cv:.2f}")
                st.metric("Specific Gravity", f"{Gf:.3f}")
                st.info(f"💡 Recommended Valve Size: **{vsize}** (approximate)")
                st.markdown("---")
                summary = {"Parameter": ["Flow Rate (GPM)", "P1 (psia)", "P2 (psia)",
                           "ΔP (psi)", "Specific Gravity", "Calculated Cv", "Suggested Size"],
                           "Value": [f"{Q:.1f}", f"{P1:.1f}", f"{P2:.1f}",
                           f"{dP:.2f}", f"{Gf:.3f}", f"{Cv:.2f}", vsize]}
                st.table(pd.DataFrame(summary))
                # PDF export
                cv_pdf = generate_pdf("Cv Calculator Report — Liquid Service", [
                    {"heading": "Input Parameters",
                     "lines": [f"Flow Rate: {Q:.1f} GPM", f"P1: {P1:.1f} psia",
                               f"P2: {P2:.1f} psia", f"Specific Gravity: {Gf:.3f}"]},
                    {"heading": "Results",
                     "lines": [f"ΔP: {dP:.2f} psi", f"Calculated Cv: {Cv:.2f}",
                               f"Recommended Size: {vsize}"]},
                    {"heading": "Formula",
                     "lines": ["Cv = Q x sqrt(Gf / dP)  — ISA/IEC 60534"]}])
                if cv_pdf:
                    st.download_button("📄 Export PDF", cv_pdf, file_name="cv_liquid.pdf",
                                       mime="application/pdf", key="pdf_cvl")

    else:  # Gas / Vapor
        st.markdown("**Formula:** &nbsp; Cv = W / (N₆ × F_P × Y × √(x × P₁ × M / T))")
        st.markdown("*N₆ = 63.3 (W in lb/h, P1 in psia, T in °R)*")
        gc1, gc2 = st.columns(2)
        with gc1:
            st.markdown("##### 📥 Process Conditions")
            W = st.number_input("Mass Flow, W (lb/h)", value=10000.0, min_value=0.0, step=100.0, key="cv_w")
            P1g = st.number_input("Upstream Pressure, P1 (psia)", value=150.0, min_value=0.01, step=5.0, key="cv_p1g")
            P2g = st.number_input("Downstream Pressure, P2 (psia)", value=100.0, min_value=0.0, step=5.0, key="cv_p2g")
            T_f = st.number_input("Temperature (°F)", value=200.0, step=10.0, key="cv_tf")
            gas_sel = st.selectbox("Gas / Vapor", list(COMMON_GASES.keys()), key="cv_gas")
            if gas_sel == "Custom":
                M = st.number_input("Molecular Weight, M", value=28.97, min_value=1.0, step=0.1, key="cv_m")
                k = st.number_input("Ratio of Specific Heats, k (Cp/Cv)", value=1.4, min_value=1.0, max_value=2.0, step=0.01, key="cv_k")
            else:
                M = COMMON_GASES[gas_sel]["M"]
                k = COMMON_GASES[gas_sel]["k"]
            xT = st.number_input("xT (valve critical pressure drop ratio)", value=0.70, min_value=0.1, max_value=1.0, step=0.01, key="cv_xt",
                                 help="Typical: Globe=0.70, Ball=0.55, Butterfly=0.35")
        with gc2:
            st.markdown("##### 📊 Results")
            dPg = P1g - P2g
            if dPg <= 0:
                st.error("⚠️ P1 must be greater than P2!")
            elif P1g <= 0:
                st.error("⚠️ P1 must be positive!")
            else:
                T_R = T_f + 459.67  # °F to °R
                Fk = k / 1.4
                x = dPg / P1g
                x_limit = Fk * xT
                choked = x >= x_limit
                x_eff = min(x, x_limit)
                Y = 1.0 - x_eff / (3.0 * Fk * xT)
                Y = max(Y, 2.0/3.0)
                N6 = 63.3
                denom = N6 * Y * math.sqrt(x_eff * P1g * M / T_R)
                Cv_gas = W / denom if denom > 0 else 0
                vsize_g = recommend_valve_size(Cv_gas)
                st.metric("ΔP (psi)", f"{dPg:.2f}")
                st.metric("x = ΔP/P1", f"{x:.4f}")
                if choked:
                    st.warning(f"⚠️ Choked flow! x ({x:.4f}) ≥ Fk·xT ({x_limit:.4f})")
                else:
                    st.info(f"✅ Subcritical flow — x ({x:.4f}) < Fk·xT ({x_limit:.4f})")
                st.metric("Y (expansion factor)", f"{Y:.4f}")
                st.metric("Calculated Cv", f"{Cv_gas:.2f}")
                st.metric("Fk", f"{Fk:.4f}")
                st.info(f"💡 Recommended Valve Size: **{vsize_g}**")
                st.markdown("---")
                gsummary = {"Parameter": ["Mass Flow (lb/h)","P1 (psia)","P2 (psia)","ΔP (psi)",
                            "Temp (°F)","Temp (°R)","Gas","Mol. Wt (M)","k (Cp/Cv)","Fk",
                            "x (ΔP/P1)","xT","Fk·xT","Flow Regime","Y","Calculated Cv","Suggested Size"],
                            "Value": [f"{W:.1f}",f"{P1g:.1f}",f"{P2g:.1f}",f"{dPg:.2f}",
                            f"{T_f:.1f}",f"{T_R:.1f}",gas_sel,f"{M:.3f}",f"{k:.3f}",f"{Fk:.4f}",
                            f"{x:.4f}",f"{xT:.3f}",f"{x_limit:.4f}",
                            "CHOKED" if choked else "Subcritical",
                            f"{Y:.4f}",f"{Cv_gas:.2f}",vsize_g]}
                st.table(pd.DataFrame(gsummary))
                cvg_pdf = generate_pdf("Cv Calculator Report — Gas Service", [
                    {"heading": "Input Parameters",
                     "lines": [f"W: {W:.1f} lb/h", f"P1: {P1g:.1f} psia", f"P2: {P2g:.1f} psia",
                               f"Temp: {T_f:.1f} °F ({T_R:.1f} °R)",
                               f"Gas: {gas_sel} (M={M:.3f}, k={k:.3f})", f"xT: {xT:.3f}"]},
                    {"heading": "Results",
                     "lines": [f"ΔP: {dPg:.2f} psi", f"x: {x:.4f}",
                               f"Regime: {'CHOKED' if choked else 'Subcritical'}",
                               f"Y: {Y:.4f}", f"Fk: {Fk:.4f}",
                               f"Calculated Cv: {Cv_gas:.2f}", f"Recommended Size: {vsize_g}"]},
                    {"heading": "Formula",
                     "lines": ["Cv = W / (N6 x Y x sqrt(x_eff x P1 x M / T))",
                               "N6 = 63.3 | Y = 1 - x/(3*Fk*xT) | Fk = k/1.4"]}])
                if cvg_pdf:
                    st.download_button("📄 Export PDF", cvg_pdf, file_name="cv_gas.pdf",
                                       mime="application/pdf", key="pdf_cvg")

    st.markdown("---")
    st.caption("⚠️ Simplified calculation per ISA/IEC 60534. Fp=1.0 assumed (no piping effects). "
               "Always verify with vendor data.")

# ══════════ TAB 4 — PIPE PRESSURE RATING ══════════
with tab4:
    st.subheader("🧮 Pipe Pressure Rating  (ASME B31.3 / Barlow)")
    st.markdown("**ASME B31.3 formula:** &nbsp; t_min = (P × D) / (2 × (S × E × W + P × Y))")
    st.caption("P=pressure, D=OD, S=allowable stress, E=joint efficiency, W=weld factor, Y=coefficient")

    calc_mode = st.radio("Calculate:", ["MAWP from pipe data", "Required wall thickness from pressure"],
                         horizontal=True, key="pr_mode")

    prc1, prc2 = st.columns(2)
    with prc1:
        st.markdown("##### 📥 Input Parameters")
        pr_nps = st.selectbox("Pipe NPS", list(PIPE_SCHEDULE.keys()), index=11, key="pr_nps")
        pr_sch = st.selectbox("Schedule", [10, 40, 80, 160], index=1, key="pr_sch")
        pr_pipe = PIPE_SCHEDULE[pr_nps]
        pr_od = pr_pipe["od"]
        pr_wt_nom = pr_pipe.get(pr_sch)

        st.markdown(f"**OD = {pr_od:.3f} in  |  Nominal Wall = "
                    f"{'N/A' if pr_wt_nom is None else f'{pr_wt_nom:.4f} in'}**")

        mat_sel = st.selectbox("Material", list(MATERIALS.keys()), index=0, key="pr_mat")
        if mat_sel == "Custom":
            S_val = st.number_input("Allowable Stress, S (psi)", value=20000.0, min_value=1.0, step=100.0, key="pr_s")
        else:
            S_val = float(MATERIALS[mat_sel]["S"])
            st.caption(f"S = {S_val:.0f} psi — {MATERIALS[mat_sel]['note']}")

        E_val = st.number_input("Joint Efficiency, E", value=1.0, min_value=0.5, max_value=1.0, step=0.05, key="pr_e",
                                help="1.0=Seamless, 0.85=ERW, 0.80=Furnace Butt Weld")
        W_val = st.number_input("Weld Factor, W", value=1.0, min_value=0.5, max_value=1.0, step=0.05, key="pr_w")
        Y_coeff = st.number_input("Y Coefficient", value=0.4, min_value=0.0, max_value=0.7, step=0.05, key="pr_y",
                                  help="0.4 for ferrous <900°F, 0.5 for cast iron, 0.7 for >900°F")
        CA = st.number_input("Corrosion Allowance, CA (in)", value=0.0625, min_value=0.0, step=0.0625, key="pr_ca",
                             help="Typical: 1/16 in = 0.0625 in for CS")
        mill_tol = st.number_input("Mill Tolerance (%)", value=12.5, min_value=0.0, max_value=25.0, step=0.5, key="pr_mt",
                                   help="Standard: 12.5% for seamless pipe")

    with prc2:
        st.markdown("##### 📊 Results")
        if pr_wt_nom is None:
            st.error(f"⚠️ Schedule {pr_sch} not available for NPS {pr_nps}")
        else:
            t_actual = pr_wt_nom * (1.0 - mill_tol/100.0) - CA  # available wall after mill tol & CA

            if calc_mode == "MAWP from pipe data":
                if t_actual <= 0:
                    st.error("⚠️ Available wall thickness ≤ 0 after CA & mill tolerance!")
                else:
                    MAWP = (2.0 * S_val * E_val * W_val * t_actual) / (pr_od - 2.0 * Y_coeff * t_actual)
                    barlow_simple = (2.0 * S_val * t_actual) / pr_od

                    st.metric("Nominal Wall", f"{pr_wt_nom:.4f} in")
                    st.metric("After Mill Tol.", f"{pr_wt_nom * (1-mill_tol/100):.4f} in")
                    st.metric("Available Wall (- CA)", f"{t_actual:.4f} in")
                    st.markdown("---")
                    st.metric("MAWP (ASME B31.3)", f"{MAWP:.1f} psi")
                    st.metric("Barlow (simplified)", f"{barlow_simple:.1f} psi")
                    st.markdown("---")
                    pr_summary = {"Parameter": ["NPS","Schedule","OD (in)","Nominal Wall (in)",
                                  "Mill Tol (%)","Wall after Mill Tol (in)","CA (in)",
                                  "Available Wall (in)","Material","S (psi)",
                                  "E","W","Y","MAWP - B31.3 (psi)","MAWP - Barlow (psi)"],
                                  "Value": [pr_nps,str(pr_sch),f"{pr_od:.3f}",f"{pr_wt_nom:.4f}",
                                  f"{mill_tol}%",f"{pr_wt_nom*(1-mill_tol/100):.4f}",f"{CA:.4f}",
                                  f"{t_actual:.4f}",mat_sel,f"{S_val:.0f}",
                                  f"{E_val:.2f}",f"{W_val:.2f}",f"{Y_coeff:.2f}",
                                  f"{MAWP:.1f}",f"{barlow_simple:.1f}"]}
                    st.table(pd.DataFrame(pr_summary))
                    pr_pdf = generate_pdf("Pipe Pressure Rating Report", [
                        {"heading": "Input Parameters",
                         "table_headers": ["Parameter","Value"],
                         "table_rows": [[p,v] for p,v in zip(pr_summary["Parameter"][:9],
                                        pr_summary["Value"][:9])]},
                        {"heading": "Results",
                         "table_headers": ["Parameter","Value"],
                         "table_rows": [[p,v] for p,v in zip(pr_summary["Parameter"][9:],
                                        pr_summary["Value"][9:])]}])
                    if pr_pdf:
                        st.download_button("📄 Export PDF", pr_pdf, file_name="pipe_rating.pdf",
                                           mime="application/pdf", key="pdf_pr")

            else:  # Required wall thickness
                P_des = st.number_input("Design Pressure (psi)", value=300.0, min_value=0.1, step=10.0, key="pr_pdes")
                t_calc = (P_des * pr_od) / (2.0 * (S_val * E_val * W_val + P_des * Y_coeff))
                t_with_ca = t_calc + CA
                t_with_mt = t_with_ca / (1.0 - mill_tol/100.0)

                st.metric("t_calc (B31.3)", f"{t_calc:.4f} in")
                st.metric("+ Corrosion Allowance", f"{t_with_ca:.4f} in")
                st.metric("+ Mill Tolerance", f"{t_with_mt:.4f} in ({t_with_mt*25.4:.2f} mm)")
                st.markdown("---")
                if pr_wt_nom and pr_wt_nom >= t_with_mt:
                    st.success(f"✅ Sch {pr_sch} wall ({pr_wt_nom:.4f} in) ≥ required ({t_with_mt:.4f} in) — **ADEQUATE**")
                elif pr_wt_nom:
                    st.error(f"❌ Sch {pr_sch} wall ({pr_wt_nom:.4f} in) < required ({t_with_mt:.4f} in) — **NOT ADEQUATE**")

                tw_summary = {"Parameter": ["Design Pressure (psi)","NPS","OD (in)",
                              "Material","S (psi)","E","W","Y",
                              "t_calc (in)","+ CA (in)","+ Mill Tol (in)",
                              "Nominal Wall Sch (in)","Adequacy"],
                              "Value": [f"{P_des:.1f}",pr_nps,f"{pr_od:.3f}",
                              mat_sel,f"{S_val:.0f}",f"{E_val:.2f}",f"{W_val:.2f}",f"{Y_coeff:.2f}",
                              f"{t_calc:.4f}",f"{t_with_ca:.4f}",f"{t_with_mt:.4f}",
                              f"{pr_wt_nom:.4f}" if pr_wt_nom else "N/A",
                              "ADEQUATE" if (pr_wt_nom and pr_wt_nom>=t_with_mt) else "NOT ADEQUATE"]}
                st.table(pd.DataFrame(tw_summary))
                tw_pdf = generate_pdf("Required Wall Thickness Report", [
                    {"heading": "Calculation per ASME B31.3",
                     "table_headers": ["Parameter","Value"],
                     "table_rows": [[p,v] for p,v in zip(tw_summary["Parameter"], tw_summary["Value"])]}])
                if tw_pdf:
                    st.download_button("📄 Export PDF", tw_pdf, file_name="wall_thickness.pdf",
                                       mime="application/pdf", key="pdf_tw")

    st.markdown("---")
    st.caption("⚠️ Allowable stresses shown are for ambient temperature per ASME B31.3. "
               "For elevated temperatures, refer to ASME B31.3 Table A-1.")

# ══════════ TAB 5 — FAVOURITES ══════════
with tab5:
    st.subheader("⭐ Your Favourite Conversions")
    if not st.session_state.favorites:
        st.info("No favourites yet.  Use the **Converter** tab → **⭐ Add to Favourites**.")
    else:
        for i, fav in enumerate(st.session_state.favorites):
            fc1, fc2, fc3, fc4 = st.columns([3,2,2,1])
            with fc1:
                st.markdown(f"**{fav['category']}**")
                st.caption(f"{fav['from']}  →  {fav['to']}")
            with fc2:
                fv = st.number_input("Val", value=1.0, format="%.6g",
                                     key=f"fv_{i}", label_visibility="collapsed")
            with fc3:
                fr = do_convert(fv, fav["category"], fav["from"], fav["to"])
                st.text_input("Res", value=f"{fr:.6g}  {fav['to']}",
                              disabled=True, key=f"fr_{i}", label_visibility="collapsed")
            with fc4:
                if st.button("🗑️", key=f"fd_{i}", help="Remove"):
                    st.session_state.favorites.pop(i)
                    save_favorites(st.session_state.favorites); st.rerun()
            st.divider()

# ══════════ TAB 6 — AI ASSISTANT ══════════
with tab6:
    st.subheader("🤖 AI-Powered Unit Conversion")
    st.markdown("Type a conversion in **plain English** — no dropdowns needed!")

    st.markdown("##### 💡 Try an example:")
    ecols = st.columns(3)
    examples = ["150 psi to bar","100 degC to degF","500 gpm to m3/h",
                "1000 lb/h to kg/h","1 atm to mmHg","25 cp to Pa.s"]
    for idx, ex in enumerate(examples):
        with ecols[idx % 3]:
            if st.button(ex, key=f"ex_{idx}", use_container_width=True):
                st.session_state.nl_query_text = ex

    query = st.text_input("🗣️ Your query", value=st.session_state.nl_query_text,
                          placeholder="e.g.  convert 150 psi to bar", key="nl_q")
    if query:
        parsed = parse_nl_query(query)
        if parsed and "error" not in parsed:
            st.success(f"### ✅  {parsed['value']:.6g}  {parsed['from']}  =  "
                       f"**{parsed['result']:.6g}  {parsed['to']}**")
            st.caption(f"Category: {parsed['category']}")
        elif parsed and "error" in parsed:
            st.error(f"⚠️ {parsed['error']}")
        else:
            if api_key:
                try:
                    from openai import OpenAI as _OAI
                    client = _OAI(api_key=api_key)
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role":"system","content":"Extract value, from_unit, to_unit from query. "
                             "Return ONLY JSON: {\"value\":N,\"from_unit\":\"alias\",\"to_unit\":\"alias\"}. "
                             "Use abbreviations: psi,bar,degC,degF,gpm,kg/h,lb,ft,m3/h,btu,hp,cp,cst."},
                            {"role":"user","content":query}],
                        temperature=0)
                    aj = json.loads(resp.choices[0].message.content.strip())
                    ar = _resolve(float(aj["value"]), aj["from_unit"], aj["to_unit"])
                    if ar and "error" not in ar:
                        st.success(f"### ✅  {ar['value']:.6g}  {ar['from']}  =  "
                                   f"**{ar['result']:.6g}  {ar['to']}**")
                        st.caption(f"Category: {ar['category']}  •  Parsed by AI ✨")
                    elif ar:
                        st.error(f"⚠️ {ar['error']}")
                except Exception as e:
                    st.error(f"AI parsing failed: {e}")
            else:
                st.warning("Could not parse. Try: **150 psi to bar**")
                st.info("💡 Add your **OpenAI API key** in the sidebar for AI parsing.")

    st.markdown("---")
    st.markdown("### 📖 Supported patterns")
    st.markdown("| Pattern | Example |\n|---|---|\n"
                "| `NUMBER UNIT to UNIT` | `150 psi to bar` |\n"
                "| `convert NUMBER UNIT to UNIT` | `convert 100 degC to degF` |\n"
                "| `how many UNIT in NUMBER UNIT` | `how many bar in 150 psi` |\n"
                "| `what is NUMBER UNIT in UNIT` | `what is 500 gpm in m3/h` |")

# ══════════ FOOTER ══════════
st.markdown("---")
st.caption("Conversion factors: Perry's ChE Handbook, NIST, ASME B36.10M, ASME B31.3. "
           "Always verify critical values for engineering use.")
