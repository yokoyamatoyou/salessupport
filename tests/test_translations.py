from app.translations import TRANSLATIONS


def test_translation_keys_complete():
    languages = list(TRANSLATIONS.keys())
    base_keys = set(TRANSLATIONS[languages[0]].keys())
    for lang in languages[1:]:
        assert set(TRANSLATIONS[lang].keys()) == base_keys, f"Missing keys in {lang}"
