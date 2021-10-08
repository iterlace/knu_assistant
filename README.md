# KNU Assistant

### Телеграм-бот, який:
- надасть тобі персоналізований розклад 
- та зручний інтерфейс запису домашніх завданнь
- єдину точку розсилки новин та важливих повідомлень одногрупникам


# Requirements
1. Python 3.9
2. Postgres 13


# Set up for development
### 1. Clone git repository
### 2. Configure the application
#### 2.1. Copy .env.example to .env
#### 2.2. Fill it with your environment variables
### 3. Set up auto-export of .env environment variables (via IDE config)
### 4. Create poetry environment
```bash
cd ./assistant/src

python -m pip install poetry
poetry install

poetry shell
```
### 5. Run tests
```bash
pytest
```
### 6. Apply all migrations
```bash
poetry run apply-migrations
```
### 7. Run the bot
```bash
poetry run run-bot
```
