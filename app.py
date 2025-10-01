from fastapi import FastAPI
import os
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import joblib
import pandas as pd

app = FastAPI(title="Car Price Predictor")

# Load data & preprocessors
df = pd.read_csv("Cleaned_data.csv")
model = joblib.load('model.joblib')
scaler = joblib.load('scaler.joblib')
ohe = joblib.load('ohe.joblib')
le = joblib.load('le.joblib')

# -------------------------------
# Input Schema
# -------------------------------
class Data(BaseModel):
    name: str = Field(..., description="name of the car")
    company: str = Field(..., description="company of the car")
    year: int = Field(..., description="Year of the car build")
    kms_driven: int = Field(..., description="how many km car driven")
    fuel_type: str = Field(..., description="fuel_type of the car")

    # Compute age dynamically (not as @computed_field, simpler)
    def get_age(self) -> int:
        return 2025 - self.year

# -------------------------------
# Routes
# -------------------------------


@app.get('/company')
def get_company():
    companies = df['company'].unique().tolist()
    return {'company': companies}

@app.get('/name/{company_name}')
def get_name(company_name: str):
    names = df[df['company'].str.lower() == company_name.lower()]['name'].unique().tolist()
    return {'company': company_name, 'name': names}

@app.get("/")
def read_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))


@app.post('/predict')
def predict(data: Data):
    # One-hot encode name + company
    encoded = ohe.transform([[data.name, data.company]])
    encoded_df = pd.DataFrame(encoded, columns=ohe.get_feature_names_out(["name", "company"]))

    # Label encode fuel_type
    fuel_encoded = le.transform([data.fuel_type])[0]
    fuel_df = pd.DataFrame([[fuel_encoded]], columns=["fuel_type_encded"])

    # Scale numeric features
    scaled = scaler.transform([[data.kms_driven, data.get_age()]])
    scaled_df = pd.DataFrame(scaled, columns=["kms_driven_scaled", "age_scaled"])

    # Final feature vector (keep same columns as training)
    final_features = pd.concat(
        [fuel_df, encoded_df, scaled_df],
        axis=1
    )

    # Prediction
    prediction = model.predict(final_features)[0]

    return JSONResponse(status_code=200, content={"Prediction": int(prediction)})
