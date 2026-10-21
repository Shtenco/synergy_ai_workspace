from pathlib import Path
BANNED=('import vk','from vk','import telegram','from telegram','import instagram','from instagram','import facebook','from facebook','import whatsapp','from whatsapp','import signal','from signal','import threads','from threads','import tiktok','from tiktok','import youtube','from youtube','smm_platforms')
def test_production_package_has_no_legacy_social_imports():
    root=Path(__file__).parents[1]
    for p in root.rglob('*.py'):
        if '/tests/' in str(p).replace('\\','/'): continue
        low=p.read_text(encoding='utf-8').lower()
        for word in BANNED: assert word not in low, f'{word} in {p}'
