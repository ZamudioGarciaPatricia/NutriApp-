from flask import Flask, render_template, request, redirect, url_for, flash
import requests


app = Flask(__name__)
app.secret_key = 'kiwi-secreto'


#Rutas

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/info')
def info():
    return render_template('info.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/recetas')
def recetas():
    return render_template('recetas.html')



#Analizador

app.secret_key = "llave_segura"

API_LLAVE = "2mVbF6kxK7xneQO7arHpkEhocL3fieky45ymC89t"



def buscar_id(nombre_busqueda):
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    datos = {"api_key": API_LLAVE, "query": nombre_busqueda}

    r = requests.get(url, params=datos)
    if r.status_code != 200:
        return None

    info = r.json()
    if info.get("foods"):
        return info["foods"][0]["fdcId"]
    return None


def traer_kcal(id_food):
    url = f"https://api.nal.usda.gov/fdc/v1/food/{id_food}"
    datos = {"api_key": API_LLAVE}

    r = requests.get(url, params=datos)
    if r.status_code != 200:
        return 0

    info = r.json()
    kcal_totales = 0

    if "foodNutrients" in info:
        for n in info["foodNutrients"]:
            if n.get("nutrient", {}).get("id") == 1008: 
                kcal_totales += n.get("amount", 0)

    return kcal_totales


def revisar_salud(kc):
    if kc > 900:
        return "No saludable"
    return "Saludable"


@app.route("/analizar_receta", methods=["GET", "POST"])
def receta_ruta():
    if request.method == "POST":
        texto = request.form.get("ingredientes", "").strip()

        if not texto:
            flash("Escribe al menos un ingrediente.", "warning")
            return redirect(url_for("receta_ruta"))

        lineas = texto.split("\n")
        total_kc = 0
        ok = []
        mal = []

        for t in lineas:
            nombre = t.strip()
            if not nombre:
                continue

            identificador = buscar_id(nombre)
            if not identificador:
                mal.append(nombre)
                continue

            kc = traer_kcal(identificador)
            total_kc += kc
            ok.append(nombre)

        estado_final = revisar_salud(total_kc)

        return render_template(
            "analizador.html",
            receta_ingresada=texto,
            lista_ok=ok,
            lista_no=mal,
            total_kc=total_kc,
            estado_salud=estado_final
        )

    return render_template(
        "analizador.html",
        receta_ingresada="",
        lista_ok=None,
        lista_no=None,
        total_kc=None,
        estado_salud=None
    )



#Registro

base_usuarios = {} 
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if request.method == 'POST':
        nombre          = request.form.get('nombre', '').strip()
        apellidos       = request.form.get('apellidos', '').strip()
        correo          = request.form.get('email', '').strip().lower()
        contrasena      = request.form.get('password', '').strip()
        edad            = request.form.get('edad', '').strip()
        sexo            = request.form.get('sexo', '').strip()
        peso            = request.form.get('peso', '').strip()
        altura          = request.form.get('altura', '').strip()
        nivel_actividad = request.form.get('nivel_actividad', '').strip()

        campos_obligatorios = {
            'nombre': nombre,
            'apellidos': apellidos,
            'correo': correo,
            'contraseña': contrasena,
            'edad': edad,
            'sexo': sexo,
            'peso': peso,
            'altura': altura,
            'nivel_actividad': nivel_actividad
        }
        for campo, valor in campos_obligatorios.items():
            if not valor:
                flash(f'{campo.capitalize()} es obligatorio', 'danger')
                return redirect(url_for('perfil'))

        base_usuarios[correo] = {
            'nombre': nombre,
            'apellidos': apellidos,
            'contraseña': contrasena,
            'edad': int(edad),
            'sexo': sexo,
            'peso': float(peso),
            'altura': float(altura),
            'nivel_actividad': nivel_actividad,
            'tipo_dieta': request.form.get('tipo_dieta') or None,
            'alergias': [a.strip() for a in request.form.get('alergias', '').split(',')] if request.form.get('alergias') else [],
            'intolerancias': [i.strip() for i in request.form.get('intolerancias', '').split(',')] if request.form.get('intolerancias') else [],
            'objetivos': request.form.getlist('objetivos'),
            'otro_objetivo': request.form.get('otro_objetivo') or None
        }
        flash('Perfil creado con éxito.')
        return redirect(url_for('inicio'))

    return render_template('incio.html')


#Calculadoras
#Nota personal: Formulas usadas

# 1. IMC = peso_kg / altura_m^2
# 2. TMB (Harris-Benedict)
#     Hombres: 88.362 + (13.397*peso) + (4.799*altura_cm) - (5.677*edad)
#     Mujeres: 447.593 + (9.247*peso) + (3.098*altura_cm) - (4.330*edad)
# 3. GCT = TMB * factor_actividad
# 4. Peso Ideal (Devine)
#     Hombres: 50 + 2.3*(pulgadas - 60)
#     Mujeres: 45.5 + 2.3*(pulgadas - 60)
# 5. Macronutrientes (modelo simple)
#     Proteínas = 2 g por kg
#     Grasas = 0.8 g por kg
#     Carbs = (calorías restantes / 4)

@app.route("/calculadora", methods=["GET", "POST"])
def calculadoras():
    resultados = {}

    if request.method == "POST":
        calc = request.form.get("calc")

        # IMC
        if calc == "imc":
            peso = float(request.form["peso"])
            altura = float(request.form["altura"])
            resultados["imc"] = round(peso / (altura ** 2), 2)

        # TMB
        if calc == "tmb":
            peso = float(request.form["peso"])
            altura = float(request.form["altura"])
            edad = int(request.form["edad"])
            sexo = request.form["sexo"]

            if sexo == "hombre":
                tmb = 88.362 + (13.397 * peso) + (4.799 * altura) - (5.677 * edad)
            else:
                tmb = 447.593 + (9.247 * peso) + (3.098 * altura) - (4.330 * edad)

            resultados["tmb"] = round(tmb)

        # GCT
        if calc == "gct":
            tmb = float(request.form["tmb"])
            factor = float(request.form["factor"])
            resultados["gct"] = round(tmb * factor)

        #peso ideal
        if calc == "ideal":
            altura = float(request.form["altura"])
            sexo = request.form["sexo"]

            pulg = altura / 2.54

            if sexo == "hombre":
                ideal = 50 + 2.3 * (pulg - 60)
            else:
                ideal = 45.5 + 2.3 * (pulg - 60)

            resultados["ideal"] = round(ideal, 1)

        #macros
        if calc == "macros":
            peso = float(request.form["peso"])
            calorias = float(request.form["calorias"])

            prote = peso * 2
            grasa = peso * 0.8
            calorias_usadas = prote * 4 + grasa * 9
            carbs = (calorias - calorias_usadas) / 4

            resultados["macros"] = {
                "prote": round(prote),
                "grasa": round(grasa),
                "carbs": round(carbs)
            }

    return render_template("calculadora.html", resultados=resultados)



if __name__ == '__main__':
    app.run(debug=True)