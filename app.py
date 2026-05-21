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
    gimnasio_id = d.get("gimnasio_id")

    if not nombre or not email or not password:
        return err("Nombre, email y contraseña son requeridos.")
    if not valid_email(email):
        return err("Email inválido.")
    if rol not in ("cliente","gimnasio","admin"):
        return err("Rol inválido.")
    if query("SELECT id FROM usuarios WHERE email=%s", (email,), fetchone=True):
        return err("El email ya está registrado.", 409)

    if gimnasio_id is not None:
        if rol != "gimnasio":
            return err("Solo usuarios con rol 'gimnasio' pueden tener un gimnasio asociado.")
        if not query("SELECT id FROM gimnasios WHERE id=%s", (gimnasio_id,), fetchone=True):
            return err("Gimnasio no válido.")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    uid = query(
        "INSERT INTO usuarios (nombre,email,password,rol,gimnasio_id) VALUES (%s,%s,%s,%s,%s)",
        (nombre, email, hashed, rol, gimnasio_id), commit=True
    )

    return ok({"id": uid, "nombre": nombre, "email": email, "rol": rol, "gimnasio_id": gimnasio_id}), 201


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
        "SELECT id,nombre,email,rol,estado,gimnasio_id,creado_en FROM usuarios ORDER BY id"
    ))


