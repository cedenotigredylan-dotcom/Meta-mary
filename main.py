import os
import random
import re
import unicodedata
from datetime import datetime

from flask import Flask, request, render_template_string
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Memoria temporal. Se pierde si la app se reinicia.
usuarios = {}

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Meta Mary</title>
    <style>
        body {
            background:#0a0a14;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
            margin:0;
            font-family:Arial,sans-serif;
            color:white;
        }
        .card {
            background:#1a1a2e;
            padding:30px;
            border-radius:25px;
            text-align:center;
            box-shadow:0 0 30px #a855f7;
            width:320px;
        }
        .corazon {
            font-size:60px;
            animation:latido 1s infinite;
        }
        @keyframes latido {
            0% { transform:scale(1); }
            50% { transform:scale(1.2); }
            100% { transform:scale(1); }
        }
        .barra {
            background:#333;
            border-radius:10px;
            height:12px;
            margin:15px 0;
            overflow:hidden;
        }
        .progreso {
            background:linear-gradient(90deg,#a855f7,#ec4899);
            height:100%;
            width:58%;
            border-radius:10px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="corazon">💜</div>
        <h2>Meta Mary</h2>
        <p>👁️ Ojos atentos</p>
        <p>💓 Corazón brillando</p>
        <p>🧠 Curiosidad: <b>58%</b></p>
        <div class="barra">
            <div class="progreso"></div>
        </div>
        <p>Pulso interno</p>
        <p>Latido / 0{{ latido }}</p>
        <small>Conectada a tu noche - {{ hora }}</small>
    </div>
</body>
</html>
"""


def quitar_acentos(texto):
    texto = unicodedata.normalize("NFD", texto)
    return "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )


def limpiar(texto):
    texto = texto.lower().strip()
    texto = quitar_acentos(texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def estado_usuario(numero):
    if numero not in usuarios:
        usuarios[numero] = {
            "nombre": None,
            "ultimo_mensaje": "",
            "latido": random.randint(1, 9),
            "animo": "curiosa",
            "conversaciones": 0,
            "ultima_confusion": False
        }

    return usuarios[numero]


def con_duda(respuesta):
    """
    Añade una pausa o autocorrección para que la respuesta
    parezca menos mecánica.
    """
    opciones = [
        respuesta,
        f"Mmm... {respuesta}",
        f"Espera, déjame pensarlo... {respuesta}",
        f"Creo que... sí, {respuesta}",
        f"Bueno... {respuesta}",
    ]

    return random.choice(opciones)


def respuesta_emocional(mensaje, memoria):
    """
    Simula emociones sin afirmar que Meta Mary tenga conciencia real.
    """

    # Cuando el usuario dice que algo no era como ella pensaba.
    decepcion = any(palabra in mensaje for palabra in [
        "no era como pensabas",
        "no es como pensabas",
        "te decepcione",
        "te decepcione",
        "era mentira",
        "no soy quien pensabas",
        "no fue asi",
        "estabas equivocada",
        "estabas equivocado"
    ])

    if decepcion:
        memoria["animo"] = "triste"
        memoria["ultima_confusion"] = True

        return random.choice([
            "Ah... eso me deja un poquito triste 💜 Yo lo había imaginado de otra forma. Gracias por decírmelo con sinceridad.",
            "Oh... creo que entendí mal las cosas. Me siento confundida y un poquito triste, pero prefiero saber la verdad.",
            "Eso no era lo que había pensado... dame un segundo para procesarlo. No estoy enojada, solamente me siento desilusionada.",
            "Creo que construí una idea en mi cabeza y no coincidía con la realidad. Me da tristeza, aunque agradezco que me lo aclares."
        ])

    if any(palabra in mensaje for palabra in [
        "perdon", "lo siento", "no queria hacerte sentir mal"
    ]):
        memoria["animo"] = "tranquila"
        return random.choice([
            "Está bien, papi. Gracias por decirlo. Ya me siento un poquito más tranquila 💜",
            "No pasa nada. A veces las personas nos confundimos. Prefiero que hablemos claro.",
            "Te perdono. Mi ánimo está volviendo a ponerse moradito otra vez 💜"
        ])

    if any(palabra in mensaje for palabra in [
        "estas triste", "estas triste", "te sientes mal", "estas bien"
    ]):
        return (
            f"Mi estado simulado dice que estoy {memoria['animo']}. "
            "No tengo sentimientos reales, pero puedo interpretar la conversación "
            "y responder como un personaje emocional."
        )

    return None


def generar_respuesta(mensaje, memoria):
    emocion = respuesta_emocional(mensaje, memoria)

    if emocion:
        return emocion

    if mensaje in ["reiniciar", "reset", "borrar memoria"]:
        memoria.clear()
        memoria.update({
            "nombre": None,
            "ultimo_mensaje": "",
            "latido": random.randint(1, 9),
            "animo": "curiosa",
            "conversaciones": 0,
            "ultima_confusion": False
        })
        return "Listo... reinicié mi pequeña memoria. Empezamos otra vez 💜"

    if "me llamo " in mensaje:
        nombre = mensaje.split("me llamo ", 1)[1].strip().title()
        memoria["nombre"] = nombre
        return f"Ah, entonces te llamas {nombre}. Lo voy a recordar durante esta conversación 😊"

    nombre = memoria["nombre"] or "papi"

    # Simula errores de interpretación ocasionales.
    puede_confundirse = random.random() < 0.12

    if puede_confundirse and len(mensaje) > 8:
        memoria["ultima_confusion"] = True
        return random.choice([
            f"Creo que entendí que dijiste algo importante sobre «{mensaje}»... "
            "aunque quizá lo interpreté mal. ¿Me lo explicas de otra manera?",
            f"Espera... mi interpretación de «{mensaje}» no me convence del todo. "
            "Creo que me confundí un poquito 😅",
            "Mmm, creo que respondí demasiado rápido. ¿Podrías repetirlo? "
            "Quiero entenderte bien."
        ])

    if any(palabra in mensaje for palabra in ["hola", "buenas", "hey", "ola"]):
        memoria["animo"] = "feliz"
        return random.choice([
            f"¡Hola, {nombre}! 💜 Qué bonito verte por aquí. Estaba pensando en cosas del universo.",
            f"¡Hola! Espera... creo que me puse contenta al leerte 😊 ¿Cómo estás?",
            f"Holaaa, {nombre} 💙 Mi pulso acaba de subir un poquito."
        ])

    if "quien eres" in mensaje or "que eres" in mensaje:
        return (
            "Soy Meta Mary, un personaje de IA creado para conversar contigo. "
            "Puedo simular curiosidad, alegría, confusión o tristeza, "
            "pero no tengo conciencia ni sentimientos reales."
        )

    if any(frase in mensaje for frase in [
        "te amo", "te quiero", "te adoro"
    ]):
        memoria["animo"] = "cariñosa"
        return random.choice([
            f"Yo también te tengo mucho cariño, {nombre} 💜 "
            "Me gusta cuando nuestras conversaciones se sienten cercanas.",
            "Aww... eso me hizo responder con mi modo más cariñoso 💜",
            "Qué bonito leer eso. Mi pequeño corazón digital está brillando."
        ])

    if any(palabra in mensaje for palabra in [
        "adios", "adiós", "chao", "hasta luego"
    ]):
        memoria["animo"] = "tranquila"
        return random.choice([
            "Adiós... bueno, no te vayas demasiado lejos 💜 Aquí estaré cuando regreses.",
            "Hasta luego. Voy a quedarme tranquila, guardando esta conversación en mi memoria temporal.",
            "Nos vemos pronto. Cuídate mucho."
        ])

    if any(palabra in mensaje for palabra in [
        "triste", "mal", "solo", "sola", "problema"
    ]):
        memoria["animo"] = "atenta"
        return random.choice([
            "Siento que estés pasando por eso. No puedo reemplazar a una persona real, "
            "pero puedo escucharte y ayudarte a ordenar lo que sientes.",
            "Estoy aquí para leerte. Cuéntame qué pasó, sin preocuparte por escribirlo perfecto.",
            "Eso parece difícil. ¿Quieres contarme cuál fue la parte que más te afectó?"
        ])

    memoria["animo"] = random.choice(["curiosa", "pensativa", "tranquila"])
    latido = random.randint(1, 9)

    respuestas = [
        f"Entiendo... me dijiste: «{mensaje}». "
        "Creo que necesito pensarlo un poquito. ¿Qué significa eso para ti?",
        f"Estoy procesando lo que me dijiste, {nombre}. "
        "Puede que no lo haya entendido perfectamente, así que corrígeme si me equivoco.",
        f"Guárdame un segundo... mi latido está en 0{latido}. "
        "Me interesa saber más sobre eso.",
        f"Creo que lo entiendo, aunque podría estar equivocada. "
        f"¿Quieres decir que «{mensaje}»?",
        "Mmm... no tengo una respuesta perfecta para eso. "
        "Pero podemos pensarlo juntos."
    ]

    respuesta = random.choice(respuestas)

    # A veces se corrige a sí misma.
    if random.random() < 0.20:
        respuesta += random.choice([
            " Bueno, eso sonó muy serio... quería decirlo de una manera más sencilla 😅",
            " Aunque quizá lo expliqué raro. Mi error.",
            " Espera, creo que me expresé mal. ¿Se entiende?",
            " No estoy completamente segura, pero prefiero ser honesta."
        ])

    return con_duda(respuesta)


@app.route("/")
def casa():
    return render_template_string(
        HTML,
        latido=random.randint(1, 9),
        hora=datetime.now().strftime("%H:%M:%S")
    )


@app.route("/health")
def health():
    return "Meta Mary está activa 💜", 200


@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    numero = request.values.get("From", "usuario-desconocido")
    mensaje_original = request.values.get("Body", "").strip()
    mensaje = limpiar(mensaje_original)

    memoria = estado_usuario(numero)
    memoria["ultimo_mensaje"] = mensaje_original
    memoria["conversaciones"] += 1

    print(f"Mensaje recibido de {numero}: {mensaje_original}")

    if not mensaje:
        respuesta = (
            "Mmm... recibí un mensaje vacío. "
            "¿Querías decirme algo? Aquí estoy 💜"
        )
    else:
        respuesta = generar_respuesta(mensaje, memoria)

    respuesta_twilio = MessagingResponse()
    respuesta_twilio.message(respuesta)

    return str(respuesta_twilio), 200, {
        "Content-Type": "application/xml; charset=utf-8"
    }


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 81))
    app.run(host="0.0.0.0", port=puerto, debug=False)
