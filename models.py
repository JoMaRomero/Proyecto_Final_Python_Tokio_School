from flask_login import UserMixin
from db import db

# Creamos una tabla de favoritos para hacer relacion many to many entre las tablas Usuarios y Cinema
# Ya que un usuario puede tener varios favoritos y una peli/serie puede tener varios usuarios.
fav = db.Table("fav",
                db.Column("id_usuario", db.Integer, db.ForeignKey("usuarios.id"), primary_key=True),
                db.Column("id_cinema", db.Integer, db.ForeignKey("cinema.id"), primary_key=True)
                )

# Creamos otra tabla como la anterior para las peliculas/series Vistas
vista = db.Table("vista",
                db.Column("id_usuario", db.Integer, db.ForeignKey("usuarios.id"), primary_key=True),
                db.Column("id_cinema", db.Integer, db.ForeignKey("cinema.id"), primary_key=True)
                )

# Creamos la clase de Usuarios
# Se le añade UserMixin para verificar si el usuario está o no logueado y si está activo
# Para comprobarlo, se usan cosas como usuario.is_authenticated y devuelve un boolean.
class Usuarios(UserMixin, db.Model):
    # No necesitamos indicar el nombre de la tabla ya que Flask-SQLAlchemy se encarga de coger
    # el nombre de la clase como nombre de tabla.
    #__tablename__ = "Usuarios"
    
    # Creamos los datos que queremos que contenga la tabla
    id = db.Column(db.Integer, primary_key=True)
    # admin se utilizará para identificar a los administradores de los usuarios
    admin = db.Column(db.Boolean, default=False, nullable = False)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    username = db.Column(db.String(25), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    
    # Dejamos al final la relación con la clase Cinema
    # Usamos back_populates para la relación inversa y así poder hacer referencia de un lado a otro,
    # en este caso usamos la palabra "usuarios" pero se puede escoger la que quiera.
    cine_fav = db.relationship("Cinema", secondary=fav, back_populates = "usuario_fav")
    cine_vista = db.relationship("Cinema", secondary=vista, back_populates = "usuario_vista")
    
    # Creamos el constructor y señalamos así los atributos que vamos a requerir al registrar usuario
    def __init__(self, admin, fullname, email, username, password):
        self.admin = admin
        self.fullname = fullname
        self.email = email
        self.username = username
        self.password = password
        print("Usuario creado con éxito")
    
    def __repr__(self): # Para mostrar datos sobre un objeto en depuración
        return f"<Usuario(id={self.id}, fullname={self.fullname}, username={self.username}, email={self.email})>"
        
    def __str__(self): # Para mostrar datos sobre un objeto
        return f"Usuario(id={self.id}, fullname={self.fullname}, username={self.username}, email={self.email})"

# Creamos la clase de Usuarios
class Cinema(db.Model):
    
    # Creamos los datos que queremos que contenga la tabla
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable = False)
    description = db.Column(db.String(1000), nullable = False)
    date = db.Column(db.Date, nullable = False)
    genre = db.Column(db.String(50), nullable = False)
    # Hacemos un boolean para saber si es pelicula o serie, siendo 0 pelicula y 1 serie.
    peli_serie = db.Column(db.Boolean, nullable = False)
    poster = db.Column(db.String(200), nullable = False)
    play = db.Column(db.String(200), nullable = False)
    
    # Relación con la tabla Usuarios
    usuario_fav = db.relationship("Usuarios", secondary=fav, back_populates = "cine_fav")
    usuario_vista = db.relationship("Usuarios", secondary=vista, back_populates = "cine_vista")
    
    # Creamos el constructor y señalamos así los atributos que vamos a requerir al registrar usuario
    def __init__(self, title, description, date, genre, peli_serie, poster, play):
        self.title = title
        self.description = description
        self.date = date
        self.genre = genre
        self.peli_serie = peli_serie
        self.poster = poster
        self.play = play
        print("Cinema creado con éxito")
    
    def __repr__(self): # Para mostrar datos sobre un objeto en depuración
        return f"<Cinema(id={self.id}, title={self.title}, date={self.date}, genre={self.genre})>"
        
    def __str__(self): # Para mostrar datos sobre un objeto
        return f"Cinema(id={self.id}, title={self.title}, date={self.date}, genre={self.genre}, peli_serie={self.peli_serie})"

# Creamos Pelicula que hereda de Cinema par añadirle las diferencias con Series.
class Pelicula(Cinema):
    # id heredada de Cinema
    id = db.Column(db.Integer, db.ForeignKey("cinema.id"), primary_key=True)
    # Indicamos la duración en minutos de la pelicula
    duration = db.Column(db.Integer, nullable=False)
    
    # Creamos el constructor de Pelicula, usando la herencia con Cinema pero sin solicitar
    # el valor de peli_serie ya que la indicaremos nosotros.
    def __init__(self, title, description, date, genre, poster, play, duration):
        super().__init__(title=title,
                         description=description,
                         date=date,
                         genre=genre,
                         poster=poster,
                         play=play,
                         peli_serie=False)
        self.duration = duration
        print("Pelicula creada con éxito")
        
    def __repr__(self): # Para mostrar datos sobre un objeto en depuración
        return f"<Pelicula(id={self.id}, title={self.title}, date={self.date}, genre={self.genre}, duration={self.duration})>"
    
    def __str__(self): # Para mostrar datos sobre un objeto
        return f"Pelicula(id={self.id}, title={self.title}, date={self.date}, genre={self.genre}, duration={self.duration})"
    
class Serie(Cinema):
    # id heredada de Cinema
    id = db.Column(db.Integer, db.ForeignKey("cinema.id"), primary_key=True)
    num_seasons = db.Column(db.Integer, nullable=False)
    num_episodes = db.Column(db.Integer, nullable=False)
    episode_duration = db.Column(db.Integer, nullable=False) # Duración en minutos
    
    # Creamos el constructor de Serie, usando la herencia con Cinema pero sin solicitar
    # el valor de peli_serie ya que la indicaremos nosotros.
    def __init__(self, title, description, date, genre, poster, play, num_seasons, num_episodes, episode_duration):
        super().__init__(title=title,
                         description=description,
                         date=date,
                         genre=genre,
                         poster=poster,
                         play=play,
                         peli_serie=True)
        self.num_seasons = num_seasons
        self.num_episodes = num_episodes
        self.episode_duration = episode_duration
        print("Serie creada con éxito")
        
    def __repr__(self): # Para mostrar datos sobre un objeto en depuración
        return f"<Serie(id={self.id}, title={self.title}, date={self.date}, genre={self.genre}, num_seasons={self.num_seasons}, num_episodes={self.num_episodes}, episode_duration={self.episode_duration})>"
    
    def __str__(self): # Para mostrar datos sobre un objeto
        return f"Serie(id={self.id}, title={self.title}, date={self.date}, genre={self.genre}, num_seasons={self.num_seasons}, num_episodes={self.num_episodes}, episode_duration={self.episode_duration})"
