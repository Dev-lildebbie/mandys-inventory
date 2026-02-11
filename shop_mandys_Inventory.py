import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

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
        font-size: 18px !important;
        padding: 2px 10px !important;
    }

    /* FAINT LINE TIGHTENER */
    hr {
        margin-top: 5px !important;
        margin-bottom: 10px !important;
    }
    
    /* THE THICK "!" ALERT */
    .thick-alert {
        font-size: 32px;
        font-weight: 900;
        color: #F06292;
        margin-left: 8px;
        vertical-align: middle;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTION (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(worksheet="Sheet1", ttl=0)

def save_data(df_to_save):
    conn.update(worksheet="Sheet1", data=df_to_save)
    st.cache_data.clear()

# Load the shop's real live data
df = load_data()
# Convert to dictionary for the UI loop
inventory_list = df.to_dict(orient="records")

# --- 3. DIALOGS (POPUPS) ---

@st.dialog("Toss this tub?")
def show_toss_popup(row_idx):
    flavor = inventory_list[row_idx]
    st.write(f"Record a loss for **{flavor['name']}**?")
    c1, c2 = st.columns(2)
    if c1.button("NO, someone will eat it"):
        st.rerun()
    if c2.button("YES, TOSS TUB"):
        df.at[row_idx, 'stock'] = int(df.at[row_idx, 'stock']) - 1
        df.at[row_idx, 'tossed'] = int(df.at[row_idx, 'tossed']) + 1
        save_data(df)
        st.rerun()

@st.dialog("Deep Dive")
def show_detail(row_idx):
    flavor = inventory_list[row_idx]
    st.subheader(f"📊 {flavor['name']}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Res", int(flavor['reserve']))
    col2.metric("Stk", int(flavor['stock']))
    col3.metric("Tossed", int(flavor['tossed']))
    
    st.divider()
    st.write("**Add Delivery**")
    c1, c2 = st.columns([2, 1])
    new_amt = c1.number_input("Tubs", min_value=0, step=1, key="deliv_in", label_visibility="collapsed")
    if c2.button("Add", use_container_width=True):
        df.at[row_idx, 'reserve'] = int(df.at[row_idx, 'reserve']) + int(new_amt)
        save_data(df)
        st.rerun()
    
    st.divider()
    st.write("**Thresholds**")
    t1, t2 = st.columns(2)
    new_high = t1.number_input("Green", value=int(flavor['high']), step=1)
    new_low = t2.number_input("Red (Alert)", value=int(flavor['low']), step=1)
    
    if st.button("Close & Save", use_container_width=True):
        df.at[row_idx, 'high'] = new_high
        df.at[row_idx, 'low'] = new_low
        save_data(df)
        st.rerun()

@st.dialog("Create New Flavor")
def add_flavor_popup():
    name = st.text_input("Flavor Name").upper()
    res = st.number_input("Initial Reserve", min_value=0)
    stk = st.number_input("Initial Stock", min_value=0)
    if st.button("SAVE FLAVOR", use_container_width=True):
        if name:
            new_row = pd.DataFrame([{"name": name, "reserve": int(res), "stock": int(stk), "tossed": 0, "low": 2, "high": 5}])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            save_data(updated_df)
            st.rerun()

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
# Split into stocked/unstocked for sorting
stocked_indices = [i for i, f in enumerate(inventory_list) if f['stock'] > 0]
out_indices = [i for i, f in enumerate(inventory_list) if f['stock'] <= 0]

for idx in stocked_indices + out_indices:
    f = inventory_list[idx]
    c1, c2, c3, c4 = st.columns([3, 4, 4, 2])
    c1.markdown(f<div class='flavor-name'>{f['name']}</div>, unsafe_allow_html=True)
    
    # RESERVE DOTS -> MOVES TO STOCK
    res_count = int(f['reserve'])
    res_dots = "● " * res_count if res_count > 0 else "Empty"
    if c2.button(res_dots, key=f"res_{idx}"):
        if res_count > 0:
            df.at[idx, 'reserve'] = res_count - 1
            df.at[idx, 'stock'] = int(f['stock']) + 1
            save_data(df)
            st.rerun()

    # STOCK DOTS -> OPENS TOSS POPUP
    stk_count = int(f['stock'])
    stk_dots = "● " * stk_count if stk_count > 0 else "Out"
    if c3.button(stk_dots, key=f"stk_{idx}"):
        show_toss_popup(idx)

    # BOXED TOTAL WITH THICK OUTSIDE ALERT
    total = int(f['reserve']) + int(f['stock'])
    needs_attention = (total <= int(f['low'])) or (int(f['reserve']) == 0)
    
    with c4:
        tc1, tc2 = st.columns([2, 1])
        tc1.button(f"[ {total} ]", key=f"tot_{idx}", on_click=show_detail, args=(idx,))
        if needs_attention:
            tc2.markdown("<span class='thick-alert'>!</span>", unsafe_allow_html=True)
