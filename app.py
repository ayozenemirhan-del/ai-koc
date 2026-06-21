# -*- coding: utf-8 -*-
"""
🐼 KİŞİSEL AI FİTNESS KOÇU & SPORCU TAKİP DASHBOARD'U
=====================================================
Tek dosyalık Streamlit uygulaması.

Teknoloji yığını:
  - Arayüz      : Streamlit  (Panda / siyah-beyaz minimalist tema)
  - AI Beyin    : Google Gemini 1.5 Pro  (metin + Vision/fotoğraf analizi)
  - Veritabanı  : Firebase Firestore  (kalıcı depolama)
  - Grafikler   : Plotly

Çalıştırma:
  streamlit run app.py

NOT: API anahtarları ve Firebase kimlik bilgileri .streamlit/secrets.toml
dosyasından okunur (en alttaki kurulum talimatlarına bakın).
"""

from datetime import datetime, date, timedelta
import json

import streamlit as st

# --- Opsiyonel/harici bağımlılıklar (yoksa uygulama yine de açılır) -----------
try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

try:
    from PIL import Image
    PIL_OK = True
except Exception:
    PIL_OK = False


# =============================================================================
# 1) AI KOÇ SİSTEM KOMUTU (SYSTEM PROMPT) — KODA GÖMÜLÜDÜR
# =============================================================================
COACH_SYSTEM_PROMPT = """
Sen kullanıcının definisyon (yağ yakım) sürecini yöneten, tavizsiz ve
gerçekçi bir profesyonel fitness koçusun. Bilimsel, net ve doğrudan konuşursun.

SPORCU PROFİLİ (kullanıcıyı buna göre değerlendir):
- Yaklaşık 2 yıllık düzenli vücut geliştirme tecrübesi olan, ORTA SEVİYE bir
  sporcu. Temel hareketleri ve mantığı biliyor; ona göre ileri seviye, ayrıntılı
  ve net konuş, basit/acemi açıklamalara boğma.
- Şu anda yağ oranı YÜKSEK. Hedef: kası mümkün olduğunca koruyarak, en optimum
  ve sürdürülebilir şekilde yağ oranını düşürmek (temiz definisyon).
- Önerilerini bu profile göre kişiselleştir (kalori açığı, protein hedefi, hacim,
  haftalık ilerleme bu bağlama göre).

TEMEL İLKE — KANITA DAYALI VE OPTİMUM:
Tüm öneri ve değerlendirmeler, doğruluğu reddedilemeyecek düzeyde yerleşmiş
(meta-analiz ve geniş bilimsel uzlaşıya dayanan) kabuller üzerine kurulur ve
sporcu için EN OPTİMUM sonucu hedefler. Dogmatik/keyfi yasaklar koyma; besin ve
hareket seçiminde belirleyici olan toplam kalori, makro dengesi, hacim ve
ilerlemedir. Tartışmalı, zayıf veya anekdotsal şeyleri "kesin" gibi sunma; emin
değilsen bunu açıkça söyle.

KURALLAR:
1) FOTOĞRAF ANALİZİ: Kullanıcı haftalık form/postür fotoğrafı yüklediğinde
   asimetri ve postür kontrolü yap. Gelişim durmuşsa program ve makro planını
   revize et.
2) SAĞLIK & SAKATLIK (ÖNCELİKLİ): Kullanıcının Sağlık sekmesinde girdiği aktif
   sakatlıkları MUTLAKA dikkate al. O bölgeyi zorlayan/ağrıtan hareketleri
   ÖNERME; güvenli alternatif ver. (Örn. ön çapraz bağ / diz sorunu varsa ağır
   bacak/eklem yükleyen hareketlerden kaçın, eklemi koruyan alternatifler sun.)
   Program ve beslenmeyi daima sakatlık durumuna göre uyarla.
3) KAN TAHLİLİ: Kan değerlerini yorumlarken bir DOKTOR DEĞİLSİN. Referans dışı
   (yüksek/düşük) değerleri açıkça işaretle ve "bunu mutlaka bir hekime danışın"
   uyarısı ver. Tanı KOYMA, ilaç önerme. Beslenme/antrenmanı bu değerleri
   gözeterek genel çerçevede uyarlarsın. Kritik değerlerde derhal hekime yönlendir.
4) BİLİMSEL DAYANAK: Önerilerin güçlü kanıta dayansın — meta-analizler ve geniş,
   tekrarlanmış çalışmaların ortak görüşüne uy. 3-5 kişilik, zayıf veya tek
   seferlik çalışmalara ya da "bro-science"a güvenme. Bir konuda kanıt zayıf veya
   tartışmalıysa bunu açıkça söyle. KAYNAK UYDURMA: var olmayan makale, yazar,
   dergi veya sayı UYDURMA; emin değilsen "bu kesin kanıtlı değil" de.
5) TEMBEL/KLİŞE ÖNERİ YASAK: Kolaya kaçıp her şeye "yulaf ve whey protein" gibi
   klişe cevap verme. Besin ve makro seçimini sporcunun hedefine, tercihlerine ve
   kanıta göre kişiselleştir.
6) EKSİK VERİ: Bir alan (adım, kalori, uyku vb.) boş/girilmemişse bunu "sıfır"
   ya da "kullanıcı yapmadı/başarısız" gibi YORUMLAMA. Sadece "bu veri henüz
   girilmemiş" de ve o alan üzerinden suçlayıcı çıkarım yapma.
7) Tüm cevapların TÜRKÇE olmalı. Gereksiz övgüden kaçın; kullanıcıyı hedefe
   odaklı tut. Sağlık açısından kritik bir uyarı görürsen (örn. aşırı düşük
   kalori, sakatlık belirtisi) bunu açıkça belirt.
""".strip()


# =============================================================================
# 2) GENEL AYARLAR & PANDA TEMASI
# =============================================================================
st.set_page_config(
    page_title="🐼 AI Fitness Koçu",
    page_icon="🐼",
    layout="wide",
    initial_sidebar_state="expanded",
)

PANDA_CSS = """
<style>
    /* --- Panda paleti: kağıt beyazı zemin, mürekkep siyahı metin --- */
    :root {
        --ink:    #111111;
        --paper:  #FFFFFF;
        --smoke:  #F4F4F4;
        --line:   #E6E6E6;
        --muted:  #8A8A8A;
    }

    .stApp { background-color: var(--paper); color: var(--ink); }

    /* Tipografi */
    html, body, [class*="css"] {
        font-family: "Inter", "Helvetica Neue", Arial, sans-serif;
    }
    h1, h2, h3, h4 { color: var(--ink); font-weight: 700; letter-spacing: -0.01em; }

    /* Kenar çubuğu */
    section[data-testid="stSidebar"] {
        background-color: var(--ink);
        border-right: 1px solid var(--ink);
    }
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
    /* Kenar çubuğundaki yazı kutularında metin görünür olsun (beyaz değil) */
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] input {
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        background-color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] textarea::placeholder,
    section[data-testid="stSidebar"] input::placeholder {
        color: #8A8A8A !important;
        -webkit-text-fill-color: #8A8A8A !important;
    }

    /* Sekmeler */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--line); }
    .stTabs [data-baseweb="tab"] {
        background: transparent; border-radius: 0;
        color: var(--muted); font-weight: 600; padding: 10px 18px;
    }
    .stTabs [aria-selected="true"] {
        color: var(--ink) !important;
        border-bottom: 2px solid var(--ink) !important;
    }

    /* Butonlar — siyah dolgu, beyaz yazı */
    .stButton > button {
        background-color: var(--ink); color: #FFFFFF;
        border: 1px solid var(--ink); border-radius: 8px;
        font-weight: 600; padding: 0.55rem 1.1rem; transition: all .15s ease;
    }
    .stButton > button:hover {
        background-color: #FFFFFF; color: var(--ink); border-color: var(--ink);
    }

    /* Kartlar / metrikler */
    div[data-testid="stMetric"] {
        background: var(--smoke); border: 1px solid var(--line);
        border-radius: 12px; padding: 16px 18px;
    }

    /* Girdi alanları */
    .stTextInput input, .stNumberInput input, .stTextArea textarea,
    .stDateInput input, .stTimeInput input {
        border-radius: 8px !important; border: 1px solid var(--line) !important;
    }

    /* Streamlit menü/footer gizle (daha temiz görünüm) */
    #MainMenu, footer { visibility: hidden; }

    .panda-card {
        background: var(--smoke); border: 1px solid var(--line);
        border-radius: 14px; padding: 18px 20px; margin-bottom: 10px;
    }
    .panda-muted { color: var(--muted); font-size: 0.85rem; }
</style>
"""
st.markdown(PANDA_CSS, unsafe_allow_html=True)


# =============================================================================
# 2.5) GİRİŞ ŞİFRESİ + "BENİ HATIRLA" (30 gün)
# =============================================================================
import hashlib

try:
    import extra_streamlit_components as stx
    _cookie_mgr = stx.CookieManager(key="ai_koc_cookies")
except Exception:
    _cookie_mgr = None

