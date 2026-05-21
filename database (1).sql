-- ============================================================
--  🗄️  FITCONNECT — Base de datos MySQL
--  Compatible con MySQL Workbench 8.x
--  Ejecutar en orden desde arriba hacia abajo
-- ============================================================

CREATE DATABASE IF NOT EXISTS fitconnect
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE fitconnect;


-- ============================================================
--  👥  USUARIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    nombre     VARCHAR(120)  NOT NULL,
    email      VARCHAR(150)  NOT NULL UNIQUE,
    password   VARCHAR(255)  NOT NULL,          -- bcrypt hash
    rol        ENUM('cliente','gimnasio','admin') NOT NULL DEFAULT 'cliente',
    estado     ENUM('Activo','Inactivo')          NOT NULL DEFAULT 'Activo',
    creado_en  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
--  🏋️  GIMNASIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS gimnasios (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    nombre       VARCHAR(120)  NOT NULL,
    ciudad       VARCHAR(100)  NOT NULL,
    precio_base  INT           NOT NULL DEFAULT 0,
    objetivo     ENUM('musculo','cardio','flexibilidad','fuerza','funcional') NOT NULL,
    rating       DECIMAL(2,1)  NOT NULL DEFAULT 0.0,
    descripcion  TEXT,
    cover_url    VARCHAR(500),
    creado_en    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
--  📋  PLANES
-- ============================================================
CREATE TABLE IF NOT EXISTS planes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    gimnasio_id     INT          NOT NULL,
    nombre          VARCHAR(120) NOT NULL,
    precio          INT          NOT NULL,
    duracion_meses  TINYINT      NOT NULL DEFAULT 1,
    descripcion     TEXT,
    destacado       TINYINT(1)   NOT NULL DEFAULT 0,
    cover_url       VARCHAR(500),
    FOREIGN KEY (gimnasio_id) REFERENCES gimnasios(id) ON DELETE CASCADE
);


-- ============================================================
--  💪  RUTINAS
-- ============================================================
CREATE TABLE IF NOT EXISTS rutinas (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    gimnasio_id       INT NOT NULL,
    nombre            VARCHAR(120) NOT NULL,
    nivel             ENUM('Principiante','Intermedio','Avanzado') NOT NULL,
    dias              TINYINT NOT NULL DEFAULT 3,
    grupos_musculares VARCHAR(300),
    cover_url         VARCHAR(500),
    FOREIGN KEY (gimnasio_id) REFERENCES gimnasios(id) ON DELETE CASCADE
);


-- ============================================================
--  🏃  EJERCICIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS ejercicios (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    rutina_id  INT          NOT NULL,
    nombre     VARCHAR(120) NOT NULL,
    series     VARCHAR(40),
    descanso   VARCHAR(40),
    FOREIGN KEY (rutina_id) REFERENCES rutinas(id) ON DELETE CASCADE
);


-- ============================================================
--  📩  SOLICITUDES DE MEMBRESÍA
-- ============================================================
CREATE TABLE IF NOT EXISTS solicitudes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT NOT NULL,
    plan_id     INT NOT NULL,
    gimnasio_id INT NOT NULL,
    estado      ENUM('Pendiente','Aprobado','Rechazado') NOT NULL DEFAULT 'Pendiente',
    fecha       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id)  REFERENCES usuarios(id)  ON DELETE CASCADE,
    FOREIGN KEY (plan_id)     REFERENCES planes(id)    ON DELETE CASCADE,
    FOREIGN KEY (gimnasio_id) REFERENCES gimnasios(id) ON DELETE CASCADE
);