@app.route("/usuarios/<int:uid>", methods=["PUT"])
def actualizar_usuario(uid):
    d = request.json or {}
    estado = d.get("estado")
    rol = d.get("rol")
    gimnasio_id = d.get("gimnasio_id")

    if estado and estado not in ("Activo","Inactivo"):
        return err("Estado inválido.")
    if rol and rol not in ("cliente","gimnasio","admin"):
        return err("Rol inválido.")
    if gimnasio_id is not None:
        if rol and rol != "gimnasio":
            return err("Solo usuarios con rol 'gimnasio' pueden tener un gimnasio asociado.")
        current = query("SELECT rol FROM usuarios WHERE id=%s", (uid,), fetchone=True)
        if current and current["rol"] != "gimnasio" and rol != "gimnasio":
            return err("Solo usuarios con rol 'gimnasio' pueden tener un gimnasio asociado.")
        if not query("SELECT id FROM gimnasios WHERE id=%s", (gimnasio_id,), fetchone=True):
            return err("Gimnasio no válido.")
        query("UPDATE usuarios SET gimnasio_id=%s WHERE id=%s", (gimnasio_id, uid), commit=True)

    if estado:
        query("UPDATE usuarios SET estado=%s WHERE id=%s", (estado, uid), commit=True)
    if rol:
        query("UPDATE usuarios SET rol=%s WHERE id=%s", (rol, uid), commit=True)

    return ok(query(
        "SELECT id,nombre,email,rol,estado,gimnasio_id FROM usuarios WHERE id=%s",
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


@app.route("/pendientes/planes", methods=["POST"])
def crear_plan_pendiente():
    d = request.json or {}
    if d.get("role") != "gimnasio":
        return err("Solo usuarios con rol 'gimnasio' pueden crear planes pendientes.", 403)

    gimnasio_id = d.get("gimnasio_id")
    nombre = (d.get("nombre") or "").strip()
    precio = d.get("precio")
    duracion_meses = d.get("duracion_meses")

    if not gimnasio_id or not nombre or precio is None or duracion_meses is None:
        return err("Gimnasio, nombre, precio y duración son requeridos.")
    if not query("SELECT id FROM gimnasios WHERE id=%s", (gimnasio_id,), fetchone=True):
        return err("Gimnasio no válido.")

    pid = query(
        "INSERT INTO pendientes_planes (gimnasio_id,nombre,precio,duracion_meses,descripcion,destacado,cover_url) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (gimnasio_id, nombre, int(precio), int(duracion_meses), d.get("descripcion",""), int(bool(d.get("destacado",0))), d.get("cover_url","")),
        commit=True
    )
    return ok({"id": pid, "estado": "Pendiente"}), 201


@app.route("/pendientes/rutinas", methods=["POST"])
def crear_rutina_pendiente():
    d = request.json or {}
    if d.get("role") != "gimnasio":
        return err("Solo usuarios con rol 'gimnasio' pueden crear rutinas pendientes.", 403)

    gimnasio_id = d.get("gimnasio_id")
    nombre = (d.get("nombre") or "").strip()
    nivel = d.get("nivel")
    dias = d.get("dias")

    if not gimnasio_id or not nombre or not nivel or dias is None:
        return err("Gimnasio, nombre, nivel y días son requeridos.")
    if nivel not in ("Principiante", "Intermedio", "Avanzado"):
        return err("Nivel inválido.")
    if not query("SELECT id FROM gimnasios WHERE id=%s", (gimnasio_id,), fetchone=True):
        return err("Gimnasio no válido.")

    rid = query(
        "INSERT INTO pendientes_rutinas (gimnasio_id,nombre,nivel,dias,grupos_musculares,cover_url) VALUES (%s,%s,%s,%s,%s,%s)",
        (gimnasio_id, nombre, nivel, int(dias), d.get("grupos_musculares",""), d.get("cover_url","")),
        commit=True
    )
    return ok({"id": rid, "estado": "Pendiente"}), 201


@app.route("/pendientes", methods=["GET"])
def listar_pendientes():
    estado = request.args.get("estado", "Pendiente")
    planes = query(
        "SELECT pp.*, g.nombre AS gimnasio FROM pendientes_planes pp JOIN gimnasios g ON pp.gimnasio_id=g.id WHERE pp.estado=%s ORDER BY pp.creado_en DESC",
        (estado,)
    )
    rutinas = query(
        "SELECT pr.*, g.nombre AS gimnasio FROM pendientes_rutinas pr JOIN gimnasios g ON pr.gimnasio_id=g.id WHERE pr.estado=%s ORDER BY pr.creado_en DESC",
        (estado,)
    )
    return ok({"planes": planes, "rutinas": rutinas})


@app.route("/pendientes/planes/<int:pid>/resolver", methods=["POST"])
def resolver_plan_pendiente(pid):
    d = request.json or {}
    if d.get("role") != "admin":
        return err("Solo el admin puede aprobar o rechazar solicitudes.", 403)

    estado = d.get("estado")
    if estado not in ("Aprobado", "Rechazado"):
        return err("Acción inválida.")

    pending = query("SELECT * FROM pendientes_planes WHERE id=%s", (pid,), fetchone=True)
    if not pending:
        return err("Solicitud de plan no encontrada.", 404)
    if pending["estado"] != "Pendiente":
        return err("Esta solicitud ya fue procesada.", 400)

    if estado == "Aprobado":
        query(
            "INSERT INTO planes (gimnasio_id,nombre,precio,duracion_meses,descripcion,destacado,cover_url) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (pending["gimnasio_id"], pending["nombre"], pending["precio"], pending["duracion_meses"], pending["descripcion"], pending["destacado"], pending["cover_url"]),
            commit=True
        )

    query("UPDATE pendientes_planes SET estado=%s WHERE id=%s", (estado, pid), commit=True)
    return ok({"id": pid, "estado": estado})


@app.route("/pendientes/rutinas/<int:rid>/resolver", methods=["POST"])
def resolver_rutina_pendiente(rid):
    d = request.json or {}
    if d.get("role") != "admin":
        return err("Solo el admin puede aprobar o rechazar solicitudes.", 403)

    estado = d.get("estado")
    if estado not in ("Aprobado", "Rechazado"):
        return err("Acción inválida.")

    pending = query("SELECT * FROM pendientes_rutinas WHERE id=%s", (rid,), fetchone=True)
    if not pending:
        return err("Solicitud de rutina no encontrada.", 404)
    if pending["estado"] != "Pendiente":
        return err("Esta solicitud ya fue procesada.", 400)

    if estado == "Aprobado":
        query(
            "INSERT INTO rutinas (gimnasio_id,nombre,nivel,dias,grupos_musculares,cover_url) VALUES (%s,%s,%s,%s,%s,%s)",
            (pending["gimnasio_id"], pending["nombre"], pending["nivel"], pending["dias"], pending["grupos_musculares"], pending["cover_url"]),
            commit=True
        )

    query("UPDATE pendientes_rutinas SET estado=%s WHERE id=%s", (estado, rid), commit=True)
    return ok({"id": rid, "estado": estado})


# ============================================================
#  SERVIDOR
# ============================================================
@app.route("/")
def index():
    return ok({"status": "FitConnect API corriendo"})
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
