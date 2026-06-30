from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dynamicDataAnalyzer import DataAnalytics
import os
import json
app= FastAPI()

class analyticsRequest(BaseModel):
    datasource: dict
    statistics: dict
    output: dict

@app.get('/')
def welcome():
    return{'status': 'running', 'msg': 'Welcome.'}

@app.post('/run-analytics')
def run_analytics(request_data: analyticsRequest):
    try:
        config_dict= request_data.model_dump()
        temp_config_path= 'temp_config.json'
        with open(temp_config_path, 'w') as file:
            json.dump(config_dict, file)

        analyzer= DataAnalytics(temp_config_path)
        analyzer.load_data()
        analyzer.process_data()
        
        results= analyzer.to_json(analyzer.results_df)

        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

        return {
            'status': 'success',
            'metric_results': results
        }

    except Exception as e:
        raise HTTPException(status_code= 500, detail=str(e))