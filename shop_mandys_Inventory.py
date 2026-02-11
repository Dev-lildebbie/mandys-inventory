import streamlit as st
import pandas as pd
import requests
from io import StringIO

# --- 1. SETUP & THEME (LOCKED IN) ---
st.set_page_config(page_title="Mandy's Inventory", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
    }

    /* THE MAIN TRUCK BORDER & YELLOW BG */
    .stApp {
        background-color: #FFEB3B; 
        border: 30px solid #F06292;
    }
    
    /* MAIN TEAL HEADER */
    .main-header {
        background-color: #00BCD4;
        padding: 8px;
        color: white;
        text-align: center;
        border: 6px solid #F06292; 
        border-radius: 15px;
        margin-bottom: 0px !important;
    }
    .main-header h1 {
        font-size: 45px; 
        font-weight: 900;
        letter-spacing: 3px;
        margin: 0;
        text-transform: uppercase;
    }

    /* THE 1-2CM GAP TIGHTENER */
    .command-zone {
        margin-top: -5px !important;
    }

    /* SEARCH BAR - NO WHITE CORNERS */
    div[data-baseweb="input"] {
        border: 5px solid #F06292 !important;
        border-radius: 12px !important;
        background-color: #e0f7fa !important;
        height: 38px !important;
    }
    .stTextInput input {
        background-color: transparent !important;
        border: none !important;
        padding: 5px !important;
    }

    /* COLUMN LABELS */
    .column-label {
        font-weight: 900;
        color: #333;
        font-size: 26px;
        text-transform: uppercase;
        margin-bottom: -10px !important;
    }
    
    .flavor-name { 
        font-size: 22px; 
        font-weight: 900; 
        color: #333; 
        text-transform: uppercase;
    }

    /* BUTTONS / DOTS STYLE */
    div.stButton > button {
        background-color: #00BCD4 !important;
        color: white !important;
        border: 4px solid #F06292 !important; 
        border-radius: 10px !important;
        font-weight: 900 !important;
        font-size: 32px !important; 
        padding: 0px 10px !important;
        font-family: monospace;
    }

    hr {
        margin-top: 5px !important;
        margin-bottom: 10px !important;
    }
    
    .thick-alert {
        font-size: 32px;
        font-weight: 900;
        color: #F06292;
        margin-left: 8px;
        vertical-align: middle;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTION ---
SHEET_ID = "1kIYPGbmp1yA-djwz5Leyc3Dvah7U97RS-DD-OyFEke8"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def load_data():
    try:
        response = requests.get(CSV_URL)
        df = pd.read_csv(StringIO(response.text))
        numeric_cols = ['reserve', 'stock', 'tossed', 'low', 'high']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=["name", "reserve", "stock", "tossed", "low", "high"])

df = load_data()
inventory_list = df.to_dict(orient="records")

# --- 3. DIALOGS ---

@st.dialog("Toss this tub?")
def show_toss_popup(row_idx):
    flavor = inventory_list[row_idx]
    st.write(f"Record a loss for **{flavor['name']}**?")
    c1, c2 = st.columns(2)
    if c1.button("NO, someone will eat it"):
        st.rerun()
    if c2.button("YES, TOSS TUB"):
        st.info("Direct writing is offline until Service Key is added.")
        st.rerun()

@st.dialog("Deep Dive")
def show_detail(row_idx):
    flavor = inventory_list[row_idx]
    st.subheader(f"📊 {flavor['name']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Res", int(flavor['reserve']))
    col2.metric("Stk", float(flavor['stock']))
    col3.metric("Tossed", int(flavor['tossed']))
    
    st.divider()
    st.write("**Add Delivery**")
    c1, c2 = st.columns([2, 1])
    new_amt = c1.number_input("Tubs", min_value=0, step=1, key="deliv_in", label_visibility="collapsed")
    if c2.button("Add", use_container_width=True):
        st.info("Manual Entry Mode active.")

    st.divider()
    st.write("**Thresholds**")
    t1, t2 = st.columns(2)
    t1.number_input("High", value=int(flavor['high']))
    t2.number_input("Low", value=int(flavor['low']))
    
    if st.button("Close", use_container_width=True):
        st.rerun()

@st.dialog("Create New Flavor")
def add_flavor_popup():
    st.markdown("### 🍦 New Flavor")
    name = st.text_input("Name").upper()
    if st.button("SAVE"): st.info("Requires Service Key.")

# --- 4. TOP SECTION ---
st.markdown("<div class='main-header'><h1>Mandy's Inventory</h1></div>", unsafe_allow_html=True)

st.markdown("<div class='command-zone'>", unsafe_allow_html=True)
h1, h2, h3, h4 = st.columns([3, 4, 4, 2])
with h1:
    col_a, col_b = st.columns([3, 1])
    col_a.markdown("<div class='column-label'>FLAVORS</div>", unsafe_allow_html=True)
    if col_b.button("➕"): add_flavor_popup()
    search = st.text_input("S", placeholder="Search...", label_visibility="collapsed")
    if search:
        match_idx = next((i for i, f in enumerate(inventory_list) if search.upper() in f['name']), None)
        if match_idx is not None: show_detail(match_idx)

h2.markdown("<div class='column-label'>RESERVE</div>", unsafe_allow_html=True)
h3.markdown("<div class='column-label'>STOCK</div>", unsafe_allow_html=True)
h4.markdown("<div class='column-label'>TOTAL</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- 5. INVENTORY LIST ---
if not df.empty:
    # SORTING: Stocked first, Out-of-stock last
    stocked_indices = [i for i, f in enumerate(inventory_list) if f['stock'] > 0]
    out_indices = [i for i, f in enumerate(inventory_list) if f['stock'] <= 0]

    for idx in stocked_indices + out_indices:
        f = inventory_list[idx]
        c1, c2, c3, c4 = st.columns([3, 4, 4, 2])
        c1.markdown(f"<div class='flavor-name'>{f['name']}</div>", unsafe_allow_html=True)
        
        # RESERVE (Dots)
        res_count = int(f['reserve'])
        res_dots = "● " * res_count if res_count > 0 else "Empty"
        c2.button(res_dots, key=f"res_{idx}")

        # STOCK (The ◒ Half-Dot Logic)
        stk_val = float(f['stock'])
        full_tubs = int(stk_val)
        is_scooped = (stk_val % 1 != 0)
        stk_visual = ("● " * full_tubs) + ("◒" if is_scooped else "")
        if stk_visual == "": stk_visual = "Out"

        if c3.button(stk_visual, key=f"stk_{idx}"):
            if is_scooped: show_toss_popup(idx)
            else: st.info("Scooping! (Set Sheet to .5 to see the ◒)")

        # TOTAL (Actual Boxed Number)
        total_val = float(f['reserve']) + stk_val
        needs_attention = (total_val <= float(f['low'])) or (float(f['reserve']) == 0)
        
        with c4:
            tc1, tc2 = st.columns([2, 1])
            # Boxed number as requested
            tc1.button(f"[ {int(total_val)} ]", key=f"tot_{idx}", on_click=show_detail, args=(idx,))
            if needs_attention:
                tc2.markdown("<span class='thick-alert'>!</span>", unsafe_allow_html=True)
