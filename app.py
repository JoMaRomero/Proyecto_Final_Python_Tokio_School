from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from db import app, db
from models import Pelicula, Serie, Usuarios, Cinema
from flask import Response, abort, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import os
from io import BytesIO

# Para añadir una imágen de portada desde el html, utilizamos los siguientes datos
# Carpeta en la que se guardará la imagen
UPLOAD_FOLDER = "static/img"
# Extensiones que se permitirá de la imagen
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
# Indicamos a la app de flask la carpeta
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Hacemos que matplotlib use Agg para que no salga el warning de usar plt fuera del hilo principal.
matplotlib.use("agg")

# Creamos una instancia de sesión de usuarios
login_m = LoginManager()

# Iniciamos el login manager con Flask
login_m.init_app(app)

# Indicamos la ruta de login en caso de que el usuario no esté con la sesión iniciada
login_m.login_view = "login"

# Clave para las cookies de la sesión
app.secret_key = "viewtube_secret_key"

# Hacemos una función que nos permita verificar las extensiones de los archivos permitidas
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Usamos un decorador para hacer entender a Flask-Login que la siguiente función
# se usará para cargar un usuario usando su id.
@login_m.user_loader
def load_usuario(usuario_id):
    return db.session.get(Usuarios, usuario_id)

#---------------------------------------------------------------
#                           ERRORES
#---------------------------------------------------------------
# Creamos una ruta para el caso en el que accedan a una página que no existe y
# aparezca el error 404, les salga una página personalizada.
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

#---------------------------------------------------------------
#               SISTEMA REGISTRO Y LOGIN/LOGOUT
#---------------------------------------------------------------

# Registro de nuevo usuario
@app.route("/registro", methods=["POST", "GET"])
def registro():
    # Realizamos las siguientes acciones en caso de usar el metodo POST
    if request.method == "POST":  
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        fullname = request.form.get("fullname")
        # Se le pone "on" para indicar que si el valor admin esta activado (como en un checkbox)
        # el usuario es admin, si no esta activado, no es admin. Así prevenimos la necesidad
        # de pasarlo como valor requerido en el siguiente if
        admin = request.form.get("admin") == "on"
        
        # Si cumple con todos los datos correctamente, se hace la creación del usuario
        if username and password and email and fullname:
            # Usamos hash para darle codificación a la contraseña y añadir seguridad
            hash_pass = generate_password_hash(password, method="pbkdf2:sha256")
            new_user = Usuarios(admin=admin, username=username, password=hash_pass, email=email, fullname=fullname)
            db.session.add(new_user)
            db.session.commit()
            
            # Usamos flash para mostrar mensajes al usuario
            flash("Usuario registrado con éxito", "success")
            return redirect(url_for("login"))  
        
        else:
            flash("Error al registrar al usuario, intentelo de nuevo más tarde.", "danger")
            return render_template("register.html")
        
    else:
        return render_template("register.html")

# Login
@app.route("/login", methods=["POST", "GET"])
def login():
    # Realizamos las siguientes acciones en caso de usar el metodo POST
    if request.method == "POST":
        # Tomamos el username y la password con el hash
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Comprobamos el usuario en la db, se hace el check de la password y se redirige a home
        usuario = db.session.query(Usuarios).filter_by(username=username).first()
        if usuario and check_password_hash(usuario.password, password):
            login_user(usuario)
            flash(f"Sesión iniciada. Bienvenido a ViewTube, \"{current_user.username}\".", "success")
            return redirect(url_for("home"))
        else:
            flash("Nombre de usuario o contraseña incorrectos.", "warning")
            
    return render_template("login.html")

# Logout
@app.route("/logout")
# Si queremos hacer logout, necesitamos estar conectados antes
@login_required
def logout():
    # Desloguea al usuario activo, muestra un mensaje flash y nos manda a home
    logout_user()
    flash("Sesión cerrada", "success")
    return redirect(url_for("home"))

#---------------------------------------------------------------
#                  CRUD PARA ADMIN EN USUARIOS
#---------------------------------------------------------------

