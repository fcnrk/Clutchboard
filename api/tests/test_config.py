def test_settings_importable():
    from app.config import settings
    assert settings.database_url.startswith("postgresql")
