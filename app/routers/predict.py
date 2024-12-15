import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from app.schemas.input_data import InputData
from app.models.ann_model import predict_podium

router = APIRouter()

# Ruta para predecir con datos individuales
@router.post("/predict")
def get_prediction(input_data: InputData):
    try:
        # Intentamos hacer la predicción con los datos
        prediction = predict_podium(input_data)
        return {"podio": prediction}
    
    except ValidationError as e:
        # En caso de error de validación, capturamos los campos incorrectos
        errors = []
        for error in e.errors():
            field_name = error.get("loc")[0]  # El nombre del campo con el error
            error_msg = error.get("msg")  # Mensaje de error
            errors.append(f"Campo '{field_name}' tiene un error: {error_msg}")
        
        # Devolvemos los errores de manera personalizada
        raise HTTPException(status_code=422, detail=errors)

# Ruta para procesar el archivo JSON y devolver resultados
@router.get("/send-data")
def send_data():
    # Ruta al archivo JSON
    file_path = os.path.join('app', 'routers', 'data.json')
    output_file_path = os.path.join('app', 'routers', 'podium-predict.json')

    # Inicializar resultados y contador de podios
    resultados = []
    podios_contador = 0

    try:
        # Leer el archivo JSON
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Procesar cada piloto
        for piloto in data:
            try:
                # Si ya hay 3 podios, el resto será automáticamente "Fuera de podio"
                if podios_contador >= 3:
                    resultados.append({"Piloto": piloto["Piloto"], "Resultado": "Fuera de podio"})
                    continue

                # Hacer la predicción directamente
                input_data = InputData(**piloto)
                prediction = predict_podium(input_data)

                # Evaluar el resultado
                if prediction == 1:
                    podios_contador += 1
                    resultado = "Podio"
                else:
                    resultado = "Fuera de podio"

                resultados.append({"Piloto": piloto["Piloto"], "Resultado": resultado})

            except Exception as e:
                resultados.append({"Piloto": piloto.get("Piloto", "Desconocido"), "Error": str(e)})

        # Guardar los resultados en un archivo JSON
        with open(output_file_path, 'w') as output_file:
            json.dump(resultados, output_file)

        # Devolver los resultados
        return resultados

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el archivo: {e}")

# Nueva ruta para obtener los pilotos en podio
@router.get("/getPodium")
def get_podium():
    output_file_path = os.path.join('app', 'routers', 'podium-predict.json')

    try:
        # Leer el archivo JSON con los resultados
        with open(output_file_path, 'r') as file:
            data = json.load(file)

        # Filtrar los pilotos que están en el podio
        podio = [piloto for piloto in data if piloto.get("Resultado") == "Podio"]

        # Devolver los pilotos en el podio
        return podio

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo: {e}")