try:
    from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    try:
        import moviepy
        print(f"MoviePy dir: {dir(moviepy)}")
    except:
        pass
