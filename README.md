# Dünyayi Gezayisun AI Rehberuylan

Bu proje, yapay zeka destekli ve çok dilli çalışan modern bir gezi rehberi sistemidir. Dünyanın farklı şehirleri için gezi rehberi verilerini bir araya getiren, yapay zeka ile açıklama çevirilerini ve mekan görsellerini zenginleştiren, çok dilli (Türkçe ve İngilizce) olarak saklayan ve kullanıcıya modern bir Streamlit arayüzü ile sunan tam çalışan bir sistemdir.

---

## Kullanılan Teknolojiler

* **Strapi CMS (Backend):** Headless CMS olarak veri yönetimini sağlar. REST API sunar.
* **Streamlit (Frontend):** Modern, duyarlı ve dinamik web arayüzünü oluşturur.
* **Python (Automation & API):** Otomasyon akışlarını, veri doğrulamayı ve entegrasyonu yönetir.
* **deep-translator:** Türkçe açıklamaları otomatik olarak İngilizceye çevirir (Google Translate motoru).
* **Groq API:** Şehir ve mekan tanıtımlarını yapay zeka ile gezi rehberi üslubunda zenginleştirir.
* **Pollinations AI:** Mekan ismine göre yapay zeka ile özgün görsel oluşturur; metin üretiminde Groq kullanılamazsa yedek servis olarak denenebilir.
* **HuggingFace Stable Diffusion XL:** Pollinations AI'ın yanıt vermediği durumlarda ikincil YZ görsel üretim servisi olarak kullanılır.
* **python-dotenv & requests:** Çevre değişkenlerini yükleme ve HTTP isteklerini yönetme.

---

## Proje Klasör Yapısı

```text
ai-travel-guide/
│
├── automation/
│   ├── data/
│   │   └── places.json        # Başlangıç gezi verileri (İstanbul, Paris, Londra)
│   ├── images/                # Otomasyon tarafından üretilen görsellerin kaydedildiği klasör
│   ├── main.py                # Otomasyon akışını başlatan ana betik
│   ├── content_enricher.py    # Groq API ile şehir/mekan tanıtımı üreten modül
│   ├── enrich_existing_content.py # Mevcut Strapi kayıtlarının tanıtımlarını YZ ile günceller
│   ├── strapi_api.py          # Strapi API entegrasyonu (Şehir/Mekan oluşturma, Görsel yükleme)
│   ├── translator.py          # Türkçe açıklamaları İngilizceye çeviren modül
│   ├── image_generator.py     # Pollinations AI / HuggingFace ile görsel üreten modül
│   ├── cleanup.py             # Tekrarlı kayıtları temizleme aracı
│   ├── requirements.txt       # Otomasyon bağımlılıkları
│   └── .env.example           # Otomasyon çevre değişkenleri şablonu
│
├── frontend-streamlit/
│   ├── app.py                 # Streamlit arayüz kodları
│   ├── api.py                 # Strapi'den veri çeken API istemcisi
│   ├── requirements.txt       # Streamlit bağımlılıkları
│   └── .env.example           # Streamlit çevre değişkenleri şablonu
│
├── run.bat                    # Tek komutla projeyi çalıştırma (Windows)
├── .gitignore                 # Git takibine alınmayacak dosyalar
└── README.md                  # Proje rehberi ve kurulum kılavuzu
```

---

## Kurulum ve Yapılandırma

### 1. Strapi CMS (Backend) Ayarları

Sistemin çalışması için öncelikle Strapi CMS'in kurulu ve çalışır durumda olması gerekmektedir.

#### A. Strapi Projesini Oluşturma
Bilgisayarınızda boş bir dizinde terminali açıp aşağıdaki komutu çalıştırarak Strapi projesi oluşturun:
```bash
npx create-strapi-app@latest my-strapi-backend --quickstart
```

#### B. İçerik Tiplerini (Content Types) Oluşturma
Strapi Admin Paneline (`http://localhost:1337/admin`) giriş yaptıktan sonra **Content-Type Builder** menüsüne gidin ve şu iki içerik tipini oluşturun:

1. **Cities (Şehirler)**:
   * **name** (Text - Short Text, *Required*) — Şehir adı (Türkçe)
   * **name_en** (Text - Short Text) — Şehir adı (İngilizce, otomasyon tarafından doldurulur)
   * **country** (Text - Short Text, *Required*) — Ülke adı (Türkçe)
   * **country_en** (Text - Short Text) — Ülke adı (İngilizce, otomasyon tarafından doldurulur)
   * **short_info** (Text - Long Text) — Kısa tanıtım (Türkçe)
   * **short_info_en** (Text - Long Text) — Kısa tanıtım (İngilizce, otomasyon tarafından doldurulur)

