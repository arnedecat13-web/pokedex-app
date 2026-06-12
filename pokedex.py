import streamlit as st
import requests

st.set_page_config(page_title="Pokemon Ultimate", page_icon="⚡", layout="wide")

if "geschiedenis" not in st.session_state:
    st.session_state["geschiedenis"] = []

if "huidige_pokemon" not in st.session_state:
    st.session_state["huidige_pokemon"] = "pikachu"

if "regio_pokemon" not in st.session_state:
    st.session_state["regio_pokemon"] = None

@st.cache_data
def haal_regio_data(gen_id):
    try:
        url = f"https://pokeapi.co/api/v2/generation/{gen_id}/"
        res = requests.get(url).json()
        species = res.get("pokemon_species", [])
        
        # Veilig sorteren op het ID (zo voorkomen we crashes als de URL anders is)
        def get_id(url):
            try:
                return int(url.rstrip("/").split("/")[-1])
            except:
                return 9999
        species.sort(key=lambda x: get_id(x["url"]))
        return species
    except Exception:
        return []

@st.cache_data
def haal_zwaktes_op(types):
    zwaktes = set()
    for t in types:
        try:
            res = requests.get(f"https://pokeapi.co/api/v2/type/{t}").json()
            for zwakte in res.get("damage_relations", {}).get("double_damage_from", []):
                zwaktes.add(zwakte["name"])
        except:
            pass
    return list(zwaktes)

def toon_pokemon(naam):
    if not naam:
        return
    url = f"https://pokeapi.co/api/v2/pokemon/{naam}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            st.error(f"Pokémon '{naam}' niet gevonden.")
            return

        data = response.json()
        p_id = data.get("id", "?")
        pokemon_naam = data.get("name", "Onbekend").upper()
        
        # Artwork veilig ophalen (crasht niet als een foto mist)
        sprites = data.get("sprites", {})
        other_sprites = sprites.get("other", {})
        official_artwork = other_sprites.get("official-artwork", {})
        artwork = official_artwork.get("front_default", "")
        
        types = [t["type"]["name"] for t in data.get("types", [])]
        stats = {stat["stat"]["name"]: stat["base_stat"] for stat in data.get("stats", [])}

        hp = stats.get("hp", 0)
        attack = stats.get("attack", 0)
        defense = stats.get("defense", 0)
        special_attack = stats.get("special-attack", 0)
        special_defense = stats.get("special-defense", 0)
        speed = stats.get("speed", 0)

        hoogte_m = data.get('height', 0) / 10
        gewicht_kg = data.get('weight', 0) / 10
        zwaktes = haal_zwaktes_op(tuple(types))

        # Veilig checken op mega/gmax
        naam_str = str(naam)
        if "-mega" in naam_str:
            st.warning("🧬 MEGA EVOLUTIE")
        elif "-gmax" in naam_str:
            st.error("💥 GIGANTAMAX")
        else:
            st.success("✨ Normale Pokémon")

        c1, c2 = st.columns([1, 2])
        with c1:
            if artwork:
                st.image(artwork, width=300)
            else:
                st.write("Geen foto beschikbaar")
        with c2:
            st.header(f"#{p_id} {pokemon_naam}")
            st.write(f"**Type:** {', '.join(types).title()}")
            st.write(f"⚠️ **Zwaktes:** {', '.join(zwaktes).title() if zwaktes else 'Geen'}")
            st.write(f"📏 **Hoogte:** {hoogte_m} meter")
            st.write(f"⚖️ **Gewicht:** {gewicht_kg} kg")
            
            st.write("### Stats")
            
            # min(waarde, 1.0) voorkomt crashen als de stat onverwacht hoger dan 255 is
            st.write(f"❤️ HP: {hp}")
            st.progress(min(hp/255, 1.0))
            st.write(f"⚔️ Attack: {attack}")
            st.progress(min(attack/255, 1.0))
            st.write(f"🛡️ Defense: {defense}")
            st.progress(min(defense/255, 1.0))
    except Exception as e:
        st.error(f"Fout bij het laden van de Pokémon: {e}")

st.title("⚡ Pokémon Ultimate Pokédex")

tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Zoeken", 
    "🌍 Regio's (Normaal)", 
    "🧬 Mega Pokédex", 
    "💥 Gmax Pokédex"
])

# ==========================================
# SUPER VEILIGE CHECKS VOOR DE TABBLADEN
# ==========================================
gekozen_pkm = st.session_state.get("regio_pokemon")
is_mega = gekozen_pkm is not None and "-mega" in str(gekozen_pkm)
is_gmax = gekozen_pkm is not None and "-gmax" in str(gekozen_pkm)
is_normaal = gekozen_pkm is not None and not is_mega and not is_gmax

with tab1:
    col_zoek, col_geschiedenis = st.columns([2, 1])

    with col_zoek:
        st.write("### Zoek een Pokémon")
        huidige = st.session_state.get("huidige_pokemon", "pikachu")
        invoer = st.text_input("Naam of Nummer (bijv. charizard, 25, gengar-mega)", huidige).lower().strip()
        
        if st.button("Zoek Pokémon"):
            st.session_state["huidige_pokemon"] = invoer
            if invoer and invoer not in st.session_state["geschiedenis"]:
                st.session_state["geschiedenis"].insert(0, invoer)
        
        st.write("---")
        toon_pokemon(st.session_state.get("huidige_pokemon"))

    with col_geschiedenis:
        st.write("### 📜 Geschiedenis")
        if len(st.session_state["geschiedenis"]) == 0:
            st.info("Je hebt nog niks gezocht.")
        else:
            for z in st.session_state["geschiedenis"][:10]:
                if st.button(f"🔄 {str(z).capitalize()}", key=f"hist_{z}"):
                    st.session_state["huidige_pokemon"] = z
                    st.rerun()

