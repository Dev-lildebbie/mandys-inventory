import streamlit as st
import pandas as pd
import requests
from io import StringIO

# --- 1. SETUP & THEME (EVERY SINGLE DETAIL) ---
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

    .stApp {
        background-color: #FFEB3B; 
        border: 30px solid #F06292;
    }
    
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

    .command-zone {
        margin-top: -5px !important;
    }

    div[data-baseweb="input"] {
        border: 5px solid #F06292 !important;
        border-radius: 12px !important;
        background-color: #e0f7fa !important;
        height: 38px !important;
    }

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
        return df
    except:
        return pd.DataFrame(columns=["name", "reserve", "stock", "tossed", "low", "high"])

df = load_data()
inventory_list = df.to_dict(orient="records")

# --- 3. DIALOGS (RESTORING ALL 50+ LINES OF POPUP LOGIC) ---

@st.dialog("Toss this tub?")
def show_toss_popup(row_idx):
    flavor = inventory_list[row_idx]
    st.write(f"Finish or Toss **{flavor['name']}**?")
    st.write("This will remove the current scooped tub from stock.")
    c1, c2 = st.columns(2)
    if c1.button("NO, KEEP IT"):
        st.rerun()
    if c2.button("YES, TOSS IT"):
        st.info("Saving changes requires the Service Account Key.")
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
    new_amt = c1.number_input("Tubs Received", min_value=0, step=1, key="deliv_in", label_visibility="collapsed")
    if c2.button("ADD", use_container_width=True):
        st.info("Write access needed to update Sheet.")
    
    st.divider()
    st.write("**Inventory Thresholds**")
    t1, t2 = st.columns(2)
    with t1:
        st.number_input("High (Green)", value=int(flavor['high']), step=1)
    with t2:
        st.number_input("Low (Alert)", value=int(flavor['low']), step=1)
    
    if st.button("CLOSE", use_container_width=True):
        st.rerun()

@st.dialog("Create New Flavor")
def add_flavor_popup():
    st.markdown("### 🍦 New Flavor Details")
    new_name = st.text_input("Flavor Name").upper()
    col_a, col_b = st.columns(2)
    new_res = col_a.number_input("Initial Reserve", min_value=0, step=1)
    new_stk = col_b.number_input("Initial Stock", min_value=0, step=1)
    
    if st.button("SAVE NEW FLAVOR", use_container_width=True):
        st.info("Direct saving is offline until Service Key is added.")

# --- 4. TOP SECTION ---
st.markdown("<div class='main-header'><h1>Mandy's Inventory</h1></div>", unsafe_allow_html=True)

st.markdown("<div class='command-zone'>", unsafe_allow_html=True)
h1, h2, h3, h4 = st.columns([3, 4, 4, 2])
with h1:
    col_a, col_b = st.columns([3, 1])
    col_a.markdown("<div class='column-label'>FLAVORS</div>", unsafe_allow_html=True)
    if col_b.button("➕"): 
        add_flavor_popup()
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
    stocked_indices = [i for i, f in enumerate(inventory_list) if f['stock'] > 0]
    out_indices = [i for i, f in enumerate(inventory_list) if f['stock'] <= 0]

    for idx in stocked_indices + out_indices:
        f = inventory_list[idx]
        c1, c2, c3, c4 = st.columns([3, 4, 4, 2])
        c1.markdown(f"<div class='flavor-name'>{f['name']}</div>", unsafe_allow_html=True)
        
        # RESERVE (Always Full Dots)
        res_count = int(f['reserve'])
        res_dots = "● " * res_count if res_count > 0 else "Empty"
        if c2.button(res_dots, key=f"res_{idx}"):
            st.info("Move to Stock logic ready for Service Key.")

        # STOCK (The Half-Full Visual Logic)
        stk_val = float(f['stock'])
        full_tubs = int(stk_val)
        is_scooped = (stk_val % 1 != 0)
        
        # ◒ is the circle that is black on BOTTOM and white on TOP
        stk_visual = ("● " * full_tubs) + ("◒" if is_scooped else "")
        if stk_visual == "": stk_visual = "Out"

        if c3.button(stk_visual, key=f"stk_{idx}"):
            if is_scooped:
                show_toss_popup(idx)
            else:
                st.info("Turning into ◒... (Requires Service Key to save)")

        # TOTAL (Actual Number Boxed)
        total = int(float(f['reserve']) + stk_val)
        needs_attention = (total <= int(f['low'])) or (int(f['reserve']) == 0)
        
        with c4:
            tc1, tc2 = st.columns([2, 1])
            tc1.button(f"[ {total} ]", key=f"tot_{idx}", on_click=show_detail, args=(idx,))
            if needs_attention:
                tc2.markdown("<span class='thick-alert'>!</span>", unsafe_allow_html=True)
                