# Crear usuarios siendo admin
@app.route("/add_usuario", methods=["POST"])
# El decorador login_required se utiliza para que no se pueda acceder
# hasta que no esté autenticado como usuario y redirige al login.
@login_required

# Utilizamos este para que los admin puedan crear usuarios manualmente mientras que
# registro es para que los usuarios se hagan sus cuentas.
def add_usuario():
    
    # Comprobamos que el usuario tenga privilegios de admin y le devolvemos error 403
    # Utilizamos current_user de Flask-Login para facilitarlo
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403
    
    # Creamos los formularios para la creación de los datos
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    fullname = request.form.get("fullname")
    # En este caso le pone "1" ya que el valor que recibimos es un boolean en vez de
    # un checkbox.
    admin = request.form.get("admin") == "1"    
    
    # Comprobamos que todos los datos estén correctamente.
    if username and password and email and fullname:
        # Usamos hash para darle codificación a la contraseña y añadir seguridad
        hash_pass = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = Usuarios(admin=admin, username=username, password=hash_pass, email=email, fullname=fullname)
        db.session.add(new_user)
        db.session.commit()
        
        # Usamos flash para mostrar mensajes al usuario
        flash("Usuario creado con éxito.", "success")
        
    else:
        flash("Error al crear al usuario.", "danger")
        
    return redirect(url_for("admin"))      

# Hacemos una ruta que nos permita seleccionar al usuario para editarlo o eliminarlo en HTML
@app.route("/select_usuario", methods=["POST"])
@login_required
def select_usuario():
    # Comprobamos si es admin
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403

    # Almacenamos el id_usuario recibido desde el form
    id_usuario = request.form.get("id_usuario")

    # Si recibimos un valor en id_usuario, lo recogemos de Usuarios
    if id_usuario:
        selected_usuario = db.session.get(Usuarios, id_usuario)
    else:
        selected_usuario = None

    # Tomamos todos los usuarios
    usuarios = db.session.query(Usuarios).all()
    
    # Pasamos también los datos de Cinema para que
    # en cuando se abra un desglose, se vean los datos en el otro. De otra forma
    # no se mostrarían los datos en cinema cuando se selecciona un usuario.
    cinema = db.session.query(Cinema).all()

    # Devolvemos los usuarios, los cinema y el usuario seleccionado
    return render_template("admin.html",
                           usuarios=usuarios,
                           cinema=cinema,
                           selected_usuario=selected_usuario)


# Eliminar usuario
@app.route("/del_usuario", methods=["POST"])
@login_required
def del_usuario():
    # Comprobamos si es admin para ceder el acceso a la información
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403

    # Tomamos el id_usuario del formulario en el html
    id_usuario = request.form.get("id_usuario")

    # Si id_usuario tiene valor, tomamos sus datos
    if id_usuario:
        usuario = db.session.get(Usuarios, id_usuario)
    else:
        usuario = None

    # Si el usuario es admin, indicamos que no se puede eliminar, si no es, lo eliminamos.
    if usuario:
        if usuario.admin:
            flash("El usuario es admin y no puede ser eliminado.", "warning")
        else:
            db.session.delete(usuario)
            db.session.commit()
            flash("El usuario ha sido eliminado.", "success")
            
    else:
        flash("El usuario no existe", "danger")

    return redirect(url_for("admin"))

# Editar usuario
@app.route("/edit_usuario/<int:id>", methods=["POST"])
@login_required
def edit_usuario(id):
    # Comprobamos si es admin para ceder el acceso a la información
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403

    # Tomamos los datos del usuario que recibimos por id
    usuario = db.session.get(Usuarios, id)

    # Si es admin, indicamos que no se puede editar, si no, indicamos los campos a editar
    if usuario:
        if usuario.admin:
            flash("El usuario es admin y no puede ser editado.", "warning")
        else:
            # Cambiamos el ussername del usuario tomado antes por el que se reciba en el formulario de username
            usuario.username = request.form.get("username")
            
            # Si editamos la contraseña, le volvemos a meter el hash para darle seguridad.
            password = request.form.get("password")
            if password:
                usuario.password = generate_password_hash(password, method="pbkdf2:sha256")

            # Cambiamos el email y el fullname del usuario que tomamos por id
            usuario.email = request.form.get("email")
            usuario.fullname = request.form.get("fullname")

            # Se manda los cambios realizados a la db
            db.session.commit()
            flash("El usuario fue editado correctamente.", "success")
            
    else:
        flash("Usuario no encontrado", "danger")

    return redirect(url_for("admin"))

