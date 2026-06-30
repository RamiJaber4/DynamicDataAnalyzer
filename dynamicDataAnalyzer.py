
import pandas as pd
import json
import polars as pl
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(), 
        ]
    )
logger= logging.getLogger(__name__)

class DataAnalytics:
    def __init__(self, config_path: str):

        self.config_path= config_path
        with open(self.config_path, 'r') as file:
            self.config= json.load(file)
        self.df= None
        self.results_df= None
        
    def read_csv(self, path: str):
        df= pd.read_csv(path)
        return df

    def read_parquet(self, path: str):
        df= pl.read_parquet(path)
        df= df.to_pandas()
        return df
            
    def read_postgreSQL(self, conn_string, table_name):
        query= f'SELECT * FROM {table_name}'
        df= pl.read_database_uri(query= query, uri= conn_string)
        df=df.to_pandas()
        return df

    def load_data(self):
        logger.info("Starting the Analytics Console Application...")

        self.datasource= self.config['datasource']['type']
        conn_str_from_config = self.config['datasource'].get('connection_string')
        if conn_str_from_config == "ENV_DB_CONNECTION_STRING":
            load_dotenv()
            actual_env_conn = os.getenv("DB_CONNECTION_STRING")
            if not actual_env_conn:
                raise ValueError("Connection String not found in .env")
            
            self.config['datasource']['connection_string'] = actual_env_conn
            self.conn_str = actual_env_conn
        else:
            self.conn_str = conn_str_from_config
        self.tableName= self.config['datasource'].get('table_name')
        self.path_file= self.config['datasource'].get('path')

    
        if self.datasource == 'csv':
            self.df= self.read_csv(self.path_file)
            logger.info('The csv file uploaded succefully')
        elif self.datasource == 'parquet':
            self.df= self.read_parquet(self.path_file)
            logger.info('The parquet file uploaded succefully')

        elif self.datasource == 'postgresql':
            self.df= self.read_postgreSQL(self.conn_str, self.tableName)
            logger.info('The database uploaded succefully')

        else:
            logger.error('The datatype of the input not supported yet.')
            raise ValueError(f"Unsupported data source type: {self.datasource}")
            return

    def process_data(self):
        cols_list= self.config['statistics']['columns']

        results= {}
        for col in cols_list:
            col_name= col['name']
            metrics= col['metrics']
            results[col_name]= self.df[col_name].agg(metrics)

        self.results_df= pd.DataFrame(results)
        logger.info("The operations done.")

    

    def to_csv(self, df: pd.DataFrame, path: str, mode: str, options: dict):
        write_mode= 'a' if mode.lower() == 'append' else 'w'
        include_head= options.get('include_header', True)
        df.to_csv(path, index= False, mode= write_mode, header= include_head)
        logger.info(f'The output uploaded succefully in csv file with path {path}')


    def to_parquet(self, df: pd.DataFrame, path: str):
        df.to_parquet(path, index= False)
        logger.info(f'The output uploaded succefully in parquet file with path {path}')

    def to_json(self, df: pd.DataFrame):
        result= {
            col: df[col].dropna().to_dict()
            for col in df.columns
        }
        logger.info('The output uploaded succefully in json file ')
            
        return result
    def load_output(self):
        output_type= self.config['output']['type'].lower()
        output_path= self.config['output']['target_path'].lower()
        write_mode = self.config['output']['mode'].lower()
        options= self.config['output'].get('options', {})

        if output_type == 'csv':
            self.to_csv(self.results_df, output_path, write_mode, options)
        elif output_type == 'parquet':
            self.to_parquet(self.results_df, output_path)
        elif output_type == 'json':
            r= self.to_json(self.results_df)
            with open("output.json", "w") as json_file:
                json.dump(r, json_file, indent=4, default= str)
        else:
            logger.error(f'The file type {output_type} not supported')
            return
        logger.info("Process completed successfully.")




