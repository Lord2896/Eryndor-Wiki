# Eryndor Wiki

Mobilna encyklopedia serwera Minecraft **Eryndor Pixelmon**.

Repozytorium zawiera **wyłącznie publiczne treści wiki** i narzędzia do ich publikowania. Kod prywatnych modów nie jest tu potrzebny.

## Status

**Treść aktualizowana niezależnie od APK.** Wprowadzone poradniki:

- Eryndor Mastery 0.4.3
- Pixelmon Cooking (zasady i efekty; ukryte receptury są dostępne wyłącznie po odkryciu w grze)
- Mushroom Foraging 1.0.9 (Atlas bez list gatunków i lokalizacji; sprzedaż oraz wymiany przez NPC)
- Pixelmon Fishing (zasady łowienia i Atlas; lista gatunków oraz lokalizacje są ukryte i odkrywane wyłącznie w grze)
- Codzienne zlecenia Daily Quests — potwierdzona pula nagród i postęp
- Eryndor Bingo 4×4 — system 24 h, nakładka GUI 0.2.8
- Kasyno 777 + CoinToShop
- Wprowadzenie do korzystania z wiki

Niepublikowane jako gotowe: Eryndor Expeditions, Rifts, Eryndor Identity, Pixelmon QoL, Dungeon, Party Games, Gymy, wątek Trade Chain oraz niepełne kroniki. Dołożymy je po ostatecznym potwierdzeniu reguł i balansu.

**Zasada:** nigdy nie publikujemy ukrytych receptur Cooking ani list gatunków ryb i grzybów, ich rzadkości, występowania czy wskazówek zdradzających odkrycia Atlasów. Sprzedaż i wymiana grzybów jest obsługiwana przez NPC — nie polecamy graczom wewnętrznych komend. Nie tworzymy fikcyjnych szczegółów (np. szans automatu, niezatwierdzonych lokacji czy nieznanych nagród). Przy konfiguracji modyfikowalnej opis jasno wskazuje domyślne wartości i odsyła do aktualnego GUI serwera. 

## Automatyczne aktualizacje

- `articles.json` — źródło artykułów, obecna wersja `revision`.
- `build_pages.py` — walidacja i budowanie plików na GitHub Pages.
- `.github/workflows/deploy-pages.yml` — publikacja po każdej zmianie artykułów.
- `manifest.json` — plik generowany automatycznie, zawiera `revision` i SHA-256 artykułów.

Aplikacja Android 0.3 sprawdza przy uruchomieniu:
`https://lord2896.github.io/Eryndor-Wiki/manifest.json`
i pobiera `articles.json`, gdy jest dostępny. Zapisuje go offline.

**Przy zmianie artykułów zwiększ pole `revision` o jeden.** GitHub Actions automatycznie wygeneruje nowy manifest. Nowego APK potrzeba dopiero przy zmianie funkcji aplikacji.

## Jednorazowa konfiguracja GitHub Pages

W repozytorium GitHub: **Settings → Pages → Build and deployment → Source → GitHub Actions**.

Po uruchomieniu workflow adres publikacji powinien być:
[https://lord2896.github.io/Eryndor-Wiki/](https://lord2896.github.io/Eryndor-Wiki/).

Aplikacja jest przeznaczona do czytania offline, a publiczna strona udostępnia jej treść. Publikacja jest darmowa w ramach limitów GitHub Pages.


## Daty artykułów i katalog plików (APK 0.4)

Każdy artykuł może mieć pole `updatedAt` z datą ostatniej **rzeczywistej** edycji treści w ISO 8601, np. `2026-10-14T15:43:38Z`. W aplikacji jest wyświetlane małym drukiem na dole, w polskim czasie (Warszawa). Samo zwiększenie globalnego numeru rewizji nie powinno zmieniać daty wszystkich artykułów.

W `articles.json` katalog pobrań znajduje się obok `articles` jako tablica `downloads`. Na początku jest pusta; nie publikujemy niegotowych linków.

Po przygotowaniu zasobu można dopisać wpis w takim formacie (to **instrukcja**, nie aktywny link):

```json
{
  "id": "eryndor-client-modpack",
  "category": "Mody klienckie",
  "title": "Paczka modów Eryndor",
  "description": "Niezbędne mody na komputer dla Minecraft 1.21.1 / Pixelmon 9.3.16.",
  "version": "1.0",
  "url": "https://ADRES-OFICJALNEGO-PLIKU-HTTPS",
  "updatedAt": "2026-10-14T15:43:38Z"
}
```

Dozwolone kategorie: `Resourcepacki`, `Mody klienckie`, `Inne`.
Link musi być prawidłowym adresem `https://`. Kliknięcie otwiera plik w zewnętrznej przeglądarce Androida.

Po zmianie katalogu lub artykułu:
1. Zwiększ `revision` o 1.
2. Jeśli zmieniono artykuł, zaktualizuj `updatedAt` tylko w tym artykule.
3. Jeśli zmieniono konkretny plik, zaktualizuj `updatedAt` tylko w tym wpisie.
4. GitHub Actions opublikuje nowy plik danych; aplikacja 0.4 pobierze go przy następnym uruchomieniu.

**Uwaga:** aplikacja 0.3 nie ma zakładki Pliki ani podpisów dat. Do korzystania z tych funkcji należy jednorazowo zainstalować APK 0.4; późniejsze zmiany artykułów i plików już nie wymagają instalacji nowego APK.
