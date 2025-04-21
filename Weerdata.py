import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import datetime # Nodig voor datetime.date

# Streamlit interface met sidebar
st.sidebar.title("Weerdata Opties")
# Gebruik datetime.date voor de standaardwaarden van date_input
default_start_date = datetime.date(2025, 4, 1)
default_end_date = datetime.date(2025, 4, 20)
start_date = st.sidebar.date_input("Startdatum", default_start_date)
end_date = st.sidebar.date_input("Einddatum", default_end_date)

st.title("Weerdata Hoofddorp")
st.write("Bekijk het weer in Hoofddorp over een geselecteerde periode.")

# Definieer API URL en vaste parameters
API_URL = "https://archive-api.open-meteo.com/v1/archive"
LATITUDE = 52.3021
LONGITUDE = 4.6886
TIMEZONE = "Europe/Amsterdam"
DAILY_PARAMS = "precipitation_sum,temperature_2m_min,temperature_2m_max"

# Functie om data op te halen
def fetch_weather_data(api_url, params):
    """Haalt weerdata op van de Open-Meteo API."""
    try:
        print(f"Aanroep naar: {api_url} met params: {params}") # Debug print
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Controleert op HTTP-fouten (bv. 404, 500)
        weather_data = response.json()
        return weather_data
    except requests.exceptions.RequestException as e:
        # Probeer meer details uit de API response te halen indien mogelijk
        error_message = f"Fout bij het ophalen van data: {e}"
        try:
            # Als de API een JSON error response geeft
            api_error = response.json()
            if 'reason' in api_error:
                error_message += f"\nAPI Foutmelding: {api_error['reason']}"
        except Exception:
            # Als er geen JSON response is of deze niet geparsed kan worden
             if 'response' in locals() and response is not None:
                 error_message += f" (Status code: {response.status_code})"

        st.error(error_message)
        return None
    except Exception as ex: # Vang andere mogelijke fouten
        st.error(f"Onverwachte fout: {ex}")
        return None

# Controleer of de startdatum niet na de einddatum ligt
if start_date > end_date:
    st.error("Startdatum mag niet na de einddatum liggen.")
else:
    # Converteer geselecteerde datums naar strings
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Stel de parameters voor de API-aanroep samen
    api_params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "daily": DAILY_PARAMS,
        "timezone": TIMEZONE
    }

    # Haal de data op
    data = fetch_weather_data(API_URL, api_params)

    # Verwerk en toon de data als deze succesvol is opgehaald
    if data and "daily" in data and data["daily"] and data["daily"]["time"]: # Extra check of 'daily' en 'time' data bevatten
        df = pd.DataFrame(data["daily"])
        df.rename(columns={
            "time": "Datum", # Hernoem 'time' naar 'Datum' voor duidelijkheid
            "precipitation_sum": "Neerslag (mm)",
            "temperature_2m_min": "Min Temp (°C)",
            "temperature_2m_max": "Max Temp (°C)"
        }, inplace=True)
        # Converteer 'Datum' kolom naar datetime objecten (alleen datum deel)
        df["Datum"] = pd.to_datetime(df["Datum"]).dt.date

        st.subheader("Tabel met weerdata")
        # Toon de tabel met de 'Datum' als index voor betere leesbaarheid
        st.dataframe(df.set_index('Datum'))

        st.subheader("Grafiek")
        fig, ax1 = plt.subplots(figsize=(10, 5))

        # Plot temperaturen
        ax1.set_xlabel("Datum")
        ax1.set_ylabel("Temperatuur (°C)", color="tab:red")
        ax1.plot(df["Datum"], df["Min Temp (°C)"], label="Min Temp (°C)", color="tab:blue", marker='o', linestyle='-')
        ax1.plot(df["Datum"], df["Max Temp (°C)"], label="Max Temp (°C)", color="tab:red", marker='o', linestyle='-')
        ax1.tick_params(axis='y', labelcolor="tab:red")
        ax1.tick_params(axis='x', rotation=45) # Roteer x-as labels voor betere leesbaarheid
        ax1.legend(loc="upper left")

        # Plot neerslag op tweede y-as
        ax2 = ax1.twinx()
        ax2.set_ylabel("Neerslag (mm)", color="tab:green")
        ax2.bar(df["Datum"], df["Neerslag (mm)"], alpha=0.5, color="tab:green", label="Neerslag (mm)")
        ax2.tick_params(axis='y', labelcolor="tab:green")
        # Zet de limiet van de neerslag-as zodat 0 onderaan begint
        ax2.set_ylim(bottom=0)
        # Voeg een aparte legende toe voor de neerslag als nodig, of combineer
        # ax2.legend(loc="upper right") # Optioneel, kan druk worden met ax1.legend

        fig.tight_layout()  # Zorgt dat alles netjes past
        st.pyplot(fig)

    elif data and "daily" in data and not data["daily"]["time"]:
         st.warning("Geen data beschikbaar voor de geselecteerde periode (API gaf lege 'daily' data terug).")
    elif not data:
        # Foutmelding is al getoond in fetch_weather_data
        st.info("Data kon niet worden opgehaald. Controleer de foutmelding hierboven.")
    else:
         st.warning("Onverwacht dataformaat ontvangen van de API.")