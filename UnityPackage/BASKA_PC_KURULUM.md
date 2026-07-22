# AI Engineer - Başka PC Kurulumu

> Qwen hesabı, ChatGPT Plus/Codex girişi ve çevrim dışı Ollama dönüşü için
> [MODEL_VE_OTONOM_KULLANIM.md](MODEL_VE_OTONOM_KULLANIM.md) belgesindeki
> **Başka bilgisayar** bölümünü de uygula.

Bu belge `AIEngineer-Complete.unitypackage` paketini başka bir bilgisayarda
kurmak ve isteğe bağlı Python/Ollama özelliklerini çalıştırmak için hazırlanmıştır.

## 1. Gereksinimler

- Unity 6 veya daha yeni bir sürüm.
- Test edilen Unity sürümü: `6000.3.18f1`.
- Yerel AI özellikleri kullanılacaksa Python 3.
- Yerel metin ve görsel modeller kullanılacaksa Ollama.

Unity araçları ve örnek sahne Python ya da Ollama kurulmadan da kullanılabilir.

## 2. Unity paketini aktar

Eski bilgisayardaki aşağıdaki dosyayı USB, bulut depolama veya ağ üzerinden yeni
bilgisayara kopyala:

```text
AIEngineer-Complete.unitypackage
```

## 3. Unity paketini içe aktar

1. Yeni bilgisayarda Unity 6 ile hedef projeyi aç.
2. Unity menüsünden **Assets > Import Package > Custom Package** seçeneğini aç.
3. `AIEngineer-Complete.unitypackage` dosyasını seç.
4. Açılan listede **Import All** düğmesine bas.
5. Unity'nin script derlemesini tamamlamasını bekle.

Paket varsayılan olarak `Assets/AIEngineer` klasörüne kurulur.

## 4. AI Engineer arayüzünü aç

Unity üst menüsünden aşağıdaki pencereyi aç:

```text
AI Engineer > Control Center
```

Control Center içerisinde görev seçimi, prompt alanı, yanıt önizleme, güvenlik
kontrolleri ve yerel backend ayarları bulunur.

## 5. Python backend'i çıkart

Yerel planlama, görsel analiz, öğrenme hafızası ve Python testleri kullanılacaksa
paket içindeki şu ZIP dosyasını bul:

```text
Assets/AIEngineer/Documentation/AIEngineer-Python-Backend.zip
```

ZIP dosyasını Unity projesinin `Assets` klasörü içine çıkartma. Projenin yanında
`AIEngineerBackend` adında ayrı bir klasöre çıkart:

```text
UnityProjen/
├── Assets/
├── Packages/
├── ProjectSettings/
└── AIEngineerBackend/
    ├── Source/
    ├── Data/
    ├── ai_config.json
    └── main.py
```

Beklenen sunucu dosyası:

```text
AIEngineerBackend/Source/Server/autonomous_server.py
```

## 6. Proje yolunu ayarla

`AIEngineerBackend/ai_config.json` dosyasını aç. `project_root` değerini yeni
bilgisayardaki Unity proje yoluna göre değiştir:

```json
{
  "project_root": "D:/UnityProjects/YeniProje"
}
```

Windows yolunda `/` kullanmak kaçış karakteri sorunlarını önler.

## 7. Python'u doğrula

PowerShell veya Komut İstemi açıp çalıştır:

```powershell
py -3 --version
```

Bir Python 3 sürümü görünmüyorsa Python 3 kur ve Windows Python Launcher
seçeneğinin etkin olduğundan emin ol. Temel backend yalnızca Python standart
kütüphanelerini kullanır; ek bir `pip install` işlemi gerekmez.

## 8. Backend klasörünü Unity'ye tanıt

1. Unity'de **AI Engineer > Control Center** penceresini aç.
2. **Choose backend folder** düğmesine bas.
3. Çıkarttığın `AIEngineerBackend` klasörünü seç.
4. **Start local engine** düğmesine bas.

Başarılı olduğunda pencerenin üst bölümünde şu durum görünür:

```text
LOCAL ENGINE ONLINE
```

Sunucu varsayılan olarak yalnızca bu bilgisayarda şu adreste çalışır:

```text
http://127.0.0.1:8080
```

## 9. Ollama modellerini kur

Yerel metin/kod ve görsel analiz özellikleri için Ollama'yı kur. Ardından:

```powershell
ollama pull qwen3:30b
ollama pull llava:7b
```

Modellerin kurulduğunu kontrol etmek için:

```powershell
ollama list
```

AI Engineer kullanılırken Ollama servisinin çalışıyor olması gerekir.

## 10. Örnek sahneyi aç

Türk mitolojisi temalı mobil marble-shooter örneği şurada bulunur:

```text
Assets/AIEngineerGenerated/Games/ReferenceZumaPrototype/ReferenceZumaPrototype.unity
```

Sahneyi çift tıklayıp Unity Play düğmesine basabilirsin.

## Sorun giderme

### Control Center menüsü görünmüyor

- Unity Console'da C# derleme hatası olup olmadığını kontrol et.
- Paket içe aktarma işleminin tamamen bittiğinden emin ol.
- `Assets > Refresh` çalıştır.

### Local engine başlamıyor

- `Choose backend folder` ile seçilen klasörün içinde
  `Source/Server/autonomous_server.py` bulunduğunu doğrula.
- `py -3 --version` komutunun çalıştığını kontrol et.
- Unity Console'daki `[AI]` ile başlayan hata mesajını incele.

### Yerel model yanıt vermiyor

- Ollama'nın açık olduğunu kontrol et.
- `ollama list` çıktısında `qwen3:30b` ve `llava:7b` modellerini doğrula.
- `ai_config.json` içindeki model ve endpoint ayarlarını kontrol et.

### Unity projesi farklı diskte

Bu sorun değildir. `ai_config.json` içindeki `project_root` değerini doğru Unity
projesine ayarla ve Control Center'dan doğru backend klasörünü yeniden seç.
