from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://seyal:seyal_dev_password@localhost:5432/seyal_dev"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    company_name: str = "SEYAL-TCHAD"
    company_currency: str = "XAF"

    # Optional: if set and no superuser exists yet, seed() creates one on
    # startup. Never hardcoded - read from the environment / .env only,
    # and meant to be unset again once the first real admin is created.
    admin_bootstrap_email: str | None = None
    admin_bootstrap_password: str | None = None


settings = Settings()
