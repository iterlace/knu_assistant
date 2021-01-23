# KNU Assistant

### Телеграм-бот, який:
- надасть тобі персоналізований розклад 
- та зручний інтерфейс запису домашніх завданнь
- єдину точку розсилки новин та важливих повідомлень одногрупникам


# Requirements
1. Python 3.8
2. Postgres 13


# Installation
### 1. Clone git repository
### 2. Configure the application
#### 2.1. Copy .env.example to .env
#### 2.2. Fill it with your environment variables
### 3. Run tests
```bash
python setup.py test
```
### 4. Install the package
for a development purpose:
```bash
python setup.py develop
```
for a production use:
```bash
python setup.py install
```
### 5. Apply all migrations
```bash
knu_assistant_apply_migrations
```
### 6. Run the bot
```bash
knu_assistant_run_bot
```
