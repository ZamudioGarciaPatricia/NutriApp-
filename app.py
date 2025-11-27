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
        return redirect(url_for('iniciar_sesion'))

    return render_template('perfil.html')


#Calculadoras

def calcular_imc(peso, altura):
    """Calcula el Índice de Masa Corporal (altura en metros)."""
    return peso / (altura ** 2)

def calcular_tmb(sexo, peso, altura_cm, edad):
    """Calcula la Tasa Metabólica Basal (Fórmula Mifflin-St Jeor)."""
    if sexo == "masculino": 
        return 10 * peso + 6.25 * altura_cm - 5 * edad + 5
    else:
        return 10 * peso + 6.25 * altura_cm - 5 * edad - 161

def calcular_gct(tmb, actividad):

    factores = {
        "sedentario": 1.2,
        "ligero": 1.375,
        "moderado": 1.55,
        "activo": 1.725,  
        "muy_activo": 1.9 
    }
    return tmb * factores.get(actividad, 1.2)



def calcular_macros(calorias):
    prote = calorias * 0.30 / 4
    carbos = calorias * 0.40 / 4     
    grasas = calorias * 0.30 / 9     
    return prote, carbos, grasas


@app.route("/calculadora", methods=["GET", "POST"])
def calculadora():
    if request.method == "POST":

        try:
            peso = float(request.form["peso"])
            altura_m = float(request.form["altura"]) 
            altura_cm = altura_m * 100 
            edad = int(request.form["edad"])
            sexo = request.form["sexo"]
            actividad = request.form["actividad"]
        except ValueError:
            return render_template("calculadora.html", error="Por favor, introduce valores numéricos válidos.")


        imc = calcular_imc(peso, altura_m)
        tmb = calcular_tmb(sexo, peso, altura_cm, edad)
        gct = calcular_gct(tmb, actividad)
        prote, carbos, grasas = calcular_macros(gct)

        return render_template(
            "resultado.html",
            imc=round(imc, 2),
            tmb=round(tmb, 2),
            gct=round(gct, 2),
            prote=round(prote, 3),
            carbos=round(carbos, 2),
            grasas=round(grasas, 2)
        )

    return render_template("calculadora.html")



if __name__ == '__main__':
    app.run(debug=True)