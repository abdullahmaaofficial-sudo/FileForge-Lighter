import os

class WebTools:
    def __init__(self,paths,output_folder='temp'):
        self.multiple_paths = paths
        self.temp_folder = output_folder
        os.makedirs(self.temp_folder,exist_ok=True)

#Might add later 