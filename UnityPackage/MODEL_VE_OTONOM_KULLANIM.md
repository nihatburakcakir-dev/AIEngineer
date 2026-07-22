# Model, Hesap ve Otonom Kullanım

Bu belge güncel Control Center model akışının ana kaynağıdır.

## Model seçenekleri

| Control Center seçeneği | İnternet ve hesap varsa | İnternet/hesap yoksa |
|---|---|---|
| Yerel (Ollama) | Kullanılmaz | `qwen3:30b` |
| Qwen (hesap > Codex) | Qwen Code kullanıcı sağlayıcısı | Codex hesabı denenir; yoksa iş durur |
| Codex Plus (hesap > Qwen) | ChatGPT hesabıyla Codex CLI | Qwen hesabı denenir; yoksa iş durur |
| Bulut (API anahtarı) | OpenRouter | Otomatik dönüş yok |

Yerel Ollama, doğrulanmış değişiklik setleriyle kod, sahne, prefab, material,
efekt ve arka plan işlemlerini uygulayabilir. Her yerel işte Unity snapshot
alır, C# derlemesini doğrular ve hata halinde otomatik geri alır. Yerel model;
seçili scriptler, proje bağlamı ve Unity paket dokümantasyonundan alınan sınırlı
ilgili kesitlerle birlikte plan üretir. Görsel analiz `llava:7b` üzerinden
yapılır. Hesap seçeneklerinde birinci hesap erişilemezse diğer hesap denenir;
ikisi de erişilemezse o hesap işi uygulanmadan durur.

## Qwen hesabı veya sağlayıcısı

1. Control Center'da **Qwen Code terminalini aç** düğmesine bas.
2. Terminalde `/auth` çalıştır.
3. Kendi API anahtarın, Coding Plan hesabın veya desteklenen sağlayıcını seç.
4. Control Center'da **Qwen (hesap > Codex)** seç.

Qwen.ai sitesine Gmail ile giriş yapmış olmak tek başına Qwen Code'u artık
etkinleştirmez. Control Center'daki **Qwen hesabını bağla (tarayıcı)** düğmesi
ModelStudio giriş sayfasını ve Qwen terminalini birlikte açar. Tarayıcıdaki
giriş sağlayıcıya aittir; kullanıcı adı veya şifre Unity'ye yazılmaz ya da
kaydedilmez. Girişten sonra terminalde `/auth` ile **Alibaba ModelStudio >
Coding Plan** veya sahip olduğun API anahtarı seçeneğini tamamla; ardından
**Qwen bağlantısını kontrol et** düğmesi etkin bağlantıyı gösterir.

Qwen Code açık kaynak bir istemcidir. Qwen OAuth ücretsiz model kotası
15 Nisan 2026'da kaldırılmıştır; değişiklik uygulamak için kendi hesabın,
Coding Plan'ın veya desteklenen sağlayıcın gerekir. Hesap yoksa Control Center
üzerinden **Yerel (30B / otonom)** seçeneği seçilerek yerel Ollama ile aynı
güvenli değişiklik/geri alma işlem hattı kullanılabilir.
Kimlik bilgileri Unity sahnesine, `ai_config.json` dosyasına veya kaynak koduna
yazılmaz.

## ChatGPT Plus ile Codex

1. Control Center'da **Codex Plus girişini aç** düğmesine bas.
2. Açılan `codex login` terminali ve tarayıcı akışını tamamla.
3. Gerekirse terminalde `codex login status` ile kontrol et.
4. Control Center'da **Codex Plus (hesap > Qwen)** seç.

ChatGPT Plus, Codex CLI kullanımını içerir; bu akış için ayrı API anahtarı
gerekmez. Codex oturumu internet yoksa veya hata verirse Qwen hesabı denenir;
yerel Ollama, Control Center'da ayrı olarak seçildiğinde hesap sağlayıcılarından
bağımsız biçimde değişiklik uygulayabilir.

## Genel yerel Unity ajanı

Control Center'daki **Yerel modele gönder** düğmesi hazır komut eşleştiren bir
şablon çalıştırmaz. `qwen3:30b`; serbest Türkçe veya İngilizce isteği, aktif
sahne özeti, seçili varlıklar, script bağlamı ve varsa referans görsel analiziyle
birlikte değerlendirir.

- Soru veya açıklama isteğinde `answer` yanıtı verir; projede değişiklik yapmaz.
- Oluşturma, düzeltme veya uygulama isteğinde doğrulanabilir bir `change_set`
  üretir. Unity ancak geçerli işlemleri snapshot, derleme ve geri alma hattından
  geçirerek uygular.
- `C:\AIEngineer\Documents\Unity\UnityDocumentation\Documentation` altındaki
  çevrimdışı Unity belgeleri istekle ilişkili paragraflar ve kod örnekleri
  bulunarak modele eklenir. Projeye ait belgeler ve aktif sahne bilgisi önceliklidir.
