# LibreCours PC

Bibliothèque gratuite de cours de Physique-Chimie avec collecte automatique de ressources dont la licence autorise explicitement la réutilisation.

## Installation
```bash
python -m venv .venv
pip install -r requirements.txt
cp .env.example .env
python app.py
```
Puis ouvrir http://127.0.0.1:5000

## Collecte
Modifier `data/sources.json`, puis lancer:
```bash
python scripts/collector.py
```

Le collecteur exige une licence identifiable (ex. CC BY 4.0 ou domaine public). Une ressource sans licence claire est laissée de côté. Les nouvelles ressources sont mises en attente de validation.

## Important
Un PDF accessible gratuitement sur Internet n'est pas automatiquement libre de redistribution. Le site conserve la source et la licence pour chaque ressource.


## Sources de départ
Le registre inclut OpenStax, PhET et OER Commons. Une plateforme peut proposer
plusieurs licences : le robot doit donc vérifier la licence de chaque ressource.

## Application Android

Le dossier `android/` contient une enveloppe Android WebView compilable. L’APK `releases/librecours-mobile-debug.apk` ouvre l’interface Flask LibreCours à partir de l’adresse du serveur saisie au premier lancement. Pour un téléphone physique, démarrez Flask avec `python app.py`, rendez le port 5000 accessible sur le réseau local, puis saisissez l’adresse de l’ordinateur, par exemple `http://192.168.1.10:5000`. L’adresse `http://10.0.2.2:5000` est prévue pour l’émulateur Android.

### Règle de publication
- Licence claire permettant la redistribution : éligible à validation.
- Licence avec restriction NonCommercial : publication seulement si les conditions
  du site sont compatibles et après vérification.
- Licence absente ou ambiguë : pas de republication automatique.
- Conserver auteur, titre, licence, URL source et date de collecte.
