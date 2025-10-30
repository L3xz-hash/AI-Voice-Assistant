import os
import time
import openai
import requests
import mouse
import numpy as np
import threading
import pyautogui
import yfinance
import pyttsx3
from linkup import LinkupClient
import speech_recognition as sr
import webbrowser
import datetime
import keyboard
from random import randint, choice
from win32api import Beep
import FINANCIAL_LLM_AGENT as agent_api
import warnings
import config


# =====> variables <======
name = 'Джарвис' # Майк
owner_name = 'Стас'
talking_speed = 125


# ---> API keys <---


# =====> configuration <======
pyautogui.FAILSAFE = False
warnings.filterwarnings('ignore')
linkup_client = LinkupClient(api_key=config.linkup_api_key)


# =====> keywords array's <======
hello_cmds = ['Привет!', 'На связи', f'{name} на связи', f'Привет {owner_name}', 'Здарова', 'Здаров, как дела?', 'Ага привет, как жизнь', 'Всегда к вашим услугам серр',
              'Добрый день', 'Доброго времени суток', 'Рад тебя слышать', 'Привет, чё нового за сегодня?', 
              'Я здесь', 'Я тут', 'Я тута', 'Рад вновь тебя слышать', 'Привет, привет', 'Здарова заебал',
              ]

seccus_cmds = ['Хорошо', 'Как скажешь', 'Не вопрос', 'Секунду', 'Сейчас', 'Выполняю', 'Окей', 'Без проблем', 'Делаю', 'Сейчас будет',
              'Ага, выполняю', 'Запрос выполнен', 'Выполняю твой запрос', 'Всегд к вашим услугам', 'Всегда к вашим услугам, сер', 'Оо да, работаем']



# =====> Functions <======
def deepseek(prompt: str, system_prompt: str, temperature: float = 1.00, max_tokens: int = 2400):

    client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=config.deepseek_free_api_key,
    )

    completion = client.chat.completions.create(
    extra_body={},
    model="deepseek/deepseek-chat-v3.1:free",
    messages=[
            {
                "role": "dev",
                "content": 'Ты личный ассистент, отвечаешь коротко и точно',
            },
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt
            }
    ],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return completion.choices[0].message.content


def mistral(prompt: str):
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config.mistral_api_key,
    )

    completion = client.chat.completions.create(
    model="mistralai/mistral-small-3.2-24b-instruct:free",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": prompt,
            },
        ]
        }
    ]
    )
    return completion.choices[0].message.content



