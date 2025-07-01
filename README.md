# EVA2SPORT 🏀⚽

Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive.

## 🚀 Installation rapide

### Prérequis
- **Windows 10/11** avec PowerShell
- **Python 3.10+** (sera installé automatiquement si nécessaire)
- **Git** pour cloner le repository

### Installation en 3 étapes

```powershell
# 1. Cloner le projet
git clone https://github.com/2nzi/EVA2SPORT.git
cd EVA2SPORT

# 2. Lancer l'installation automatique
.\install.ps1

# 3. Démarrer Jupyter
uv run jupyter lab ou utiliser IDE avec le notebook
```

**C'est tout !** 🎉 L'installation se charge de :
- ✅ Détecter votre GPU automatiquement  
- ✅ Installer Python 3.10 si nécessaire
- ✅ Télécharger le modèle SAM2
- ✅ Configurer l'environnement complet

### Si vous avez des problèmes

```powershell
# Pour réinstaller complètement
.\install.ps1 -Force

# Si vous préférez pip à uv
.\install.ps1 -UsePip

# Si vous n'avez pas de GPU NVIDIA
.\install.ps1 -CPUOnly
```

## 📊 Utilisation

Après installation, ouvrez un des notebooks :
- `notebook/SAM_inference.ipynb` - Segmentation basique
- `notebook/SAM_viz.ipynb` - Visualisation avancée

## 💡 Aide

- **Problème d'installation ?** Lancez `.\install.ps1 -Force`
- **GPU non détecté ?** Vérifiez vos drivers NVIDIA
- **Erreur PowerShell ?** Lancez en tant qu'administrateur