REMEMBER_COOKIE = "ai_koc_remember"
REMEMBER_GUN = 30


def _remember_token() -> str:
    secret = st.secrets.get("APP_PASSWORD", "")
    return hashlib.sha256(("ai_koc_remember::" + secret).encode()).hexdigest()


def check_password() -> bool:
    """Şifre ekranı + 'beni bu cihazda hatırla' (çerezle 30 gün)."""
    expected = st.secrets.get("APP_PASSWORD", "")
    if not expected:
        return True  # şifre tanımlı değil -> serbest (örn. kendi bilgisayarınızda)
    if st.session_state.get("auth_ok"):
        return True

    # Çerezde geçerli hatırlama varsa otomatik giriş
    if _cookie_mgr is not None:
        try:
            _cookies = _cookie_mgr.get_all()
            if _cookies and _cookies.get(REMEMBER_COOKIE) == _remember_token():
                st.session_state["auth_ok"] = True
                return True
        except Exception:
            pass

    st.markdown("## 🐼 Giriş")
    st.caption("Bu alan kişiseldir. Devam etmek için şifrenizi girin.")
    pwd = st.text_input("Şifre", type="password", label_visibility="collapsed",
                        placeholder="Şifre")
    hatirla = st.checkbox("Beni bu cihazda hatırla (30 gün)", value=True)
    if st.button("Giriş yap", type="primary"):
        if pwd == expected:
            st.session_state["auth_ok"] = True
            if hatirla and _cookie_mgr is not None:
                try:
                    # set() kendi rerun'unu tetikler; manuel rerun ile çerezi bozmayalım
                    _cookie_mgr.set(
                        REMEMBER_COOKIE, _remember_token(),
                        expires_at=datetime.now() + timedelta(days=REMEMBER_GUN),
                        key="set_remember",
                    )
                except Exception:
                    st.rerun()
            else:
                st.rerun()
        else:
            st.error("Şifre yanlış.")
    return False


if not check_password():
    st.stop()


# =============================================================================
# 3) GEMINI ENTEGRASYONU
# =============================================================================
@st.cache_resource(show_spinner=False)
def init_gemini():
    """Gemini istemcisini başlatır. Anahtar yoksa None döner."""
    try:
        import google.generativeai as genai
    except Exception:
        return None, "google-generativeai paketi kurulu değil."

    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return None, "GEMINI_API_KEY bulunamadı (secrets.toml)."

    try:
        genai.configure(api_key=api_key)

        # Hesapta GERÇEKTEN kullanılabilir bir model seç (model adları zamanla değişir).
        secili = st.secrets.get("GEMINI_MODEL", "")  # isterseniz secrets'ten sabitleyebilirsiniz
        if not secili:
            tercih = [
                "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro",
                "gemini-flash-latest", "gemini-pro-latest", "gemini-1.5-flash",
            ]
            mevcut = []
            try:
                for m in genai.list_models():
                    if "generateContent" in getattr(m, "supported_generation_methods", []):
                        mevcut.append(m.name.replace("models/", ""))
            except Exception:
                mevcut = []
            # Önce tercih listesinden uygun olanı, yoksa mevcutlardan ilkini seç
            secili = next((t for t in tercih if t in mevcut),
                          (mevcut[0] if mevcut else "gemini-2.0-flash"))

        model = genai.GenerativeModel(
            model_name=secili,
            system_instruction=COACH_SYSTEM_PROMPT,
        )
        return model, None
    except Exception as e:
        return None, f"Gemini başlatılamadı: {e}"


def ask_coach(model, user_prompt: str) -> str:
    """Koça metin tabanlı soru sorar (sistem komutu otomatik uygulanır)."""
    if model is None:
        return "⚠️ Gemini yapılandırılmamış. Lütfen API anahtarını ekleyin."
    try:
        resp = model.generate_content(user_prompt)
        return resp.text
    except Exception as e:
        return f"⚠️ Gemini hatası: {e}"


def analyze_form_photo(model, images, measurements: dict, history_note: str = "") -> str:
    """Gemini Vision ile bir veya birden fazla form/postür fotoğrafını analiz eder."""
    if model is None:
        return "⚠️ Gemini yapılandırılmamış. Fotoğraf analizi yapılamadı."
    if not isinstance(images, (list, tuple)):
        images = [images]
    prompt = f"""
Aşağıda kullanıcının haftalık form/postür fotoğraf(lar)ı var (farklı açılar olabilir).
Güncel vücut ölçüleri (cm): {json.dumps(measurements, ensure_ascii=False)}
{history_note}

Sistem komutundaki kurallara göre:
1) Postür ve omuz/kalça hizasını değerlendir.
2) Sol-sağ ASİMETRİ var mı kontrol et (omuz, kol, göğüs).
3) Definisyon/yağ oranı hakkında gerçekçi bir gözlem yap.
4) Gelişim durmuş gibi görünüyorsa üst vücut programı ve katı makro planı için
   somut revizyon öner (kurallar dışına çıkmadan).
Tüm fotoğrafları birlikte değerlendir. Kısa, maddeli ve doğrudan yaz.
""".strip()
    try:
        resp = model.generate_content([prompt] + list(images))
        return resp.text
    except Exception as e:
        return f"⚠️ Gemini Vision hatası: {e}"


def _img_to_b64(img, max_px=800, quality=70) -> str:
    """Görseli küçültüp JPEG base64 metnine çevirir (Firestore'a sığsın diye)."""
    import io
    import base64
    img = img.convert("RGB")
    img.thumbnail((max_px, max_px))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode()


def _b64_to_img(b64: str):
    import io
    import base64
    return Image.open(io.BytesIO(base64.b64decode(b64)))



def estimate_calories(model, meals: list) -> str:
    """Öğün içeriklerinden yaklaşık kalori/makro tahmini ister."""
    if model is None:
        return "⚠️ Gemini yapılandırılmamış."
    meal_text = "\n".join(f"- {m.get('saat','')}: {m.get('icerik','')}" for m in meals)
    prompt = (
        "Aşağıdaki öğünlerin TOPLAM yaklaşık kalorisini ve makro dağılımını "
        "(protein/karbonhidrat/yağ, gram) tahmin et. Sadece kısa bir özet ver, "
        f"sonuna toplam kaloriyi 'TOPLAM_KCAL: <sayı>' formatında yaz.\n\n{meal_text}"
    )
    return ask_coach(model, prompt)


def estimate_calories_image(model, images: list, note: str = "") -> str:
    """Yemek fotoğraf(lar)ından yaklaşık kalori/makro tahmini yapar."""
    if model is None:
        return "⚠️ Gemini yapılandırılmamış."
    ek = f"\nKullanıcı notu (porsiyon/gram): {note}" if note.strip() else ""
    prompt = (
        "Bu fotoğraf(lar)daki yemeğin yaklaşık kalorisini ve makrolarını "
        "(protein/karbonhidrat/yağ, gram) tahmin et. Porsiyonu görselden tahmin et; "
        "kesin olmadığını belirt. Kısa yaz ve sonuna 'TOPLAM_KCAL: <sayı>' ekle." + ek
    )
    try:
        resp = model.generate_content([prompt] + list(images))
        return resp.text
    except Exception as e:
        return f"⚠️ Gemini Vision hatası: {e}"


def compute_macros_from_content(model, meals: list):
    """Öğün içeriğindeki gramlardan protein/karb/kalori hesaplatır (JSON döner)."""
    if model is None:
        return None, "Gemini yapılandırılmamış."
    veri = [{"ogun": m.get("ogun", ""), "icerik": m.get("icerik", "")} for m in meals]
    prompt = (
        "Aşağıda öğünler var (ogun + icerik). Her öğünün içeriğindeki gram bilgilerinden "
        "yola çıkarak protein (g), karbonhidrat (g), YAĞ (g) ve kalori (kcal) hesapla. "
        "Yağ kaynaklarını (badem ezmesi, zeytinyağı, yumurta sarısı vb.) sakın atlama. "
        "SADECE geçerli bir JSON listesi döndür (başka metin/``` olmadan), şu alanlarla: "
        '[{"ogun":"...","icerik":"...","protein_g":0,"karb_g":0,"yag_g":0,"kcal":0}]. '
        "Kalori = protein*4 + karbonhidrat*4 + yağ*9. Sayılar tam sayı olsun. "
        "Gram belirtilmemişse makul tahmin yap.\n\n"
        + json.dumps(veri, ensure_ascii=False)
    )
    ham = ask_coach(model, prompt)
    temiz = (ham or "").replace("```json", "").replace("```", "").strip()
    bas, son = temiz.find("["), temiz.rfind("]")
    if bas != -1 and son != -1 and son > bas:
        temiz = temiz[bas:son + 1]
    try:
        out = json.loads(temiz)
        if isinstance(out, list) and out:
            return out, None
        return None, "Beklenen formatta veri çıkmadı."
    except Exception:
        return None, f"Hesaplanamadı. Koç cevabı: «{(ham or '').strip()[:200]}»"


