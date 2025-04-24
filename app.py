import asyncio
import aiohttp
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'crypto_price_comparison_secret_key'  # Necessário para usar sessions

# Traduções disponíveis
translations = {
    'pt': {
        'title': 'Comparação de Preços de Criptomoedas',
        'select_crypto': 'Selecionar Criptomoeda',
        'crypto_pair': 'Par de Criptomoeda:',
        'custom_pair': 'Ou digite um par personalizado:',
        'compare': 'Comparar Preços',
        'last_updated': 'Última atualização:',
        'exchange': 'Corretora',
        'spot_price': 'Preço à Vista',
        'futures_price': 'Preço Futuros',
        'difference': 'Diferença',
        'best_price': 'Melhor Preço',
        'no_data': 'Dados não disponíveis',
        'loading': 'Carregando preços...',
        'error': 'Falha ao buscar preços. Por favor, tente novamente.',
        'bitcoin': 'Bitcoin (BTC/USDT)',
        'ethereum': 'Ethereum (ETH/USDT)',
        'binance': 'Binance Coin (BNB/USDT)',
        'solana': 'Solana (SOL/USDT)',
        'ripple': 'Ripple (XRP/USDT)',
        'theme': 'Tema',
        'light': 'Claro',
        'dark': 'Escuro'
    },
    'en': {
        'title': 'Cryptocurrency Price Comparison',
        'select_crypto': 'Select Cryptocurrency',
        'crypto_pair': 'Cryptocurrency Pair:',
        'custom_pair': 'Or enter a custom trading pair:',
        'compare': 'Compare Prices',
        'last_updated': 'Last updated:',
        'exchange': 'Exchange',
        'spot_price': 'Spot Price',
        'futures_price': 'Futures Price',
        'difference': 'Difference',
        'best_price': 'Best Price',
        'no_data': 'No data available',
        'loading': 'Loading prices...',
        'error': 'Failed to fetch prices. Please try again.',
        'bitcoin': 'Bitcoin (BTC/USDT)',
        'ethereum': 'Ethereum (ETH/USDT)',
        'binance': 'Binance Coin (BNB/USDT)',
        'solana': 'Solana (SOL/USDT)',
        'ripple': 'Ripple (XRP/USDT)',
        'theme': 'Theme',
        'light': 'Light',
        'dark': 'Dark'
    },
    'es': {
        'title': 'Comparación de Precios de Criptomonedas',
        'select_crypto': 'Seleccionar Criptomoneda',
        'crypto_pair': 'Par de Criptomoneda:',
        'custom_pair': 'O ingrese un par personalizado:',
        'compare': 'Comparar Precios',
        'last_updated': 'Última actualización:',
        'exchange': 'Exchange',
        'spot_price': 'Precio Spot',
        'futures_price': 'Precio Futuros',
        'difference': 'Difference',
        'best_price': 'Mejor Precio',
        'no_data': 'Datos no disponibles',
        'loading': 'Cargando precios...',
        'error': 'Error al obtener precios. Por favor, inténtelo de nuevo.',
        'bitcoin': 'Bitcoin (BTC/USDT)',
        'ethereum': 'Ethereum (ETH/USDT)',
        'binance': 'Binance Coin (BNB/USDT)',
        'solana': 'Solana (SOL/USDT)',
        'ripple': 'Ripple (XRP/USDT)',
        'theme': 'Tema',
        'light': 'Claro',
        'dark': 'Oscuro'
    }
}

# URLs das corretoras para links diretos
EXCHANGE_URLS = {
    "Binance": {
        "spot": "https://www.binance.com/pt-BR/trade/{symbol}_USDT",
        "futures": "https://www.binance.com/pt-BR/futures/{symbol}USDT"
    },
    "Bitget": {
        "spot": "https://www.bitget.com/pt-BR/spot/{symbol}_USDT",
        "futures": "https://www.bitget.com/pt-BR/mix/usdt/{symbol}_UMCBL"
    },
    "Bybit": {
        "spot": "https://www.bybit.com/pt-BR/trade/spot/{symbol}/USDT",
        "futures": "https://www.bybit.com/pt-BR/trade/usdt/{symbol}/USDT"
    },
    "MEXC": {
        "spot": "https://www.mexc.com/pt-BR/exchange/{symbol}_USDT",
        "futures": "https://www.mexc.com/pt-BR/futures/exchange/{symbol}_USDT"
    },
    "Gate.io": {
        "spot": "https://www.gate.io/pt/trade/{symbol}_USDT",
        "futures": "https://www.gate.io/pt/futures_trade/{symbol}_USDT"
    }
}

# Exchange API functions
async def get_binance_price(session, symbol, market="spot"):
    try:
        endpoint = (
            f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
            if market == "futures"
            else f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        )
        
        async with session.get(endpoint) as response:
            if response.status == 200:
                data = await response.json()
                return {"price": float(data["price"])}
            else:
                return {"error": f"API error: {response.status}"}
    except Exception as e:
        return {"error": str(e)}

async def get_bitget_price(session, symbol, market="spot"):
    try:
        # Bitget requires different symbol format
        formatted_symbol = f"{symbol}_UMCBL" if market == "futures" else symbol.replace("USDT", "_USDT")
        
        endpoint = (
            f"https://api.bitget.com/api/mix/v1/market/ticker?symbol={formatted_symbol}"
            if market == "futures"
            else f"https://api.bitget.com/api/spot/v1/market/ticker?symbol={formatted_symbol}"
        )
        
        async with session.get(endpoint) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("code") == "00000" and data.get("data"):
                    price_key = "last" if market == "futures" else "close"
                    return {"price": float(data["data"][price_key])}
                else:
                    return {"error": "Invalid response from Bitget"}
            else:
                return {"error": f"API error: {response.status}"}
    except Exception as e:
        return {"error": str(e)}