#---------------------------------------------------------------
#                  CRUD PARA ADMIN EN CINEMA
#---------------------------------------------------------------
# Agregar un cinema siendo admin
@app.route("/add_cinema", methods=["POST"])
# Verificamos que este logueado primero
@login_required
def add_cinema():
    # Comprobamos que el usuario tenga privilegios de admin y le devolvemos error 403
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403
    
    # Creamos los formularios para la creación de los datos
    title = request.form.get("title")
    description = request.form.get("description")
    date = request.form.get("date")
    genre = request.form.get("genre")
    play = request.form.get("play")
    peli_serie = request.form.get("peli_serie")
    
    # Configuramos el formato de la fecha para que aparezca en el formato de fecha de Python
    date_time = datetime.strptime(date, "%Y-%m-%d").date()
    
    # Indicamos como actuar con la imágen que se reciba.
    archivo = request.files.get("poster")
    if archivo and allowed_file(archivo.filename):
        filename = secure_filename(archivo.filename)
        archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        poster = filename
    else:
        poster = None
    
    # Determinamos el tipo de contenido y la creación
    if peli_serie == "0":  # Pelicula
        duration = request.form.get("duration")
        if title and description and date and genre and duration and poster and play:
            new_peli = Pelicula(title=title, 
                                description=description, 
                                date=date_time, 
                                genre=genre,
                                poster=poster,
                                play=play,
                                duration=duration)
            db.session.add(new_peli)
            db.session.commit()
            flash("Pelicula añadida con éxito.", "success")
        else:
            flash("Error al crear la pelicula.", "danger")
    
    elif peli_serie == "1":  # Serie
        num_seasons = request.form.get("num_seasons")
        num_episodes = request.form.get("num_episodes")
        episode_duration = request.form.get("episode_duration")
        if title and description and date and genre and num_seasons and num_episodes and episode_duration and poster and play:
            new_serie = Serie(title=title, 
                              description=description, 
                              date=date_time, 
                              genre=genre,
                              poster=poster,
                              play=play,
                              num_seasons=num_seasons,
                              num_episodes=num_episodes,
                              episode_duration=episode_duration)
            db.session.add(new_serie)
            db.session.commit()
            flash("Serie añadida con éxito.", "success")
            
        else:
            flash("Error al crear la serie.", "danger")
    
    else:
        flash("Tipo de contenido no válido.", "danger")
    
    return redirect(url_for("admin"))

# Seleccionar cine para editar/eliminar en HTML
@app.route("/select_cine", methods=["POST"])
@login_required
def select_cine():
    # Comprobamos si es admin para ceder el acceso a la información
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403

    # Tomamos el id del cine que recibimos desde el formulario html
    id_cine = request.form.get("id_cine")

    # Si recibimos algun valor, tomamos todos los datos de ese cinema
    if id_cine:
        selected_cine = db.session.get(Cinema, id_cine)
        if selected_cine:
            # Si el cinema tomado es una peli, se toman los datos desde pelicula
            # si no, se toman de Serie
            if selected_cine.peli_serie == 0:
                selected_cine = db.session.get(Pelicula, id_cine)
            else:
                selected_cine = db.session.get(Serie, id_cine)
        else:
            selected_cine = None
    else:
        selected_cine = None

    # Tomamos todos los datos de usuarios y de cinema para que en el html
    # se pueda abrir el desglose de edit/eliminar de cinema y de usuario.
    usuarios = db.session.query(Usuarios).all()
    cinema = db.session.query(Cinema).all()

    return render_template("admin.html",
                           cinema=cinema,
                           usuarios=usuarios,
                           selected_cine=selected_cine)

