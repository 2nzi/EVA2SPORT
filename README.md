# EVA2SPORT 🏀⚽

Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive.

## 🚀 Installation rapide

### Prérequis
- **Windows 10/11** avec PowerShell
- **Python 3.10+** (sera installé automatiquement si nécessaire)
- **Git** pour cloner le repository
- **~5GB d'espace disque** (modèles + dépendances)
- **Connexion internet** pour téléchargements

### Installation en 3 étapes

```powershell
# 1. Cloner le projet
git clone https://github.com/2nzi/EVA2SPORT.git
cd EVA2SPORT

# 2. Lancer l'installation automatique
.\install.ps1

# 3. Démarrer Jupyter
uv run jupyter lab
# ou ouvrir les notebooks dans votre IDE préféré

```

**C'est tout !** 🎉 L'installation se charge de :
- ✅ Détecter votre GPU automatiquement  
- ✅ Installer Python 3.10 si nécessaire
- ✅ Télécharger le modèle SAM2
- ✅ Configurer l'environnement complet

*⏱️ Temps d'installation : 5-15 minutes selon votre connexion*

### Si vous avez des problèmes

```


## 📊 Utilisation

Après installation, ouvrez un des notebooks :
- `notebook/SAM_inference.ipynb` - Segmentation basique
- `notebook/SAM_viz.ipynb` - Visualisation avancée

### Premier test
```powershell
# Vérifier que tout fonctionne
uv run python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
```
```

## 5. **Ajouter section contact/support :**

```markdown
## 💡 Aide

- **Problème d'installation ?** Lancez `.\install.ps1 -Force`
- **GPU non détecté ?** Vérifiez vos drivers NVIDIA
- **Erreur PowerShell ?** Lancez en tant qu'administrateur

### Support
- 🐛 **Bugs** : [Ouvrir une issue](https://github.com/2nzi/EVA2SPORT/issues)
- 💬 **Questions** : [Discussions](https://github.com/2nzi/EVA2SPORT/discussions)
- 📧 **Contact** : []
```

## 6. **Optionnel : Badge de statut :**

En haut du README :
```markdown
# EVA2SPORT 🏀⚽

[![Install Status](https://img.shields.io/badge/install-automatic-green)](./install.ps1)
[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://python.org)
[![PyTorch](https://img.shields.io/badge/pytorch-2.5+-orange)](https://pytorch.org)

Pipeline de segmentation vidéo avec SAM2 pour l'analyse sportive.
```