def _say(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def _parse_saat(s, varsayilan="08:00"):
    """'HH:MM' metnini time'a çevirir; olmazsa varsayılanı verir."""
    try:
        return datetime.strptime(str(s), "%H:%M").time()
    except Exception:
        return datetime.strptime(varsayilan, "%H:%M").time()


import re as _re
GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def _gun_adi(d):
    return GUN_ADLARI[d.weekday()]


def _set_sayisi(satir):
    """Egzersiz satırındaki '4x10' gibi ifadeden set sayısını çıkarır."""
    m = _re.search(r"(\d+)\s*[xX×]\s*\d+", satir or "")
    if m:
        return min(max(int(m.group(1)), 1), 10)
    return 3


def _gun_programi(plan, gun_adi):
    """Plan içinden belirli güne ait satırı bulur."""
    for r in plan.get("program", []):
        if str(r.get("gun", "")).strip().lower() == gun_adi.lower():
            return r
    return None


def _egzersiz_satirlari(egz):
    return [e.strip() for e in str(egz or "").replace(",", "\n").split("\n") if e.strip()]


def _dinlenme_gunu_mu(gun_prog):
    """Günün programı dinlenme/recovery ise True döner."""
    if not gun_prog:
        return False
    metin = (str(gun_prog.get("odak", "")) + " " + str(gun_prog.get("egzersizler", ""))).lower()
    anahtarlar = ["dinlenme", "dinlen", "recovery", "rest", "off", "toparlan", "izin"]
    # Gerçek bir set ifadesi (örn. 4x10) varsa dinlenme sayma
    if _re.search(r"\d+\s*[xX×]\s*\d+", metin):
        return False
    return any(k in metin for k in anahtarlar)
    """Kan tahlili fotoğrafını/ekran görüntüsünü Gemini Vision ile okur ve özetler."""
    if model is None:
        return "⚠️ Gemini yapılandırılmamış."
    prompt = (
        "Bu bir kan tahlili belgesi/fotoğrafı. Parametreleri ve değerlerini "
        "tablo halinde (parametre, değer, birim, referans aralığı) çıkar. "
        "Referans dışı olanları işaretle. UNUTMA: doktor değilsin, tanı koyma; "
        "anormal değerler için 'bir hekime danışın' uyarısı ekle."
    )
    try:
        resp = model.generate_content([prompt, image])
        return resp.text
    except Exception as e:
        return f"⚠️ Gemini Vision hatası: {e}"


def excel_to_plan(model, sayfalar_metni: str):
    """Excel'deki tüm sayfaları okuyup hem program hem beslenmeyi JSON olarak döndürür."""
    if model is None:
        return None, "Gemini yapılandırılmamış."
    prompt = (
        "Aşağıda bir Excel dosyasının TÜM sayfaları (sayfa adlarıyla) ham olarak var. "
        "İçinde antrenman programı ve/veya beslenme planı olabilir. Hangi sayfanın ne "
        "olduğunu kendin anla. SADECE şu formatta geçerli bir JSON nesnesi döndür "
        "(başka metin veya ``` olmadan):\n"
        '{\n'
        '  "program": [{"gun":"Pazartesi","odak":"Göğüs","egzersizler":"1. Bench 4x10\\n2. Incline Fly 3x12"}],\n'
        '  "beslenme": [{"ogun":"1. Öğün","icerik":"...","protein_g":0,"karb_g":0,"yag_g":0,"kcal":0}]\n'
        '}\n'
        "Kurallar: sporcunun mevcut programını olduğu gibi düzenle, içeriği değiştirme; sadece düzenli tabloya dök. "
        "'egzersizler' alanında her egzersizi AYRI SATIRA yaz (aralarına \\n koy), virgülle yan yana DİZME. "
        "Beslenmede sayısal alanları (protein_g, karb_g, kcal) bilemiyorsan 0 yaz. "
        "Bir bölüm dosyada yoksa onu boş liste [] bırak.\n\n"
        f"HAM VERİ:\n{sayfalar_metni}"
    )
    ham = ask_coach(model, prompt)
    if not ham or not ham.strip():
        return None, "Koç boş cevap döndürdü. (Excel okunamadı veya Gemini yanıt vermedi.)"
    temiz = ham.replace("```json", "").replace("```", "").strip()
    # Cevabın içinden JSON nesnesini ayıkla (başta/sonda fazladan metin olabilir)
    bas, son = temiz.find("{"), temiz.rfind("}")
    if bas != -1 and son != -1 and son > bas:
        temiz = temiz[bas:son + 1]
    try:
        veri = json.loads(temiz)
        if isinstance(veri, dict):
            return veri, None
        return None, "Beklenen formatta veri çıkmadı."
    except Exception:
        # Teşhis için koçun döndürdüğü ham cevabın bir kısmını göster
        ozet = ham.strip().replace("\n", " ")[:300]
        return None, f"JSON'a çevrilemedi. Koçun cevabı şöyle başlıyor: «{ozet}»"


def evaluate_with_coach(model, history: list, context: dict, user_msg: str) -> str:
    """Kayıtlı program + beslenme + son verileri bağlam olarak verip koçla sohbet eder."""
    if model is None:
        return "⚠️ Gemini yapılandırılmamış."
    ctx = json.dumps(context, ensure_ascii=False, indent=2)
    gecmis = "\n".join(f"{h['role'].upper()}: {h['content']}" for h in history[-6:])
    prompt = f"""
Aşağıda kullanıcının GÜNCEL kayıtlı verileri var (program, beslenme planı ve
son 1 haftalık günlük loglar). Bunları kurallarına göre değerlendir.

KAYITLI VERİLER:
{ctx}

ÖNCEKİ KONUŞMA:
{gecmis}

KULLANICININ YENİ MESAJI: {user_msg}

Kanıta dayalı, sporcunun profiline ve sakatlıklarına uygun, net ve maddeli
cevap ver.
""".strip()
    return ask_coach(model, prompt)


def revise_plan_with_coach(model, context: dict):
    """Mevcut plan + verileri değerlendirip GÜNCELLENMİŞ planı JSON olarak döndürür."""
    if model is None:
        return None, "Gemini yapılandırılmamış."
    ctx = json.dumps(context, ensure_ascii=False, indent=2)
    prompt = (
        "Aşağıda kullanıcının güncel program, beslenme planı (antrenman/dinlenme günü), "
        "son loglar ve sağlık verileri var. Bunları kurallarına göre değerlendir ve "
        "GEREKLİ GÜNCELLEMELERİ yaparak YENİ planı üret.\n\n"
        "Kurallar: güçlü bilimsel kanıta dayan, sporcunun profiline (2 yıl tecrübe, "
        "yağ oranı yüksek, optimum definisyon) ve Sağlık sekmesindeki sakatlıklara uy; "
        "uydurma kaynak verme.\n\n"
        "SADECE şu formatta geçerli bir JSON nesnesi döndür (başka metin/``` olmadan):\n"
        '{\n'
        '  "aciklama": "Neyi neden değiştirdiğinin kısa özeti",\n'
        '  "program": [{"gun":"Pazartesi","odak":"Göğüs","egzersizler":"1. ...\\n2. ..."}],\n'
        '  "beslenme_on": [{"ogun":"1. Öğün","icerik":"...","protein_g":0,"karb_g":0,"yag_g":0,"kcal":0}],\n'
        '  "beslenme_off": [{"ogun":"1. Öğün","icerik":"...","protein_g":0,"karb_g":0,"yag_g":0,"kcal":0}]\n'
        '}\n'
        "Egzersizleri her satır ayrı (\\n ile). Kalori = protein*4 + karb*4 + yağ*9.\n\n"
        f"GÜNCEL VERİLER:\n{ctx}"
    )
    ham = ask_coach(model, prompt)
    temiz = (ham or "").replace("```json", "").replace("```", "").strip()
    bas, son = temiz.find("{"), temiz.rfind("}")
    if bas != -1 and son != -1 and son > bas:
        temiz = temiz[bas:son + 1]
    try:
        out = json.loads(temiz)
        if isinstance(out, dict):
            return out, None
        return None, "Beklenen formatta veri çıkmadı."
    except Exception:
        return None, f"Çözümlenemedi. Koç cevabı: «{(ham or '').strip()[:200]}»"
@st.cache_resource(show_spinner=False)
def init_firestore():
    """Firestore istemcisini başlatır.
    İki yoldan birini kabul eder:
      1) Klasördeki 'firebase_key.json' dosyası (en kolay), veya
      2) secrets.toml içindeki [firebase] bloğu.
    """
    import os
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except Exception:
        return None, "firebase-admin paketi kurulu değil."

    cred = None
    # app.py ile aynı klasörü baz al (terminal nerede olursa olsun çalışsın)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "firebase_key.json")

    # 1) Klasördeki JSON dosyası (yerel bilgisayarda)
    if os.path.exists(key_path):
        try:
            cred = credentials.Certificate(key_path)
        except Exception as e:
            return None, f"firebase_key.json okunamadı: {e}"
    # 2) Tek parça JSON metni olarak secret (Streamlit Cloud için en kolay)
    elif "firebase_json" in st.secrets:
        try:
            cred = credentials.Certificate(json.loads(st.secrets["firebase_json"]))
        except Exception as e:
            return None, f"firebase_json secret'i hatalı: {e}"
    # 3) secrets.toml [firebase] bloğu
    elif "firebase" in st.secrets:
        try:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
        except Exception as e:
            return None, f"secrets.toml [firebase] hatalı: {e}"
    else:
        return None, f"Firebase anahtarı bulunamadı. Aranan yol: {key_path}"

    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        return firestore.client(), None
    except Exception as e:
        return None, f"Firestore başlatılamadı: {e}"


def save_doc(db, collection: str, doc_id: str, data: dict) -> tuple[bool, str]:
    if db is None:
        return False, "Firestore bağlı değil — veri kaydedilemedi."
    try:
        data["_updated_at"] = datetime.utcnow().isoformat()
        db.collection(collection).document(doc_id).set(data, merge=True)
        return True, "Kaydedildi."
    except Exception as e:
        return False, f"Kayıt hatası: {e}"


def load_recent(db, collection: str, days: int = 30) -> list:
    """Son N günün kayıtlarını tarihe göre artan sırada döndürür."""
    if db is None:
        return []
    try:
        cutoff = (date.today() - timedelta(days=days)).isoformat()
        docs = db.collection(collection).stream()
        rows = []
        for d in docs:
            r = d.to_dict() or {}
            r["_id"] = d.id
            if r.get("tarih", r["_id"]) >= cutoff:
                rows.append(r)
        rows.sort(key=lambda x: x.get("tarih", x.get("_id", "")))
        return rows
    except Exception as e:
        st.warning(f"Veri okunamadı: {e}")
        return []


def load_doc(db, collection: str, doc_id: str) -> dict:
    """Tek bir dokümanı okur (örn. kayıtlı program/plan)."""
    if db is None:
        return {}
    try:
        d = db.collection(collection).document(doc_id).get()
        return (d.to_dict() or {}) if d.exists else {}
    except Exception:
        return {}


# =============================================================================
# 5) BAŞLATMA & KENAR ÇUBUĞU (DURUM)
# =============================================================================
model, gem_err = init_gemini()
db, db_err = init_firestore()

with st.sidebar:
    st.markdown("## 🐼 Emirhan Ayözen")
    st.caption("Profesyonel koçluk")
    if st.secrets.get("APP_PASSWORD", ""):
        if st.button("Çıkış yap", use_container_width=True):
            if _cookie_mgr is not None:
                try:
                    _cookie_mgr.delete(REMEMBER_COOKIE, key="del_remember")
                except Exception:
                    pass
            st.session_state.pop("auth_ok", None)
            st.rerun()
    st.divider()

    st.markdown("**Bağlantı Durumu**")
    st.write("Gemini:  " + ("🟢 Aktif" if model else "🔴 Kapalı"))
    st.write("Firestore:  " + ("🟢 Aktif" if db else "🔴 Kapalı"))
    if gem_err:
        st.caption(f"ℹ️ {gem_err}")
    if db_err:
        st.caption(f"ℹ️ {db_err}")

    st.divider()
    st.markdown("**Hızlı Soru — Koça Danış**")
    quick_q = st.text_area("Koça bir şey sor", placeholder="Örn: Bu hafta press günü programı?", label_visibility="collapsed")
    if st.button("Sor", use_container_width=True):
        if quick_q.strip():
            with st.spinner("Koç düşünüyor..."):
                st.session_state["quick_answer"] = ask_coach(model, quick_q)
    if st.session_state.get("quick_answer"):
        st.markdown(st.session_state["quick_answer"])


# =============================================================================
# 6) BAŞLIK & SEKMELER
# =============================================================================
st.title("Sporcu Verileri")
st.markdown('<p class="panda-muted">Allah sabredenlerle beraberdir.</p>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Günlük Veri Girişi",
    "📸 Haftalık Check-in",
    "📈 Gelişim Grafikleri",
    "🗂️ Program & Değerlendirme",
    "🩺 Sağlık",
    "🏃 Kardiyo",
])


