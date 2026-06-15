import os
import requests

TOKEN = os.getenv("TOKEN_BOT")

# BASE DE DATOS COMPLETA: MERVAL, CRIPTOS E INTERNACIONALES POR SECTOR
UNIVERSO_ACTIVOS = {
    # --- PANEL LÍDER MERVAL (ARGENTINA) ---
    "ALUA.BA":  {"desc": "Aluar", "tags": "aluminio metalurgia industria materiales merval"},
    "BBAR.BA":  {"desc": "Banco BBVA Argentina", "tags": "banco finanzas bancario merval bba"},
    "BMA.BA":   {"desc": "Banco Macro", "tags": "banco finanzas bancario merval macro"},
    "BYMA.BA":  {"desc": "Bolsas y Mercados Argentinos", "tags": "finanzas bolsa mercado merval"},
    "CEPU.BA":  {"desc": "Central Puerto", "tags": "energia electricidad servicios merval cepu"},
    "COME.BA":  {"desc": "Sociedad Comercial del Plata", "tags": "holding empresa merval comercial"},
    "EDN.BA":   {"desc": "Edenor", "tags": "electricidad energia servicios merval"},
    "GGAL.BA":  {"desc": "Grupo Financiero Galicia", "tags": "banco finanzas bancario galicia merval"},
    "IRSA.BA":  {"desc": "IRSA", "tags": "bienes raices inmuebles propiedades merval"},
    "LOMA.BA":  {"desc": "Loma Negra", "tags": "cemento construccion industria merval"},
    "METR.BA":  {"desc": "Metrogas", "tags": "gas energia servicios merval"},
    "MIRG.BA":  {"desc": "Mirgor", "tags": "tecnologia industrial automotriz merval"},
    "PAMP.BA":  {"desc": "Pampa Energía", "tags": "energia petroleo gas electricidad merval pampa"},
    "SUPV.BA":  {"desc": "Banco Supervielle", "tags": "banco finanzas bancario merval"},
    "TECO2.BA": {"desc": "Telecom Argentina", "tags": "telecomunicaciones tecnologia internet merval"},
    "TGNO4.BA": {"desc": "Transportadora Gas del Norte", "tags": "gas energia servicios merval tgn"},
    "TGSU2.BA": {"desc": "Transportadora Gas del Sur", "tags": "gas energia servicios merval tgs"},
    "TRAN.BA":  {"desc": "Transener", "tags": "electricidad energia servicios merval"},
    "TXAR.BA":  {"desc": "Ternium Argentina", "tags": "siderurgia acero industria merval ternium"},
    "VALO.BA":  {"desc": "Banco de Valores", "tags": "banco finanzas merval"},
    "YPFD.BA":  {"desc": "YPF Clase D", "tags": "petroleo gas energia combustibles merval ypf"},
    
    # --- CRIPTOMONEDAS VOLÁTILES (DIARIAS) ---
    "BTC-USD":  {"desc": "Bitcoin USD", "tags": "cripto criptomoneda bitcoin btc volatilidad diaria"},
    "ETH-USD":  {"desc": "Ethereum USD", "tags": "cripto criptomoneda ethereum eth volatilidad contratos"},
    "BNB-USD":  {"desc": "Binance Coin USD", "tags": "cripto criptomoneda binance bnb utilidad"},
    "SOL-USD":  {"desc": "Solana USD", "tags": "cripto criptomoneda solana sol daytrading volatilidad rapida"},
    "XRP-USD":  {"desc": "Ripple USD", "tags": "cripto criptomoneda ripple xrp pagos"},
    "ADA-USD":  {"desc": "Cardano USD", "tags": "cripto criptomoneda cardano ada"},
    "AVAX-USD": {"desc": "Avalanche USD", "tags": "cripto criptomoneda avalanche avax"},
    "DOT-USD":  {"desc": "Polkadot USD", "tags": "cripto criptomoneda polkadot dot"},
    "LINK-USD": {"desc": "Chainlink USD", "tags": "cripto criptomoneda chainlink link oraculo"},
    "DOGE-USD": {"desc": "Dogecoin USD", "tags": "cripto criptomoneda dogecoin doge memecoin volatilidad diaria"},
    
    # --- CRIPTOMONEDAS ESTABLES (VALEN 1 DÓLAR) ---
    "USDT-USD": {"desc": "Tether USD (USDT)", "tags": "cripto criptomoneda stablecoin estable dolar usdt fiat digital"},
    "USDC-USD": {"desc": "USD Coin (USDC)", "tags": "cripto criptomoneda stablecoin estable dolar usdc coinbase circle"},
    "DAI-USD":  {"desc": "Dai (DAI)", "tags": "cripto criptomoneda stablecoin estable dolar dai descentralizada maker"},

    # --- SECTOR AGRO ---
    "CRES.BA":  {"desc": "Cresud", "tags": "agro agropecuario campo propiedades cresud"},
    "MOLA.BA":  {"desc": "Molinos Agro", "tags": "agro alimentos oleaginoso exportacion molinos"},
    "LEDE.BA":  {"desc": "Ledesma", "tags": "agro azucar papel economia ledesma"},

    # --- MERCADO INTERNACIONAL ---
    "GC=F":     {"desc": "Oro Futuros (Gold)", "tags": "oro metal refugio mineria minerales exterior commodity"},
    "GOLD":     {"desc": "Barrick Gold", "tags": "mineria oro metal minerales exterior barrick"},
    "FCX":      {"desc": "Freeport-McMoRan", "tags": "cobre mineria metal minerales exterior fcx"},
    "ALB":      {"desc": "Albemarle Corporation", "tags": "litio mineria quimica minerales baterias exterior"},
    "VALE":     {"desc": "Vale S.A.", "tags": "hierro mineria metal minerales exterior brasil vale"},
    "NVDA":     {"desc": "NVIDIA Corporation", "tags": "tecnologia ia inteligencia artificial chips semiconductores exterior nvidia"},
    "AAPL":     {"desc": "Apple Inc.", "tags": "tecnologia iphone hardware celulares software exterior apple"},
    "MSFT":     {"desc": "Microsoft Corporation", "tags": "tecnologia software windows nube ia exterior microsoft"},
    "AMD":     {"desc": "Advanced Micro Devices", "tags": "tecnologia chips procesadores hardware semiconductores exterior amd"},
    "TSM":      {"desc": "Taiwan Semiconductor", "tags": "tecnologia chips fabricacion semiconductores exterior tsmc"},
    "XOM":      {"desc": "Exxon Mobil", "tags": "energia petroleo gas combustible exterior exxon"},
    "CVX":      {"desc": "Chevron Corporation", "tags": "energia petroleo gas combustible exterior chevron"},
    "SHEL":     {"desc": "Shell plc", "tags": "energia petroleo gas combustible exterior shell"},
    "BP":       {"desc": "BP plc (British Petroleum)", "tags": "energia petroleo gas combustible exterior bp"},
    "GOOGL":    {"desc": "Alphabet Inc. (Google)", "tags": "comunicaciones internet tecnologia buscador google exterior alphabet"},
    "META":     {"desc": "Meta Platforms (Facebook)", "tags": "comunicaciones redes sociales instagram metaverso exterior facebook meta"},
    "NFLX":     {"desc": "Netflix Inc.", "tags": "comunicaciones streaming entretenimiento peliculas exterior netflix"},
    "DIS":      {"desc": "The Walt Disney Company", "tags": "comunicaciones entretenimiento medios exterior disney"},
    "TSLA":     {"desc": "Tesla Inc.", "tags": "automotrices autos electricos tecnologia baterias exterior tesla estados unidos usa"},
    "BYDDF":    {"desc": "BYD Company (Gigante Eléctrico)", "tags": "automotrices autos electricos china asiatico exterior byd vehiculos"},
    "NIO":      {"desc": "NIO Inc. (Autos Eléctricos)", "tags": "automotrices autos electricos china asiatico exterior nio vehiculos"},
    "F":        {"desc": "Ford Motor Company", "tags": "automotrices autos industria vehiculos exterior ford tradicional estados unidos usa"},
    "GM":       {"desc": "General Motors", "tags": "automotrices autos industria vehiculos exterior gm tradicional estados unidos usa"},
    "TM":       {"desc": "Toyota Motor Corp", "tags": "automotrices autos vehiculos japon asiatico exterior toyota tradicional"},
    "RACE":     {"desc": "Ferrari N.V. (Lujo)", "tags": "automotrices autos vehiculos italia europa exterior ferrari lujo race"},
    "SPY":      {"desc": "S&P 500 ETF", "tags": "usa eeuu etf mercado exterior bolsa estados unidos general index"}
}