# Editar Pelicula o serie
@app.route("/edit_cine/<int:id>", methods=["POST"])
@login_required
def edit_cine(id):
    # Comprobamos que el usuario tenga privilegios de admin y le devolvemos error 403
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403
    
    # Tomamos el id de pelicula y serie para permitimos la edición de lo que se pida.
    cine = db.session.get(Cinema, id)
    peli = db.session.get(Pelicula, id)
    serie = db.session.get(Serie, id)
    
    # Si recibimos algun dato de cine desde la id recibida
    # tomamos los datos de el formulario html en sus puntos requeridos.
    if cine:
        cine.title = request.form.get("title")
        cine.description = request.form.get("description")
        date_format = request.form.get("date")
        cine.date = datetime.strptime(date_format, "%Y-%m-%d").date()
        cine.genre = request.form.get("genre")
        cine.play = request.form.get("play")
        
        # Para el poster
        archivo = request.files.get("poster")
        if archivo and allowed_file(archivo.filename):
            filename = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            cine.poster = filename
        
        # En caso de que sea una película
        if cine.peli_serie == 0:
            peli.duration = request.form.get("duration")
            
        # En caso de ser una serie
        else:
            serie.num_seasons = request.form.get("num_seasons")
            serie.num_episodes = request.form.get("num_episodes")
            serie.episode_duration = request.form.get("episode_duration")
        
        db.session.commit()
        flash("Pelicula/Serie editada correctamente", "success")
                         
    else:
        flash("Pelicula/Serie no encontrada", "danger")
        
    return redirect(url_for("admin"))

# Eliminar Pelicula o Serie
@app.route("/del_cine", methods=["POST"])
@login_required
def del_cine():
    # Comprobamos que el usuario tenga privilegios de admin y le devolvemos error 403
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403
    
    # Cogemos el id del cinema que queremos eliminar
    id_cine = request.form.get("id_cine")
    
    # Si existe algún id_cine, tomamos todos sus datos y lo eliminamos de la db
    if id_cine:
        cine = db.session.get(Cinema, id_cine)
        
        if cine:
            # Si tiene alguna relación con pelicula o con serie, también se elimina de esa tabla
            db.session.query(Pelicula).filter_by(id=id_cine).delete()
            db.session.query(Serie).filter_by(id=id_cine).delete()
            
            db.session.delete(cine)
            db.session.commit()
            flash("La pelicula/serie eliminada correctamente", "success")
        else:
            flash("La pelicula/serie que quiere eliminar no existe", "danger")
    else:
        flash("No se indicó el ID de la peli/serie", "danger")
        
    return redirect(url_for("admin"))

#---------------------------------------------------------------
#           AÑADIR/QUITAR RELACION ENTRE USUARIO Y CINEMA
#---------------------------------------------------------------
# Pillamos la id del usuario y del cinema que escribamos en el formulario
# y le añadimos la relación entre ambos en favoritos.
@app.route("/favoritos/<int:id_usuario>/<int:id_cine>", methods=["POST"])
@login_required
def favoritos(id_usuario, id_cine):
    
    # Guardamos la id del usuario y de cinema
    usuario = db.session.get(Usuarios, id_usuario)
    cine = db.session.get(Cinema, id_cine)

    # Con el id de usuario y usando el cine_fav de relationship, indicamos la id de
    # la pelicula o serie que queremos unir.
    
    # Si el usuario ya tiene relacion, la quitamos
    if cine in usuario.cine_fav:
        usuario.cine_fav.remove(cine)
        db.session.commit()
        flash("Eliminado de favoritos.", "success")
    # Si no tiene relación, lo añadimos
    elif cine not in usuario.cine_fav:
        usuario.cine_fav.append(cine)
        db.session.commit()
        flash("Añadido a favoritos.", "success")
    else:
        flash("ERROR: No se pudo añadir/elminar de favoritos", "danger")
    
    # Observamos si la solicitud viene desde /buscar o desde otro enlace ya que
    # si el return es de vuelta a /buscar, dara error.
    if request.referrer and request.referrer.endswith(url_for("buscar")):
        return redirect(url_for("favs"))
    
    return redirect(request.referrer)


