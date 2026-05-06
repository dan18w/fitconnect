from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import bcrypt
import re
import os

app = Flask(__name__)
CORS(app, origins=["https://fitconnect-orpin-one.vercel.app", "http://localhost:3000", "http://127.0.0.1:5500"])

# ── CONEXIÓN A DB (Railway) ────────────────────────────────
def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port=int(os.getenv("MYSQLPORT", 3306))
    )

def query(sql, params=(), fetchone=False, commit=False):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql, params)

    if commit:
        db.commit()
        result = cursor.lastrowid
    elif fetchone:
        result = cursor.fetchone()
    else:
        result = cursor.fetchall()

    cursor.close()
    db.close()
    return result

def err(msg, code=400):
    return jsonify({"error": msg}), code

def ok(data=None, msg="ok"):
    return jsonify(data) if data is not None else jsonify({"message": msg})

def valid_email(e):
    return re.match(r"[^@]+@[^@]+\.[^@]+", e)


# ============================================================
#  AUTENTICACION
# ============================================================

@app.route("/register", methods=["POST"])
def register():
    d = request.json or {}
    nombre = d.get("nombre","").strip()
    email = d.get("email","").strip().lower()
    password = d.get("password","")
    rol = d.get("rol","cliente")

    if not nombre or not email or not password:
        return err("Nombre, email y contraseña son requeridos.")
    if not valid_email(email):
        return err("Email inválido.")
    if rol not in ("cliente","gimnasio","admin"):
        return err("Rol inválido.")
    if query("SELECT id FROM usuarios WHERE email=%s", (email,), fetchone=True):
        return err("El email ya está registrado.", 409)

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    uid = query(
        "INSERT INTO usuarios (nombre,email,password,rol) VALUES (%s,%s,%s,%s)",
        (nombre, email, hashed, rol), commit=True
    )

    return ok({"id": uid, "nombre": nombre, "email": email, "rol": rol}), 201


@app.route("/login", methods=["POST"])
def login():
    d = request.json or {}
    email = d.get("email","").strip().lower()
    password = d.get("password","")

    if not email or not password:
        return err("Email y contraseña requeridos.")

    user = query(
        "SELECT * FROM usuarios WHERE email=%s AND estado='Activo'",
        (email,), fetchone=True
    )

    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return err("Credenciales incorrectas.", 401)

    user.pop("password", None)
    return ok(user)


# ============================================================
#  USUARIOS
# ============================================================

@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return ok(query(
        "SELECT id,nombre,email,rol,estado,creado_en FROM usuarios ORDER BY id"
    ))


@app.route("/usuarios/<int:uid>", methods=["PUT"])
def actualizar_usuario(uid):
    d = request.json or {}
    estado = d.get("estado")
    rol = d.get("rol")

    if estado and estado not in ("Activo","Inactivo"):
        return err("Estado inválido.")
    if rol and rol not in ("cliente","gimnasio","admin"):
        return err("Rol inválido.")

    if estado:
        query("UPDATE usuarios SET estado=%s WHERE id=%s", (estado, uid), commit=True)
    if rol:
        query("UPDATE usuarios SET rol=%s WHERE id=%s", (rol, uid), commit=True)

    return ok(query(
        "SELECT id,nombre,email,rol,estado FROM usuarios WHERE id=%s",
        (uid,), fetchone=True
    ))


@app.route("/usuarios/<int:uid>", methods=["DELETE"])
def eliminar_usuario(uid):
    query("DELETE FROM usuarios WHERE id=%s", (uid,), commit=True)
    return ok(msg="Usuario eliminado")


# ============================================================
#  GIMNASIOS
# ============================================================

@app.route("/gimnasios", methods=["GET"])
def listar_gimnasios():
    ciudad = request.args.get("ciudad")
    objetivo = request.args.get("objetivo")
    precio_max = request.args.get("precio_max")

    sql = "SELECT * FROM gimnasios WHERE 1=1"
    params = []

    if ciudad:
        sql += " AND ciudad LIKE %s"
        params.append(f"%{ciudad}%")

    if objetivo:
        sql += " AND objetivo=%s"
        params.append(objetivo)

    if precio_max:
        sql += " AND precio_base<=%s"
        params.append(int(precio_max))

    sql += " ORDER BY rating DESC"

    return ok(query(sql, params))


@app.route("/gimnasios/<int:gid>", methods=["GET"])
def detalle_gimnasio(gid):
    gym = query("SELECT * FROM gimnasios WHERE id=%s", (gid,), fetchone=True)

    if not gym:
        return err("Gimnasio no encontrado.", 404)

    gym["planes"] = query("SELECT * FROM planes WHERE gimnasio_id=%s", (gid,))
    gym["rutinas"] = query("SELECT * FROM rutinas WHERE gimnasio_id=%s", (gid,))

    return ok(gym)


@app.route("/gimnasios", methods=["POST"])
def crear_gimnasio():
    d = request.json or {}

    for f in ("nombre","ciudad","precio_base","objetivo"):
        if not d.get(f):
            return err(f"Campo requerido: {f}")

    if d["objetivo"] not in ("musculo","cardio","flexibilidad","fuerza","funcional"):
        return err("Objetivo inválido.")

    gid = query(
        "INSERT INTO gimnasios (nombre,ciudad,precio_base,objetivo,rating,descripcion,cover_url) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (d["nombre"], d["ciudad"], d["precio_base"], d["objetivo"],
         d.get("rating",0.0), d.get("descripcion",""), d.get("cover_url","")),
        commit=True
    )

    return ok({"id": gid}), 201


# ============================================================
#  SERVIDOR
# ============================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