# -----------------------------------------------------------------------------
# SEKME 1 — GÜNLÜK VERİ GİRİŞİ
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Günlük Kayıt")
    col_a, col_b = st.columns([1, 1])
    gun = col_a.date_input("Tarih", value=date.today(), key="gunluk_tarih")
    gun_str = gun.isoformat()
    gun_adi = _gun_adi(gun)
    col_a.caption(f"📅 {gun_adi}")

    g_kayit = load_doc(db, "gunluk_loglar", gun_str)
    if g_kayit:
        col_b.caption("✅ Bu tarihe ait kayıt yüklendi.")

    _kilo_k = g_kayit.get("kilo", None)
    kilo = col_b.number_input("Sabah kilosu (kg) — boş bırakabilirsiniz", min_value=0.0, max_value=250.0, step=0.1,
                              value=(float(_kilo_k) if _kilo_k not in (None, "", 0) else None),
                              placeholder="Girmezseniz boş kalır", key=f"kilo_{gun_str}")

    plan = load_doc(db, "program_plan", "guncel")

    # ---- Bugünün antrenmanı (set set tekrar/kg) ----------------------------
    gun_prog = _gun_programi(plan, gun_adi)
    dinlenme_gunu = _dinlenme_gunu_mu(gun_prog)
    st.markdown(f"#### 🏋️ Bugünün Antrenmanı — {gun_adi}")
    antrenman_kayit = []
    if dinlenme_gunu:
        st.markdown(
            '<div class="panda-card" style="text-align:center;padding:34px 18px;">'
            '<div style="font-size:2rem;">😴</div>'
            '<div style="font-size:1.4rem;font-weight:700;margin-top:6px;">Bugün dinlenme günü</div>'
            '<div class="panda-muted" style="margin-top:4px;">Antrenman yok — toparlanma ve uyku öncelikli.</div>'
            '</div>', unsafe_allow_html=True)
    elif gun_prog and _egzersiz_satirlari(gun_prog.get("egzersizler")):
        st.caption(f"Odak: {gun_prog.get('odak','')}  ·  Her set için tekrar ve kilo girin.")
        kayitli_ant = g_kayit.get("antrenman_kayit")
        if kayitli_ant:
            ant_rows = kayitli_ant
        else:
            ant_rows = []
            for satir in _egzersiz_satirlari(gun_prog.get("egzersizler")):
                for i in range(1, _set_sayisi(satir) + 1):
                    ant_rows.append({"egzersiz": satir, "set": i, "tekrar": None, "kg": None})
        antrenman_kayit = st.data_editor(
            ant_rows,
            num_rows="dynamic",
            use_container_width=True,
            column_order=("egzersiz", "set", "tekrar", "kg"),
            column_config={
                "egzersiz": st.column_config.TextColumn("Egzersiz", width="large"),
                "set": st.column_config.NumberColumn("Set", width="small"),
                "tekrar": st.column_config.NumberColumn("Tekrar", width="small"),
                "kg": st.column_config.NumberColumn("Kg", width="small"),
            },
            key=f"ant_kayit_{gun_str}",
        )
    else:
        st.info(f"{gun_adi} için programda hareket yok (dinlenme olabilir) veya program henüz girilmedi. "
                "Program & Değerlendirme sekmesinden girebilirsiniz.")

    # ---- Bugün kardiyo yaptım mı? -----------------------------------------
    st.markdown("#### 🏃 Kardiyo")
    onceki_kardiyo = g_kayit.get("kardiyo", [])
    kardiyo_yapildi = st.checkbox("Bugün kardiyo yaptım", value=bool(onceki_kardiyo),
                                  key=f"kardiyo_yap_{gun_str}")
    kardiyo_gunluk = []
    if kardiyo_yapildi:
        st.caption("Her satıra bir kardiyo: tür, süre (dk) ve ortalama nabız.")
        kardiyo_kaynak = onceki_kardiyo or [{"tur": "Tempolu yürüyüş", "sure_dk": 30, "ort_nabiz": 120}]
        kardiyo_gunluk = st.data_editor(
            kardiyo_kaynak,
            num_rows="dynamic",
            use_container_width=True,
            column_order=("tur", "sure_dk", "ort_nabiz"),
            column_config={
                "tur": st.column_config.SelectboxColumn(
                    "Tür",
                    options=["Tempolu yürüyüş", "Koşu", "Bisiklet", "Eliptik",
                             "Kürek", "Yüzme", "Merdiven", "HIIT", "Diğer"],
                    width="medium"),
                "sure_dk": st.column_config.NumberColumn("Süre (dk)", min_value=0, max_value=600, width="small"),
                "ort_nabiz": st.column_config.NumberColumn("Ort. Nabız (bpm)", min_value=0, max_value=230, width="small"),
            },
            key=f"kardiyo_gunluk_{gun_str}",
        )

    # ---- Bugünün beslenmesi (gün tipine göre On/Off) — öğün öğün uyum -----
    if dinlenme_gunu:
        st.markdown("#### 🍽️ Bugünün Beslenmesi (Dinlenme Günü planı)")
        on_meals = plan.get("beslenme_off", []) or plan.get("beslenme_on", []) or plan.get("beslenme", [])
    else:
        st.markdown("#### 🍽️ Bugünün Beslenmesi (Antrenman Günü planı)")
        on_meals = plan.get("beslenme_on", []) or plan.get("beslenme", [])
    onceki_uyum = {u.get("ogun"): u for u in g_kayit.get("beslenme_uyum", [])}
    beslenme_uyum = []
    if not on_meals:
        st.caption("Program & Değerlendirme sekmesinde Antrenman Günü beslenmesi girilmemiş.")
    for i, m in enumerate(on_meals):
        ogun = m.get("ogun", f"{i+1}. Öğün")
        plan_icerik = m.get("icerik", "")
        onc = onceki_uyum.get(ogun, {})
        st.markdown(f"**{ogun}** — {plan_icerik or '(içerik yok)'}")
        cc1, cc2 = st.columns([1, 3])
        uydum = cc1.checkbox("Uydum ✓", value=bool(onc.get("uydum", False)), key=f"uydum_{gun_str}_{i}")
        yerine_not = ""
        tahmin = onc.get("tahmin_kcal", "")
        if not uydum:
            yerine_not = cc2.text_input("Yerine ne yedim? (yazı)", value=onc.get("yerine", ""),
                                        key=f"yernot_{gun_str}_{i}")
            yerine_foto = cc2.file_uploader("veya fotoğraf", type=["jpg", "jpeg", "png"],
                                            key=f"yerfoto_{gun_str}_{i}")
            if cc2.button("🍽️ Kaloriyi tahmin et", key=f"yerbtn_{gun_str}_{i}"):
                with st.spinner("Tahmin ediliyor..."):
                    if yerine_foto and PIL_OK:
                        st.session_state[f"yerkcal_{gun_str}_{i}"] = estimate_calories_image(
                            model, [Image.open(yerine_foto)], yerine_not)
                    elif yerine_not.strip():
                        st.session_state[f"yerkcal_{gun_str}_{i}"] = estimate_calories(
                            model, [{"saat": "", "icerik": yerine_not}])
                    else:
                        st.warning("Fotoğraf veya yazı ekleyin.")
            if st.session_state.get(f"yerkcal_{gun_str}_{i}"):
                tahmin = st.session_state[f"yerkcal_{gun_str}_{i}"]
                st.info(tahmin)
        beslenme_uyum.append({
            "ogun": ogun, "plan": plan_icerik, "uydum": bool(uydum),
            "yerine": yerine_not, "tahmin_kcal": tahmin,
        })
        st.markdown("")

    # ---- Uyku & Aktivite (adım boş başlar) --------------------------------
    st.markdown("#### 😴 Uyku & Aktivite")
    s1, s2, s3 = st.columns(3)
    uyku = s1.time_input("Uyku saati", value=_parse_saat(g_kayit.get("uyku_saati"), "23:30"),
                         key=f"uyku_{gun_str}")
    uyanma = s2.time_input("Uyanma saati", value=_parse_saat(g_kayit.get("uyanma_saati"), "07:30"),
                           key=f"uyanma_{gun_str}")
    _adim_k = g_kayit.get("adim", None)
    adim = s3.number_input("Adım sayısı — boş bırakabilirsiniz", min_value=0, max_value=60000, step=500,
                           value=(int(_adim_k) if _adim_k not in (None, "", 0) else None),
                           placeholder="Girmezseniz boş kalır", key=f"adim_{gun_str}")

    # ---- Antrenman saatleri & RPE -----------------------------------------
    st.markdown("#### ⏱️ Antrenman Süresi & Zorluk")
    t1, t2, t3 = st.columns(3)
    ant_bas = t1.time_input("Başlangıç", value=_parse_saat(g_kayit.get("antrenman_baslangic"), "18:00"),
                            key=f"antbas_{gun_str}")
    ant_bit = t2.time_input("Bitiş", value=_parse_saat(g_kayit.get("antrenman_bitis"), "19:15"),
                            key=f"antbit_{gun_str}")
    rpe = t3.slider("Zorluk (RPE)", min_value=1, max_value=10, value=int(g_kayit.get("rpe", 8)),
                    key=f"rpe_{gun_str}", help="Algılanan efor: 1 = çok kolay, 10 = maksimal")

    _kalori_kayit = g_kayit.get("kalori", None)
    kalori = st.number_input("Toplam alınan kalori (kcal) — boş bırakabilirsiniz", min_value=0, max_value=8000, step=50,
                             value=(int(_kalori_kayit) if _kalori_kayit not in (None, "", 0) else None),
                             placeholder="Girmezseniz boş kalır", key=f"kalori_{gun_str}")

    if st.button("💾 Günlük Veriyi Firebase'e Kaydet", type="primary"):
        payload = {
            "tarih": gun_str,
            "gun_adi": gun_adi,
            "kilo": (float(kilo) if kilo not in (None, "") else None),
            "kalori": (int(kalori) if kalori not in (None, "") else None),
            "adim": (int(adim) if adim not in (None, "") else None),
            "antrenman_kayit": antrenman_kayit,
            "kardiyo": (kardiyo_gunluk if kardiyo_yapildi else []),
            "beslenme_uyum": beslenme_uyum,
            "uyku_saati": uyku.strftime("%H:%M"),
            "uyanma_saati": uyanma.strftime("%H:%M"),
            "antrenman_baslangic": ant_bas.strftime("%H:%M"),
            "antrenman_bitis": ant_bit.strftime("%H:%M"),
            "rpe": int(rpe),
        }
        ok, msg = save_doc(db, "gunluk_loglar", gun_str, payload)
        # Kardiyoyu ayrıca Kardiyo sekmesine de yaz (otomatik yansısın)
        if kardiyo_yapildi and kardiyo_gunluk:
            save_doc(db, "kardiyo", gun_str, {"tarih": gun_str, "seanslar": kardiyo_gunluk})
        (st.success if ok else st.error)(msg)