# Ruta para añadir pelicula/serie en visto
@app.route("/vistos/<int:id_usuario>/<int:id_cine>", methods=["POST"])
@login_required
def vistos(id_usuario, id_cine):

    # Guardamos la id del usuario y de cinema
    usuario = db.session.get(Usuarios, id_usuario)
    cine = db.session.get(Cinema, id_cine)

    # Con el id de usuario y usando el cine_vista de relationship, indicamos la id de
    # la pelicula o serie que queremos unir.
    
    # Si el usuario tiene en visto el cine, lo quita
    if cine in usuario.cine_vista:
        usuario.cine_vista.remove(cine)
        db.session.commit()
        flash("Eliminado de Vistos.", "success")
    # Si no lo tiene en visto, lo añade.
    elif cine not in usuario.cine_vista:
        usuario.cine_vista.append(cine)
        db.session.commit()
        flash("Añadido a Vistos.", "success")
    else:
        flash("ERROR: No se pudo añadir/elminar de favoritos", "danger")
        
    if request.referrer and request.referrer.endswith(url_for("buscar")):
        return redirect(url_for("home"))
    
    return redirect(request.referrer)

#---------------------------------------------------------------
#                           GRÁFICAS
#---------------------------------------------------------------
# Creamos una función para no repetirse a la hora de crear las gráficas
def plantilla_graph(df, color, xlabel, ylabel, title):
    plt.figure(figsize=(4, 4)) # Creamos una figura indicando las pulgadas (4 ancho, 4 alto)
    plt.bar(df["titulo"], df["num_usuarios"], color=color) # Creamos la gráfica de barras
    plt.xlabel(xlabel) # Nombre de eje x
    plt.ylabel(ylabel) # Nombre de eje y
    plt.title(title) # Titulo de la gráfica
    plt.xticks(rotation=45, ha="right") # Rotamos el nombre del eje x a la derecha en 45 grados
    plt.tight_layout() # Función que ajusta los parametros automáticamente.
    
    img = BytesIO() # Se crea un buffer en memoria que almacena la imagen
    plt.savefig(img, format="png") # Guardamos el gráfico en formato png en el buffer
    img.seek(0) # Reseteamos la posición del cursor del buffer al inicio para ver la imagen desde el principio.
    plt.close() # Cerramos la figura.
    
    return img
    
# Creamos una ruta que nos permita extraer los datos de la base de datos y generar la gráfica de favoritos
@app.route("/graph_fav")
@login_required
def graph_fav():
    # Comprobamos que el usuario tenga privilegios de admin y le devolvemos error 403
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403
    
    # Comprobamos las películas y cuantos usuarios la tienen en fav.
    cinemas = db.session.query(Cinema).all()
    
    # Creamos una lista en la que almacenaremos los datos
    datos = []
    
    # En el bucle, miramos cada pelicula, los usuarios que lo tienen en fav y se añade a datos
    for cine in cinemas:
        num_usuarios = len(cine.usuario_fav) # num de usuarios con la cinema en fav.
        
        # Hacemos que, en caso de que el título sea mayor que 10 carácteres, se reduzca y se añadan ...
        if len(cine.title) > 10:
            titulo = cine.title[:10] + "..."
        else:
            titulo = cine.title
            
        datos.append({
            "titulo": titulo,
            "num_usuarios": num_usuarios
        })
    
    # Convertimos datos a DataFrame de pandas
    df = pd.DataFrame(datos)
    img_graph = plantilla_graph(df, "blue", "Pelicula/Serie", "Número de usuarios", "Cantidad de Favoritos")
    return Response(img_graph.getvalue(), mimetype="image/png")