'''Main AI Voice Assistant class'''
class Assistant:
    def __init__(self, name: str = name, owner_name: str = owner_name, speed: int = talking_speed, log: bool = False):
        self.name = name
        self.owner = owner_name
        self.speed = speed
        self.log = log

    def search(self, search_query: str):
        search_response = linkup_client.search(
                query=search_query,
                depth="standard",
                output_type="searchResults",
                include_images=False,
            )
        return search_response
    

    def say(self, text: str):
        if self.log:
            self.speaker = pyttsx3.init()
            self.speaker.setProperty(name=self.name, value=self.speed)
            self.speaker.say(text=text)
            self.speaker.runAndWait()
            print(f'Assistant: {text}')
        else:
            self.speaker = pyttsx3.init()
            self.speaker.setProperty(name=self.name, value=self.speed)
            self.speaker.say(text=text)
            self.speaker.runAndWait()
        

    def listen(self):
        if self.log:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                print("Слушаю...")
                r.pause_threshold = 2.0
                audio = r.listen(source)
            
            try:
                print("Распознаю...")
                query = r.recognize_google(audio, language='ru-RU')
                print(f"Вы сказали: {query}")
                return query.lower()
            except Exception as e:
                print("Повторите, пожалуйста...")
                return ""
        else:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.pause_threshold = 2.0
                audio = r.listen(source)
            
            try:
                query = r.recognize_google(audio, language='ru-RU')
                return query.lower()
            except Exception as e:
                return ""
            
    def check_tasks(self, query: any):
        query += ' '
        
        if 'привет' in query or 'здарова' in query or 'здорово' in query or 'салам' in query or 'здравствуй' in query:
            self.say(choice(hello_cmds))
        
        elif ('время' in query or 'времени' in query) and ('сколько' in query or 'сейчас' in query or ' по ' in query):
            current_time = datetime.datetime.now().strftime("%H:%M")
            self.say(f"{choice(['Сейчас', 'На данный момент', 'Щас', 'Текущее время'])}: {current_time}")

        elif 'дата' in query or 'число' in query:
            current_date = datetime.datetime.now().strftime("%d.%m.%Y")
            self.say(f"{choice(['Сегодня', 'Сегодняшнее число', 'сегодняшная дата'])} {current_date}")
        
        # desktop & system
        elif "создай папку" in query:
            folder_name = query.replace("создай папку", "").strip()
            if folder_name:
                try:
                    os.mkdir(folder_name)
                    self.say(f"Папка {folder_name} создана")
                except:
                    self.say("Не удалось создать папку")
            else:
                self.say("Как назвать папку?")
                query = self.listen()
                query = query.replace(' с ', '')
                if len(query.split(' ')) >= 2:
                    query = query.split(' ')
                    folder_name = query[-1]
                    os.makedirs(folder_name)
                else:
                    os.makedirs(query)
        

        elif "браузер" in query:
            if randint(0, 3) == 2:
                self.say(choice(seccus_cmds))
            webbrowser.open("https://www.google.com")
            self.say("Браузер открыт")

        elif 'vk' in query or 'вк ' in query or 'вконтакте' in query:
            webbrowser.open('https://vk.ru/al_feed.php')
        elif 'ютуб' in query or 'youtube' in query:
            webbrowser.open('https://www.youtube.com/')

        elif 'музык' in query:
            webbrowser.open('https://vk.ru/audio')

        elif ('создатель' in query or 'разработчик' in query) and 'твой' in query:
            self.say(f'Мой создатель: Великий и могучий {self.owner}')


        elif 'выключи' in query and ('пк' in query or 'компьютер' in query):
            os.system('shutdown /p')


        # rofls
        elif 'я дома' in query or 'я пришёл' in query:
            self.say(choice(['Окей, включая жёское гей порно', 'Ну давай повеселимся', 'Рад вас видеть сер. Включаю ваш любимый контент']))
            web_ahaha = choice(['https://www.youtube.com/watch?v=PB-opnWtmVM', 'https://www.youtube.com/watch?v=9SNBuk7Utco&t=1s', 
                                    'https://youtu.be/42tidRwoNks?si=lT06Q54cfItHuj38', 'https://www.youtube.com/watch?v=JV0UgKunXbo',
                                    'https://sex-studentki.live/video/zaceni-figurku-brat-kak-dumaesh-trahnut-menja-ty-byl-by-rad-27694', 'https://sex-studentki.live/'])
            webbrowser.open_new_tab(web_ahaha)
            if web_ahaha == 'https://sex-studentki.live/video/zaceni-figurku-brat-kak-dumaesh-trahnut-menja-ty-byl-by-rad-27694':
                pyautogui.moveTo(0,0)
                time.sleep(0.09)
                mouse.click()

        elif 'шухер' in query:
            pyautogui.moveTo(0, 0)
            time.sleep(0.075)
            mouse.click()

            pyautogui.hotkey('alt', 'tab')

        elif 'полноэкранный' in query or 'экран' in query:
            keyboard.press('f')

        
        # usefully
        elif ('биткоин' in query or 'bitcoin'  in query) and ('куда пойдёт' in query or 'будет' in query or 'прогноз' in query or 'анализ' in query or 'сигнал' in query or 'аналит' in query):
            self.say(choice(['Аналитика', 'Аналазирую', 'Проведённый анализ по Биткоину', 'Мой анализ битка']))
            forecast = agent_api.llm_agent_analysis(ticker='Биткоин', market='Crypto')
            self.say(forecast['news_summary'])
            self.say(forecast['price_summary'])
            self.say(forecast['comprehensive_summary'])
            self.say(forecast['forecast'])

        elif ('газпром' in query or 'gazprom'  in query) and ('куда пойдёт' in query or 'будет' in query or 'прогноз' in query or 'анализ' in query or 'сигнал' in query or 'аналит' in query):
            self.say(choice(['Аналитика', 'Аналазирую', 'Провожу анализ по Газрому', 'Анализирую акции газпрома']))
            forecast = agent_api.llm_agent_analysis(ticker='Акции Газпром', market='Stock')
            self.say(forecast['news_summary'])
            self.say(forecast['price_summary'])
            self.say(forecast['comprehensive_summary'])
            self.say(forecast['forecast'])

        elif ('сбер' in query or 'sber'  in query) and ('куда пойдёт' in query or 'будет' in query or 'прогноз' in query or 'анализ' in query or 'сигнал' in query or 'аналит' in query):
            self.say(choice(['Аналитика', 'Аналазирую', 'Провожу анализ по СБербанку', 'Анализирую акции сбера']))
            forecast = agent_api.llm_agent_analysis(ticker='Акции Сбербанк', market='Stock')
            self.say(forecast['news_summary'])
            self.say(forecast['price_summary'])
            self.say(forecast['comprehensive_summary'])
            self.say(forecast['forecast'])

        elif ('рубль' in query or 'rub'  in query) and ('куда пойдёт' in query or 'будет' in query or 'прогноз' in query or 'анализ' in query or 'сигнал' in query or 'аналит' in query):
            self.say(choice(['Аналитика', 'Аналазирую', 'Провожу анализ по Рублю', 'Анализи Российский рубль']))
            forecast = agent_api.llm_agent_analysis(ticker='Рубль', market='Forex')
            self.say(forecast['news_summary'])
            self.say(forecast['price_summary'])
            self.say(forecast['comprehensive_summary'])
            self.say(forecast['forecast'])

        elif ('доллар' in query or 'dollar'  in query) and ('куда пойдёт' in query or 'будет' in query or 'прогноз' in query or 'анализ' in query or 'сигнал' in query or 'аналит' in query):
            self.say(choice(['Аналитика', 'Аналазирую', 'Проведённый анализ по Доллару', 'Провожу свой анализ доллара США']))
            forecast = agent_api.llm_agent_analysis(ticker='Доллар', market='Forex')
            self.say(forecast['news_summary'])
            self.say(forecast['price_summary'])
            self.say(forecast['comprehensive_summary'])
            self.say(forecast['forecast'])


        
        elif 'биткоин' in query or 'bitcoin' in query and ('сколько' in query or 'цена' in query or 'стоит' in query or 'курс' in query):
            bitcoin_price = yfinance.download(tickers='BTC-USD', period='1d', interval='1h')[['Close']].iloc[-1]
            webbrowser.open('https://yandex.ru/finance/currencies/btc_rub')
            self.say(f'Текущая цена биткоина {int(bitcoin_price)}$')

        elif 'доллар' in query or 'dollar' in query and ('сколько' in query or 'цена' in query or 'стоит' in query or 'курс' in query):
            dollar_price = yfinance.download(tickers='RUB=X', period='1d', interval='1h')[['Close']].iloc[-1]
            webbrowser.open('https://yandex.ru/finance/currencies/usd_rub')
            self.say(f'Сейчас курс доллара к рублю: {float(np.round(dollar_price, 2))} рублей')

        elif 'евро' in query or 'euro' in query and ('сколько' in query or 'цена' in query or 'стоит' in query or 'курс' in query):
            self.say(text=choice(seccus_cmds))
            webbrowser.open('https://yandex.ru/finance/currencies/EUR_RUB')


        else:
            if 'найди' in query or 'расскажи' in query or 'о чём' in query or 'почему' in query or 'для чего' in query or 'где' in query or 'как' in query:
                try:
                    search_query = mistral(prompt=f'Сгенерируй поисковой запрос в браузер для поиска нужной информации, основываясь на просьбу\запрос пользователя:\n{query}')
                    search_results = self.search(search_query=search_query, max_results=20)['results']
                    ai_answer = deepseek(prompt=f'Дай ответ пользователю на вопрос: {query}\nИмею полученую информацию с интернета:\n{search_results}', 
                                     system_prompt=f'Ты личный помощьник {self.owner} который может отвечать на любые вопросы.\nТебя зовут {self.name}\nТы активен, дружелюбен и имеешь хорошее чувство юмора\nОтвечаешь грамотно структурирую информацию, полученную с интернета', 
                                     temperature=1.2, max_tokens=1700)
                except:
                    search_results = self.search(search_query=query, max_results=40)['results']
                    ai_answer = deepseek(prompt=f'Дай ответ пользователю на вопрос: {query}\nИмею полученую информацию с интернета:\n{search_results}', 
                                     system_prompt=f'Ты личный помощьник {self.owner} который может отвечать на любые вопросы.\nТебя зовут {self.name}\nТы активен, дружелюбен и имеешь хорошее чувство юмора\nОтвечаешь грамотно структурирую информацию, полученную с интернета', 
                                     temperature=1.2, max_tokens=1700)
                    
                ai_answer.replace('*', '')
                ai_answer.replace('#', '')
                self.say(ai_answer)

            else:
                query_words = query.split(' ')
                if len(query_words) >= 5:
                    ai_answer = deepseek(prompt=query, 
                                        system_prompt=f'Ты личный помощьник {self.owner} который может отвечать на любые вопросы.\nТебя зовут {self.name}\nТы активен, дружелюбен и имеешь хорошее чувство юмора', 
                                        temperature=1.4, max_tokens=1700)
            
                    ai_answer.replace('*', '')
                    ai_answer.replace('#', '')
                    self.say(ai_answer)



    def run(self):
        self.name = self.name.lower()
        self.owner = self.owner.lower()

        while True:
            query = self.listen()
            
            if query == "":
                continue
            
            if self.name in query:
                self.check_tasks(query=query)
                for i in range(6):
                    query = self.listen()
                    self.check_tasks(query=query)

            if self.log == True:
                print('-------------\n')


if __name__ == '__main__':
    Beep(500, 700)
    os.system('cls')
    print(f'------------->\nАссистент {name}\nРазработан {owner_name}ом в целях "По приколу"\n------------->\n\n')
    assistant = Assistant(name=name, owner_name=owner_name, speed=talking_speed, log=True)
    assistant.say(f'{name} на связи!')
    time.sleep(1)
    assistant.run()