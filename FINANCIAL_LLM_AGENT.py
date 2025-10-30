from linkup import LinkupClient
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain
from langchain.chat_models import ChatOpenAI
import config


def search(self, search_query: str):
        search_response = self.linkup_client.search(
                query=search_query,
                depth="standard",
                output_type="searchResults",
                include_images=False,
            )
            
        
        return search_response

def llm_agent_analysis(ticker: str, market: str , temperature: float = 0.7):

    # --------------->
    linkup_client = LinkupClient(api_key=config.linkup_api_key)

    llm = ChatOpenAI(
        model='deepseek/deepseek-chat-v3.1:free',
        temperature=temperature,
        openai_api_key=config.deepseek_free_api_key,
        base_url=config.base_url
    )

    # ---------- 1) News chain ----------
    news_prompt = PromptTemplate(
        input_variables=["news_data"],
        template="Вот все собранные новости и рыночная информация:\n{news_data}\n\nСуммируй ключевые моменты в 3-5 пунктах и оцени общий тон рынка (-1..1)."
    )
    news_chain = LLMChain(llm=llm, prompt=news_prompt, output_key="news_summary")

    # ---------- 2) Price analysis chain ----------
    price_prompt = PromptTemplate(
        input_variables=["price_data"],
        template="""Проанализируй следующие данные о ценах и рыночных движениях:
{price_data}

Проанализируй: текущие уровни цен, тренд, волатильность, ключевые уровни поддержки/сопротивления. Коротко, но содержательно."""
    )
    price_chain = LLMChain(llm=llm, prompt=price_prompt, output_key="price_summary")

    # ---------- 3) Comprehensive analysis chain ----------
    analysis_prompt = PromptTemplate(
        input_variables=["comprehensive_data"],
        template="""Проанализируй ВСЕ следующие рыночные данные:
{comprehensive_data}

Сделай комплексный анализ включая:
1. Фундаментальные показатели
2. Макроэкономическую ситуацию
3. Мнения экспертов и инфлюенсеров
4. Технические индикаторы
5. Рыночные индексы и отчеты
6. Экономический календарь
Выдели ключевые выводы и факторы влияния."""
    )
    analysis_chain = LLMChain(llm=llm, prompt=analysis_prompt, output_key="comprehensive_summary")

    # ---------- 4) Final forecast chain ----------
    forecast_prompt = PromptTemplate(
        input_variables=["news_summary", "price_summary", "comprehensive_summary"],
        template=(
            "СВОДКА АНАЛИЗА:\n"
            "1. Новостной анализ: {news_summary}\n"
            "2. Анализ цены: {price_summary}\n"
            "3. Комплексный анализ: {comprehensive_summary}\n\n"
            "НА ОСНОВАНИИ ВСЕХ ДАННЫХ ДАЙ ТОРГОВЫЙ СИГНАЛ:\n"
            "- BUY / SELL / HOLD\n"
            "- Уровень уверенности (0..1)\n"
            "- Ключевая причина (1 предложение)\n"
            "- Потенциальные риски"
        )
    )
    forecast_chain = LLMChain(llm=llm, prompt=forecast_prompt, output_key="forecast")

    # ---------- SequentialChain ----------
    overall_chain = SequentialChain(
        chains=[news_chain, price_chain, analysis_chain, forecast_chain],
        input_variables=["news_data", "price_data", "comprehensive_data"],
        output_variables=["news_summary", "price_summary", "comprehensive_summary", "forecast"],
        verbose=True
    )

    def get_comprehensive_market_data(ticker: str, market: str):
        """Получение ВСЕХ рыночных данных через Tavily"""
        
        # 1. Ценовые данные и технический анализ
        price_queries = [
            f"текущая цена {ticker} {market}",
            f"исторические данные цены {ticker}",
            f"график {ticker} технический анализ",
            f"tradingview анализ {ticker}",
            f"поддержка и сопротивление {ticker}",
            f"волатильность {ticker} {market}"
        ]
        
        # 2. Фундаментальные данные
        fundamental_queries = [
            f"фундаментальный анализ {ticker} {market}",
            f"отчеты компании {ticker}" if market.lower() in ['stock', 'stocks'] else f"фундаментальные показатели {ticker}",
            f"финансовые результаты {ticker}",
            f"дивиденды {ticker}" if market.lower() in ['stock', 'stocks'] else f"доходность {ticker}"
        ]
        
        # 3. Макроэкономические данные
        macro_queries = [
            "макроэкономические показатели сегодня",
            "ключевые ставки ЦБ ФРС",
            "инфляционные данные",
            "ВВП экономический рост",
            "рыночные индексы S&P500 NASDAQ Dow Jones",
            "экономический календарь на неделю"
        ]
        
        # 4. Экспертные мнения и аналитика
        expert_queries = [
            f"мнение аналитиков о {ticker}",
            f"прогнозы экспертов {ticker} {market}",
            f"топ трейдеры мнение о {ticker}",
            f"инфлюенсеры криптовалюты анализ" if market.lower() == 'crypto' else f"финансовые инфлюенсеры анализ",
            f"хедж фонды мнение о {ticker}",
            f"институциональные инвесторы {ticker}"
        ]
        
        # 5. Рыночные индикаторы и настроения
        indicator_queries = [
            f"рыночные индикаторы {market}",
            f"индекс страха и жадности",
            f"открытый интерес {ticker}" if market.lower() == 'crypto' else f"объемы торгов {ticker}",
            f"данные спроса и предложения {ticker}",
            f"доминирование BTC" if market.lower() == 'crypto' else f"отраслевые индексы",
            "рыночные настроения sentiment анализ"
        ]
        
        # 6. Новости и события
        news_queries = [
            f"последние новости {ticker}",
            f"события влияющие на {ticker}",
            f"корпоративные новости {ticker}" if market.lower() in ['stock', 'stocks'] else f"новости проекта {ticker}",
            "геополитические события рынки",
            "регуляторные новости финансовые рынки",
            f"партнерства и интеграции {ticker}"
        ]

        # Выполняем все поисковые запросы
        all_data = {}
        
        # Группируем запросы по категориям
        query_categories = {
            "Ценовые данные и технический анализ": price_queries,
            "Фундаментальные данные": fundamental_queries,
            "Макроэкономика": macro_queries,
            "Экспертные мнения": expert_queries,
            "Рыночные индикаторы": indicator_queries,
            "Новости и события": news_queries
        }
        
        for category, queries in query_categories.items():
            category_data = []
            for query in queries:
                try:
                    result = search(search_query=query, max_results=3)
                    category_data.append(f"Запрос: {query}\nРезультат: {result}\n{'-'*50}")
                except Exception as e:
                    category_data.append(f"Запрос: {query}\nОшибка: {str(e)}\n{'-'*50}")
            all_data[category] = "\n".join(category_data)
        
        return all_data

    def get_consolidated_news_data(ticker: str, market: str):
        """Получение консолидированных новостных данных"""
        news_queries = [
            f"главные финансовые новости сегодня",
            f"новости {ticker} {market}",
            f"рыночные новости {market}",
            "экономические новости",
            f"технические новости {ticker}" if market.lower() in ['crypto', 'tech'] else f"отраслевые новости {market}",
            "геополитика влияние на рынки",
            f"социальные медиа обсуждение {ticker}",
            f"форумы трейдеров мнения {ticker}"
        ]
        
        consolidated_news = []
        for query in news_queries:
            try:
                result = search(search_query=query, max_results=2)
                consolidated_news.append(f"=== {query} ===\n{result}\n")
            except Exception as e:
                consolidated_news.append(f"=== {query} ===\nОшибка получения данных: {str(e)}\n")
        
        return "\n".join(consolidated_news)

    def get_detailed_price_data(ticker: str, market: str):
        """Получение детальных данных о цене через Tavily"""
        price_queries = [
            f"текущая цена {ticker} {market} биржа",
            f"историческая цена {ticker} график",
            f"технический анализ {ticker} tradingview",
            f"ценовые уровни {ticker} поддержка сопротивление",
            f"волатильность {ticker} ATR",
            f"тренд {ticker} анализ",
            f"объемы торгов {ticker}",
            f"свечной анализ {ticker}",
            f"индикаторы RSI MACD {ticker}"
        ]
        
        price_data = []
        for query in price_queries:
            try:
                result = search(search_query=query, max_results=2)
                price_data.append(f"**{query}**\n{result}\n{'-'*40}")
            except Exception as e:
                price_data.append(f"**{query}**\nОшибка: {str(e)}\n{'-'*40}")
        
        return "\n".join(price_data)

    # ---------- Run ----------
    inputs = {
        "news_data": get_consolidated_news_data(ticker=ticker, market=market),
        "price_data": get_detailed_price_data(ticker=ticker, market=market),
        "comprehensive_data": get_comprehensive_market_data(ticker=ticker, market=market),
    }
    
    # Получить все выходы (dict)
    outputs = overall_chain(inputs)
    
    return outputs