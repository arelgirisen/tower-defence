# Tower Defense Deluxe - 10 Levels

GitHub'a yükleyebileceğin, `pygame` ile yapılmış tek klasörlük bir tower defense oyunu.

## Yeni eklenenler
- Ana menü
- Devam Et sistemi
- JSON kayıt sistemi (`savegame.json`)
- Ayarlar ekranı
- Daha profesyonel panel / HUD arayüzü
- Duraklatma ekranı
- Oyun sonu özet ekranı

## Özellikler
- 10 bölüm / 10 wave
- 3 farklı kule:
  - Blaster
  - Sniper
  - Rapid
- Kule geliştirme ve satma sistemi
- Farklı düşman türleri:
  - normal
  - fast
  - tank
  - boss
- Harita üstünde yerleştirme
- Dış asset gerektirmez, her şey kodla çizilir
- Otomatik kayıt ve manuel kayıt

## Kurulum
```bash
pip install -r requirements.txt
python main.py
```

## Kontroller
- Sol tık: kule yerleştir / kule seç / menü düğmeleri
- `1` = Blaster
- `2` = Sniper
- `3` = Rapid
- `SPACE` = wave başlat
- `S` = kaydet
- `ESC` = duraklat / geri dön
- `R` = yeni oyun başlat

## Kayıt sistemi
- Oyun sırasında kayıt dosyası proje klasöründe `savegame.json` olarak oluşur.
- Menüde **Devam Et** ile kaldığın yerden devam edebilirsin.
- Ayarlar ve en iyi ilerleme `settings.json` içinde tutulur.

## GitHub'a yükleme
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin SENIN_REPO_LINKIN
git push -u origin main
```

## Proje yapısı
- `main.py` → oyunun ana dosyası
- `requirements.txt` → gereken paketler
- `README.md` → açıklama
- `savegame.json` → oyun kaydı (oynadıkça oluşur)
- `settings.json` → ayarlar ve meta kayıt (oynadıkça oluşur)
