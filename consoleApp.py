from dynamicDataAnalyzer import DataAnalytics
def main():
    obj= DataAnalytics('config.json')
    obj.load_data()
    obj.process_data()
    obj.load_output()
    
if __name__ == "__main__":
    main()