import streamlit as st
import os
from src.constants import TRANSITIONS, DEFAULT_SLIDE_DURATION, DEFAULT_TRANSITION_DURATION
from src.video_processor import process_quick_clip, process_custom_video, generate_preview_transition
from src.utils import create_slide_image, safe_remove

# Get absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
ASSETS_DIR = os.path.join(project_root, "assets")


def render_sidebar():
    """Renders the sidebar with Gogi Branding."""
    with st.sidebar:
        # Logo
        # Logo
        logo_path = os.path.join(ASSETS_DIR, "images", "Gogi Clip Maker.png")
        if os.path.exists(logo_path):
             st.image(logo_path, use_container_width=True)
        else:
            st.title("Gogi Clip Maker")
            
        st.markdown("---")
        mode = st.radio("Select Mode", ["Quick Clip", "Custom Clip (Wizard)"])
        st.markdown("---")
        st.markdown("### About")
        st.info("Professional video creation tool by **Gogi Software**.")
        return mode

def render_quick_clip_page():
    """Renders the Quick Clip interface."""
    st.header("Quick Clip Creator")
    st.markdown("Generate a music video instantly from a collection of images.")
    
    uploaded_images = st.file_uploader("1. Upload Images", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True, key="quick_images")
    if uploaded_images:
        st.success(f"{len(uploaded_images)} images uploaded.")
        
    uploaded_audio = st.file_uploader("2. Upload Background Music", type=['mp3', 'wav'], key="quick_audio")
    
    if st.button("🚀 Generate Video", key="quick_generate", type="primary"):
        if not uploaded_images or not uploaded_audio:
            st.error("Please upload both images and music.")
            return
            
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        output_file, audio_temp = process_quick_clip(uploaded_images, uploaded_audio, status_text, progress_bar)
        
        if output_file:
            st.success("Video created successfully!")
            st.video(output_file)
            with open(output_file, "rb") as file:
                st.download_button(
                    label="Download Video",
                    data=file,
                    file_name="gogi_quick_clip.mp4",
                    mime="video/mp4"
                )
            # Cleanup audio temp
            safe_remove(audio_temp)