# Creamos una ruta que nos permita extraer los datos de la base de datos y generar la gráfica de favoritos
@app.route("/graph_vistas")
@login_required
def graph_vistas():
    # Comprobamos que el usuario tenga privilegios de admin y le devolvemos error 403
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403
    
    # Comprobamos las películas y cuantos usuarios la tienen en fav.
    cinemas = db.session.query(Cinema).all()
    
    # Creamos una lista en la que almacenaremos los datos
    datos = []
    
    # En el bucle, miramos cada pelicula, los usuarios que lo tienen en fav y se añade a datos
    for cine in cinemas:
        num_usuarios = len(cine.usuario_vista) # num de usuarios con la cinema en fav.
        
        # Hacemos que, en caso de que el título sea mayor que 10 carácteres, se reduzca y se añadan ...
        if len(cine.title) > 10:
            titulo = cine.title[:10] + "..."
        else:
            titulo = cine.title
            
        datos.append({
            "titulo": titulo,
            "num_usuarios": num_usuarios
        })
    
    # Convertimos datos a DataFrame de pandas
    df = pd.DataFrame(datos)
    img_graph = plantilla_graph(df, "red", "Pelicula/Serie", "Número de usuarios", "Cantidad de Vistas")
    return Response(img_graph.getvalue(), mimetype="image/png")

# Creamos una ruta que nos permita extraer los datos de la base de datos y generar la gráfica de favoritos
@app.route("/graph_tiempo")
@login_required
# En este caso no añadimos la verificación de admin ya que esta gráfica es para los usuarios
def graph_tiempo():
    # Esta gráfica es para que los usuarios vean su tiempo invertido en peliculas y series    
    peliculas = db.session.query(Pelicula).all()
    series = db.session.query(Serie).all()
    
    # Creamos una lista en la que almacenaremos los datos
    pelis_vistas = []
    series_vistas = []
    
    # Bucle para ver el tiempo invertido en películas
    for peli in peliculas:
        if current_user in peli.usuario_vista:
            pelis_vistas.append(peli)
    
    for serie in series:
        if current_user in serie.usuario_vista:
            series_vistas.append(serie)
    
    # Vamos sumando la duración de la peli para tener el total
    tiempo_pelis = 0
    for peli in pelis_vistas:
        tiempo_pelis += peli.duration
    
    # Sumamos la duración de la serie, multiplicando la cantidad de episodios
    # con la cantidad de temporadas que haya y la duracion de los episodios.
    tiempo_series = 0
    for serie in series_vistas:
        tiempo_series += serie.episode_duration * serie.num_episodes * serie.num_seasons
    
    # Dividimos los tipos en Peliculas y Series para saber el tiempo invertido en uno y otro
    datos = {
        "tipo": ["Películas", "Series"],
        "tiempo": [tiempo_pelis, tiempo_series]
    }
    
    # Convertimos datos a DataFrame de pandas
    df = pd.DataFrame(datos) 
        
    # Creamos la gráfica
    plt.figure(figsize=(4, 4)) # Creamos una figura indicando las pulgadas (4 ancho, 4 alto)
    plt.bar(df["tipo"], df["tiempo"], color="green") # Creamos la gráfica de barras
    plt.xlabel("Categoría") # Nombre de eje x
    plt.ylabel("Tiempo (minutos)") # Nombre de eje y
    plt.title("Tiempo invertido en Películas y Series") # Titulo de la gráfica
    plt.xticks(rotation=45, ha="right") # Rotamos el nombre del eje x a la derecha en 45 grados
    plt.tight_layout() # Función que ajusta los parametros automáticamente.
    
    img = BytesIO() # Se crea un buffer en memoria que almacena la imagen
    plt.savefig(img, format="png") # Guardamos el gráfico en formato png en el buffer
    img.seek(0) # Reseteamos la posición del cursor del buffer al inicio para ver la imagen desde el principio.
    plt.close() # Cerramos la figura.
    
    return Response(img.getvalue(), mimetype="image/png")