with tab2:
    st.write("### Ontdek Normale Pokémon per Regio")
    regios = {
        "Kanto (Generatie 1)": 1, "Johto (Generatie 2)": 2, "Hoenn (Generatie 3)": 3,
        "Sinnoh (Generatie 4)": 4, "Unova (Generatie 5)": 5, "Kalos (Generatie 6)": 6,
        "Alola (Generatie 7)": 7, "Galar (Generatie 8)": 8, "Paldea (Generatie 9)": 9
    }
    
    gekozen_regio = st.selectbox("Kies een regio:", list(regios.keys()))
    gen_id = regios[gekozen_regio]
    
    if is_normaal:
        st.write(f"#### Info Geselecteerde Pokémon")
        toon_pokemon(gekozen_pkm)
        st.write("---")

    species = haal_regio_data(gen_id)
    if species:
        st.success(f"Er zijn {len(species)} Pokémon ontdekt in {gekozen_regio}! Ze staan netjes op nummer.")
        kolommen = st.columns(5)
        for i, s in enumerate(species):
            p_naam = s.get("name", "")
            try:
                p_id = s["url"].rstrip("/").split("/")[-1]
            except:
                p_id = "0"
            foto_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{p_id}.png"
            
            with kolommen[i % 5]:
                st.image(foto_url)
                if st.button(f"#{p_id} {p_naam.capitalize()}", key=f"btn_regio_{p_id}_{p_naam}"):
                    st.session_state["regio_pokemon"] = p_naam
                    st.rerun()
    else:
        st.warning("Kon de Pokémon voor deze regio niet laden. Probeer het later nog eens.")

with tab3:
    st.write("### 🧬 De Mega Evolutie Pokédex")
    st.write("Ontdek álle krachtige Mega Evoluties uit de geschiedenis!")
    
    mega_lijst = [
        "venusaur-mega", "charizard-mega-x", "charizard-mega-y", "blastoise-mega", 
        "beedrill-mega", "pidgeot-mega", "alakazam-mega", "slowbro-mega", "gengar-mega", 
        "kangaskhan-mega", "pinsir-mega", "gyarados-mega", "aerodactyl-mega", 
        "mewtwo-mega-x", "mewtwo-mega-y", "ampharos-mega", "steelix-mega", "scizor-mega", 
        "heracross-mega", "houndoom-mega", "tyranitar-mega", "sceptile-mega", "blaziken-mega", 
        "swampert-mega", "gardevoir-mega", "sableye-mega", "mawile-mega", "aggron-mega", 
        "medicham-mega", "manectric-mega", "sharpedo-mega", "camerupt-mega", "altaria-mega", 
        "banette-mega", "absol-mega", "glalie-mega", "salamence-mega", "metagross-mega", 
        "latias-mega", "latios-mega", "rayquaza-mega", "lopunny-mega", "garchomp-mega", 
        "lucario-mega", "abomasnow-mega", "gallade-mega", "audino-mega", "diancie-mega"
    ]
    
    if is_mega:
        st.write(f"#### Info Geselecteerde Mega")
        toon_pokemon(gekozen_pkm)
        st.write("---")

    mega_cols = st.columns(5)
    for i, mega_naam in enumerate(mega_lijst):
        with mega_cols[i % 5]:
            try:
                mega_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{mega_naam}").json()
                mega_id = mega_data.get("id", "?")
                mega_foto = mega_data.get("sprites", {}).get("front_default", "")
                if mega_foto:
                    st.image(mega_foto)
                if st.button(f"#{mega_id} {mega_naam.replace('-mega', ' Mega').title()}", key=f"btn_mega_{mega_naam}"):
                    st.session_state["regio_pokemon"] = mega_naam
                    st.rerun()
            except:
                pass

with tab4:
    st.write("### 💥 De Gigantamax Pokédex")
    st.write("Bekijk álle gigantische Gmax vormen!")
    
    gmax_lijst = [
        "venusaur-gmax", "charizard-gmax", "blastoise-gmax", "butterfree-gmax", 
        "pikachu-gmax", "meowth-gmax", "machamp-gmax", "gengar-gmax", 
        "kingler-gmax", "lapras-gmax", "eevee-gmax", "snorlax-gmax", 
        "garbodor-gmax", "melmetal-gmax", "rillaboom-gmax", "cinderace-gmax", 
        "inteleon-gmax", "corviknight-gmax", "orbeetle-gmax", "drednaw-gmax", 
        "coalossal-gmax", "flapple-gmax", "appletun-gmax", "sandaconda-gmax", 
        "toxtricity-gmax", "centiskorch-gmax", "hatterene-gmax", "grimmsnarl-gmax", 
        "alcremie-gmax", "copperajah-gmax", "duraludon-gmax"
    ]
    
    if is_gmax:
        st.write(f"#### Info Geselecteerde Gigantamax")
        toon_pokemon(gekozen_pkm)
        st.write("---")

    gmax_cols = st.columns(5)
    for i, gmax_naam in enumerate(gmax_lijst):
        with gmax_cols[i % 5]:
            try:
                gmax_data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{gmax_naam}").json()
                gmax_id = gmax_data.get("id", "?")
                gmax_foto = gmax_data.get("sprites", {}).get("front_default", "")
                if gmax_foto:
                    st.image(gmax_foto)
                if st.button(f"#{gmax_id} {gmax_naam.replace('-gmax', ' Gmax').title()}", key=f"btn_gmax_{gmax_naam}"):
                    st.session_state["regio_pokemon"] = gmax_naam
                    st.rerun()
            except:
                pass