2. **Places (Mekanlar)**:
   * **name** (Text - Short Text, *Required*) — Mekan adı (Türkçe)
   * **name_en** (Text - Short Text) — Mekan adı (İngilizce, otomasyon tarafından doldurulur)
   * **description_tr** (Text - Long Text, *Required*) — Türkçe açıklama
   * **description_en** (Text - Long Text) — İngilizce açıklama (çeviri ile otomasyon tarafından doldurulur)
   * **rating** (Decimal, örn: 4.8) — Puan
   * **cover_image** (Media - Single media, *Images only*) — Kapak görseli (otomasyon tarafından yüklenir)
   * **city** (Relation — `Places` belongs to one `City`, `Cities` has many `Places`)

*Her iki içerik tipini oluşturduktan sonra sağ üstteki **Save** butonuna basarak sunucunun yeniden başlamasını bekleyin.*

#### C. Dil Desteğini Aktifleştirme (TR + EN)
Bu projede Strapi i18n desteği şema seviyesinde aktiftir. `STRAPI_PLUGIN_I18N_INIT_LOCALE_CODE=tr` değeriyle varsayılan locale Türkçe olarak ayarlanır.

Strapi Admin Panelinde:
1. **Settings > Global Settings > Internationalization** menüsüne gidin.
2. Varsayılan locale'in `tr` olduğunu kontrol edin.
3. **Add new locale** ile `en` locale'ini ekleyin.
4. **Content-Type Builder** içinde `City` ve `Place` content type'larında Internationalization ayarının aktif olduğunu kontrol edin.