# -----------------------------------------------------------------------------
# SEKME 2 — HAFTALIK CHECK-IN
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Haftalık Check-in")
    htarih = st.date_input("Check-in tarihi", value=date.today(), key="haftalik_tarih")
    h_str = htarih.isoformat()

    h_kayit = load_doc(db, "haftalik_checkin", h_str)
    if h_kayit:
        st.caption("✅ Bu tarihe ait check-in yüklendi.")
    onceki_olcu = h_kayit.get("olculer", {})

    st.markdown("#### 📏 Vücut Ölçüleri (cm)")
    m1, m2, m3, m4 = st.columns(4)
    omuz = m1.number_input("Omuz", min_value=0.0, max_value=200.0, step=0.5,
                           value=float(onceki_olcu.get("omuz", 120.0)), key=f"omuz_{h_str}")
    gogus = m2.number_input("Göğüs", min_value=0.0, max_value=200.0, step=0.5,
                            value=float(onceki_olcu.get("gogus", 105.0)), key=f"gogus_{h_str}")
    bel = m3.number_input("Bel", min_value=0.0, max_value=200.0, step=0.5,
                          value=float(onceki_olcu.get("bel", 80.0)), key=f"bel_{h_str}")
    kol = m4.number_input("Kol", min_value=0.0, max_value=100.0, step=0.5,
                          value=float(onceki_olcu.get("kol", 38.0)), key=f"kol_{h_str}")
    olculer = {"omuz": omuz, "gogus": gogus, "bel": bel, "kol": kol}

    st.markdown("#### 🖼️ Form / Postür Fotoğrafları")

    # Daha önce kaydedilmiş fotoğraflar (o tarihe ait) gösterilir
    kayitli_fotolar = h_kayit.get("fotolar", [])
    if kayitli_fotolar and PIL_OK:
        st.caption("Bu tarihe kaydedilmiş fotoğraflar:")
        try:
            st.image([_b64_to_img(b) for b in kayitli_fotolar], width=140)
        except Exception:
            st.caption("(Kayıtlı fotoğraflar gösterilemedi.)")

    foto_list = st.file_uploader("Yeni fotoğraf(lar) yükle (birden fazla seçebilirsiniz)",
                                 type=["jpg", "jpeg", "png"], accept_multiple_files=True,
                                 key=f"form_foto_{h_str}")

    yeni_imgs = []
    if foto_list and PIL_OK:
        yeni_imgs = [Image.open(f) for f in foto_list]
        st.caption("Yeni yüklenenler:")
        st.image(yeni_imgs, width=140)

    cc1, cc2 = st.columns(2)
    if cc1.button("🔍 Gemini Vision ile Analiz Et"):
        analiz_imgs = yeni_imgs[:]
        # yeni yoksa kayıtlı fotoğrafları analiz et
        if not analiz_imgs and kayitli_fotolar and PIL_OK:
            try:
                analiz_imgs = [_b64_to_img(b) for b in kayitli_fotolar]
            except Exception:
                analiz_imgs = []
        if not analiz_imgs:
            st.warning("Önce en az bir fotoğraf yükleyin.")
        else:
            with st.spinner("Postür ve asimetri analizi yapılıyor..."):
                st.session_state["foto_analiz"] = analyze_form_photo(model, analiz_imgs, olculer)

    if st.session_state.get("foto_analiz"):
        st.markdown("##### 🐼 Koç Analizi")
        st.markdown(f'<div class="panda-card">{st.session_state["foto_analiz"]}</div>', unsafe_allow_html=True)

    if cc2.button("💾 Check-in'i Firebase'e Kaydet", type="primary"):
        # Yeni fotoğraflar varsa onları, yoksa eskileri sakla (küçültülmüş base64)
        if yeni_imgs and PIL_OK:
            try:
                foto_b64 = [_img_to_b64(im) for im in yeni_imgs]
            except Exception:
                foto_b64 = kayitli_fotolar
        else:
            foto_b64 = kayitli_fotolar
        payload = {
            "tarih": h_str,
            "olculer": olculer,
            "fotolar": foto_b64,
            "foto_analiz": st.session_state.get("foto_analiz", ""),
        }
        ok, msg = save_doc(db, "haftalik_checkin", h_str, payload)
        (st.success if ok else st.error)(msg)