def render_custom_clip_page():
    """Renders the Custom Clip Wizard."""
    st.header("Custom Clip Creator")
    
    # Initialize session state
    if 'wizard_step' not in st.session_state:
        st.session_state.wizard_step = 1
    if 'slides' not in st.session_state:
        st.session_state.slides = []
    if 'current_slide_index' not in st.session_state:
        st.session_state.current_slide_index = -1 
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None

    # Step 1: Audio
    if st.session_state.wizard_step == 1:
        st.subheader("Step 1: Background Music")
        st.markdown("Start by choosing the soundtrack for your potential masterpiece.")
        
        uploaded_audio = st.file_uploader("Upload Music (Optional)", type=['mp3', 'wav'], key="wizard_audio")
        
        if st.button("Next: Start Designing Slides ➡"):
            if uploaded_audio:
                st.session_state.audio_file = uploaded_audio
            st.session_state.wizard_step = 2
            st.session_state.current_slide_index = -1 # Start with adding a new slide
            st.rerun()

    # Step 2: Slides
    elif st.session_state.wizard_step == 2:
        st.subheader("Step 2: Design Your Slides")
        
        # Navigation
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅ Back"):
                st.session_state.wizard_step = 1
                st.rerun()
        with c3:
            if len(st.session_state.slides) > 0:
                if st.button("Next: Finish ➡", type="primary"):
                    st.session_state.wizard_step = 3
                    st.rerun()

        st.markdown("---")
        
        col_edit, col_preview = st.columns([1, 1])
        
        # Determining Edit State
        is_editing = st.session_state.current_slide_index >= 0 and st.session_state.current_slide_index < len(st.session_state.slides)
        
        if is_editing:
            current_slide = st.session_state.slides[st.session_state.current_slide_index]
            header_text = f"Editing Slide {st.session_state.current_slide_index + 1}"
        else:
            current_slide = {
                'type': 'image',
                'content': None,
                'color': '#000000',
                'duration': DEFAULT_SLIDE_DURATION,
                'transition': 'crossfade',
                'transition_duration': DEFAULT_TRANSITION_DURATION,
                'text': '',
                'text_color': '#ffffff'
            }
            header_text = "New Slide"

        with col_edit:
            st.markdown(f"### {header_text}")
            
            slide_type = st.selectbox("Slide Type", ["Image", "Solid Color"], index=0 if current_slide['type'] == 'image' else 1)
            content = current_slide['content']
            color = current_slide['color']
            
            if slide_type == "Image":
                uploaded_img = st.file_uploader("Upload Image", type=['jpg', 'png', 'jpeg'], key=f"edit_img_{st.session_state.current_slide_index}")
                if uploaded_img:
                    content = uploaded_img
            else:
                color = st.color_picker("Background Color", value=current_slide['color'])

            text_overlay = st.text_input("Text Overlay", value=current_slide['text'])
            text_color = st.color_picker("Text Color", value=current_slide['text_color'])
            
            st.markdown("#### Timing")
            duration = st.number_input("Duration (seconds)", min_value=1.0, value=float(current_slide['duration']))
            
            st.markdown("#### Transition")
            c_trans, c_prev = st.columns([3, 1])
            with c_trans:
                transition = st.selectbox("Effect", TRANSITIONS, index=TRANSITIONS.index(current_slide['transition']))
            
            trans_duration = st.number_input("Transition Duration", min_value=0.5, max_value=2.0, value=float(current_slide['transition_duration']))
            
            # Save / Add Logic
            st.markdown("---")
            if st.button("Save Slide", type="primary", use_container_width=True):
                if slide_type == "Image" and not content:
                    st.error("Please upload an image!")
                else:
                    new_data = {
                        'type': slide_type.lower(),
                        'content': content,
                        'color': color,
                        'duration': duration,
                        'transition': transition,
                        'transition_duration': trans_duration,
                        'text': text_overlay,
                        'text_color': text_color
                    }
                    if is_editing:
                        st.session_state.slides[st.session_state.current_slide_index] = new_data
                        st.success("Updated!")
                    else:
                        st.session_state.slides.append(new_data)
                        st.success("Added!")
                        st.rerun()
                            
            if is_editing:
                if st.button("Delete Slide", type="secondary", use_container_width=True):
                    st.session_state.slides.pop(st.session_state.current_slide_index)
                    st.session_state.current_slide_index = -1
                    st.rerun()

        with col_preview:
            st.markdown("### Preview")
            preview_data = {
                'type': slide_type.lower(),
                'content': content,
                'color': color,
                'text': text_overlay,
                'text_color': text_color
            }
            if preview_data['type'] == 'image' and not preview_data['content']:
                st.info("Upload image to see preview")
            else:
                try:
                    img_preview = create_slide_image(preview_data)
                    st.image(img_preview, caption="Static Preview", use_container_width=True)
                except Exception as e:
                    st.error(str(e))
            
            if is_editing and st.session_state.current_slide_index > 0:
                 if st.button("▶ Play Transition"):
                    prev_s = st.session_state.slides[st.session_state.current_slide_index - 1]
                    curr_s = preview_data.copy()
                    curr_s['transition'] = transition
                    curr_s['transition_duration'] = trans_duration
                    
                    v_path = generate_preview_transition(prev_s, curr_s)
                    st.video(v_path)
                    safe_remove(v_path)

        # Slide Strip
        st.markdown("---")
        st.subheader("Storyboard")
        
        if st.button("➕ Add New Slide"):
            st.session_state.current_slide_index = -1
            st.rerun()
            
        if st.session_state.slides:
            cols = st.columns(min(len(st.session_state.slides), 8))
            for i, slide in enumerate(st.session_state.slides):
                label = f"#{i+1}"
                if i < len(cols):
                     with cols[i]:
                        if st.button(label, key=f"nav_{i}", type="primary" if i == st.session_state.current_slide_index else "secondary"):
                            st.session_state.current_slide_index = i
                            st.rerun()

    # Step 3: Finish
    elif st.session_state.wizard_step == 3:
        st.subheader("Step 3: Render Video")
        st.success(f"Ready to render {len(st.session_state.slides)} slides.")
        
        if st.button("⬅ Back to Slides"):
             st.session_state.wizard_step = 2
             st.rerun()
             
        if st.button("🎬 Create Final Video", type="primary"):
            status_text = st.empty()
            progress_bar = st.progress(0)
            
            output_file, audio_temp = process_custom_video(st.session_state.slides, st.session_state.audio_file, status_text, progress_bar)
            
            if output_file:
                st.success("Video created successfully!")
                st.video(output_file)
                with open(output_file, "rb") as file:
                    st.download_button(
                        label="Download Video",
                        data=file,
                        file_name="gogi_custom_clip.mp4",
                        mime="video/mp4"
                    )
                safe_remove(audio_temp)
