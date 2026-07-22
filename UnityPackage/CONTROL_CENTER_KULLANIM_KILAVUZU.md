# AI Engineer Control Center Kullanım Kılavuzu

> **Güncel otonom işleyiş ve Qwen/Codex hesap kurulumu:**
> [MODEL_VE_OTONOM_KULLANIM.md](MODEL_VE_OTONOM_KULLANIM.md) dosyasına bak.
> Aşağıdaki eski hazır-özellik örnekleri yalnızca örnek olarak korunmuştur;
> güncel sürüm, sürümlü değişiklik setiyle genel script/sahne/prefab/efekt üretip
> derleyebilir, onarabilir ve geri alabilir.

Bu kılavuz Unity içindeki **AI Engineer > Control Center** penceresinin ne işe
yaradığını ve bir oyuna yeni özellik eklemek için hangi adımların izleneceğini
açıklar.

## Control Center nasıl açılır?

Unity üst menüsünden:

```text
AI Engineer > Control Center
```

Pencerenin üstündeki `Türkçe / English` seçimi arayüz dilini değiştirir. Tercih
Unity tarafından saklanır.

## Sol menüler ne işe yarar?

### Oluştur

Yeni bir sistem, GameObject, prefab, script taslağı veya UI bileşeni planlamak
için kullanılır.

Örnek istekler:

```text
Oyuncu için can, hasar ve iyileşme sistemi oluştur.
Ana menü için mobil uyumlu ayarlar paneli oluştur.
Top mermileri için object pool sistemi oluştur.
```

### Analiz

Mevcut sahneyi veya scriptleri değiştirmeden önce incelemek için kullanılır.
Performans, eksik referans, mimari ve mobil uyumluluk sorunlarını belirler.

Örnek istekler:

```text
Aktif sahneyi performans açısından analiz et.
ZumaShooter scriptinde mobil giriş sorunlarını bul.
Sahnede eksik script ve prefab referansı var mı kontrol et.
```

### Onar

Bilinen bir hata veya bozuk davranış için güvenli düzeltme planı hazırlamak için
kullanılır. Hata mesajını ve beklenen davranışı açıkça yazmak gerekir.

Örnek istek:

```text
Android'de Ateş Et düğmesine basınca iki top atılıyor. UI dokunuşunun ikinci
atışı tetiklemesini engelle ve Play Mode'da doğrula.
```

### Oyunlar

Mevcut oyuna mekanik, efekt, özel top, combo, bölüm veya mobil UI özelliği ekleme
istekleri burada hazırlanır. Yeni bir oyun prototipi oluşturma istekleri de bu
sekmeden verilir.

### Hafıza

Daha önce bulunan risklerin ve alınan mühendislik kararlarının yeni plana dahil
edilmesini ister. Aynı hataların tekrar edilmesini azaltmak için kullanılır.

## Oyuna özellik nasıl eklenir?

1. Değiştirmek istediğin sahneyi Unity'de aç.
2. **AI Engineer > Control Center** penceresini aç.
3. Soldan **Oyunlar** menüsünü seç.
4. **Hazır görev** listesinden uygun görevi seç veya Talimat alanına kendi
   isteğini yaz.
5. **İncelenebilir plan oluştur** düğmesine bas.
6. Yanıt Önizleme alanında hedef sahne, scriptler, riskler ve doğrulama adımlarını
   kontrol et.
7. Plan desteklenen ve uygulanabilir bir özellikse **Onayla ve uygula** düğmesi
   etkinleşir. Düğmeye basıp son onayı verdiğinde Control Center aktif sahneyi
   değiştirir ve kaydeder.

**Onayla ve uygula** yalnızca Control Center içinde uygulama işleyicisi bulunan
özelliklerde etkinleşir. Diğer istekler inceleme amaçlı plan olarak kalır; bu
durumda yanıtın sonunda "otomatik uygulanmadı" yazısı görünür. Böyle bir planı
uygulamak için AI Engineer geliştirme oturumunu/Codex'i veya paketteki desteklenen
oluşturucu menülerini kullanabilirsin.

### Top patlamasında yıldırım örneği

Şu istek doğrudan desteklenir:

```text
Toplar her patladığında yukarıdan aşağıya yıldırım çaksın.
```

Plan oluşturulduktan sonra **Onayla ve uygula** düğmesine basılır. Control Center:

- Aktif sahneye `AI Feature - Ball Pop Lightning` nesnesini ekler.
- Mevcut renkli top patlama efektlerini izler.
- Her yeni patlamada `Lightning Hit Blue` efektini patlama noktasının üstünde
  oluşturur ve aşağı indirir.
