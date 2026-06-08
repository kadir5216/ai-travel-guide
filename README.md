# YZ Destekli Gezi Rehberi (AI Travel Guide)

Bu proje, yapay zeka destekli ve çok dilli çalışan modern bir gezi rehberi sistemidir. Dünyanın farklı şehirleri için gezi rehberi verilerini bir araya getiren, yapay zeka ile açıklama çevirilerini ve mekan görsellerini zenginleştiren, çok dilli (Türkçe ve İngilizce) olarak saklayan ve kullanıcıya modern bir Streamlit arayüzü ile sunan tam çalışan bir sistemdir.

---

## Kullanılan Teknolojiler

* **Strapi CMS (Backend):** Headless CMS olarak veri yönetimini sağlar. REST API sunar.
* **Streamlit (Frontend):** Modern, duyarlı ve dinamik web arayüzünü oluşturur.
* **Python (Automation & API):** Otomasyon akışlarını, veri doğrulamayı ve entegrasyonu yönetir.
* **deep-translator:** Türkçe açıklamaları otomatik olarak İngilizceye çevirir.
* **Pollinations AI:** Mekan ismine göre yapay zeka ile görsel oluşturur.
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
│   ├── strapi_api.py          # Strapi API entegrasyonu (Şehir/Mekan oluşturma, Görsel yükleme)
│   ├── translator.py          # Türkçe açıklamaları İngilizceye çeviren modül
│   ├── image_generator.py     # Pollinations AI ile görsel üreten modül
│   ├── requirements.txt       # Otomasyon bağımlılıkları
│   └── .env.example           # Otomasyon çevre değişkenleri şablonu
│
├── frontend-streamlit/
│   ├── app.py                 # Streamlit arayüz kodları
│   ├── api.py                 # Strapi'den veri çeken API istemcisi
│   ├── requirements.txt       # Streamlit bağımlılıkları
│   └── .env.example           # Streamlit çevre değişkenleri şablonu
│
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
   * **name** (Text - Short Text, *Required*)
   * **country** (Text - Short Text, *Required*)
   * **short_info** (Text - Long Text)

2. **Places (Mekanlar)**:
   * **name** (Text - Short Text, *Required*)
   * **description_tr** (Text - Long Text, *Required*)
   * **description_en** (Text - Long Text)
   * **rating** (Decimal, örn: 4.8)
   * **cover_image** (Media - Single media, *Images only*)
   * **city** (Relation - **Place** belongs to one **City** | `Places` has one `City`, `Cities` has many `Places` seçeneğini seçin)

*Her iki içerik tipini oluşturduktan sonra sağ üstteki **Save** butonuna basarak sunucunun yeniden başlamasını bekleyin.*

#### C. API Token Oluşturma
Otomasyonun Strapi API'ye erişebilmesi ve görsel yükleyebilmesi için bir erişim anahtarı oluşturmalısınız:
1. Strapi Admin Panelinde **Settings > API Tokens > Create new API Token** yolunu izleyin.
2. Token adı olarak **"AI Travel Token"** girin.
3. Token Type değerini **Custom** seçin.
4. **Permissions (Yetkiler)** kısmında aşağıdakileri işaretleyin:
   * **Cities:** `find`, `findOne`, `create`, `update`
   * **Places:** `find`, `findOne`, `create`, `update`
   * **Upload (Medya):** `upload` (Görsellerin yüklenebilmesi için gereklidir)
5. Sayfayı kaydedin. Ekranınızda görünecek olan Token'ı kopyalayıp güvenli bir yere kaydedin.

---

### 2. Environment Variables (Çevre Değişkenleri)

Projede hassas bilgileri (URL'ler, Token'lar vb.) gizli tutmak için `.env` dosyaları kullanılmaktadır. Dosyaları şablonlardan türeterek oluşturabilirsiniz.

#### Python Otomasyon Klasörü (`automation/`)
`automation/` klasöründe yer alan `.env.example` dosyasını kopyalayıp `.env` adında yeni bir dosya oluşturun ve içeriğini doldurun:
```env
STRAPI_URL=http://localhost:1337
STRAPI_API_TOKEN=kopyaladiginiz_api_token_degeri
```

#### Streamlit Klasörü (`frontend-streamlit/`)
`frontend-streamlit/` klasöründe yer alan `.env.example` dosyasını kopyalayıp `.env` adında yeni bir dosya oluşturun ve içeriğini doldurun:
```env
STRAPI_URL=http://localhost:1337
```

---

## Çalıştırma Adımları

### 1. Python Otomasyonunu Çalıştırma
Otomasyon, `places.json` verilerini alarak Türkçe açıklamaları İngilizceye çevirir, yapay zeka ile görsel üretir ve bunları Strapi backend veritabanına kaydeder.

Sanal ortam oluşturup gerekli kütüphaneleri yükleyin ve çalıştırın:
```bash
# automation/ dizininde çalıştırın
cd automation
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 2. Streamlit Çalıştırma
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

*(Lütfen `REPO_URL` yerine kendi oluşturduğunuz GitHub Repository linkini yazın).*
