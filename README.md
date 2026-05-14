# 🔄 Engineering Unit Converter Pro

A comprehensive, web-based engineering toolkit built with **Streamlit** — designed for **Process Engineers** in Oil & Gas, Petrochemical, and Chemical industries.

---

## ✨ Features

| Tab | Feature | Description |
|---|---|---|
| 🔄 **Converter** | 19 unit categories | Pressure, Temperature, Flow, Viscosity, Density, Energy, Power, Heat Flux, Thermal Conductivity, and more |
| | 🔄 Swap button | Instantly flip From/To units |
| | ⭐ Favourites | Save frequently used conversions |
| | 📋 Batch conversion | Convert multiple values at once |
| | 📄 PDF export | Download results as professional PDF |
| 🔩 **Pipe Schedule** | ASME B36.10M | NPS 1/2" to 24", Sch 10/40/80/160 — wall thickness, ID, flow area, weight |
| | Toggle inches/mm | Instant unit switching |
| 🔧 **Cv Calculator** | Liquid service | Cv = Q × √(Gf/ΔP) with valve size recommendation |
| | Gas/Vapor service | ISA/IEC 60534 with choked flow detection, Y factor, Fk |
| | 12 common gases | Auto-populate M and k values |
| 🧮 **Pipe Rating** | ASME B31.3 | Calculate MAWP or required wall thickness |
| | 13 pipe materials | A106, A312, A335, API 5L with allowable stresses |
| | Engineering inputs | Corrosion allowance, mill tolerance, joint efficiency |
| ⭐ **Favourites** | Persistent storage | Saved to JSON, quick-convert from favourites tab |
| 🤖 **AI Assistant** | Natural language | Type "150 psi to bar" — no dropdowns needed |
| | OpenAI integration | Optional API key for complex query parsing |

---

## 🚀 Quick Start

```bash
# 1. Clone / download files
# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run unit_converter_pro.py
```

Opens at **http://localhost:8501** 🎉

---

## ☁️ Deploy to Streamlit Cloud (Free!)

1. Push files to a **GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Connect your repo → Set main file to `unit_converter_pro.py`
4. *(Optional)* Add OpenAI API key in App Settings → Secrets
5. Click **Deploy** → Get a public URL!

---

## 📂 Project Structure

```
unit-converter-pro/
├── unit_converter_pro.py   # Main Streamlit app (~700 lines)
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── favorites.json          # Auto-created when you save favourites
```

---

## 📖 AI Query Patterns

| Pattern | Example |
|---|---|
| `NUMBER UNIT to UNIT` | `150 psi to bar` |
| `convert NUMBER UNIT to UNIT` | `convert 100 degC to degF` |
| `how many UNIT in NUMBER UNIT` | `how many bar in 150 psi` |
| `what is NUMBER UNIT in UNIT` | `what is 500 gpm in m3/h` |

---

## 🔧 Cv Calculator — Formulas

**Liquid:** `Cv = Q × √(Gf / ΔP)`
- Q in US GPM, Gf = specific gravity, ΔP in psi

**Gas/Vapor (ISA/IEC 60534):** `Cv = W / (N₆ × Y × √(x_eff × P₁ × M / T))`
- W in lb/h, P1 in psia, T in °R, M = molecular weight
- N₆ = 63.3, Y = 1 - x/(3·Fk·xT), Fk = k/1.4

---

## 🧮 Pipe Rating — Formula (ASME B31.3)

`t_min = (P × D) / (2 × (S × E × W + P × Y))`

- P = design pressure, D = OD, S = allowable stress
- E = joint efficiency, W = weld factor, Y = coefficient (0.4 typ.)

---

## 📜 References

- Perry's Chemical Engineers' Handbook
- NIST — Standard unit definitions
- ASME B36.10M — Pipe schedule data
- ASME B31.3 — Process piping
- ISA/IEC 60534 — Control valve sizing

---

Built with ❤️ for Process Engineers