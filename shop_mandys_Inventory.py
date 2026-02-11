import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- 1. SETUP & THEME (EVERY PETTY DETAIL LOCKED) ---
st.set_page_config(page_title="Mandy's Inventory", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .block-container { padding-top: 0.5rem !important; padding-bottom: 2rem !important; }

    /* TRUCK THEME: YELLOW BG & PINK BORDER */
    .stApp {
        background-color: #FFEB3B; 
        border: 30px solid #F06292;
    }
    
    .main-header {
        background-color: #00BCD4;
        padding: 8px; color: white;
        text-align: center; border: 6px solid #F06292; 
        border-radius: 15px;
        margin-bottom: 0px !important;
    }
    .main-header h1 {
        font-size: 45px; font-weight: 900;
        letter-spacing: 3px; margin: 0;
        text-transform: uppercase;
    }

    div[data-baseweb="input"] {
        border: 5px solid #F06292 !important;
        border-radius: 12px !important;
        background-color: #e0f7fa !important;
    }

    .column-label {
        font-weight: 900; color: #333;
        font-size: 26px; text-transform: uppercase;
        margin-bottom: -10px !important;
    }
    
    .flavor-name { 
        font-size: 22px; font-weight: 900; 
        color: #333; text-transform: uppercase;
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

    .thick-alert {
        font-size: 32px; font-weight: 900;
        color: #F06292; margin-left: 8px;
        vertical-align: middle;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTION (THE SCRUBBER FIX) ---
# We fix the key formatting before Streamlit tries to use it.
creds = st.secrets["connections"]["gsheets"].to_dict()
if "private_key" in creds:
    creds["private_key"] = creds["private_key"].replace("\\n", "\n")

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
    if c1.button("No, someone will eat it"):
        st.rerun()
    if c2.button("YES, TOSS"):
        if 'tossed' in df.columns:
            df.at[row_idx, 'tossed'] = float(df.at[row_idx].get('tossed', 0)) + 0.5
        df.at[row_idx, 'stock'] = float(df.at[row_idx, 'stock']) - 0.5
        save_data(df)

@st.dialog("Deep Dive")
def show_detail(row_idx):
    flavor = df.iloc[row_idx]
    st.subheader(f"📊 {flavor['name']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Res", int(flavor['reserve']))
    col2.metric("Stk", float(flavor['stock']))
    col3.metric("Tossed", float(flavor.get('tossed', 0)))
    
    st.divider()
    st.write("**Add Delivery**")
    c1, c2 = st.columns([2, 1])
    new_amt = c1.number_input("Tubs", min_value=0, step=1, key="deliv_in")
    if c2.button("Add", use_container_width=True):
        df.at[row_idx, 'reserve'] = int(df.at[row_idx, 'reserve']) + new_amt
        save_data(df)

    st.divider()
    st.write("**Thresholds**")
    t1, t2 = st.columns(2)
    new_high = t1.number_input("High", value=int(flavor.get('high', 5)))
    new_low = t2.number_input("Low", value=int(flavor.get('low', 1)))
    if st.button("UPDATE SETTINGS", use_container_width=True):
        df.at[row_idx, 'high'] = new_high
        df.at[row_idx, 'low'] = new_low
        save_data(df)
    if st.button("Close", use_container_width=True):
        st.rerun()

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
st.divider()

# --- 5. LIST (SORTED: STOCKED TOP, OUT BOTTOM) ---
display_df = df.copy()
if search:
    display_df = display_df[display_df['name'].str.contains(search.upper())]

stocked = display_df[display_df['stock'] > 0]
out = display_df[display_df['stock'] <= 0]
sorted_display = pd.concat([stocked, out])

for idx, row in sorted_display.iterrows():
    c1, c2, c3, c4 = st.columns([3, 4, 4, 2])
    clean_name = row['name'].replace("(Active)", "").strip()
    c1.markdown(f"<div class='flavor-name'>{clean_name}</div>", unsafe_allow_html=True)
    
    # RESERVE (Dots)
    res_val = int(row['reserve'])
    res_label = "● " * res_val if res_val > 0 else "Empty"
    if c2.button(res_label, key=f"res_{idx}"):
        if res_val > 0:
            df.at[idx, 'reserve'] = int(df.at[idx, 'reserve']) - 1
            df.at[idx, 'stock'] = float(df.at[idx, 'stock']) + 1
            save_data(df)

    # STOCK (Dots & ◒)
    stk_val = float(row['stock'])
    stk_visual = ("● " * int(stk_val)) + ("◒" if stk_val % 1 != 0 else "")
    if stk_visual == "": stk_visual = "Out"
    if c3.button(stk_visual, key=f"stk_{idx}"):
        if stk_val % 1 != 0: show_toss_popup(idx)
        else:
            df.at[idx, 'stock'] = float(df.at[idx, 'stock']) - 0.5
            save_data(df)

    # TOTAL (Actual Boxed Number)
    total_val = float(row['reserve']) + stk_val
    needs_attention = (total_val <= float(row.get('low', 1))) or (float(row['reserve']) == 0)
    with c4:
        tc1, tc2 = st.columns([2, 1])
        if tc1.button(f"[ {int(total_val)} ]", key=f"tot_{idx}"):
            show_detail(idx)
        if needs_attention:
            tc2.markdown("<span class='thick-alert'>!</span>", unsafe_allow_html=True)