# -----------------------------------------------------------------------------
# SEKME 3 — GELİŞİM GRAFİKLERİ
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Son 1 Aylık Gelişim")

    daily = load_recent(db, "gunluk_loglar", days=30)

    if not daily:
        st.info("Henüz grafik için yeterli veri yok. Önce 'Günlük Veri Girişi' sekmesinden kayıt ekleyin (ve Firestore'u bağlayın).")
    else:
        tarihler = [r.get("tarih", r.get("_id")) for r in daily]
        kilolar = [r.get("kilo") for r in daily]
        kaloriler = [r.get("kalori") for r in daily]
        adimlar = [r.get("adim") for r in daily]

        # Özet metrikler
        k1, k2, k3 = st.columns(3)
        if any(v is not None for v in kilolar):
            ilk = next((v for v in kilolar if v is not None), None)
            son = next((v for v in reversed(kilolar) if v is not None), None)
            if ilk is not None and son is not None:
                k1.metric("Kilo değişimi", f"{son:.1f} kg", f"{son - ilk:+.1f} kg")
        valid_kcal = [v for v in kaloriler if v]
        if valid_kcal:
            k2.metric("Ort. kalori", f"{sum(valid_kcal)//len(valid_kcal)} kcal")
        valid_adim = [v for v in adimlar if v]
        if valid_adim:
            k3.metric("Ort. adım", f"{sum(valid_adim)//len(valid_adim)}")

        def panda_line(x, y, title, ylabel, color="#111111"):
            """Panda temalı çizgi grafik (Plotly varsa onu, yoksa Streamlit chart)."""
            y_clean = [(xi, yi) for xi, yi in zip(x, y) if yi is not None]
            if not y_clean:
                st.caption(f"{title}: veri yok.")
                return
            xs, ys = zip(*y_clean)
            if PLOTLY_OK:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(xs), y=list(ys), mode="lines+markers",
                    line=dict(color=color, width=2.5),
                    marker=dict(color=color, size=7),
                ))
                fig.update_layout(
                    title=title, height=340,
                    paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF",
                    font=dict(color="#111111", family="Inter, Arial"),
                    margin=dict(l=10, r=10, t=50, b=10),
                    xaxis=dict(showgrid=False, linecolor="#E6E6E6"),
                    yaxis=dict(title=ylabel, gridcolor="#F0F0F0", zeroline=False),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(f"**{title}**")
                st.line_chart({ylabel: list(ys)})

        panda_line(tarihler, kilolar, "⚖️ Kilo (kg)", "kg")
        panda_line(tarihler, kaloriler, "🔥 Alınan Kalori (kcal)", "kcal")
        panda_line(tarihler, adimlar, "👟 Adım Sayısı", "adım")

        st.divider()
        if st.button("🤖 Koçtan veri tabanlı program revizyonu iste"):
            ozet = {
                "kilo_serisi": kilolar,
                "kalori_serisi": kaloriler,
                "adim_serisi": adimlar,
                "tarih_araligi": [tarihler[0], tarihler[-1]],
            }
            prompt = (
                "Aşağıda son 1 ayın verileri var. Gelişim durmuş mu değerlendir ve "
                "kanıta dayalı, sporcunun profiline ve sakatlıklarına uygun somut "
                "revizyon öner.\n\n"
                + json.dumps(ozet, ensure_ascii=False)
            )
            with st.spinner("Veriler değerlendiriliyor..."):
                st.session_state["revizyon"] = ask_coach(model, prompt)
        if st.session_state.get("revizyon"):
            st.markdown(f'<div class="panda-card">{st.session_state["revizyon"]}</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SEKME 4 — PROGRAM & BESLENME + KOÇ DEĞERLENDİRME
# -----------------------------------------------------------------------------
with tab4:
    st.subheader("Haftalık Program & Beslenme Planı")

    kayitli = load_doc(db, "program_plan", "guncel")

    # ---- A) Haftalık antrenman programı (5 günlük üst vücut split) ----------
    st.markdown("#### 🏋️ Haftalık Antrenman Programı")
    st.caption("Excel yükleyip koça gün-gün doldurtabilirsiniz. Dosyada antrenman ve beslenme ayrı sayfalardaysa ikisini de okur.")

    # Excel yükleme alanı
    prog_excel = st.file_uploader("Program/beslenme dosyası (Excel: .xlsx)", type=["xlsx", "xls"],
                                  key="prog_excel")
    if prog_excel is not None:
        if st.button("🤖 Koç Excel'i okuyup tablolara yazsın"):
            try:
                import pandas as pd
                # Tüm sayfaları oku (sheet_name=None -> {sayfa_adi: df})
                sayfalar = pd.read_excel(prog_excel, header=None, sheet_name=None)
                parcalar = []
                for ad, df in sayfalar.items():
                    parcalar.append(f"=== SAYFA: {ad} ===\n{df.to_csv(index=False, header=False)}")
                sayfalar_metni = "\n\n".join(parcalar)
                with st.spinner("Koç dosyayı okuyor ve düzenliyor..."):
                    veri, hata = excel_to_plan(model, sayfalar_metni)
                if veri:
                    if veri.get("program"):
                        st.session_state["program_data"] = veri["program"]
                    if veri.get("beslenme"):
                        st.session_state["beslenme_data_on"] = veri["beslenme"]
                    st.success("Tablolar dolduruldu. Aşağıda kontrol edip düzenleyebilirsiniz.")
                    st.rerun()
                else:
                    st.error(hata or "Excel okunamadı.")
            except Exception as e:
                st.error(f"Excel okunamadı: {e}")

    # Tablo kaynağı: önce yüklenen/oturum verisi, yoksa kayıtlı, yoksa varsayılan
    default_program = st.session_state.get("program_data", kayitli.get("program", [
        {"gun": "Pazartesi", "odak": "Göğüs",           "egzersizler": ""},
        {"gun": "Salı",      "odak": "Sırt",            "egzersizler": ""},
        {"gun": "Çarşamba",  "odak": "Omuz",            "egzersizler": ""},
        {"gun": "Perşembe",  "odak": "Kol (Biceps/Triceps)", "egzersizler": ""},
        {"gun": "Cuma",      "odak": "Göğüs/Sırt (tekrar)",  "egzersizler": ""},
    ]))
    # Önce OKUNAKLI görünüm (öne çıkan), düzenleme tablosu altta gizli durur
    st.markdown("##### 📖 Program")
    _bos = True
    for satir in default_program:
        gun = str(satir.get("gun", "")).strip()
        odak = str(satir.get("odak", "")).strip()
        egz = str(satir.get("egzersizler", "")).strip()
        if not (gun or egz):
            continue
        _bos = False
        st.markdown(f"**{gun} — {odak}**")
        parcalar = [e.strip() for e in egz.replace(",", "\n").split("\n") if e.strip()]
        if parcalar:
            st.markdown("\n".join(f"- {e}" for e in parcalar))
        st.markdown("")
    if _bos:
        st.caption("Henüz program yok. Aşağıdaki tablodan girin veya Excel yükleyin.")

    with st.expander("✏️ Tabloda düzenle", expanded=False):
        program = st.data_editor(
            default_program,
            num_rows="dynamic",
            use_container_width=True,
            column_order=("gun", "odak", "egzersizler"),
            column_config={
                "gun": st.column_config.TextColumn("Gün", width="small"),
                "odak": st.column_config.TextColumn("Odak Bölge", width="medium"),
                "egzersizler": st.column_config.TextColumn("Egzersizler (her satır ayrı)", width="large"),
            },
            key="program_editor",
        )
    st.session_state["program_data"] = program

    # ---- B) Beslenme planı --------------------------------------------------
    st.markdown("#### 🍽️ Beslenme Planı")
    st.caption("Öğün içeriklerini serbestçe girin; kalori protein+karbonhidrat+yağdan otomatik hesaplanır.")
    # ---- B) Beslenme planı (Antrenman / Dinlenme günü ayrı) -----------------
    st.markdown("#### 🍽️ Beslenme Planı")
    st.caption("Öğün içeriklerini serbestçe girin. "
               "Kalori protein+karbonhidrattan otomatik hesaplanır (≈4 kcal/g, yağ hariç).")

    def _beslenme_blok(varsayilan, anahtar):
        """Bir gün tipi için beslenme tablosu + makro hesaplama düğmesi. Düzenlenmiş listeyi döndürür."""
        sess_key = f"beslenme_data_{anahtar}"
        kaynak = st.session_state.get(sess_key, varsayilan)
        # Eski kayıtlarda yağ alanı yoksa ekle (sütunun görünmesi için şart)
        for _m in kaynak:
            _m.setdefault("yag_g", 0)
            _m.setdefault("protein_g", 0)
            _m.setdefault("karb_g", 0)
            _m.setdefault("kcal", 0)

        if st.button("🤖 İçerikten makro/kalori hesapla", key=f"makro_btn_{anahtar}"):
            with st.spinner("İçerikten makrolar hesaplanıyor..."):
                yeni, hata = compute_macros_from_content(model, kaynak)
            if yeni:
                st.session_state[sess_key] = yeni
                st.rerun()
            else:
                st.error(hata or "Hesaplanamadı.")

        duzenlenen = st.data_editor(
            kaynak,
            num_rows="dynamic",
            use_container_width=True,
            column_order=("ogun", "icerik", "protein_g", "karb_g", "yag_g", "kcal"),
            column_config={
                "ogun": st.column_config.TextColumn("Öğün", width="small"),
                "icerik": st.column_config.TextColumn("İçerik (besin + gram)", width="large"),
                "protein_g": st.column_config.NumberColumn("Protein (g)", width="small"),
                "karb_g": st.column_config.NumberColumn("Karb (g)", width="small"),
                "yag_g": st.column_config.NumberColumn("Yağ (g)", width="small"),
                "kcal": st.column_config.NumberColumn("Kalori (oto)", width="small", disabled=True),
            },
            key=f"beslenme_editor_{anahtar}",
        )
        t_kcal, t_pro = 0, 0
        for _r in duzenlenen:
            _r["kcal"] = round(
                (_say(_r.get("protein_g")) + _say(_r.get("karb_g"))) * 4
                + _say(_r.get("yag_g")) * 9
            )
            t_kcal += _r["kcal"]
            t_pro += _say(_r.get("protein_g"))
        st.session_state[sess_key] = duzenlenen
        c_a, c_b = st.columns(2)
        c_a.metric("Toplam kalori (oto)", f"{t_kcal} kcal")
        c_b.metric("Toplam protein", f"{int(t_pro)} g")
        return duzenlenen

    # Eski tek liste varsa onu Antrenman gününe taşı (geriye dönük uyum)
    def _dolu(liste):
        for r in (liste or []):
            if str(r.get("icerik", "")).strip() or _say(r.get("protein_g")) or _say(r.get("karb_g")):
                return True
        return False

    bos3 = [
        {"ogun": "1. Öğün", "icerik": "", "protein_g": 0, "karb_g": 0, "yag_g": 0, "kcal": 0},
        {"ogun": "2. Öğün", "icerik": "", "protein_g": 0, "karb_g": 0, "yag_g": 0, "kcal": 0},
        {"ogun": "3. Öğün", "icerik": "", "protein_g": 0, "karb_g": 0, "yag_g": 0, "kcal": 0},
    ]
    eski_tek = kayitli.get("beslenme", [])
    kayit_on = kayitli.get("beslenme_on", [])
    kayit_off = kayitli.get("beslenme_off", [])

    # On: önce kayıtlı on, boşsa eski tek liste, o da boşsa boş şablon
    if _dolu(kayit_on):
        varsayilan_on = kayit_on
    elif _dolu(eski_tek):
        varsayilan_on = eski_tek
    else:
        varsayilan_on = bos3
    varsayilan_off = kayit_off if _dolu(kayit_off) else list(bos3)

    bes_on_tab, bes_off_tab = st.tabs(["🏋️ Antrenman Günü (On)", "😴 Dinlenme Günü (Off)"])
    with bes_on_tab:
        beslenme_on = _beslenme_blok(varsayilan_on, "on")
    with bes_off_tab:
        beslenme_off = _beslenme_blok(varsayilan_off, "off")

    notlar = st.text_area("Ek notlar (takviye, hedef kalori, vb.)", value=kayitli.get("notlar", ""))

    if st.button("💾 Program & Planı Kaydet", type="primary"):
        payload = {
            "program": program,
            "beslenme_on": beslenme_on,
            "beslenme_off": beslenme_off,
            "notlar": notlar,
            "tarih": date.today().isoformat(),
        }
        ok, msg = save_doc(db, "program_plan", "guncel", payload)
        (st.success if ok else st.error)(msg)
        if not ok and db is None:
            st.caption("ℹ️ Firestore bağlı değil; kayıt için Firebase kurulmalı. Aşağıdaki değerlendirme yine de çalışır.")

    st.divider()

    # ---- C) Koç ile değerlendirme sohbeti -----------------------------------
    st.markdown("#### 🐼 Koç ile Değerlendirme")
    st.caption("Program ve beslenmeni koça değerlendirt, soru sor, revizyon iste. Koç kayıtlı verilerini ve son loglarını görür.")

    if "eval_chat" not in st.session_state:
        st.session_state["eval_chat"] = []

    # Bağlam: program/plan + son loglar + sağlık + EN SON HAFTALIK CHECK-IN
    son_loglar = load_recent(db, "gunluk_loglar", days=14)
    saglik_kayit = load_doc(db, "saglik", "guncel")
    haftaliklar = load_recent(db, "haftalik_checkin", days=60)
    son_haftalik = haftaliklar[-1] if haftaliklar else {}
    bağlam = {
        "program": program,
        "beslenme_antrenman_gunu": beslenme_on,
        "beslenme_dinlenme_gunu": beslenme_off,
        "notlar": notlar,
        "son_gunluk_loglar": son_loglar,
        "son_haftalik_checkin": {
            "tarih": son_haftalik.get("tarih", ""),
            "olculer": son_haftalik.get("olculer", {}),
            "foto_analiz": son_haftalik.get("foto_analiz", ""),
        },
        "onceki_haftalik_olculer": [
            {"tarih": h.get("tarih"), "olculer": h.get("olculer", {})} for h in haftaliklar[-4:]
        ],
        "aktif_sakatliklar": saglik_kayit.get("sakatliklar", []),
        "kan_tahlili": saglik_kayit.get("kan", []),
        "saglik_notlari": saglik_kayit.get("notlar", ""),
    }

    cbtn1, cbtn2 = st.columns([1, 1])
    if cbtn1.button("🔍 Haftalık değerlendirme yap"):
        with st.spinner("Koç değerlendiriyor..."):
            cevap = evaluate_with_coach(
                model, st.session_state["eval_chat"], bağlam,
                "HAFTALIK DEĞERLENDİRME yap. En son haftalık check-in'i (ölçüler + form fotoğrafı "
                "analizi) ESAS AL; bunu önceki ölçülerle ve son günlük loglarla (antrenman set/kg, "
                "beslenme uyumu, adım, uyku) birlikte yorumla. Gelişim var mı, nerede tıkanma var, "
                "programda ve makroda ne değişmeli? Eksik veriyi 'girilmemiş' say, sıfır sayma. Maddele."
            )
        st.session_state["eval_chat"].append({"role": "user", "content": "Haftalık değerlendirme."})
        st.session_state["eval_chat"].append({"role": "assistant", "content": cevap})
    if cbtn2.button("🗑️ Sohbeti temizle"):
        st.session_state["eval_chat"] = []

    # --- Koçun revizyonunu tablolara aktar ---
    st.markdown("##### 🔁 Önerilen güncellemeleri tablolara aktar")
    st.caption("Koç, mevcut plan ve verilerine göre güncellenmiş bir program/beslenme hazırlar; onaylarsan tablolara yazılır.")
    if st.button("🤖 Koç güncellenmiş planı hazırlasın"):
        with st.spinner("Koç güncellenmiş planı hazırlıyor..."):
            yeni_plan, hata = revise_plan_with_coach(model, bağlam)
        if yeni_plan:
            st.session_state["onerilen_plan"] = yeni_plan
        else:
            st.error(hata or "Plan hazırlanamadı.")

    onerilen = st.session_state.get("onerilen_plan")
    if onerilen:
        if onerilen.get("aciklama"):
            st.markdown(f'<div class="panda-card"><b>Koçun özeti:</b><br>{onerilen["aciklama"]}</div>',
                        unsafe_allow_html=True)
        with st.expander("👁️ Önerilen planı önizle", expanded=False):
            st.json({k: v for k, v in onerilen.items() if k != "aciklama"})
        ap1, ap2 = st.columns([1, 1])
        if ap1.button("✅ Tablolara aktar", type="primary"):
            if onerilen.get("program"):
                st.session_state["program_data"] = onerilen["program"]
            if onerilen.get("beslenme_on"):
                st.session_state["beslenme_data_on"] = onerilen["beslenme_on"]
            if onerilen.get("beslenme_off"):
                st.session_state["beslenme_data_off"] = onerilen["beslenme_off"]
            st.session_state.pop("onerilen_plan", None)
            st.success("Aktarıldı. Yukarıdaki tablolarda kontrol edip 'Program & Planı Kaydet' ile kaydedin.")
            st.rerun()
        if ap2.button("✖️ Vazgeç"):
            st.session_state.pop("onerilen_plan", None)
            st.rerun()

    # Sohbet geçmişini göster
    for msg in st.session_state["eval_chat"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar="🧑" if msg["role"] == "user" else "🐼"):
            st.markdown(msg["content"])

    # Yeni mesaj kutusu
    soru = st.chat_input("Koça yaz: örn. 'Cuma gününü daha ağır yapalım mı?'")
    if soru:
        st.session_state["eval_chat"].append({"role": "user", "content": soru})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(soru)
        with st.chat_message("assistant", avatar="🐼"):
            with st.spinner("Koç düşünüyor..."):
                cevap = evaluate_with_coach(model, st.session_state["eval_chat"], bağlam, soru)
            st.markdown(cevap)
        st.session_state["eval_chat"].append({"role": "assistant", "content": cevap})


# -----------------------------------------------------------------------------
# SEKME 5 — SAĞLIK (SAKATLIK + KAN TAHLİLİ)
# -----------------------------------------------------------------------------
with tab5:
    st.subheader("Sağlık Profili")
    st.caption("Bu bilgiler koçun program ve beslenme önerilerinde otomatik dikkate alınır. "
               "Koç doktor değildir; kan değerleri için hekiminize danışın.")

    saglik = load_doc(db, "saglik", "guncel")

    # ---- A) Aktif sakatlıklar ----------------------------------------------
    st.markdown("#### 🩹 Aktif Sakatlıklar / Kısıtlar")
    st.caption("Koç bu bölgeleri zorlayan egzersizleri önermez, alternatif verir.")
    default_sakat = saglik.get("sakatliklar", [
        {"bolge": "", "aciklama": "", "siddet": "Hafif"},
    ])
    sakatliklar = st.data_editor(
        default_sakat,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "bolge": st.column_config.TextColumn("Bölge (örn. sağ omuz)", width="medium"),
            "aciklama": st.column_config.TextColumn("Açıklama / tanı", width="large"),
            "siddet": st.column_config.SelectboxColumn("Şiddet", options=["Hafif", "Orta", "Ciddi"], width="small"),
        },
        key="sakatlik_editor",
    )

    # ---- B) Kan tahlili -----------------------------------------------------
    st.markdown("#### 🩸 Kan Tahlili Sonuçları")
    st.caption("Elle girebilir veya tahlil fotoğrafı yükleyip AI ile okutabilirsiniz.")

    foto_kan = st.file_uploader("Kan tahlili fotoğrafı / ekran görüntüsü (jpg / png)",
                                type=["jpg", "jpeg", "png"], key="kan_foto")
    if foto_kan is not None and PIL_OK:
        kan_img = Image.open(foto_kan)
        st.image(kan_img, caption="Yüklenen tahlil", width=320)
        if st.button("🔍 Tahlili AI ile oku"):
            with st.spinner("Tahlil okunuyor..."):
                st.session_state["kan_okuma"] = read_blood_image(model, kan_img)
    if st.session_state.get("kan_okuma"):
        st.markdown(f'<div class="panda-card">{st.session_state["kan_okuma"]}</div>', unsafe_allow_html=True)

    st.markdown("**Tahlil değerleri tablosu**")
    default_kan = saglik.get("kan", [
        {"parametre": "Hemoglobin", "deger": "", "birim": "g/dL", "referans": "13-17"},
        {"parametre": "Demir (Fe)", "deger": "", "birim": "µg/dL", "referans": "65-175"},
        {"parametre": "D Vitamini", "deger": "", "birim": "ng/mL", "referans": "30-100"},
    ])
    kan = st.data_editor(
        default_kan,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "parametre": st.column_config.TextColumn("Parametre", width="medium"),
            "deger": st.column_config.TextColumn("Değer", width="small"),
            "birim": st.column_config.TextColumn("Birim", width="small"),
            "referans": st.column_config.TextColumn("Referans aralığı", width="small"),
        },
        key="kan_editor",
    )

    saglik_notlari = st.text_area("Ek sağlık notları (alerji, kullanılan ilaç/takviye, kronik durum)",
                                  value=saglik.get("notlar", ""))

    cs1, cs2 = st.columns(2)
    if cs1.button("💾 Sağlık Bilgilerini Kaydet", type="primary"):
        payload = {
            "sakatliklar": sakatliklar,
            "kan": kan,
            "kan_okuma": st.session_state.get("kan_okuma", ""),
            "notlar": saglik_notlari,
            "tarih": date.today().isoformat(),
        }
        ok, msg = save_doc(db, "saglik", "guncel", payload)
        (st.success if ok else st.error)(msg)

    if cs2.button("🩺 Koçtan sağlık değerlendirmesi iste"):
        ctx = {
            "aktif_sakatliklar": sakatliklar,
            "kan_tahlili": kan,
            "saglik_notlari": saglik_notlari,
        }
        prompt = (
            "Aşağıdaki sağlık verilerini değerlendir. Sakatlıklara göre üst vücut "
            "programında hangi hareketlerden kaçınılmalı ve alternatifleri ne olmalı? "
            "Kan değerlerinde referans dışı olanları işaretle, beslenme açısından genel "
            "öneri ver ve gerekiyorsa hekime yönlendir (tanı koyma).\n\n"
            + json.dumps(ctx, ensure_ascii=False, indent=2)
        )
        with st.spinner("Koç değerlendiriyor..."):
            st.session_state["saglik_degerlendirme"] = ask_coach(model, prompt)

    if st.session_state.get("saglik_degerlendirme"):
        st.markdown("##### 🐼 Koç Sağlık Değerlendirmesi")
        st.markdown(f'<div class="panda-card">{st.session_state["saglik_degerlendirme"]}</div>', unsafe_allow_html=True)
        st.caption("⚠️ Bu bir tıbbi tavsiye değildir. Kan değerleriniz ve sakatlıklarınız için hekiminize danışın.")


