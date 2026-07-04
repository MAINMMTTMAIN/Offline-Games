import arabic_reshaper
from bidi.algorithm import get_display

def render_persian_text(font, text, color, bg=None):
    """رندر متن فارسی با اتصال حروف و جهت صحیح"""
    reshaped = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped)
    return font.render(bidi_text, True, color, bg)

def reshape_persian(text):
    """تبدیل متن فارسی به فرمت مناسب برای نمایش"""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)
