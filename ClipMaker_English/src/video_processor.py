import time
import random
import os
import streamlit as st
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, VideoFileClip
from moviepy.video.fx import CrossFadeIn, SlideIn, Resize, Rotate
from proglog import ProgressBarLogger

from src.constants import SCREEN_SIZE, FPS, TRANSITIONS
from src.utils import resize_and_pad_image, create_slide_image, save_uploaded_file, safe_remove
from PIL import Image
import numpy as np

class StreamlitLogger(ProgressBarLogger):
    def __init__(self, status_text, progress_bar):
        super().__init__(init_state=None, bars=None, ignored_bars=None, logged_bars='all', min_time_interval=0, ignore_bars_under=0)
        self.status_text = status_text
        self.progress_bar = progress_bar
        self.start_time = time.time()

    def callback(self, **changes):
        pass

    def bars_callback(self, bar, attr, value, old_value=None):
        if 'total' in self.bars[bar]:
            percentage = (value / self.bars[bar]['total'])
            if percentage > 0:
                self.progress_bar.progress(min(percentage, 1.0))
                
                elapsed_time = time.time() - self.start_time
                estimated_total_time = elapsed_time / percentage
                remaining_time = estimated_total_time - elapsed_time
                
                mins, secs = divmod(int(remaining_time), 60)
                self.status_text.text(f"Processing: {int(percentage * 100)}% - Remaining: {mins:02d}:{secs:02d}")

def apply_transition_effect(clip, trans_type, duration):
    """Applies a transition effect to a clip."""
    if trans_type == 'crossfade':
        return clip.with_effects([CrossFadeIn(duration=duration)])
    elif trans_type == 'slide_left':
        return clip.with_effects([SlideIn(duration=duration, side='right')])
    elif trans_type == 'slide_right':
        return clip.with_effects([SlideIn(duration=duration, side='left')])
    elif trans_type == 'slide_up':
        return clip.with_effects([SlideIn(duration=duration, side='bottom')])
    elif trans_type == 'slide_down':
        return clip.with_effects([SlideIn(duration=duration, side='top')])
    elif trans_type == 'zoom_in':
        def zoom_func(t):
            return 0.1 + 0.9 * (t / duration) if t < duration else 1.0
        return clip.with_effects([Resize(zoom_func)])
    elif trans_type == 'spin_in':
        def spin_func(t):
            return 360 * (t / duration) if t < duration else 0
        def zoom_func(t):
            return 0.1 + 0.9 * (t / duration) if t < duration else 1.0
        return clip.with_effects([Rotate(spin_func), Resize(zoom_func)])
    return clip

def process_quick_clip(uploaded_images, uploaded_audio, status_text, progress_bar):
    """
    Logic for generating the Quick Clip video.
    """
    audio_path = None
    audio_clip = None
    final_clip = None
    
    try:
        status_text.text("Processing audio...")
        audio_path = save_uploaded_file(uploaded_audio)
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        
        num_images = len(uploaded_images)
        transition_duration = 1.0 
        
        if num_images > 1:
            duration_per_image = (audio_duration + transition_duration * (num_images - 1)) / num_images
        else:
            duration_per_image = audio_duration
            transition_duration = 0

        clips = []
        status_text.text("Processing images...")
        
        for i, img_file in enumerate(uploaded_images):
            img = Image.open(img_file)
            img = resize_and_pad_image(img)
            img_array = np.array(img)
            
            try:
                clip = ImageClip(img_array).with_duration(duration_per_image)
            except AttributeError:
                clip = ImageClip(img_array).set_duration(duration_per_image)
            
            start_time = i * (duration_per_image - transition_duration)
            clip = clip.with_start(start_time)
            
            if i > 0:
                trans_type = random.choice(TRANSITIONS)
                clip = apply_transition_effect(clip, trans_type, transition_duration)

            clips.append(clip)
            progress_bar.progress((i + 1) / num_images * 0.1)

        status_text.text("Composing video...")
        final_clip = CompositeVideoClip(clips, size=SCREEN_SIZE)
        
        # Determine method to set audio based on moviepy version
        if hasattr(final_clip, 'with_audio'):
            final_clip = final_clip.with_audio(audio_clip)
        else:
            final_clip = final_clip.set_audio(audio_clip)
            
        final_clip = final_clip.with_duration(audio_duration)
        
        output_filename = "final_video.mp4"
        logger = StreamlitLogger(status_text, progress_bar)
        final_clip.write_videofile(output_filename, fps=FPS, codec="libx264", audio_codec="aac", logger=logger)
        
        return output_filename, audio_path

    except Exception as e:
        st.error(f"Error processing video: {e}")
        import traceback
        st.text(traceback.format_exc())
        return None, audio_path
        
    finally:
        if final_clip: final_clip.close()
        if audio_clip: audio_clip.close()