-- ============================================================
--  📝  BLOG
-- ============================================================
CREATE TABLE IF NOT EXISTS blog_posts (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    titulo     VARCHAR(300) NOT NULL,
    extracto   TEXT         NOT NULL,
    contenido  LONGTEXT,
    autor      VARCHAR(120) NOT NULL,
    categoria  ENUM('musculo','nutricion','cardio','fuerza','bienestar','motivacion','general')
               NOT NULL DEFAULT 'general',
    cover_url  VARCHAR(500),
    publicado  TINYINT(1)   NOT NULL DEFAULT 1,
    creado_en  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
--  📊  DATOS DE PRUEBA
-- ============================================================

-- Usuarios (contraseñas en texto plano solo para prueba;
--           en producción el backend las guarda como bcrypt)
INSERT INTO usuarios (nombre, email, password, rol) VALUES
('Admin FitConnect', 'admin@fitconnect.com',  '$2b$12$HASH_ADMIN',   'admin'),
('Juan Pérez',       'juan@gmail.com',         '$2b$12$HASH_JUAN',    'cliente'),
('Laura Mendoza',    'laura@gmail.com',         '$2b$12$HASH_LAURA',   'cliente'),
('FitZone Pro',      'fitzone@gym.com',         '$2b$12$HASH_FITZONE', 'gimnasio'),
('CardioCity',       'cardio@gym.com',          '$2b$12$HASH_CARDIO',  'gimnasio');

-- Gimnasios
INSERT INTO gimnasios (nombre, ciudad, precio_base, objetivo, rating, descripcion) VALUES
('FitZone Pro',  'Montería',    80000,  'musculo',      4.8, 'El gimnasio más completo de Montería con equipos de última generación.'),
('CardioCity',   'Montería',    50000,  'cardio',       4.5, 'Especialistas en cardio y quema de grasa. Clases en vivo todos los días.'),
('CrossPower',   'Bogotá',     120000,  'funcional',    4.9, 'CrossFit y entrenamiento funcional de alto rendimiento en Bogotá.'),
('ZenFit',       'Medellín',    60000,  'flexibilidad', 4.7, 'Yoga, pilates y meditación. Encuentra tu equilibrio en Medellín.'),
('PowerHouse',   'Medellín',    95000,  'fuerza',       4.8, 'Halterofilia y powerlifting. Zona de pesas libres exclusiva.'),
('EliteFit',     'Cali',       110000,  'musculo',      4.6, 'Entrenamiento de élite con coaches certificados en Cali.'),
('PrimeFit',     'Barranquilla',70000,  'funcional',    4.4, 'Entrenamiento funcional y HIIT con resultados reales.'),
('AquaFit',      'Cartagena',   75000,  'cardio',       4.5, 'Aquaeróbicos y natación terapéutica en Cartagena.'),
('SpeedTrack',   'Bogotá',      90000,  'cardio',       4.3, 'Pista de atletismo profesional y cardio de alta intensidad.'),
('CoreZone',     'Bucaramanga', 65000,  'fuerza',       4.6, 'Fortalecimiento de core, funcional y TRX en Bucaramanga.');

-- Planes
INSERT INTO planes (gimnasio_id, nombre, precio, duracion_meses, destacado, descripcion) VALUES
(1, 'Básico FitZone',        80000,  1, 0, 'Acceso sala de pesas, vestuarios y 2 clases grupales por semana.'),
(1, 'Premium FitZone',      150000,  1, 1, 'Todo en Básico más clases ilimitadas y 2 sesiones con coach.'),
(1, 'VIP FitZone',          220000,  1, 0, 'Todo en Premium más rutina personalizada y acceso 24 horas.'),
(2, 'Mensual CardioCity',    50000,  1, 0, 'Sala de cardio completa y clases de zumba una vez por semana.'),
(2, 'Trimestral CardioCity',130000,  3, 1, 'Acceso completo por 3 meses. Ahorra $20.000.'),
(3, 'CrossPower Starter',   120000,  1, 0, 'WODs diarios y coaching grupal con equipamiento CrossFit.'),
(3, 'CrossPower Elite',     200000,  1, 1, 'Programación personalizada y análisis de movimiento.'),
(4, 'ZenFit Básico',         60000,  1, 0, 'Clases de yoga 3 veces por semana y meditación guiada.'),
(4, 'ZenFit Full',          100000,  1, 1, 'Yoga ilimitado, pilates y coach personal mensual.'),
(5, 'PowerHouse Pro',       160000,  1, 1, 'Coaching de halterofilia y zona exclusiva de pesas.'),
(6, 'EliteFit Gold',        180000,  1, 1, 'Sala VIP 24 horas, coach personal y plan nutricional.'),
(7, 'PrimeFit Completo',    120000,  1, 1, 'HIIT diario, funcional en grupo y app de seguimiento.'),
(8, 'AquaFit Mensual',       75000,  1, 0, 'Piscina semiolímpica y clases de aquaeróbicos.'),
(9, 'SpeedTrack Semestral', 480000,  6, 0, 'Pista de atletismo por 6 meses completos. Ahorra $60.000.'),
(10,'CoreZone Plus',        110000,  1, 1, 'TRX y funcional ilimitado con evaluación postural.');

-- Solicitudes de membresía de ejemplo
INSERT INTO solicitudes (usuario_id, plan_id, gimnasio_id, estado) VALUES
(1, 2, 1, 'Pendiente'),
(3, 5, 2, 'Aprobado'),
(5, 9, 4, 'Pendiente');

-- Rutinas
INSERT INTO rutinas (gimnasio_id, nombre, nivel, dias, grupos_musculares) VALUES
(1,  'Hipertrofia Total',     'Intermedio',   5, 'Pecho, Espalda, Piernas, Hombros, Brazos'),
(2,  'Cardio Explosivo',      'Principiante', 3, 'Full Body, Core'),
(1,  'Powerlifting Base',     'Avanzado',     4, 'Piernas, Espalda, Pecho'),
(3,  'CrossFit WOD',          'Intermedio',   6, 'Full Body'),
(4,  'Yoga & Movilidad',      'Principiante', 3, 'Full Body, Core, Caderas'),
(5,  'Olympic Lifting',       'Avanzado',     4, 'Full Body, Espalda, Piernas'),
(6,  'Body Recomposition',    'Intermedio',   5, 'Pecho, Espalda, Glúteos, Core'),
(7,  'Funcional Express',     'Principiante', 3, 'Full Body, Core'),
(2,  'Cardio & Tonificación', 'Principiante', 4, 'Piernas, Glúteos, Core, Brazos'),
(4,  'Pilates Core',          'Principiante', 3, 'Core, Espalda, Caderas'),
(9,  'Running Intervals',     'Intermedio',   4, 'Piernas, Core, Glúteos'),
(10, 'Core & Fuerza',         'Intermedio',   4, 'Core, Espalda baja, Abdomen');

-- Ejercicios (para la rutina 1 — Hipertrofia Total)
INSERT INTO ejercicios (rutina_id, nombre, series, descanso) VALUES
(1, 'Press Banca',  '4x10', '90s'),
(1, 'Dominadas',    '3x8',  '60s'),
(1, 'Sentadilla',   '4x12', '120s'),
(1, 'Curl Bíceps',  '3x12', '60s'),
-- Rutina 2 — Cardio Explosivo
(2, 'HIIT 20min',   '1 ronda', 'Variable'),
(2, 'Burpees',      '3x15',    '45s'),
(2, 'Plancha',      '3x60s',   '30s'),
-- Rutina 3 — Powerlifting Base
(3, 'Sentadilla',   '5x5', '3min'),
(3, 'Peso Muerto',  '4x4', '3min'),
(3, 'Press Banca',  '5x5', '3min'),
-- Rutina 4 — CrossFit WOD
(4, 'Thrusters',    '3x21', '60s'),
(4, 'Pull-ups',     '3x21', '60s'),
(4, 'Box Jumps',    '3x15', '45s');

-- Blog posts
INSERT INTO blog_posts (titulo, extracto, autor, categoria) VALUES
('Cómo gané 5 kg de músculo en 6 meses sin suplementos caros',
 'Comparto mi experiencia real entrenando en el gym del barrio, comiendo normal y siendo constante.',
 'Camilo Torres', 'musculo'),
('Lo que como en un día de entreno y no gasto un dineral',
 'Desayuno, almuerzo, merienda y cena de alguien que va al gym 4 veces por semana con presupuesto normal.',
 'Valentina Ríos', 'nutricion'),
('Dejé el gym 3 veces antes de volverlo un hábito real',
 'No fue motivación, no fue disciplina de acero. Fue entender por qué fallaba antes y cambiarlo.',
 'Sebastián Gómez', 'motivacion'),
('Empecé a correr a los 34 años y esto es lo que nadie me contó',
 'Rodillas, respiración, ritmo, zapatillas... todo lo que aprendí por las malas.',
 'Laura Mendoza', 'cardio'),
('Dormir mejor me cambió el cuerpo más que cualquier rutina',
 'Llevaba meses en el gym sin ver resultados. Empecé a dormir 8 horas y en 4 semanas noté la diferencia.',
 'Daniela Herrera', 'bienestar');


-- ============================================================
--  🔍  VISTAS ÚTILES (opcionales)
-- ============================================================

-- Vista: solicitudes completas
CREATE OR REPLACE VIEW v_solicitudes AS
SELECT
    s.id,
    s.estado,
    s.fecha,
    u.nombre  AS cliente,
    u.email   AS cliente_email,
    p.nombre  AS plan,
    p.precio,
    g.nombre  AS gimnasio,
    g.ciudad
FROM solicitudes s
JOIN usuarios  u ON s.usuario_id  = u.id
JOIN planes    p ON s.plan_id     = p.id
JOIN gimnasios g ON s.gimnasio_id = g.id;

-- Vista: rutinas con nombre del gimnasio
CREATE OR REPLACE VIEW v_rutinas AS
SELECT
    r.*,
    g.nombre AS gimnasio_nombre,
    g.ciudad
FROM rutinas r
JOIN gimnasios g ON r.gimnasio_id = g.id;
