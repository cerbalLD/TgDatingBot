import os


def get_anonymous_media_path(is_male: bool) -> str:
    filename = "men.PNG" if is_male else "women.PNG"
    return os.path.normpath(os.path.join("assets", "anon", filename))