#---------------------------------------------------------------
#                           BUSCADOR
#---------------------------------------------------------------
# Creamos una ruta para el buscador que requerirá de metodos GET y POST
@app.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar():
    if request.method == "POST":
        # Tomamos los datos de la búsqueda, tanto su género como el contenido de la busqueda
        contenido_titulo = request.form.get("contenido_titulo")
        contenido_genero = request.form.get("contenido_genero")
        
        # Almacenamos en peliculas y series
        peli = db.session.query(Pelicula)
        serie = db.session.query(Serie)
        
        
        # Lo que tengamos en el buscado, lo usamos como filtro con los títulos de pelis y series
        if contenido_titulo:
            peli = peli.filter(Pelicula.title.contains(contenido_titulo))
            serie = serie.filter(Serie.title.contains(contenido_titulo))
        # Volvemos a filtrar dependiendo del género que se haya escogido
        if contenido_genero:
            peli = peli.filter(Pelicula.genre == contenido_genero)
            serie = serie.filter(Serie.genre == contenido_genero)
        
        peliculas = peli.all()
        series = serie.all()
        
        # Almacenamos en resultados el contenido final
        resultados = peliculas + series
        
        # Para los botones de Favoritos y Vistas
        id_fav = []
        id_vista = []
        
        for cine in current_user.cine_fav:
            id_fav.append(cine.id)
        
        for cine in current_user.cine_vista:
            id_vista.append(cine.id)
        
        # Nos manda a search.html con el contenido que hayamos sacado
        return render_template("search.html", 
                               cinema=resultados,
                               contenido=contenido_titulo,
                               genero=contenido_genero,
                               id_fav=id_fav,
                               id_vista=id_vista)
        
    # En caso de escribir en el buscador manualmente el enlace /buscar, saltará un error 404 en vez de 405.
    abort(404)

#---------------------------------------------------------------
#                              RUTAS
#---------------------------------------------------------------
# Ruta principal o Inicio
@app.route("/")
def home():    
    return render_template("index.html")

# Acceso a Peliculas
@app.route("/peliculas")
@login_required
def peliculas():
    # Tomamos todos los datos de usuarios, cinema y pelicula
    usuarios = db.session.query(Usuarios).all()
    cinema = db.session.query(Cinema).all()
    peliculas = db.session.query(Pelicula).all()
    
    # Para los botones de Favoritos y Vistas
    id_fav = []
    id_vista = []
    
    # Comprobamos en cada pelicula del usuario actual si tiene o no en favoritos la pelicula
    # y la almacenamos para mostrar en el HTML si tiene o no favoritos
    for cine in current_user.cine_fav:
        id_fav.append(cine.id)
    
    # Hacemos lo mismo para vista
    for cine in current_user.cine_vista:
        id_vista.append(cine.id)
    
    # Devolvemos todos los datos y nos encargamos de mostrar las cosas con Jinja2
    return render_template("peliculas.html",
                           usuarios=usuarios,
                           cinema=cinema,
                           peliculas=peliculas,
                           id_fav=id_fav,
                           id_vista=id_vista)
    
# Acceso a Series
@app.route("/series")
@login_required
def series():
    # Tomamos todos los datos de usuarios, cinema y serie
    usuarios = db.session.query(Usuarios).all()
    cinema = db.session.query(Cinema).all()
    series = db.session.query(Serie).all()
    
    # Para los botones de Favoritos y Vistas
    id_fav = []
    id_vista = []
    
    # Comprobamos en cada serie del usuario actual si tiene o no en favoritos la serie
    # y la almacenamos para mostrar en el HTML si tiene o no favoritos
    for cine in current_user.cine_fav:
        id_fav.append(cine.id)
    
    # Hacemos lo mismo para vista
    for cine in current_user.cine_vista:
        id_vista.append(cine.id) 
    
    # Devolvemos todos los datos y nos encargamos de mostrar las cosas con Jinja2    
    return render_template("series.html",
                           usuarios=usuarios,
                           cinema=cinema,
                           series=series,
                           id_fav=id_fav,
                           id_vista=id_vista)
    
