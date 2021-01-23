
from telegram import Bot
from environs import Env


env = Env()
# Read .env into os.environ
env.read_env(".env")

DEBUG = env.bool("DEBUG")
BOT_TOKEN = env.str("BOT_TOKEN")
BOT_NAME = env.str("BOT_NAME")
BOT_WORKERS = env.int("BOT_WORKERS")

DB_HOST = env.str("DB_HOST")
DB_PORT = env.int("DB_PORT")
DB_NAME = env.str("DB_NAME")
DB_USERNAME = env.str("DB_USERNAME")
DB_PASSWORD = env.str("DB_PASSWORD")
DB_STRING = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}".format(
    user=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    name=DB_NAME,
)

bot = Bot(token=BOT_TOKEN)
