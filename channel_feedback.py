#Adding module for database
import sqlite3

#Creating connection w/ database, creating table
connection = sqlite3.connect(r'.\data\unique_message.db')
cursor = connection.cursor()

#Still thinking about the structure of data in this database
#cursor.execute("CREATE TABLE IF NOT EXISTS messages (id text PRIMARY KEY, forwarded_date integer, id_chat integer, id_channel integer, id_user integer)")


# Подключаем модуль для телеграма
import telebot

# Указываем токен
bot=telebot.TeleBot("1436783779:AAGy6-qZp-kxAr4nHygf-lst1kfRvdbabXg")

#=========================================================================

from telebot import types

# Делаем клавиатуры
kb_empty = types.ReplyKeyboardRemove()
#--------------------------------------------------------------------
kb_reply = types.ForceReply()

#=========================================================================

# Функция для прослушки и записи сообщений бота
def send_and_log(chat_id, bot_text, kb=kb_empty):
    f=open(".\logs\chat_"+str(chat_id)+".txt","a+")
    message=bot.send_message(chat_id, bot_text, reply_markup=kb)
    if type(message.text)==str:
        f.write(" >> bot: " + message.text + "\n")
    else:
        f.write(" >> bot : That's not a text, so here's ID: " + str(message.message_id) +"\n")
    f.close()

# Функция для прослушки и записи сообщений пользователя
def log_user(messages):
    for message in messages:
        f=open(".\logs\chat_"+str(message.chat.id)+".txt","a+")
        try:
            f.write(" >>" + message.from_user.username + ":" + message.text + "\n")
        except TypeError:
            f.write(" >> " + message.from_user.username + "That's not a text, so here's ID: " + str(message.message_id) +"\n")
        f.close()
        
#func that checks uniqueness of tha message and adds it to the list of unique ones
def unique_message(date):
    flag = True #uniqueness flag
    
    #for line in f:
        #i=i+1
        #flag = (date != int(line) or date == None) and flag
    
    if flag and (date != None):
        insert_query = "INSERT into switch values (?, ?, ?)"
        #Kinda stuck in here
        #data=(str(message.message_id)+str(message.chat.id),message.forward_date,)
        cursor.execute(insert_query, data)
        connection.commit()
    
    return flag

#=========================================================================

# Реагируем на команды

@bot.message_handler(commands=['start'])
def start(message):
    send_and_log(message.chat.id, "Привет! Сбрось мне дз или любую другую важную информацию.") #Можно заменить на kb_reply_menu

@bot.message_handler(commands=['help'])
def help_message(message):
    send_and_log(message.chat.id, "Со всеми вопросами пока обращаться к @the_Yttra")

@bot.message_handler(content_types=['text', 'document', 'photo', 'voice', 'contact', 'sticker'])
def user_to_headboy(message):
    if unique_message(message.forward_date):
        forward_to_id = 858871102 #That's Yttra's chat_id. Chargoal's chat_id is 425730055
        bot.forward_message(forward_to_id, message.chat.id, message.message_id)
        
#=========================================================================

#Ожидаем сообщений пользователя
bot.set_update_listener(log_user)

# Запускаем постоянный опрос бота в Телеграме
bot.polling(none_stop=True, interval=0)