- Özelliği sahneye kaydeder.

Bu özellik için projede şu prefabın bulunması gerekir:

```text
Assets/Matthew Guz/Hits Effects FREE/Prefab/Lightning Hit Blue.prefab
```

Kurulumu bağımsız olarak sınamak için şu menü kullanılabilir:

```text
AI Engineer > Games > Validate Ball-Pop Lightning
```

Test kısa süreliğine Play Mode'a girer, örnek bir top-vuruş parçacığı oluşturur,
yıldırımı arar ve sonucu Console'a `[AI Acceptance] PASS` veya `FAIL` olarak yazar.

## İyi bir özellik isteği nasıl yazılır?

İstek içinde şu beş bilgiyi vermek en iyi sonucu sağlar:

1. Hedef sahne veya oyun.
2. Eklenecek özelliğin davranışı.
3. Kullanılacak giriş yöntemi.
4. UI ve görsel beklenti.
5. Özelliğin tamamlandığını gösteren kabul koşulları.

### Özel top örneği

```text
ReferenceZumaPrototype sahnesine üç özel top ekle.

- Bomba topu: çarptığı topun sağındaki ve solundaki iki topu da yok etsin.
- Gökbörü topu: aynı renkteki bütün topları kısa mavi alev efektiyle temizlesin.
- Yavaşlatma topu: top zincirini 5 saniye yüzde 40 yavaşlatsın.
- Özel toplar normal toplardan farklı ikon ve parçacık efekti kullansın.
- Mobil Ateş Et düğmesi ve dokunmatik nişan alma çalışmaya devam etsin.
- Kullanım sayısı HUD üzerinde gösterilsin.
- Play Mode testinde her özel topun etkisi ve skor değişimi doğrulansın.
```

### Combo ve efekt örneği

```text
Arka arkaya 4 saniye içinde yapılan eşleşmeleri combo olarak say. Combo arttıkça
skor çarpanı 1x, 2x, 3x ve 4x olsun. Ekranın ortasında kısa combo yazısı, top
patlamasında renkli parçacık ve hafif kamera sarsıntısı göster. Efektler mobilde
performans sorunu oluşturmaması için object pool kullansın.
```

### Bölüm sistemi örneği

```text
Oyuna 10 bölümlük ilerleme sistemi ekle. Her bölümde zincir hızı ve renk sayısı
artsın. Bölüm başlangıç paneli, duraklatma, kazanma ve kaybetme ekranları mobil
safe-area içinde çalışsın. İlerleme yerel olarak kaydedilsin.
```

## Hazır Unity oluşturucuları

Control Center planlama ve inceleme ekranıdır. Pakette ayrıca doğrudan çalışan
oluşturucular bulunur:

```text
AI Engineer > Characters
AI Engineer > Games
AI Engineer > Package
```

- **Characters:** 2D/3D karakter placeholder prefab üretir.
- **Games:** desteklenen oyun prototiplerini oluşturur.
- **Package:** güncel AI Engineer varlıklarını `.unitypackage` olarak dışa aktarır.

## Backend ve Python durumu

Pencerenin sağında görünen:

- **Python Backend:** `Source/Server/autonomous_server.py` içeren çalışma klasörüdür.
- **Python Çalıştırıcı:** kullanılacak `python.exe` veya Windows `py` başlatıcısıdır.
- **Yerel motoru başlat:** `127.0.0.1:8080` adresindeki yerel servisi başlatır.

Üstte **YEREL MOTOR ÇEVRİMİÇİ** görünmüyorsa backend ya da Python yolu yanlış
olabilir. İlgili seçim düğmeleriyle doğru klasör/dosyayı seç ve tekrar başlat.

## Yanıt gelmiyorsa

1. **Console'u aç** düğmesine bas.
2. `[AI]` ile başlayan mesajı kontrol et.
3. Backend klasöründe `Source/Server/autonomous_server.py` olduğunu doğrula.
4. Python çalıştırıcısının mevcut olduğunu doğrula.
5. Yerel model gerekiyorsa Ollama'nın çalıştığını kontrol et.

## Güvenli kullanım

- Büyük değişiklikten önce Git commit veya proje yedeği oluştur.
- Önce **Analiz**, sonra **Oyunlar/Oluştur**, hata varsa **Onar** akışını kullan.
- Yanıt Önizleme içindeki dosya hedeflerini ve riskleri okumadan değişikliği
  uygulama.
- Özellik isteğine mutlaka Play Mode kabul koşulu ekle.
