import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. SETUP & THEME (THE TRUCK LOOK) ---
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

    /* SEARCH BAR */
    div[data-baseweb="input"] {
        border: 5px solid #F06292 !important;
        border-radius: 12px !important;
        background-color: #e0f7fa !important;
        height: 38px !important;
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

    /* THE BOXED TOTAL STYLE */
    .total-box-styled {
        border: 4px solid #333;
        padding: 2px 10px;
        border-radius: 8px;
        font-weight: 900;
        font-size: 24px;
        background-color: white;
        display: inline-block;
        text-align: center;
        min-width: 60px;
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

# --- 2. DATA CONNECTION (THE SCRUBBER) ---
creds = st.secrets["connections"]["gsheets"].to_dict()
if "private_key" in creds:
    creds["private_key"] = creds["private_key"].strip().replace("\\n", "\n")

conn = st.connection("gsheets", type=GSheetsConnection, **creds)
df = conn.read(ttl="0s")

def save_data(updated_df):
    conn.update(data=updated_df)
    st.cache_data.clear()
    st.rerun()

# --- 3. DIALOGS (POPUPS) ---

@st.dialog("Toss this tub?")
def show_toss_popup(row_idx):
    flavor_name = df.at[row_idx, 'name']
    st.write(f"Record a loss for **{flavor_name}**?")
    c1, c2 = st.columns(2)
    # Locked in: The specific phrasing you requested
    if c1.button("No, someone will eat it"):
        st.rerun()
    if c2.button("YES, TOSS"):
        df.at[row_idx, 'stock'] = float(df.at[row_idx, 'stock']) - 0.5
        save_data(df)

@st.dialog("Create New Flavor")
def add_flavor_popup():
    st.markdown("### 🍦 New Flavor")
    name = st.text_input("Name").upper()
    res = st.number_input("Reserve", min_value=0, step=1)
    stk = st.number_input("Stock", min_value=0, step=1)
    if st.button("SAVE NEW FLAVOR"):
        new_row = pd.DataFrame([{"name": name, "reserve": res, "stock": stk, "tossed": 0, "low": 1, "high": 5}])
        updated_df = pd.concat([df, new_row], ignore_index=True)
        save_data(updated_df)

# --- 4. TOP SECTION ---
st.markdown("<div class='main-header'><h1>Mandy's Inventory</h1></div>", unsafe_allow_html=True)

st.markdown("<div style='margin-top: 15px;'>", unsafe_allow_html=True)
h1, h2, h3, h4 = st.columns([3, 4, 4, 2])
with h1:
    col_a, col_b = st.columns([3, 1])
    col_a.markdown("<div class='column-label'>FLAVORS</div>", unsafe_allow_html=True)
    if col_b.button("➕"): add_flavor_popup()
    search = st.text_input("S", placeholder="Search...", label_visibility="collapsed")

h2.markdown("<div class='column-label'>RESERVE</div>", unsafe_allow_html=True)
h3.markdown("<div class='column-label'>STOCK</div>", unsafe_allow_html=True)
h4.markdown("<div class='column-label'>TOTAL</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- 5. INVENTORY LIST (SORTED & DOTS) ---
display_df = df.copy()
if search:
    display_df = display_df[display_df['name'].str.contains(search.upper())]

# Layout: In-stock at top, then out of stock
stocked = display_df[display_df['stock'] > 0]
out_of_stock = display_df[display_df['stock'] <= 0]
sorted_display = pd.concat([stocked, out_of_stock])

for idx, row in sorted_display.iterrows():
    c1, c2, c3, c4 = st.columns([3, 4, 4, 2])
    
    # Flavor Name (No "(Active)")
    clean_name = row['name'].replace("(Active)", "").strip()
    c1.markdown(f"<div class='flavor-name'>{clean_name}</div>", unsafe_allow_html=True)
    
    # RESERVE (Dots for tubs)
    res_val = int(row['reserve'])
    res_dots = "● " * res_val if res_val > 0 else "Empty"
    if c2.button(res_dots, key=f"res_{idx}"):
        if res_val > 0:
            df.at[idx, 'reserve'] -= 1
            df.at[idx, 'stock'] += 1
            save_data(df)

    # STOCK (Dots & Scooped ◒)
    stk_val = float(row['stock'])
    full_tubs = int(stk_val)
    is_scooped = (stk_val % 1 != 0)
    stk_visual = ("● " * full_tubs) + ("◒" if is_scooped else "")
    if stk_visual == "": stk_visual = "Out"

    if c3.button(stk_visual, key=f"stk_{idx}"):
        if is_scooped:
            show_toss_popup(idx)
        else:
            df.at[idx, 'stock'] -= 0.5
            save_data(df)

    # TOTAL (Actual number, boxed)
    total_val = float(row['reserve']) + stk_val
    needs_attention = (total_val <= float(row['low'])) or (float(row['reserve']) == 0)
    
    with c4:
        tc1, tc2 = st.columns([2, 1])
        tc1.markdown(f"<div class='total-box-styled'>{int(total_val)}</div>", unsafe_allow_html=True)
        if needs_attention:
            tc2.markdown("<span class='thick-alert'>!</span>", unsafe_allow_html=True)
