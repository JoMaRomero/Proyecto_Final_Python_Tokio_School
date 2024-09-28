import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Instanciamos el servidor web de Flask y le indicamos la ruta absoluta para flask_sqlalchemy
app = Flask(__name__, instance_path = os.path.abspath("./database"))

# Indicamos el nombre del fichero y el nombre del fichero de bbdd
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///datos.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Iniciamos app para que Flask pueda usar db.
db = SQLAlchemy(app)