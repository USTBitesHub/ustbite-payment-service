from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = ""
    rabbitmq_url: str = ""
    redis_url: str = ""
    jwt_secret: str = "ustbite-jwt-secret-change-in-prod"

    class Config:
        env_file = ".env"

settings = Settings()