async def get_bybit_price(session, symbol, market="spot"):
    try:
        endpoint = (
            f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
            if market == "futures"
            else f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={symbol}"
        )
        
        async with session.get(endpoint) as response:
            if response.status == 200:
                data = await response.json()
                
                if market == "futures":
                    if data.get("result") and len(data["result"]) > 0:
                        return {"price": float(data["result"][0]["last_price"])}
                    else:
                        return {"error": "No data returned from Bybit"}
                else:
                    if data.get("result") and data["result"].get("list") and len(data["result"]["list"]) > 0:
                        return {"price": float(data["result"]["list"][0]["lastPrice"])}
                    else:
                        return {"error": "No data returned from Bybit"}
            else:
                return {"error": f"API error: {response.status}"}
    except Exception as e:
        return {"error": str(e)}

async def get_mexc_price(session, symbol, market="spot"):
    try:
        endpoint = (
            f"https://contract.mexc.com/api/v1/contract/ticker?symbol={symbol}"
            if market == "futures"
            else f"https://api.mexc.com/api/v3/ticker/price?symbol={symbol}"
        )
        
        async with session.get(endpoint) as response:
            if response.status == 200:
                data = await response.json()
                
                if market == "futures":
                    if data.get("data") and len(data["data"]) > 0:
                        return {"price": float(data["data"][0]["last"])}
                    else:
                        return {"error": "No data returned from MEXC"}
                else:
                    if data.get("price"):
                        return {"price": float(data["price"])}
                    else:
                        return {"error": "No data returned from MEXC"}
            else:
                return {"error": f"API error: {response.status}"}
    except Exception as e:
        return {"error": str(e)}

async def get_gateio_price(session, symbol, market="spot"):
    try:
        # Gate.io uses different symbol format
        formatted_symbol = symbol.replace("USDT", "_USDT")
        
        endpoint = (
            f"https://api.gateio.ws/api/v4/futures/usdt/contracts/{formatted_symbol}"
            if market == "futures"
            else f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={formatted_symbol}"
        )
        
        async with session.get(endpoint) as response:
            if response.status == 200:
                data = await response.json()
                
                if market == "futures":
                    if data.get("last_price"):
                        return {"price": float(data["last_price"])}
                    else:
                        return {"error": "No data returned from Gate.io"}
                else:
                    if data and len(data) > 0 and data[0].get("last"):
                        return {"price": float(data[0]["last"])}
                    else:
                        return {"error": "No data returned from Gate.io"}
            else:
                return {"error": f"API error: {response.status}"}
    except Exception as e:
        return {"error": str(e)}

async def fetch_all_prices(symbol):
    async with aiohttp.ClientSession() as session:
        # Fetch both spot and futures prices in parallel
        spot_tasks = [
            get_binance_price(session, symbol, "spot"),
            get_bitget_price(session, symbol, "spot"),
            get_bybit_price(session, symbol, "spot"),
            get_mexc_price(session, symbol, "spot"),
            get_gateio_price(session, symbol, "spot")
        ]
        
        futures_tasks = [
            get_binance_price(session, symbol, "futures"),
            get_bitget_price(session, symbol, "futures"),
            get_bybit_price(session, symbol, "futures"),
            get_mexc_price(session, symbol, "futures"),
            get_gateio_price(session, symbol, "futures")
        ]
        
        # Execute all tasks in parallel
        all_tasks = spot_tasks + futures_tasks
        all_results = await asyncio.gather(*all_tasks)
        
        # Split results
        spot_results = all_results[:5]
        futures_results = all_results[5:]
        
        exchanges = ["Binance", "Bitget", "Bybit", "MEXC", "Gate.io"]
        
        # Calculate lowest prices
        spot_valid_prices = [data["price"] for data, exch in zip(spot_results, exchanges) if "price" in data]
        futures_valid_prices = [data["price"] for data, exch in zip(futures_results, exchanges) if "price" in data]
        
        spot_lowest = min(spot_valid_prices) if spot_valid_prices else None
        futures_lowest = min(futures_valid_prices) if futures_valid_prices else None
        
        # Combine results
        combined_results = {}
        for i, exchange in enumerate(exchanges):
            # Generate URLs for this exchange and symbol
            base_symbol = symbol.replace("USDT", "")
            spot_url = EXCHANGE_URLS[exchange]["spot"].replace("{symbol}", base_symbol)
            futures_url = EXCHANGE_URLS[exchange]["futures"].replace("{symbol}", base_symbol)
            
            combined_results[exchange] = {
                "spot": spot_results[i],
                "futures": futures_results[i],
                "spot_lowest": spot_lowest,
                "futures_lowest": futures_lowest,
                "spot_url": spot_url,
                "futures_url": futures_url
            }
        
        return combined_results

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in translations:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/set_theme/<theme>')
def set_theme(theme):
    if theme in ['light', 'dark']:
        session['theme'] = theme
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    # Definir idioma padrão se não estiver na sessão
    if 'language' not in session:
        session['language'] = 'pt'  # Português como padrão
    
    # Definir tema padrão se não estiver na sessão
    if 'theme' not in session:
        session['theme'] = 'dark'  # Tema escuro como padrão
    
    # Obter traduções para o idioma atual
    lang = session['language']
    theme = session['theme']
    
    return render_template('index.html', 
                          translations=translations[lang], 
                          current_lang=lang,
                          current_theme=theme)

@app.route('/api/prices')
def get_prices():
    symbol = request.args.get('symbol', 'BTCUSDT')
    
    # Run the async function in the synchronous Flask context
    prices = asyncio.run(fetch_all_prices(symbol))
    
    # Add timestamp
    response = {
        "prices": prices,
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