# Ruta de favoritos
@app.route("/favs")
@login_required
def favs():
    #Almacenamos todas las películas y series
    peliculas = db.session.query(Pelicula).all()
    series = db.session.query(Serie).all()
    
    # Para los botones de Favoritos y Vistas
    id_fav = []
    id_vista = []
    
    # Comprobamos en cada pelicula y serie del usuario actual si tiene o no en favoritos la peli/serie
    # y la almacenamos para mostrar en el HTML si tiene o no favoritos
    for cine in current_user.cine_fav:
        id_fav.append(cine.id)
        
    # Hacemos lo mismo para vista
    for cine in current_user.cine_vista:
        id_vista.append(cine.id)
        
    # Filtramos las películas que el usuario tiene en favoritos aprovechandonos de id_fav
    fav_pelis = []
    for peli in peliculas:
        if peli.id in id_fav:
            fav_pelis.append(peli)
    
    # Hacemos el mismo filtrado con las series
    fav_series = []
    for serie in series:
        if serie.id in id_fav:
            fav_series.append(serie)
            
    # Unimos las listas de peliculas y series favoritas
    cinema = fav_pelis + fav_series
    
    return render_template("favoritos.html",
                           cinema=cinema,
                           id_fav=id_fav,
                           id_vista=id_vista)
    
@app.route("/vista")
@login_required
def vista():
    #Almacenamos todas las películas y series
    peliculas = db.session.query(Pelicula).all()
    series = db.session.query(Serie).all()
    
    # Para los botones de Favoritos y Vistas
    id_fav = []
    id_vista = []
    
    # Comprobamos en cada pelicula y serie del usuario actual si tiene o no en favoritos la peli/serie
    # y la almacenamos para mostrar en el HTML si tiene o no favoritos
    for cine in current_user.cine_fav:
        id_fav.append(cine.id)
    
    # Hacemos el mismo filtrado con las series
    for cine in current_user.cine_vista:
        id_vista.append(cine.id)
        
    # Filtramos las películas que el usuario tiene en vistas
    vista_pelis = []
    for peli in peliculas:
        if peli.id in id_vista:
            vista_pelis.append(peli)
    
    # Hacemos el mismo filtrado con las series
    vista_series = []
    for serie in series:
        if serie.id in id_vista:
            vista_series.append(serie)
            
    # Unimos las listas de peliculas y series favoritas
    cinema = vista_pelis + vista_series
    
    return render_template("vistos.html",
                           cinema=cinema,
                           id_fav=id_fav,
                           id_vista=id_vista)
    
# Ruta para las Gráficas del usuario
@app.route("/grafica", methods=["GET"])
@login_required
def grafica():
    # tomamos show_tiempo del htmly se muestra en caso de ser true el boolean
    show_tiempo = request.args.get("show_tiempo") == "true"
    
    return render_template("grafica.html",
                           show_tiempo=show_tiempo)
    
# Ruta de ADMIN
@app.route("/admin", methods=["GET"])
@login_required
def admin():
    # Comprobamos que el usuario tenga privilegios de admin y le devolvemos error 403
    if not current_user.admin:
        return "No tienes permisos para esta acción", 403
    
    usuarios = db.session.query(Usuarios).all()
    cinema = db.session.query(Cinema).all()
    peliculas = db.session.query(Pelicula).all()
    series = db.session.query(Serie).all()
    
    show_fav = request.args.get("show_fav") == "true"
    show_vistas = request.args.get("show_vistas") == "true"
    
    return render_template("admin.html",
                           usuarios=usuarios,
                           cinema=cinema,
                           peliculas=peliculas,
                           series=series,
                           show_fav=show_fav,
                           show_vistas=show_vistas)
    
    

#-----------FIN------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Creamos todas las tablas de db
        app.run(debug=True) # Dejamos el debug = True para que al modificar codigo, se reinicie el servidor de Flask