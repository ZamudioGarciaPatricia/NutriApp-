from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import requests

USUARIOS = {} 


app = Flask(__name__)
app.secret_key = 'kiwi-secreto'
API_KEY = "2mVbF6kxK7xneQO7arHpkEhocL3fieky45ymC89t" 


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
BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ingredientes = []
        
        for i in range(1, 11):
            nombre = request.form.get(f"ingrediente{i}")
            if nombre and nombre.strip():
                ingredientes.append(nombre.strip())

        if not ingredientes:
            flash("Debes ingresar al menos un ingrediente.")
            return render_template("index.html")

        calorias_totales = 0
        proteinas_totales = 0

        for item in ingredientes:
            params = {
                "api_key": API_KEY,
                "query": item
            }

            r = requests.get(BASE_URL, params=params)

            if r.status_code != 200:
                flash(f"No se pudo consultar: {item}")
                continue

            data = r.json()

            if "foods" not in data or len(data["foods"]) == 0:
                flash(f"No se encontró información para: {item}")
                continue

            alimento = data["foods"][0]

            calories = 0
            protein = 0

            for nutriente in alimento.get("foodNutrients", []):
                nombre = nutriente.get("nutrientName", "").lower()

                if "energy" in nombre and nutriente.get("unitName") == "KCAL":
                    calories = nutriente.get("value", 0)

                if "protein" in nombre:
                    protein = nutriente.get("value", 0)

            calorias_totales += calories
            proteinas_totales += protein

        if calorias_totales < 600:
            saludable = "Sí, es una receta saludable"
        else:
            saludable = "No, es alta en calorías"

        return render_template(
            "calculadora.html",
            calorias=calorias_totales,
            proteinas=proteinas_totales,
            saludable=saludable
        )

    return render_template("calculadora.html")



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