def generate_preview_transition(prev_slide, curr_slide):
    """
    Generates a preview video for a transition.
    """
    trans_duration = float(curr_slide['transition_duration'])
    preview_duration = trans_duration * 2.0
    
    img_prev = create_slide_image(prev_slide)
    img_curr = create_slide_image(curr_slide)
    
    try:
        clip_prev = ImageClip(img_prev).with_duration(preview_duration)
    except AttributeError:
        clip_prev = ImageClip(img_prev).set_duration(preview_duration)
        
    try:
        clip_curr = ImageClip(img_curr).with_duration(preview_duration)
    except AttributeError:
        clip_curr = ImageClip(img_curr).set_duration(preview_duration)
        
    offset = 0.5 * trans_duration
    
    clip_prev = clip_prev.with_duration(offset + trans_duration).with_start(0)
    clip_curr = clip_curr.with_duration(offset + trans_duration).with_start(offset)
    
    trans_type = curr_slide['transition']
    clip_curr = apply_transition_effect(clip_curr, trans_type, trans_duration)
        
    final = CompositeVideoClip([clip_prev, clip_curr], size=SCREEN_SIZE)
    final = final.with_duration(preview_duration)
    
    import tempfile
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.close()
    
    final.write_videofile(tfile.name, fps=FPS, codec="libx264", audio=False, logger=None)
    return tfile.name

def process_custom_video(slides, audio_file, status_text, progress_bar):
    """
    Logic for generating the Custom Clip video.
    """
    audio_path = None
    audio_clip = None
    final_clip = None
    
    try:
        status_text.text("Preparing resources...")
        
        if audio_file:
            audio_path = save_uploaded_file(audio_file)
            audio_clip = AudioFileClip(audio_path)
            
        clips = []
        current_start_time = 0.0
        total_slides = len(slides)
        
        for i, slide in enumerate(slides):
            status_text.text(f"Processing slide {i+1}/{total_slides}...")
            
            img_array = create_slide_image(slide)
            duration = float(slide['duration'])
            trans_type = slide['transition']
            trans_duration = float(slide['transition_duration'])
            
            try:
                clip = ImageClip(img_array).with_duration(duration)
            except AttributeError:
                clip = ImageClip(img_array).set_duration(duration)
            
            clip = clip.with_start(current_start_time)
            
            if i > 0:
                clip = apply_transition_effect(clip, trans_type, trans_duration)
            
            clips.append(clip)
            
            if i < total_slides - 1:
                next_trans_duration = float(slides[i+1]['transition_duration'])
                current_start_time = current_start_time + duration - next_trans_duration
            else:
                current_start_time += duration
            
            progress_bar.progress((i + 1) / total_slides * 0.5)

        status_text.text("Composing video...")
        final_clip = CompositeVideoClip(clips, size=SCREEN_SIZE)
        
        video_duration = clips[-1].start + clips[-1].duration
        final_clip = final_clip.with_duration(video_duration)

        if audio_clip:
            if audio_clip.duration < video_duration:
                 # Audio is shorter, final clip handles it by cutting audio (loops not implemented per prev requirement)
                 final_clip = final_clip.with_audio(audio_clip)
            else:
                # Audio is longer, extend last slide
                diff = audio_clip.duration - video_duration
                if diff > 0:
                     last_slide = slides[-1]
                     new_duration = float(last_slide['duration']) + diff
                     
                     old_last_clip = clips.pop()
                     old_start_time = old_last_clip.start
                     
                     img_array = create_slide_image(last_slide)
                     try:
                        clip = ImageClip(img_array).with_duration(new_duration)
                     except AttributeError:
                        clip = ImageClip(img_array).set_duration(new_duration)
                        
                     clip = clip.with_start(old_start_time)
                     
                     # Re-apply transition if needed
                     if len(clips) > 0:
                         trans_type = last_slide['transition']
                         trans_duration = float(last_slide['transition_duration'])
                         clip = apply_transition_effect(clip, trans_type, trans_duration)
                             
                     clips.append(clip)
                     final_clip = CompositeVideoClip(clips, size=SCREEN_SIZE)
                     final_clip = final_clip.with_duration(audio_clip.duration)
                     final_clip = final_clip.with_audio(audio_clip)
                else:
                     final_clip = final_clip.with_audio(audio_clip)

        output_filename = "custom_video.mp4"
        logger = StreamlitLogger(status_text, progress_bar)
        final_clip.write_videofile(output_filename, fps=FPS, codec="libx264", audio_codec="aac", logger=logger)
        
        return output_filename, audio_path

    except Exception as e:
        st.error(f"Error processing video: {e}")
        import traceback
        st.text(traceback.format_exc())
        return None, audio_path
    
    finally:
        if final_clip: final_clip.close()
        if audio_clip: audio_clip.close()