def enviar_a_telegram(chat_id, texto):
    url     = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    try: 
        requests.post(url, data=payload, timeout=10)
    except Exception as e: 
        print(f"[ERROR Telegram Buscar]: {e}")

def ejecutar_busqueda(argumento, chat_id):
    if not argumento:
        enviar_a_telegram(chat_id, "⚠️ <b>Uso correcto:</b> <code>/buscar [término/sector]</code>\n\n💡 Ejemplos:\n• <code>/buscar dolar</code>\n• <code>/buscar estable</code>\n• <code>/buscar cripto</code>")
        return

    termino = argumento.lower().strip()
    termino = termino.replace("é", "e").replace("á", "a").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    resultados = []

    for ticker, info in UNIVERSO_ACTIVOS.items():
        nombre_completo = info["desc"].lower()
        etiquetas = info["tags"]
        
        if termino in ticker.lower() or termino in nombre_completo or termino in etiquetas:
            alias_corto = ticker.replace(".BA", "").replace("-USD", "").replace("=F", "")
            if alias_corto == "YPFD": alias_corto = "YPF"
            
            resultados.append(f"🏢 <b>{info['desc']}</b> ({ticker})\n• Analizar: /analizar {alias_corto}")

    if not resultados:
        enviar_a_telegram(chat_id, f"❌ No encontré ningún activo o sector relacionado con '<b>{argumento}</b>'.")
    else:
        separador = "\n──────────────────────\n"
        mensaje_final = f"✨ <b>RESULTADOS PARA: '{argumento}'</b>\n──────────────────────\n" + separador.join(resultados)
        enviar_a_telegram(chat_id, mensaje_final)