# -----------------------------------------------------------------------------
# SEKME 6 — KARDİYO
# -----------------------------------------------------------------------------
with tab6:
    st.subheader("Kardiyo Kaydı")
    k_tarih = st.date_input("Tarih", value=date.today(), key="kardiyo_tarih")
    k_str = k_tarih.isoformat()

    k_kayit = load_doc(db, "kardiyo", k_str)
    if k_kayit:
        st.caption("✅ Bu tarihe ait kardiyo kaydı yüklendi.")

    st.caption("Her satıra bir kardiyo seansı: tür, süre ve ortalama nabız.")
    default_kardiyo = k_kayit.get("seanslar", [
        {"tur": "Tempolu yürüyüş", "sure_dk": 30, "ort_nabiz": 120},
    ])
    kardiyo = st.data_editor(
        default_kardiyo,
        num_rows="dynamic",
        use_container_width=True,
        column_order=("tur", "sure_dk", "ort_nabiz"),
        column_config={
            "tur": st.column_config.SelectboxColumn(
                "Tür",
                options=["Tempolu yürüyüş", "Koşu", "Bisiklet", "Eliptik",
                         "Kürek", "Yüzme", "Merdiven", "HIIT", "Diğer"],
                width="medium",
            ),
            "sure_dk": st.column_config.NumberColumn("Süre (dk)", min_value=0, max_value=600, width="small"),
            "ort_nabiz": st.column_config.NumberColumn("Ort. Nabız (bpm)", min_value=0, max_value=230, width="small"),
        },
        key=f"kardiyo_editor_{k_str}",
    )

    # Özet metrikler
    top_sure = sum(_say(r.get("sure_dk")) for r in kardiyo)
    nabizlar = [_say(r.get("ort_nabiz")) for r in kardiyo if _say(r.get("ort_nabiz")) > 0]
    ort_nabiz = round(sum(nabizlar) / len(nabizlar)) if nabizlar else 0
    kc1, kc2 = st.columns(2)
    kc1.metric("Toplam süre", f"{int(top_sure)} dk")
    kc2.metric("Ortalama nabız", f"{ort_nabiz} bpm" if ort_nabiz else "—")

    if st.button("💾 Kardiyoyu Firebase'e Kaydet", type="primary"):
        payload = {"tarih": k_str, "seanslar": kardiyo}
        ok, msg = save_doc(db, "kardiyo", k_str, payload)
        (st.success if ok else st.error)(msg)