- Referans görsel tek parça dekor olarak kopyalanmak zorunda değildir. Modelden
  eylem istendiğinde yön, ekran oranı, Canvas, düzen ve etkileşimleri yorumlayıp
  düzenlenebilir Unity UI öğeleri ve gerçek `Button` davranışı planlaması beklenir.

Modelin doğrudan kontrolsüz dosya yazmasına izin verilmez. Eksik veya yarım JSON,
boş işlem listesi ve desteklenmeyen işlem manifesti uygulanmadan reddedilir.

## Dosya müdahalesi nasıl yapılır?

Yerel Ollama, Qwen ve Codex aktif projeyi okuyabilir. Güvenlik ve geri alma
için modelin doğrudan kontrolsüz yazmasına izin verilmez. Bunun yerine model
şunları içeren `ai-engineer.change-set/v1` manifesti üretir:

- tam C# dosyası yazma veya kesin metin değiştirme;
- klasör, sahne ve GameObject oluşturma;
- component ve serialized property ekleme;
- prefab, material ve particle effect oluşturma;
- görselden 2D/3D karakter prefabı üretme;
- oyun prototipi oluşturma ve sahneyi kaydetme.

Unity her işten önce snapshot alır, dosyaları uygular, C# derlemesini bekler,
hata varsa en fazla seçilen sayıda onarır, Play Mode kontrolünü çalıştırır ve
başarısız işte otomatik geri alır. **Son işlemi geri al** düğmesi son transaction'ı
elle de geri çevirir.

## Oyuna özellik ekleme

1. Hedef sahneyi aç ve ilgili varlıkları Project penceresinde seç.
2. **Oyunlar** veya **Oluştur** bölümünü seç.
3. Davranış, mobil/masaüstü hedefi, UI, efekt ve kabul koşullarını yaz.
4. Gerekirse referans görsel seç.
5. Modeli seçip **Yerel modele gönder** düğmesine bas.
6. HIGH riskli planı önizlemeden sonra onayla; diğer planlar Tam Otonom açıksa
   kendiliğinden ilerler.

Örnek:

```text
ReferenceZumaPrototype sahnesine mobil bomba topu ekle. Çarptığı topun iki
yanındaki topları da yok etsin, Türk mitolojisi temalı kısa mavi ateş efekti ve
ekran sarsıntısı kullansın. HUD safe-area içinde kullanım sayısını göstersin.
C# derlemesini ve Play Mode'da skor artışını doğrula.
```

## Oyun giriş UI'ı

Oyunun ilk ekranı, temasını ve oyuncunun ne yapacağını ilk bakışta anlatmalıdır.
**Oluştur** alanına aşağıdaki gibi bir istek yazın. Sistem mobil safe-area kullanan;
oyun adı, amaç, açıklama ve tek ana eylem düğmesi bulunan bir başlangıç ekranı
oluşturur. `Assets/...prefab` yolu verirseniz ekran bir prefab olarak kaydedilir;
vermezseniz aktif sahneye eklenir.

```text
Türk mitolojisi temalı mobil top patlatma oyunum için giriş UI'ı oluştur.
Başlık “Gök Kurt: Ateş Yolu”, açıklama “Renkli küreleri eşleştir, kutsal
ormandaki mavi ateşi koru.”, düğme “MACERAYA BAŞLA” olsun. Lacivert-mavi ateş
teması kullan ve Assets/AIEngineerGenerated/UI/GokKurtStart.prefab olarak kaydet.
```

## Başka bilgisayar

1. `AIEngineer-Complete.unitypackage` paketini içe aktar.
2. `Documentation/AIEngineer-Python-Backend.zip` dosyasını proje dışındaki
   `AIEngineerBackend` klasörüne çıkar.
3. Python 3, Ollama, `qwen3:30b` ve `llava:7b` kur.
4. Qwen Code isteniyorsa resmî Windows kurucusunu kullan:

```powershell
irm https://qwen-code-assets.oss-cn-hangzhou.aliyuncs.com/installation/install-qwen-standalone.ps1 | iex
```

5. Codex/ChatGPT hesabı isteniyorsa resmî Codex CLI kurucusunu kullan:

```powershell
$env:CODEX_NON_INTERACTIVE=1; irm https://chatgpt.com/codex/install.ps1 | iex
codex login
```

6. Control Center'da backend/Python yollarını seçip yerel motoru başlat.
7. CLI yolu otomatik bulunmazsa **Qwen yolunu seç** veya **Codex yolunu seç**.

## Sorun giderme

- Backend `Source/Server/autonomous_server.py` içermelidir.
- Servis yalnızca `http://127.0.0.1:8080` adresinde çalışır.
- Qwen hesabını değiştirmek için Qwen terminalinde `/auth` kullan.
- Codex hesabını kontrol etmek için `codex login status` kullan.
- Hesapların ikisi de çalışmıyorsa o hesap isteği güvenle durur; gerekirse model
  açılır menüsünden **Yerel (30B / otonom)** seçilerek yerel işlem başlatılabilir.
