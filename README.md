Reconnaissance d’émotions faciales (Keras/TensorFlow)

Classer des visages en 7 émotions : anger, disgust, fear, happy, neutral, sad, surprise.

1) Installation (env. virtuel conseillé)
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install tensorflow numpy matplotlib pillow h5py opencv-python-headless
# SciPy pour l’augmentation d’images :
python -m pip install "scipy==1.10.1"  # si Python 3.8/3.9 ; sinon: python -m pip install scipy

2) Données (structure)
dataset/
  ├─ train/ (anger, disgust, fear, happy, neutral, sad, surprise)
  └─ val/   (anger, disgust, fear, happy, neutral, sad, surprise)


Astuce : supprime les dossiers parasites (.ipynb_checkpoints) dans dataset/.

3) Lancer le notebook

Ouvre emotion-detector.ipynb dans VS Code.

Si pas de GPU, mets en première cellule :

import os; os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


Exécute les cellules dans l’ordre : data → modèle → compile → fit.

4) Sauvegarde / chargement
# Sauver
model.save("model.keras")         # format recommandé
model.save_weights("weights.h5")  # poids seuls (optionnel)

# Charger
from tensorflow import keras
model = keras.models.load_model("model.keras", compile=False)