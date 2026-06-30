from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dynamicDataAnalyzer import DataAnalytics
import os
import json
import uuid
from time import sleep
app= FastAPI()

tasks_storage= {}

class analyticsRequest(BaseModel):
    datasource: dict
    statistics: dict
    output: dict

def background_worker(task_id: uuid, config_dict: dict):
    try:
        tasks_storage[task_id]= {'status' : 'Working', 'results': None}
        temp_config_path= 'temp_config.json'
        with open(temp_config_path, 'w') as file:
            json.dump(config_dict, file)

        analyzer= DataAnalytics(temp_config_path)
        analyzer.load_data()
        analyzer.process_data()
        sleep(30)
        
        results= analyzer.to_json(analyzer.results_df)

        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

        tasks_storage[task_id]= {'status': 'Completed', 'results': results}
    except Exception as e:
        tasks_storage[task_id]= {'status': 'Failed', 'error': str(e)}
@app.get('/')
def welcome():
    return{'status': 'running', 'msg': 'Welcome.'}

@app.post('/run-analytics')
def run_analytics(request_data: analyticsRequest,background_tasks: BackgroundTasks):

    config_dict= request_data.model_dump()
    task_id= str(uuid.uuid4())
    tasks_storage[task_id]={'status': 'Pending', 'results': None}
    background_tasks.add_task(background_worker, task_id, config_dict)
    return {
        'status': 'submitted',
        'msg': 'Analysis Started in the background, you can check status using task ID',
        'task_id': task_id
    }
@app.get('/check-task/{task_id}')
def check_task(task_id):
    task_info= tasks_storage[task_id]
    if task_info['status'] == 'Failed':
        return {
            'task_id': task_id,
            'status' : task_info['status'],
            'msg' : task_info.get('error')
        }
    elif task_info['status'] == 'Pending':
        return {
            'task_id': task_id,
            'status' : task_info['status'],
            'msg' : 'The task waits to run.'
        }
    elif task_info['status'] == 'Working':
        return {
            'task_id': task_id,
            'status' : task_info['status'],
            'msg' : 'The task is running.'
        }
    else:
        return{
            'task_id': task_id,
            'status': 'Completed',
            'results': task_info['results']

        }