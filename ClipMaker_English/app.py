import streamlit as st
import os

# Set page config MUST be the first Streamlit command
st.set_page_config(
    page_title="Gogi Clip Maker",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.ui import render_sidebar, render_quick_clip_page, render_custom_clip_page

def load_css():
    """Loads custom CSS."""
    # Build absolute path to css file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(current_dir, "assets", "css", "style.css")
    
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at: {css_path}")
            
def main():
    load_css()
    
    # Render Sidebar and get mode
    mode = render_sidebar()
    
    # Route Logic
    if mode == "Quick Clip":
        render_quick_clip_page()
    elif mode == "Custom Clip (Wizard)":
        render_custom_clip_page()
    else:
        # Fallback
        render_quick_clip_page()

if __name__ == "__main__":
    main()
