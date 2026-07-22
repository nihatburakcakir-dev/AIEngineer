# AI Engineer v0.3.0 — Sürüm Notları

Yayın tarihi: 22 Temmuz 2026  
Hedef branch: `develop`  
Unity uyumluluğu: Unity 6 / 6000.x

## Genel bakış

v0.3.0, AI Engineer projesini basit bir komut penceresinden; Unity projesini, aktif sahneyi, mevcut C# API'lerini, varlıkları ve yerel Unity dokümantasyonunu inceleyebilen, değişikliklerini işlem günlüğü içinde uygulayabilen yerel-öncelikli bir Unity üretim aracına dönüştürür.

Bu sürümün ana hedefi, model cevabını doğrudan dosyalara yazmak yerine önce incelenebilir bir değişiklik setine çevirmek ve yalnızca doğrulamadan geçen işlemleri Unity'ye uygulamaktır.

## Başlıca yenilikler

### Yerel model ve iki aşamalı gameplay planlama

- Metin ve kod planlama için `qwen3:30b` desteği eklendi.
- Referans görsel analizi için yerel `llava:7b` desteği eklendi.
- Bomba, güçlendirme, mermi, düşman veya zincir reaksiyonu gibi gameplay istekleri iki aşamada ele alınır:
  1. Davranış, üretim/dağıtım, efekt/ses, mevcut sistem entegrasyonu ve kabul testleri çıkarılır.
  2. Bu mimariye bağlı çalıştırılabilir Unity değişiklik seti üretilir.
- Kod içeren planlar için yerel model cevap bütçesi artırıldı.
- Bozuk veya eksik JSON cevabı Unity'ye ulaşmadan yeniden planlanır.

### Projeye dayalı doğrulama

- Aktif sahnedeki gerçek GameObject yolları modele aktarılır.
- Projedeki C# sınıflarının public metot ve alanları küçük bir `script_api` özeti olarak çıkarılır.
- Modelin var olmayan `RemoveBall` benzeri metotları çağırması uygulamadan önce engellenir.
- `add_component` ve `set_property` işlemleri yalnızca gerçek Hierarchy nesnelerini hedefleyebilir.
- Eksik prefab, ses, materyal veya başka bir Unity asset yolu ön doğrulamada reddedilir.
- Yeni bir gameplay `MonoBehaviour` sahneye veya prefaba bağlanmamışsa değişiklik seti tamamlanmış kabul edilmez.
- İstenen rastgele davranışın kodu ve efekt bağlantıları bulunmadan gameplay planı uygulanmaz.

### Otonom uygulama ve geri alma

- Dosya işlemleri, Unity işlemleri ve doğrulamalar ayrı aşamalarda yürütülür.
- C# dosyaları yazıldıktan sonra Unity derlemesi beklenir.
- Derleme başarılıysa sahne, prefab, materyal, efekt ve component işlemleri uygulanır.
- İstenirse Play Mode doğrulaması çalıştırılır.
- Hata Unity/derleyici tanılarıyla modele geri gönderilir.
- Düzeltme başarılı olmazsa işlem yedeğinden geri alınır.
- Son başarılı işlem Control Center üzerinden geri alınabilir.

### Güvenli Unity çıktı alanı

- AI Engineer paketinin kendi `Assets/AIEngineer` klasörü otonom değişikliklere kapalıdır.
- Oyun, karakter, UI ve diğer üretimler `Assets/AIEngineerGenerated` altında tutulur.
- Paket içindeki örnek bir sahne açıkken değişiklik istenirse sahne önce düzenlenebilir proje alanına kopyalanır.
- Eski `Assets/AIEngineer/GeneratedGames` ve `GeneratedCharacters` yolları otomatik olarak yeni güvenli çıktı alanına yönlendirilir.

### Mobil UI ve referans görsel iş akışı

- Model, referans görsel için `rebuild`, `background` veya `hero` düzenini seçebilir.
- Görsel yerleşimi `contain` veya `cover` olarak belirlenebilir; görüntüler artık zorla esnetilmez.
- CTA konumu dokuz normalize anchor seçeneğiyle model tarafından belirlenebilir.
- Başlat CTA'sı gerçek Unity Button olarak üretilir.
- Buton mevcut gameplay kökünü görünür yapabilir veya geçerli bir Unity sahnesini açabilir.
- Mevcut oluşturulmuş menü model kararıyla güvenli şekilde yenisiyle değiştirilebilir.
- Yatay ve dikey mobil CanvasScaler düzenleri desteklenir.

### Model sağlayıcıları

- Yerel Ollama çalışma modu ana çalışma biçimidir.
- Qwen Code hesap bağlantısı ve terminal akışı eklendi.
- Codex CLI hesap bağlantısı eklendi.
- Hesap tabanlı sağlayıcılar kullanıldığında mutasyon yetkisi doğrudan modele verilmez; model yine incelenebilir değişiklik seti üretir.
- Bulut kullanımı isteğe bağlıdır ve API anahtarı olmadan yerel çalışma devam eder.

### Unity üretim yetenekleri

- C# dosyası oluşturma ve kontrollü metin değiştirme
- GameObject oluşturma
- Component ekleme ve serialized alan bağlama
- Prefab ve materyal oluşturma
- ParticleSystem tabanlı efekt oluşturma
- Mobil giriş UI'si oluşturma
- 2D/3D karakter prefabı oluşturma
- Oyun prototipi ve örnek marble-shooter sahneleri oluşturma
- Sahne kaydetme, doğrulama ve işlem bazlı geri alma

## Control Center kullanımı

Unity menüsünden `AI Engineer > Control Center` penceresini açın.

1. Çalışma alanını seçin: Oluştur, Analiz, Onar, Oyunlar veya Hafıza.
2. İsteğinizi doğal Türkçe veya İngilizce yazın.
3. Gerekirse referans görsel seçin.
4. Yerel model veya hesap sağlayıcısını seçin.
5. Önce plan oluşturun ve işlemleri inceleyin.
6. Yalnızca doğru hedef ve yolları içeren planı otonom uygulayın.
7. Console, derleme ve Play Mode sonuçlarını kontrol edin.
8. Gerekirse `Son işlemi geri al` seçeneğini kullanın.

## Kurulum ve yükseltme