#### D. API Token Oluşturma
Otomasyonun Strapi API'ye erişebilmesi ve görsel yükleyebilmesi için bir erişim anahtarı oluşturmalısınız:
1. Strapi Admin Panelinde **Settings > API Tokens > Create new API Token** yolunu izleyin.
2. Token adı olarak **"AI Travel Token"** girin.
3. Token Type değerini **Custom** seçin.
4. **Permissions (Yetkiler)** kısmında aşağıdakileri işaretleyin:
   * **Cities:** `find`, `findOne`, `create`, `update`
   * **Places:** `find`, `findOne`, `create`, `update`
   * **Upload (Medya):** `upload` (Görsellerin Media Library'ye yüklenebilmesi için gereklidir)
5. Sayfayı kaydedin. Ekranınızda görünecek olan Token'ı kopyalayıp güvenli bir yere kaydedin.

#### E. Public API Erişim İzinleri (Frontend için)
Streamlit frontend'in token olmadan veri okuyabilmesi için:
1. **Settings > Users & Permissions Plugin > Roles > Public** yolunu izleyin.
2. **Cities** altında `find` ve `findOne` kutularını işaretleyin.
3. **Places** altında `find` ve `findOne` kutularını işaretleyin.
4. Sayfayı kaydedin.

---

### 2. Environment Variables (Çevre Değişkenleri)

Projede hassas bilgileri (URL'ler, Token'lar vb.) gizli tutmak için `.env` dosyaları kullanılmaktadır.

> ⚠️ **Güvenlik Notu:** `.env` dosyaları `.gitignore` ile Git takibinden çıkarılmıştır. Gerçek token değerlerini asla GitHub'a pushlamayın.

#### Python Otomasyon Klasörü (`automation/`)
`automation/` klasöründe yer alan `.env.example` dosyasını kopyalayıp `.env` adında yeni bir dosya oluşturun ve içeriğini doldurun:
```env
STRAPI_URL=http://localhost:1337
STRAPI_API_TOKEN=kopyaladiginiz_api_token_degeri
POLLINATIONS_API_KEY=pollinations_api_key_degeri
GROQ_API_KEY=groq_api_key_degeri
GROQ_TEXT_MODEL=llama-3.3-70b-versatile
POLLINATIONS_TEXT_MODEL=nova-fast
HUGGINGFACE_API_KEY=opsiyonel_huggingface_api_anahtariniz
```

**Not:** `GROQ_API_KEY`, şehir ve mekan tanıtımlarını yapay zeka ile üretmek için kullanılır. Groq anahtarı https://console.groq.com/keys adresinden alınabilir. `POLLINATIONS_API_KEY` görsel üretimi için kullanılır; güncel Pollinations unified API için https://enter.pollinations.ai üzerinden anahtar oluşturabilirsiniz. `POLLINATIONS_TEXT_MODEL`, Groq başarısız olursa yedek metin üretimi için kullanılır. `HUGGINGFACE_API_KEY` opsiyoneldir; Pollinations görsel üretimi başarısız olduğunda ikincil alternatif olarak kullanılır.

#### Streamlit Klasörü (`frontend-streamlit/`)
`frontend-streamlit/` klasöründe yer alan `.env.example` dosyasını kopyalayıp `.env` adında yeni bir dosya oluşturun ve içeriğini doldurun:
```env
STRAPI_URL=http://localhost:1337
```

---

## Çalıştırma Adımları

### Hızlı Başlatma (Tek Komut)
Proje kök dizininde `run.bat` dosyasını çalıştırarak tüm süreci başlatabilirsiniz:
```bash
run.bat
```

### Manuel Çalıştırma

#### 1. Python Otomasyonunu Çalıştırma
Otomasyon, `places.json` verilerini alarak Türkçe tanıtımları **Groq API** ile zenginleştirir, `deep-translator` ile İngilizceye çevirir, **Pollinations AI** ile yapay zeka görseli üretir ve bunları Strapi backend veritabanına kaydeder.

Sanal ortam oluşturup gerekli kütüphaneleri yükleyin ve çalıştırın:
```bash
# automation/ dizininde çalıştırın
cd automation
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Yalnızca mevcut Strapi kayıtlarındaki şehir ve mekan tanıtımlarını YZ ile yeniden üretmek isterseniz görsel yükleme adımını çalıştırmadan şu scripti kullanabilirsiniz:

```bash
python enrich_existing_content.py
```

#### 2. Streamlit Çalıştırma
Streamlit, Strapi üzerinden aldığı şehir ve mekan verilerini modern kart tasarımıyla kullanıcıya sunar.

Sanal ortam oluşturup çalıştırın:
```bash
# frontend-streamlit/ dizininde çalıştırın
cd ../frontend-streamlit
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
*Uygulama başarıyla çalıştığında tarayıcınızda otomatik olarak `http://localhost:8501` adresi açılacaktır.*

---

## Sistem Mimarisi

```
┌────────────────────────────────────────────────────────────┐
│                    Otomasyon Motoru (Python)                │
│                                                            │
│  places.json → main.py (Orkestratör)                       │
│                   ├── content_enricher.py                   │
│                   │     Groq API → TR tanıtım                │
│                   ├── translator.py (deep-translator)      │
│                   │     TR → EN çeviri                      │
│                   ├── image_generator.py                   │
│                   │     Pollinations AI → HuggingFace       │
│                   └── strapi_api.py                        │
│                         POST /api/upload (Görsel)           │
│                         POST /api/cities (Şehir)            │
│                         POST /api/places (Mekan)            │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│              Strapi CMS (Backend & Veritabanı)             │
│                                                            │
│  Media Library ←── Görseller fiziksel olarak yüklenir      │
│  Cities Collection ←── Şehir verileri (TR + EN)            │
│  Places Collection ←── Mekan verileri (TR + EN + Görsel)   │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│            Streamlit Frontend (Kullanıcı Arayüzü)          │
│                                                            │
│  app.py → api.py (GET /api/cities, GET /api/places)        │
│  Çok dilli arayüz (TR / EN)                                │
│  Modern kart tasarımı ile şehir ve mekan gösterimi          │
└────────────────────────────────────────────────────────────┘
```

---

## YZ Metin Üretim Stratejisi

Tanıtım içerikleri iki aşamalı bir akışla hazırlanır:

1. `places.json` içindeki temel şehir ve mekan bilgileri okunur.
2. `content_enricher.py`, Groq API üzerinden bu temel açıklamaları daha bilgilendirici bir Türkçe gezi rehberi paragrafına dönüştürür.
3. Üretilen Türkçe metinler `deep-translator` ile İngilizceye çevrilir.
4. Türkçe ve İngilizce metinler Strapi'deki `Cities` ve `Places` koleksiyonlarına REST API ile kaydedilir.

Groq API anahtarı yoksa veya Groq isteği başarısız olursa sistem Pollinations text API'yi yedek olarak dener. Yedek servis de başarısız olursa mevcut temel açıklamayı kullanarak çalışmaya devam eder. Bu sayede otomasyon tamamen durmaz; ancak en iyi sonuç için `GROQ_API_KEY` tanımlı olmalıdır.

---

## Görsel Üretim Stratejisi

Sistem, mekan görselleri için aşağıdaki öncelik sırasına göre yapay zeka ile görsel üretir:

1. **Pollinations AI (Birincil):** Mekan adı İngilizceye çevrilerek bir prompt oluşturulur ve Pollinations AI unified API üzerinden `POLLINATIONS_API_KEY` ile görsel üretilir.
2. **HuggingFace Stable Diffusion XL (İkincil):** Pollinations AI başarısız olursa ve `.env` dosyasında `HUGGINGFACE_API_KEY` tanımlıysa, HuggingFace API'si üzerinden Stable Diffusion modeli ile görsel üretilir.
3. **picsum.photos (Son Çare):** Tüm YZ servisleri başarısız olursa, mekan adına göre seed kullanılarak picsum.photos'tan stok görsel indirilir.

Üretilen görseller önce `automation/images/` klasörüne kaydedilir, ardından Strapi'nin `POST /api/upload` endpoint'i aracılığıyla **Media Library'ye fiziksel olarak yüklenir** ve ilgili mekan kaydının `cover_image` alanına bağlanır.

---

## GitHub Kullanımı

Projeyi GitHub'a yüklemek için aşağıdaki komut dizisini proje kök dizininde (root) sırasıyla çalıştırabilirsiniz. `.gitignore` dosyası sayesinde hassas ayar dosyaları (`.env`) ve Python sanal ortamı (`venv/`) GitHub repository'sine yüklenmeyecektir.

```bash
# Proje ana dizininde (ai-travel-guide/) çalıştırın
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin REPO_URL
git push -u origin main
```

*(Lütfen `REPO_URL` yerine kendi oluşturduğunuz GitHub Repository linkini yazın.)*

---

## 🚀 Render ile Canlıya Alma (Deployment)

Proje, [Render](https://render.com) üzerinde **ücretsiz olarak** yayınlanabilir. Aşağıdaki adımları izleyin:

### Ön Gereksinimler

1. **GitHub hesabı** ve repo'ya pushlanmış proje kodu
2. **Render hesabı** (https://render.com — GitHub ile giriş yapabilirsiniz)
3. **Cloudinary hesabı** (https://cloudinary.com — ücretsiz, medya dosyaları için gerekli)

### Adım 1: Cloudinary Hesabı Oluşturma

Render'ın disk alanı geçicidir (ephemeral), bu nedenle Strapi'ye yüklenen görseller Cloudinary'de saklanır.

1. https://cloudinary.com adresine gidin ve ücretsiz hesap oluşturun.
2. Dashboard'da şu bilgileri not edin:
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### Adım 2: Render Blueprint ile Otomatik Kurulum

Proje kök dizinindeki `render.yaml` dosyası tüm servisleri otomatik olarak tanımlar.

1. https://dashboard.render.com adresine gidin.
2. **New > Blueprint** seçeneğine tıklayın.
3. GitHub repo'nuzu bağlayın.
4. Render, `render.yaml` dosyasını okuyarak şu servisleri otomatik oluşturacaktır:
   - **PostgreSQL Veritabanı** (`ai-travel-guide-db`)
   - **Strapi Backend** (`ai-travel-guide-strapi`)
   - **Streamlit Frontend** (`ai-travel-guide-frontend`)
5. İstenilen ortam değişkenlerini doldurun:
   - `CLOUDINARY_NAME` → Cloudinary Cloud Name
   - `CLOUDINARY_KEY` → Cloudinary API Key
   - `CLOUDINARY_SECRET` → Cloudinary API Secret

Blueprint, frontend servisi için `STRAPI_INTERNAL_HOSTPORT` değerini otomatik üretir. Bu değer Streamlit'in Strapi'ye Render private network üzerinden bağlanmasını sağlar.

### Adım 3: Strapi Backend Ortam Değişkenleri (Render Dashboard)

Render Dashboard'da **ai-travel-guide-strapi** servisine gidin ve **Environment** sekmesinde şu değişkenleri ekleyin:

| Değişken | Değer |
|----------|-------|
| `UPLOAD_PROVIDER` | `cloudinary` *(render.yaml içinde otomatik tanımlı)* |
| `CLOUDINARY_NAME` | *(Cloudinary Cloud Name)* |
| `CLOUDINARY_KEY` | *(Cloudinary API Key)* |
| `CLOUDINARY_SECRET` | *(Cloudinary API Secret)* |

### Adım 4: Strapi Admin Panel Kurulumu

Deploy tamamlandıktan sonra:

1. `https://ai-travel-guide-strapi.onrender.com/admin` adresine gidin.
2. İlk yönetici hesabını oluşturun.
3. **Settings > API Tokens** bölümünden yeni bir token oluşturun.
4. **Settings > Users & Permissions > Public** rolünde Cities ve Places için `find` ve `findOne` izinlerini verin.

### Adım 5: Otomasyon ile Veri Yükleme

Lokaldeki otomasyon scriptini Render Strapi'ye bağlayarak veri yükleyin:

```bash
# automation/.env dosyasını güncelleyin:
# STRAPI_URL=https://ai-travel-guide-strapi.onrender.com
# STRAPI_API_TOKEN=render_strapi_api_tokeniniz

cd automation
python main.py
```

### Adım 6: Kontrol

Her iki servis de çalıştığında:
- **Strapi Admin:** `https://ai-travel-guide-strapi.onrender.com/admin`
- **Streamlit Frontend:** `https://ai-travel-guide-frontend.onrender.com`

> ⚠️ **Not:** Render'ın ücretsiz planında servisler 15 dakika kullanılmadığında uyku moduna geçer. İlk erişimde ~30 saniye bekleme olabilir.
