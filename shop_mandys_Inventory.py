import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. SETUP & THEME (THE PINK TRUCK) ---
st.set_page_config(page_title="Mandy's Inventory", layout="wide")

st.markdown("""
    <style>
    header, #MainMenu, footer, .stAppDeployButton {visibility: hidden;}
    .block-container { padding-top: 0.5rem !important; padding-bottom: 2rem !important; }
    .stApp { background-color: #FFEB3B; border: 30px solid #F06292; }
    
    .main-header {
        background-color: #00BCD4; padding: 8px; color: white;
        text-align: center; border: 6px solid #F06292; border-radius: 15px;
    }
    .main-header h1 { font-size: 45px; font-weight: 900; margin: 0; text-transform: uppercase; }

    .column-label { font-weight: 900; color: #333; font-size: 26px; text-transform: uppercase; }
    .flavor-name { font-size: 22px; font-weight: 900; color: #333; text-transform: uppercase; }

    div.stButton > button {
        background-color: #00BCD4 !important; color: white !important;
        border: 4px solid #F06292 !important; border-radius: 10px !important;
        font-weight: 900 !important; font-size: 32px !important; 
        padding: 0px 10px !important; font-family: monospace;
    }
    
    .total-box {
        border: 4px solid #333; padding: 5px; border-radius: 8px;
        font-weight: 900; font-size: 24px; background-color: white;
        display: inline-block; text-align: center; min-width: 50px;
    }

    .thick-alert { font-size: 32px; font-weight: 900; color: #F06292; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTION (THE CLASH FIX) ---
raw_creds = st.secrets["connections"]["gsheets"].to_dict()
sheet_url = raw_creds.get("spreadsheet")

# Scrub the private key and remove 'spreadsheet' to prevent connection errors
if "private_key" in raw_creds:
    raw_creds["private_key"] = raw_creds["private_key"].replace("\\n", "\n").strip()

# Initialize connection without keyword conflicts
conn = st.connection("gsheets", type=GSheetsConnection, spreadsheet=sheet_url, service_account=raw_creds)
df = conn.read(ttl="0s")

def save_data(updated_df):
    conn.update(data=updated_df)
    st.cache_data.clear()
    st.rerun()

# --- 3. DIALOGS ---
@st.dialog("Toss this tub?")
def show_toss_popup(row_idx):
    st.write(f"Record a loss for **{df.at[row_idx, 'name']}**?")
    if st.button("YES, TOSS"):
        df.at[row_idx, 'stock'] = float(df.at[row_idx, 'stock']) - 0.5
        save_data(df)

@st.dialog("Deep Dive")
def show_detail(row_idx):
    flavor = df.iloc[row_idx]
    st.subheader(f"📊 {flavor['name']}")
    st.write("**Add Delivery**")
    new_amt = st.number_input("Tubs", min_value=0, step=1)
    if st.button("Add"):
        df.at[row_idx, 'reserve'] = int(df.at[row_idx, 'reserve']) + new_amt
        save_data(df)
    st.divider()
    t1, t2 = st.columns(2)
    new_high = t1.number_input("High", value=int(flavor.get('high', 5)))
    new_low = t2.number_input("Low", value=int(flavor.get('low', 1)))
    if st.button("Update Thresholds"):
        df.at[row_idx, 'high'], df.at[row_idx, 'low'] = new_high, new_low
        save_data(df)

@st.dialog("New Flavor")
def add_flavor_popup():
    name = st.text_input("Name").upper()
    res = st.number_input("Reserve", min_value=0)
    stk = st.number_input("Stock", min_value=0)
    if st.button("SAVE"):
        new_row = pd.DataFrame([{"name": name, "reserve": res, "stock": stk, "low": 1, "high": 5}])
        save_data(pd.concat([df, new_row], ignore_index=True))

# --- 4. HEADER ---
st.markdown("<div class='main-header'><h1>Mandy's Inventory</h1></div>", unsafe_allow_html=True)
h1, h2, h3, h4 = st.columns([3, 4, 4, 2])
with h1:
    ca, cb = st.columns([3, 1])
    ca.markdown("<div class='column-label'>FLAVORS</div>", unsafe_allow_html=True)
    if cb.button("➕"): add_flavor_popup()
    search = st.text_input("S", placeholder="Search...", label_visibility="collapsed")
h2.markdown("<div class='column-label'>RESERVE</div>", unsafe_allow_html=True)
h3.markdown("<div class='column-label'>STOCK</div>", unsafe_allow_html=True)
h4.markdown("<div class='column-label'>TOTAL</div>", unsafe_allow_html=True)
st.divider()

# --- 5. LIST ---
display_df = df.copy()
if search: display_df = display_df[display_df['name'].str.contains(search.upper())]

# Sorting: In stock top, Out of stock bottom
sorted_display = pd.concat([display_df[display_df['stock'] > 0], display_df[display_df['stock'] <= 0]])

for idx, row in sorted_display.iterrows():
    c1, c2, c3, c4 = st.columns([3, 4, 4, 2])
    c1.markdown(f"<div class='flavor-name'>{row['name'].replace('(Active)','')}</div>", unsafe_allow_html=True)
    
    # RESERVE
    res_val = int(row['reserve'])
    if c2.button("● " * res_val if res_val > 0 else "Empty", key=f"r{idx}"):
        if res_val > 0:
            df.at[idx, 'reserve'], df.at[idx, 'stock'] = res_val - 1, float(row['stock']) + 1
            save_data(df)

    # STOCK
    stk_val = float(row['stock'])
    stk_vis = ("● " * int(stk_val)) + ("◒" if stk_val % 1 != 0 else "")
    if c3.button(stk_vis if stk_vis else "Out", key=f"s{idx}"):
        if stk_val % 1 != 0: show_toss_popup(idx)
        else:
            df.at[idx, 'stock'] = stk_val - 0.5
            save_data(df)

    # TOTAL
    total = int(row['reserve'] + stk_val)
    with c4:
        col_t1, col_t2 = st.columns([2, 1])
        if col_t1.button(f"[{total}]", key=f"t{idx}"): show_detail(idx)
        if total <= int(row.get('low', 1)) or int(row['reserve']) == 0:
            col_t2.markdown("<span class='thick-alert'>!</span>", unsafe_allow_html=True)
